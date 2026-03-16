"""
database.py — Supabase read/write operations for user profiles.
All user data is stored in the 'users' table with phone_number as the primary key.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("supabase_key")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_user(phone: str) -> dict | None:
    """Fetch a user profile by phone number. Returns dict or None."""
    response = supabase.table("Auto_bot").select("*").eq("phone_number", phone).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def save_user(phone: str, name: str, roll_number: str, section: str, branch: str, year: str, email: str = "") -> dict:
    """Insert a new user profile into Supabase."""
    data = {
        "phone_number": phone,
        "name": name,
        "roll_number": roll_number,
        "section": section,
        "branch": branch,
        "year": year,
        "email": email,
        "forms_filled": 0,
    }
    response = supabase.table("Auto_bot").insert(data).execute()
    return response.data[0] if response.data else data


def update_user(phone: str, name: str, roll_number: str, section: str, branch: str, year: str, email: str = "") -> dict:
    """Update an existing user profile."""
    data = {
        "name": name,
        "roll_number": roll_number,
        "section": section,
        "branch": branch,
        "year": year,
    }
    if email:
        data["email"] = email
    response = supabase.table("Auto_bot").update(data).eq("phone_number", phone).execute()
    return response.data[0] if response.data else data


def increment_forms_filled(phone: str) -> None:
    """Increment the forms_filled counter for a user after a successful submission."""
    user = get_user(phone)
    if user:
        current_count = user.get("forms_filled", 0)
        supabase.table("Auto_bot").update({"forms_filled": current_count + 1}).eq("phone_number", phone).execute()


def delete_user(phone: str) -> None:
    """Delete a user profile from Supabase."""
    supabase.table("Auto_bot").delete().eq("phone_number", phone).execute()
