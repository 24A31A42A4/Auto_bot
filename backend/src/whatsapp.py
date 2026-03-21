"""
whatsapp.py — Meta Cloud API outgoing message sender.
Sends WhatsApp messages via the Meta Graph API using httpx (async).
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("Acess_token")
PHONE_NUMBER_ID = os.getenv("phone_no_id")

GRAPH_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}


async def send_message(to_phone: str, text: str) -> dict:
    """
    Send a text message to a WhatsApp user via Meta Cloud API.

    Args:
        to_phone: Recipient phone number (e.g. '919876543210')
        text: Message body text

    Returns:
        API response as dict
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GRAPH_API_URL, headers=HEADERS, json=payload, timeout=30.0)
            data = response.json()
            if response.status_code != 200:
                print(f"❌ [whatsapp] Send failed! Status: {response.status_code}, Response: {data}")
            else:
                print(f"✅ [whatsapp] Message sent successfully to {to_phone}")
            return data
        except Exception as e:
            print(f"❌ [whatsapp] Error sending message: {e}")
            return {"error": str(e)}
async def send_button_message(to_phone: str, text: str, buttons: list[tuple[str, str]]) -> dict:
    """
    Send an interactive button message to a WhatsApp user.

    Args:
        to_phone: Recipient phone number
        text: Main body text above the buttons
        buttons: List of (id, title) tuples for the buttons (max 3)

    Returns:
        API response
    """
    button_payloads = []
    for btn_id, btn_title in buttons[:3]:  # WhatsApp limit is 3 buttons
        button_payloads.append({
            "type": "reply",
            "reply": {
                "id": btn_id,
                "title": btn_title
            }
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": button_payloads}
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GRAPH_API_URL, headers=HEADERS, json=payload, timeout=30.0)
            data = response.json()
            if response.status_code != 200:
                print(f"❌ [whatsapp] Button send failed! Status: {response.status_code}, Response: {data}")
            else:
                print(f"✅ [whatsapp] Button message sent to {to_phone}")
            return data
        except Exception as e:
            print(f"❌ [whatsapp] Error sending button message: {e}")
            return {"error": str(e)}
