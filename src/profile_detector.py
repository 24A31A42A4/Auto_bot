"""
profile_detector.py — Personal field keyword matching.
Checks each question text against keyword lists to decide whether to fill
from the user profile or send to Gemini AI.
"""

# Keyword mappings: if the question text contains any of these keywords,
# the corresponding profile field is used instead of Gemini AI.
KEYWORD_MAP = {
    "name": {
        "keywords": ["name", "your name", "full name", "student name", "name of the student", "participant name", "candidate name"],
        "profile_field": "name",
    },
    "roll_number": {
        "keywords": ["roll", "register number", "regd", "roll number", "registration number", "reg.no", "reg no", "id number", "hall ticket", "ht number", "pin"],
        "profile_field": "roll_number",
    },
    "section": {
        "keywords": ["section", "sec", "class section", "college", "institution", "university", "institute"],
        "profile_field": "section",
    },
    "branch": {
        "keywords": ["branch", "dept", "department", "stream", "course", "specialization", "discipline"],
        "profile_field": "branch",
    },
    "year": {
        "keywords": ["year", "yr", "semester", "sem", "academic year"],
        "profile_field": "year",
    },
    "email": {
        "keywords": ["email", "mail", "gmail", "email address"],
        "profile_field": "email",
    },
    "phone": {
        "keywords": ["phone", "mobile", "contact", "whatsapp"],
        "profile_field": "phone_number",
    },
}


def detect_personal_field(question_text: str) -> str | None:
    """
    Check if a question is asking for personal information.
    """
    question_lower = question_text.lower().strip()
    
    # Debug print to see what we are comparing
    # print(f"[profile_detector] Checking question: '{question_lower}'")

    for field, info in KEYWORD_MAP.items():
        for keyword in info["keywords"]:
            # Simple substring match
            if keyword in question_lower:
                # To be sure it's not a partial match of another word, 
                # we check if it's a whole word or significant enough
                # E.g., 'name' shouldn't match 'exam' (if we weren't stripping)
                print(f"[profile_detector] ✅ MATCH: '{question_lower}' matched keyword '{keyword}' -> field '{info['profile_field']}'")
                return info["profile_field"]

    return None


def get_profile_value(profile: dict, field_name: str) -> str:
    """
    Get the value of a profile field.

    Args:
        profile: User profile dict from Supabase
        field_name: The field name to look up (e.g. 'name', 'roll_number')

    Returns:
        The profile value as string, or empty string if not found
    """
    return str(profile.get(field_name, ""))
