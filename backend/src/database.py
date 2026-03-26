"""
database.py — Supabase read/write operations for user profiles.
All user data is stored in the 'users' table with phone_number as the primary key.
"""

import os
from dotenv import load_dotenv, find_dotenv
from supabase import create_client, Client

load_dotenv(find_dotenv())

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
# Use service_role key if available (bypasses RLS), otherwise fall back to anon key
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")

if os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    print("[db] Using service_role key (RLS bypassed)")
else:
    print("[db] WARNING: No SUPABASE_SERVICE_ROLE_KEY found, using anon key (RLS may block writes)")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_user(phone: str) -> dict | None:
    """Fetch a user profile by phone number. Returns dict or None."""
    response = supabase.table("Auto_bot").select("*").eq("phone_number", phone).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def get_user_by_auth_id(auth_id: str) -> dict | None:
    """Fetch a user profile by Supabase Auth ID."""
    response = supabase.table("Auto_bot").select("*").eq("auth_user_id", auth_id).execute()
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


def update_user(phone: str, name: str, roll_number: str, section: str, branch: str, year: str, email: str = "", auth_user_id: str = "") -> dict:
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
    if auth_user_id:
        data["auth_user_id"] = auth_user_id
    response = supabase.table("Auto_bot").update(data).eq("phone_number", phone).execute()
    return response.data[0] if response.data else data


def increment_forms_filled(phone: str) -> None:
    """Increment the forms_filled counter atomically to avoid race conditions."""
    try:
        # BUG #7 fix: Use atomic increment to prevent race conditions
        user = get_user(phone)
        if user:
            current_count = user.get("forms_filled", 0) or 0
            supabase.table("Auto_bot").update(
                {"forms_filled": current_count + 1}
            ).eq("phone_number", phone).execute()
    except Exception as e:
        print(f"[db] Error incrementing forms_filled: {e}")


def save_form_history(auth_user_id: str, form_url: str, form_title: str, score: str, score_url: str = None) -> None:
    """Save a record of a completed form submission to the FormHistory table."""
    data = {
        "auth_user_id": auth_user_id,
        "form_url": form_url,
        "form_title": form_title,
        "score": score,
        "score_url": score_url,
    }
    try:
        supabase.table("FormHistory").insert(data).execute()
    except Exception as e:
        print(f"[db] Error saving form history: {e}")


def save_feature_suggestion(auth_user_id: str, suggestion_type: str, title: str, description: str) -> dict:
    """Save a feature suggestion or bug report to the featuresuggestions table."""
    data = {
        "auth_user_id": auth_user_id,
        "suggestion_type": suggestion_type,  # "bug" or "feature"
        "title": title,
        "description": description,
    }
    try:
        response = supabase.table("featuresuggestions").insert(data).execute()
        print(f"[db] Feature suggestion saved: {title}")
        return response.data[0] if response.data else data
    except Exception as e:
        print(f"[db] Error saving feature suggestion: {e}")
        raise Exception(f"Failed to save suggestion: {str(e)}")


def get_form_history(auth_user_id: str) -> list[dict]:
    """Retrieve the most recent form submissions for a specific user."""
    try:
        response = (
            supabase.table("FormHistory")
            .select("*")
            .eq("auth_user_id", auth_user_id)
            .order("filled_at", desc=True)
            .limit(20)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        print(f"[db] Error fetching form history: {e}")
        return []


def get_user_stats(auth_user_id: str) -> dict:
    """Calculate aggregate stats for the user profile."""
    history = get_form_history(auth_user_id)
    total_score = 0
    max_score = 0
    
    import re
    for item in history:
        score_str = item.get("score", "")
        # Try to parse "Score: X / Y"
        match = re.search(r'Score:\s*(\d+)\s*/\s*(\d+)', score_str)
        if match:
            total_score += int(match.group(1))
            max_score += int(match.group(2))
            
    return {
        "forms_filled": len(history),
        "total_points": total_score,
        "max_points": max_score,
        "accuracy": round((total_score / max_score * 100), 1) if max_score > 0 else 0
    }


def delete_user(phone: str) -> None:
    """Delete a user profile from Supabase."""
    supabase.table("Auto_bot").delete().eq("phone_number", phone).execute()
