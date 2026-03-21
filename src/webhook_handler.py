"""
webhook_handler.py — The brain of the bot.
Handles all incoming WhatsApp message routing logic.
Parses Meta webhook payload, validates links, checks profiles,
triggers form automation, and sends replies.
"""

import re
from src.database import get_user, save_user, update_user, increment_forms_filled, delete_user
from src.whatsapp import send_message, send_button_message
from src.form_bot import fill_form


def is_google_form_link(text: str) -> str | None:
    """
    Check if the message contains a Google Form link.
    Returns the URL if found, None otherwise.
    """
    # Match forms.gle short links and docs.google.com/forms links
    patterns = [
        r'(https?://forms\.gle/\S+)',
        r'(https?://docs\.google\.com/forms/\S+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def is_update_command(text: str) -> bool:
    """Check if the message is a profile update command."""
    return text.strip().upper().startswith("UPDATE")


def parse_registration_data(text: str) -> dict | None:
    """
    Parse pipe-separated registration data from user message.
    Expected format: NAME | ROLL NUMBER | SECTION | BRANCH | YEAR | EMAIL

    Returns dict with parsed fields or None if parsing fails.
    """
    # Remove "UPDATE" prefix if present
    clean_text = text.strip()
    if clean_text.upper().startswith("UPDATE"):
        clean_text = clean_text[6:].strip()

    parts = [p.strip() for p in clean_text.split("|")]

    if len(parts) < 5:
        return None

    data = {
        "name": parts[0],
        "roll_number": parts[1],
        "section": parts[2],
        "branch": parts[3],
        "year": parts[4],
    }

    if len(parts) >= 6 and parts[5]:
        data["email"] = parts[5]

    return data


async def process_message(phone: str, message_text: str) -> None:
    """
    Main message processing function. Called as a background task from FastAPI.

    Args:
        phone: Sender's WhatsApp phone number
        message_text: The full message text
    """
    text = message_text.strip()

    # ─── Case 1: PROFILE Management (Text Commands + Buttons) ───
    if is_update_command(text) or text == "update_profile":
        if is_update_command(text):
            data = parse_registration_data(text)
            if data:
                update_user(
                    phone=phone,
                    name=data["name"],
                    roll_number=data["roll_number"],
                    section=data["section"],
                    branch=data["branch"],
                    year=data["year"],
                    email=data.get("email", ""),
                )
                await send_message(phone, "✅ Profile updated successfully!")
                return
        
        # If it was just the button click or parsing failed, send instructions
        await send_message(
            phone,
            "📝 *How to Update Your Profile*\n\n"
            "Send a message in this format:\n"
            "UPDATE\n"
            "NAME | ROLL NUMBER | SECTION | BRANCH | YEAR | EMAIL"
        )
        return

    if text == "delete_profile":
        await send_button_message(
            phone,
            "⚠️ *Confirm Deletion*\n\n"
            "Are you sure you want to delete your profile? This will remove all your saved data.",
            [("confirm_delete", "Yes, Delete"), ("cancel_delete", "No, Cancel")]
        )
        return

    if text == "confirm_delete":
        delete_user(phone)
        await send_message(phone, "🗑️ Your profile has been deleted. Send 'Hi' anytime to register again!")
        return

    if text == "cancel_delete":
        await send_message(phone, "✅ Deletion cancelled. Your profile is safe!")
        return

    # ─── Case 2: Google Form link ───
    form_url = is_google_form_link(text)
    if form_url:
        user = get_user(phone)

        if not user:
            # New user — send registration instructions
            await send_button_message(
                phone,
                "👋 Hi! I'm AutoForm Bot. I need your details once to fill forms for you.\n\n"
                "Please send them in this format:\n"
                "*NAME | ROLL NUMBER | SECTION | BRANCH | YEAR | EMAIL*\n\n"
                "Example:\n"
                "vijay | 24A31A42A4 | A | CSE | 2028 | vijay@gmail.com",
                [("help_registration", "How to Register?")]
            )
            return

        # Existing user — process the form
        await send_message(phone, f"⏳ Got it {user['name']}! Filling your form...")

        try:
            result = await fill_form(form_url, user)
            increment_forms_filled(phone)
            await send_button_message(
                phone, 
                f"✅ Done! {result}",
                [("fill_another", "Fill Another Form"), ("help", "Get Help")]
            )
        except Exception as e:
            print(f"[webhook_handler] Form filling error: {e}")
            await send_message(phone, f"❌ Error filling form: {str(e)}\n\nPlease try again.")

        return

    # ─── Case 3: Registration data (pipe-separated) ───
    if "|" in text:
        data = parse_registration_data(text)
        if data:
            existing = get_user(phone)
            if existing:
                await send_message(phone, "ℹ️ You already have a profile. To update, send:\n\nUPDATE\nNAME | ROLL NUMBER | SECTION | BRANCH | YEAR | EMAIL")
                return

            save_user(
                phone=phone,
                name=data["name"],
                roll_number=data["roll_number"],
                section=data["section"],
                branch=data["branch"],
                year=data["year"],
                email=data.get("email", ""),
            )
            await send_button_message(
                phone,
                f"✅ Profile saved, {data['name']}!\n\n"
                "Now just forward me any Google Form link and I'll fill it for you in 30 seconds 🚀",
                [("help", "How it works?"), ("example", "See Example")]
            )
            return

    if text == "help":
        await send_message(
            phone,
            "🚀 *AutoForm Bot Capabilities*\n\n"
            "- 🛡️ *Privacy*: Your data is stored securely in Supabase.\n"
            "- ⚡ *Speed*: Forms filled in ~30 seconds.\n"
            "- 🎯 *Accuracy*: 100% correct personal details using your profile.\n"
            "- 🤖 *AI Brain*: Advanced expert reasoning for specialized questions.\n\n"
            "Just forward any Google Form link to get started!"
        )
        return

    if text == "example":
        await send_message(
            phone,
            "📝 *Example Profile Format*\n\n"
            "vijay | 24A31A42A4 | A | CSE | 2028 | vijay@gmail.com"
        )
        return

    if text == "help_registration":
        await send_message(
            phone,
            "👋 *How to Register*\n\n"
            "Simply send your details separated by pipes (|):\n\n"
            "NAME | ROLL | SECTION | BRANCH | YEAR | EMAIL\n\n"
            "Example: vijay | 24A31A42A4 | A | CSE | 2028 | vijay@gmail.com"
        )
        return

    if text == "fill_another":
        await send_message(phone, "🚀 Ready! Just forward me any Google Form link.")
        return

    # ─── Case 4: Casual chat — reply using Gemini AI ───
    user = get_user(phone)
    if user:
        # If registered, send a menu along with the AI reply
        user_name = user["name"]
        reply = generate_chat_reply(text, user_name)
        await send_button_message(
            phone,
            reply,
            [("update_profile", "Update Profile"), ("delete_profile", "Delete Profile"), ("help", "Capabilities")]
        )
    else:
        # If new, just do standard AI reply (which will ask for registration)
        reply = generate_chat_reply(text, "there")
        await send_message(phone, reply)


def generate_chat_reply(user_message: str, user_name: str) -> str:
    """
    Use Gemini AI to generate a friendly, conversational reply.
    """
    from google import genai
    import os
    from dotenv import load_dotenv

    load_dotenv()
    client = genai.Client(api_key=os.getenv("gemini_api_key"))
    
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ]
    
    prompt = f"""You are AutoForm Bot, a friendly WhatsApp bot that helps college students 
auto-fill Google Forms using AI. You're chatty, helpful, and use emojis.

The user's name is {user_name}. They sent you this message: "{user_message}"

Reply in a friendly, conversational way (max 3 sentences). Be warm and natural.
Use emojis naturally.

IF USER IS NEW (name is 'there'):
1. Greet them and introduce yourself briefly.
2. Tell them you can fill Google Forms automatically in seconds.
3. You MUST ask them to register first by sending their details in this EXACT format:
   NAME | ROLL NUMBER | SECTION | BRANCH | YEAR | EMAIL
   Example: vijay | 24A31A42A4 | A | CSE | 2028 | vijay@gmail.com
IF USER IS REGISTERED (name is NOT 'there'):
1. Greet them by name: {user_name}.
2. If they are just chatting, reply normally but subtly remind them they can forward any Google Form link to you.
3. DO NOT ask for their registration details again.

General Capabilities (explain if asked):
- Forward any Google Form link
- Forms filled in ~30 seconds using AI
- Get score/confirmation immediately"""

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                print(f"[webhook_handler] Model {model_name} rate limited, trying next...")
                continue
            else:
                print(f"[webhook_handler] Chat reply error with {model_name}: {e}")
                continue

    # Final fallback if all models fail
    return (
        f"👋 Hey {user_name}! I'm AutoForm Bot 🤖\n\n"
        "I can auto-fill Google Forms for you!\n"
        "Just forward me any Google Form link and I'll handle the rest in 30 seconds 🚀"
    )

