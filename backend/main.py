"""
main.py — FastAPI entry point for AutoForm Bot.
Defines all routes: webhook verification, message handling, user profile CRUD, and health check.
"""
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

from fastapi.middleware.cors import CORSMiddleware
from src.webhook_handler import process_message
from src.database import get_user, save_user, update_user, get_user_by_auth_id, increment_forms_filled, save_form_history, get_form_history
from src.form_bot import fill_form

app = FastAPI(title="AutoForm Bot", description="WhatsApp bot that auto-fills Google Forms using AI")

# CORS middleware for React frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Verify token for Meta webhook setup (you can set any string)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "autoform_bot_verify_token")

# Global store for bot progress (in-memory for now)
# Structure: { auth_id: { "logs": [], "result": None, "active": False } }
bot_status = {}


# ─── Webhook Endpoints ───────────────────────────────────────────────


@app.get("/webhook")
async def webhook_verify(request: Request):
    """
    Meta webhook verification endpoint.
    Called once during webhook setup — responds to the hub.challenge.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("[webhook] ✅ Webhook verified successfully")
        return PlainTextResponse(content=challenge, status_code=200)

    print("[webhook] ❌ Webhook verification failed")
    return PlainTextResponse(content="Forbidden", status_code=403)


@app.post("/webhook")
async def webhook_receive(request: Request, background_tasks: BackgroundTasks):
    """
    Receives incoming WhatsApp messages from Meta Cloud API.
    Immediately returns 200, then processes the message in the background.
    """
    body = await request.json()

    try:
        # Extract message data from Meta's webhook payload
        entry = body.get("entry", [])
        if not entry:
            return {"status": "no entry"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "no changes"}

        value = changes[0].get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "no messages"}

        # Get the first message
        message = messages[0]
        phone = message.get("from", "")
        message_text = ""

        # Handle different message types
        msg_type = message.get("type", "")
        if msg_type == "text":
            message_text = message.get("text", {}).get("body", "")
        elif msg_type == "interactive":
            # Handle interactive messages (buttons, etc.)
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                # Prioritize button ID for logic, title as fallback
                message_text = interactive.get("button_reply", {}).get("id", "")
                if not message_text:
                    message_text = interactive.get("button_reply", {}).get("title", "")

        if phone and message_text:
            # Process message in background so we can return 200 immediately
            background_tasks.add_task(process_message, phone, message_text)

    except Exception as e:
        print(f"[webhook] Error parsing webhook: {e}")

    # Always return 200 to Meta to prevent retries
    return {"status": "received"}


# ─── User Profile Endpoints ──────────────────────────────────────────


class UserProfile(BaseModel):
    phone_number: str
    name: str
    roll_number: str
    section: str
    branch: str
    year: str
    email: str = ""


@app.post("/user/save")
async def save_user_profile(profile: UserProfile):
    """Save a new user profile to Supabase."""
    existing = get_user(profile.phone_number)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists. Use PUT /user/update to update.")

    result = save_user(
        phone=profile.phone_number,
        name=profile.name,
        roll_number=profile.roll_number,
        section=profile.section,
        branch=profile.branch,
        year=profile.year,
        email=profile.email,
    )
    return {"status": "saved", "user": result}


@app.put("/user/update")
async def update_user_profile(profile: UserProfile):
    """Update an existing user profile."""
    existing = get_user(profile.phone_number)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found. Use POST /user/save first.")

    result = update_user(
        phone=profile.phone_number,
        name=profile.name,
        roll_number=profile.roll_number,
        section=profile.section,
        branch=profile.branch,
        year=profile.year,
        email=profile.email,
    )
    return {"status": "updated", "user": result}


@app.get("/user/{phone}")
async def get_user_profile(phone: str):
    """Check if a user profile exists by phone number."""
    user = get_user(phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "found", "user": user}


# ─── Health Check ─────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint for Render uptime monitoring."""
    return {"status": "ok", "service": "AutoForm Bot"}


class FormRequest(BaseModel):
    url: str

@app.post("/api/fill-form")
async def api_fill_form(request: Request, form_req: FormRequest, background_tasks: BackgroundTasks):
    # Simple auth: Header "Authorization: Bearer <auth_id>"
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    auth_id = auth_header.split(" ")[1]
    user_profile = get_user_by_auth_id(auth_id)
    
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please complete registration.")

    # Initialize status for this user
    bot_status[auth_id] = {
        "logs": ["Job started..."],
        "result": None,
        "active": True
    }

    def status_callback(msg: str):
        if auth_id in bot_status:
            bot_status[auth_id]["logs"].append(msg)

    async def run_fill_task():
        try:
            full_result = await fill_form(form_req.url, user_profile, status_callback=status_callback)
            score = full_result["score"]
            title = full_result["title"]
            score_url = full_result.get("score_url")
            
            bot_status[auth_id]["result"] = {
                "score": score,
                "score_url": score_url,
                "title": title
            }
            bot_status[auth_id]["active"] = False
            
            # Save to history with score URL
            save_form_history(auth_id, form_req.url, title, score, score_url=score_url)
            
            # If successful, increment counter
            if "Score:" in score or "successfully" in score:
                increment_forms_filled(user_profile["phone_number"])
        except Exception as e:
            bot_status[auth_id]["logs"].append(f"Error: {str(e)}")
            bot_status[auth_id]["active"] = False

    background_tasks.add_task(run_fill_task)
    return {"message": "Form filling started", "auth_id": auth_id}

@app.get("/api/status/{auth_id}")
async def get_bot_status(auth_id: str):
    if auth_id not in bot_status:
        return {"logs": [], "result": None, "active": False}
    return bot_status[auth_id]

@app.get("/api/history/{auth_id}")
async def get_history(auth_id: str):
    history = get_form_history(auth_id)
    return history


@app.get("/api/stats/{auth_id}")
async def get_stats(auth_id: str):
    from src.database import get_user_stats
    stats = get_user_stats(auth_id)
    return stats
