"""
profile_detector.py — Personal field keyword matching.
Checks each question text against keyword lists to decide whether to fill
from the user profile or send to Gemini AI.

Uses word-boundary matching, length checks, and quiz-indicator filtering
to prevent quiz questions (e.g. math word problems containing "year") from
matching as personal fields.
"""

import re

# Keywords that indicate a question is a quiz/academic question, NOT a personal field.
QUIZ_INDICATORS = [
    "what is the", "what is a", "what is an", "what are the", "what was", "what were",
    "explain", "define", "describe", "how many", "how much", "how does",
    "how is", "how are", "how do", "why is", "why are", "why does",
    "calculate", "find the", "solve", "compute", "evaluate", "value of",
    "identify", "list the", "mention", "state the",
    "true or false", "select the", "choose the",
    "name the", "name a", "name any", "name two", "name three",
    "give an example", "write a program", "what type",
    "if the", "then find", "depreciates", "statements:", "following:",
    "pointing to", "sum of", "ratio", "percentage", "arithmetic progression",
    "each year", "in 3 years", "end of", "beginning of",
]

# Keyword mappings: order matters — check specific fields like roll_number/section/college before bare name
KEYWORD_MAP = {
    "roll_number": {
        "keywords": [
            r"\broll\s*(?:no|number|num)\b", r"\broll\b",
            r"\bregister\s*(?:no|number)\b", r"\bregistration\s*(?:no|number)\b",
            r"\bregd\b", r"\breg(?:\.|\s)*no\b", r"\breg\.\s+no\b", r"\brno\b",
            r"\bid\s*number\b", r"\bhall\s*ticket\b", r"\bht\s*(?:no|number)\b",
        ],
        "profile_field": "roll_number",
    },
    "section": {
        "keywords": [
            r"\bcollege\s+name\b", r"\bname\s+of\s+the\s+institution\b",
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
    "name": {
        "keywords": [
            r"\byour\s+name\b", r"\bfull\s+name\b", r"\bstudent\s+name\b",
            r"\bname\s+of\s+the\s+student\b", r"\bparticipant\s+name\b",
            r"\bcandidate\s+name\b", r"\benter\s+name\b", r"\bname\b",
        ],
        "profile_field": "name",
    },
}


def detect_personal_field(question_text: str) -> str | None:
    """
    Check if a question is asking for personal information.
    Uses length thresholds, word-boundary regex, and quiz-indicator filtering
    to avoid false positives on academic quiz questions.
    """
    question_lower = question_text.lower().strip()

    # 1. Long questions (>45 chars) with question numbering, question mark or problem phrases are quiz items
    if len(question_lower) > 45:
        if re.search(r'^\d+[\.\)]', question_lower) or '?' in question_lower or re.search(r'\b(if|then|find|value|total|sum|count|each|per|number of|depreciates)\b', question_lower):
            return None

    # 2. Check quiz indicators
    for indicator in QUIZ_INDICATORS:
        if indicator in question_lower:
            return None

    # 3. Match against keyword patterns (word-boundary aware)
    for field, info in KEYWORD_MAP.items():
        for pattern in info["keywords"]:
            if re.search(pattern, question_lower):
                # Extra safety: bare "year", "section", "branch", "roll" must not match long text > 35 chars
                if pattern in (r"\byear\b", r"\bsection\b", r"\bbranch\b", r"\broll\b") and len(question_lower) > 35:
                    continue
                print(f"[profile_detector] MATCH: '{question_lower[:40]}...' matched pattern '{pattern}' -> field '{info['profile_field']}'")
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
