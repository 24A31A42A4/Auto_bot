"""
main.py — FastAPI entry point for AutoForm Bot.
Defines all routes: webhook verification, message handling, user profile CRUD, and health check.
"""
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import os
import sys

# Vercel Playwright Support
if os.getenv("VERCEL"):
    try:
        import vercel_playwright
        vercel_playwright.install()
    except ImportError:
        pass

load_dotenv(find_dotenv())

from fastapi.middleware.cors import CORSMiddleware
from src.webhook_handler import process_message
from src.database import get_user, save_user, update_user, get_user_by_auth_id, increment_forms_filled, save_form_history, get_form_history, save_feature_suggestion
from src.form_bot import fill_form

app = FastAPI(
    title="AutoForm Bot", 
    description="WhatsApp bot that auto-fills Google Forms using AI",
    root_path="/_/backend"
)

# CORS middleware for React frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
# Handle potential list of origins if provided as comma-separated string
origins = [o.strip() for o in FRONTEND_URL.split(",") if o.strip()]
if "http://localhost:5173" not in origins:
    origins.append("http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use wildcard for now to guarantee connectivity on Railway
    allow_credentials=False, # Credentials (cookies) not needed for Bearer auth
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


# ─── Profile Endpoints (by auth_user_id — used by frontend) ──────────


class ProfileUpdate(BaseModel):
    name: str
    email: str = ""
    roll_number: str
    section: str
    branch: str
    year: str


@app.get("/profile/{auth_id}")
async def get_profile_by_auth(auth_id: str):
    """Fetch a user profile by Supabase Auth ID. Used by frontend Profile page."""
    user = get_user_by_auth_id(auth_id)
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")
    return user


@app.put("/profile/{auth_id}")
async def update_profile_by_auth(auth_id: str, profile: ProfileUpdate):
    """Update a user profile by auth_user_id. Bypasses RLS by going through backend."""
    from src.database import supabase as db_client

    # Verify user exists
    existing = get_user_by_auth_id(auth_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Profile not found")

    update_data = {
        "name": profile.name,
        "email": profile.email,
        "roll_number": profile.roll_number,
        "section": profile.section,
        "branch": profile.branch,
        "year": profile.year,
    }

    response = db_client.table("Auto_bot").update(update_data).eq("auth_user_id", auth_id).execute()

    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=500, detail="Update failed — no rows modified")

    return {"status": "updated", "user": response.data[0]}


# ─── Health Check ─────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint for Render uptime monitoring."""
    return {"status": "ok", "service": "AutoForm Bot"}


class FormRequest(BaseModel):
    url: str

@app.post("/fill-form")
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

    def run_fill_in_thread():
        """Run Playwright in a separate thread with its own event loop (Windows fix)."""
        import asyncio as _asyncio
        import io as _io
        import sys as _sys
        
        # Windows: ProactorEventLoop is the ONLY loop type that supports subprocesses
        if sys.platform == "win32":
            loop = _asyncio.ProactorEventLoop()
        else:
            loop = _asyncio.new_event_loop()
        _asyncio.set_event_loop(loop)
        
        try:
            # Create a custom stream that duplicates to both stdout and status_callback
            class DuplicateStream:
                def __init__(self, original_stream, callback):
                    self.original = original_stream
                    self.callback = callback
                    self.buffer = ""
                
                def write(self, msg):
                    self.original.write(msg)  # Print to terminal
                    if msg and msg.strip():  # Only send non-empty lines to callback
                        self.buffer += msg
                        if '\n' in msg:
                            for line in self.buffer.split('\n'):
                                if line.strip():
                                    self.callback(line)
                            self.buffer = ""
                
                def flush(self):
                    self.original.flush()
            
            # Redirect stdout to capture and duplicate
            original_stdout = _sys.stdout
            _sys.stdout = DuplicateStream(original_stdout, status_callback)
            
            try:
                full_result = loop.run_until_complete(
                    fill_form(form_req.url, user_profile, status_callback=status_callback)
                )
            finally:
                _sys.stdout = original_stdout
            
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
        finally:
            loop.close()

    # Run in a separate thread so Playwright gets its own event loop
    import threading
    thread = threading.Thread(target=run_fill_in_thread, daemon=True)
    thread.start()
    
    return {"message": "Form filling started", "auth_id": auth_id}

@app.get("/status/{auth_id}")
async def get_bot_status(auth_id: str):
    if auth_id not in bot_status:
        return {"logs": [], "result": None, "active": False}
    return bot_status[auth_id]

@app.get("/history/{auth_id}")
async def get_history(auth_id: str):
    history = get_form_history(auth_id)
    return history


@app.get("/stats/{auth_id}")
async def get_stats(auth_id: str):
    from src.database import get_user_stats
    stats = get_user_stats(auth_id)
    return stats


# ─── Feature Suggestion Endpoint ──────────────────────────────────

class FeatureSuggestion(BaseModel):
    suggestion_type: str  # "bug" or "feature"
    title: str
    description: str


@app.post("/suggest")
async def submit_suggestion(request: Request, suggestion: FeatureSuggestion):
    """Submit a feature suggestion or bug report."""
    # Get auth_id from header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    auth_id = auth_header.split(" ")[1]
    
    # Validate inputs
    if suggestion.suggestion_type not in ["bug", "feature"]:
        raise HTTPException(status_code=400, detail="suggestion_type must be 'bug' or 'feature'")
    
    if not suggestion.title or len(suggestion.title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    if not suggestion.description or len(suggestion.description.strip()) == 0:
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    
    try:
        result = save_feature_suggestion(
            auth_user_id=auth_id,
            suggestion_type=suggestion.suggestion_type,
            title=suggestion.title,
            description=suggestion.description
        )
        return {
            "status": "success",
            "message": f"Thank you! Your {suggestion.suggestion_type} report has been saved.",
            "id": result.get("id") if isinstance(result, dict) else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving suggestion: {str(e)}")
