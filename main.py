"""
main.py — FastAPI entry point for AutoForm Bot.
Defines all routes: webhook verification, message handling, user profile CRUD, and health check.
"""

import os
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.webhook_handler import process_message
from src.database import get_user, save_user, update_user

app = FastAPI(title="AutoForm Bot", description="WhatsApp bot that auto-fills Google Forms using AI")

# Verify token for Meta webhook setup (you can set any string)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "autoform_bot_verify_token")


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
