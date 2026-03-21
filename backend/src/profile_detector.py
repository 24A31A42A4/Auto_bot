"""
profile_detector.py — Personal field keyword matching.
Checks each question text against keyword lists to decide whether to fill
from the user profile or send to Gemini AI.

Uses word-boundary matching to avoid false positives (e.g. "Name the capital"
should NOT match as a personal "name" field).
"""

import re

# Keywords that indicate a question is a quiz/academic question, NOT a personal field.
# If any of these appear in the question, skip personal field detection.
QUIZ_INDICATORS = [
    "which", "what is the", "what are the", "what was", "what were",
    "explain", "define", "describe", "how many", "how much", "how does",
    "how is", "how are", "how do", "why is", "why are", "why does",
    "calculate", "find the", "solve", "compute", "evaluate",
    "identify", "list the", "mention", "state the",
    "true or false", "select the", "choose the",
    "name the", "name a", "name any", "name two", "name three",
    "give an example", "write a program", "what type",
]

# Keyword mappings: if the question text contains any of these keywords
# as whole words, the corresponding profile field is used instead of Gemini AI.
KEYWORD_MAP = {
    "name": {
        "keywords": [
            r"\byour\s+name\b", r"\bfull\s+name\b", r"\bstudent\s+name\b",
            r"\bname\s+of\s+the\s+student\b", r"\bparticipant\s+name\b",
            r"\bcandidate\s+name\b", r"\benter\s+name\b",
        ],
        "profile_field": "name",
    },
    "roll_number": {
        "keywords": [
            r"\broll\s*(?:no|number|num)\b", r"\broll\b",
            r"\bregister\s*(?:no|number)\b", r"\bregistration\s*(?:no|number)\b",
            r"\bregd\b", r"\breg\.?\s*no\b",
            r"\bid\s*number\b", r"\bhall\s*ticket\b", r"\bht\s*(?:no|number)\b",
        ],
        "profile_field": "roll_number",
    },
    "section": {
        "keywords": [
            r"\bsection\b", r"\bclass\s+section\b",
            r"\bcollege\b", r"\binstitution\b", r"\buniversity\b", r"\binstitute\b",
        ],
        "profile_field": "section",
    },
    "branch": {
        "keywords": [
            r"\bbranch\b", r"\bdepartment\b", r"\bdept\b",
            r"\bstream\b", r"\bcourse\b", r"\bspeciali[sz]ation\b", r"\bdiscipline\b",
        ],
        "profile_field": "branch",
    },
    "year": {
        "keywords": [
            r"\byear\s+of\s+study\b", r"\bcurrent\s+year\b", r"\bacademic\s+year\b",
            r"\bsemester\b", r"\bsem\b", r"\byear\b",
        ],
        "profile_field": "year",
    },
    "email": {
        "keywords": [
            r"\bemail\b", r"\bmail\s*id\b", r"\bgmail\b", r"\bemail\s*address\b",
        ],
        "profile_field": "email",
    },
    "phone": {
        "keywords": [
            r"\bphone\b", r"\bmobile\b", r"\bwhatsapp\b",
        ],
        "profile_field": "phone_number",
    },
}


def detect_personal_field(question_text: str) -> str | None:
    """
    Check if a question is asking for personal information.
    Uses word-boundary regex matching and quiz-indicator filtering
    to avoid false positives.
    """
    question_lower = question_text.lower().strip()

    # First check: if the question looks like a quiz/academic question, skip detection
    for indicator in QUIZ_INDICATORS:
        if indicator in question_lower:
            return None

    # Second check: match against keyword patterns (word-boundary aware)
    for field, info in KEYWORD_MAP.items():
        for pattern in info["keywords"]:
            if re.search(pattern, question_lower):
                print(f"[profile_detector] ✅ MATCH: '{question_lower}' matched pattern '{pattern}' -> field '{info['profile_field']}'")
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
