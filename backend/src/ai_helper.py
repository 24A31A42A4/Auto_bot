import os
import json
import re
import time
from google import genai
from google.genai import types
from openai import OpenAI  # For Deepseek API (OpenAI-compatible)
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def get_client():
    return genai.Client(api_key=os.getenv("gemini_api_key"))

def get_deepseek_client():
    """Get Deepseek client using OpenAI-compatible API."""
    api_key = os.getenv("deepseek_api_key")
    if not api_key:
        print("[ai_helper] ⚠️ deepseek_api_key not configured in .env")
        return None
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# Models to try in order of preference (verified March 2026 Gemini models)
MODELS_TO_TRY = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

# Deepseek models
DEEPSEEK_MODELS = ["deepseek-chat"]

# How many times to retry a rate-limited model before moving to next
RATE_LIMIT_RETRIES = 5
RATE_LIMIT_DELAY = 5  # seconds to wait before retrying


def answer_questions(questions: list[dict], user_profile: dict = None, form_title: str = "") -> list[str]:
    """
    Send a batch of quiz questions to Gemini (with Deepseek fallback) and get answers.
    """
    if not questions:
        return []

    # Build the prompt
    profile_context = ""
    if user_profile:
        profile_context = f"\nUSER CONTEXT (Use these ONLY for personal/identity questions like 'What is your name?'):\n"
        for k, v in user_profile.items():
            profile_context += f"- {k.replace('_', ' ').title()}: {v}\n"

    form_context = ""
    if form_title:
        form_context = f"\nFORM/QUIZ CONTEXT: This quiz is titled \"{form_title}\". Use this to understand the subject domain.\n"

    prompt_parts = [
        "You are an elite expert with mastery across ALL academic subjects.\n\n"
        "YOUR #1 GOAL: Get EVERY answer CORRECT.\n\n"
        "STRICT RULES:\n"
        "1. For MULTIPLE CHOICE questions: Return ONLY the exact content string of the option you choose.\n"
        "2. For CHECKBOX questions: Select ALL correct options separated by ' | '\n"
        "3. For SHORT TEXT: Provide ONLY the final answer.\n"
        f"{profile_context}"
        f"{form_context}\n"
        "QUESTIONS TO SOLVE:"
    ]

    for i, q in enumerate(questions, 1):
        prompt_parts.append(f"\nQ{i}: {q['question']}")
        if q.get("options"):
            prompt_parts.append(f"   Options: {json.dumps(q['options'])}")
        prompt_parts.append(f"   Type: {q['type']}")

    prompt_parts.append(
        "\n\nIMPORTANT: Respond with ONLY a valid JSON array of answer strings, nothing else. "
        "Example: [\"Option A text\", \"Option X | Option Y\", \"42\"]"
    )

    prompt = "\n".join(prompt_parts)

    # Try Gemini Models
    api_key = os.getenv("gemini_api_key")
    if api_key:
        try:
            client = get_client()
            for model_name in MODELS_TO_TRY:
                for attempt in range(RATE_LIMIT_RETRIES + 1):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(temperature=0.0)
                        )
                        response_text = response.text.strip()
                        if response_text.startswith("```"):
                            lines = response_text.split("\n")
                            lines = [l for l in lines if not l.strip().startswith("```")]
                            response_text = "\n".join(lines)
                        
                        json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
                        if json_match:
                            response_text = json_match.group(0)
                        
                        answers = json.loads(response_text)
                        validated_answers = []
                        for idx, ans in enumerate(answers):
                            if idx < len(questions):
                                validated_answers.append(_validate_answer(ans, questions[idx]))
                        return validated_answers
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "429" in error_msg or "rate" in error_msg:
                            if attempt < RATE_LIMIT_RETRIES:
                                time.sleep(RATE_LIMIT_DELAY)
                                continue
                        break # Next model
        except:
            pass

    # Try Deepseek Fallback
    ds_client = get_deepseek_client()
    if ds_client:
        for ds_model in DEEPSEEK_MODELS:
            try:
                response = ds_client.chat.completions.create(
                    model=ds_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                response_text = response.choices[0].message.content.strip()
                json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
                
                answers = json.loads(response_text)
                validated_answers = []
                for idx, ans in enumerate(answers):
                    if idx < len(questions):
                        validated_answers.append(_validate_answer(ans, questions[idx]))
                return validated_answers
            except:
                continue

    return ["Unable to determine answer"] * len(questions)


def answer_with_image(question_text: str, image_bytes: bytes, user_profile: dict = None) -> str:
    """Handle image-based questions with vision models."""
    prompt = f"Question: {question_text}\nAnswer this based on the image provided. Return ONLY the final answer text."
    
    api_key = os.getenv("gemini_api_key")
    if api_key:
        try:
            client = get_client()
            for model_name in MODELS_TO_TRY:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")]
                    )
                    if response.text:
                        return response.text.strip()
                except:
                    continue
        except:
            pass

    return "Unable to answer from image"


def _validate_answer(answer: str, question: dict) -> str:
    """Validate AI answer against question options."""
    if question["type"] not in ["radio", "checkbox", "dropdown"] or not question.get("options"):
        return answer

    options = question["options"]
    if question["type"] == "checkbox":
        # Multi-select
        parts = [p.strip() for p in str(answer).split("|")]
        valid_parts = []
        for p in parts:
            match = _find_best_option_match(p, options)
            if match:
                valid_parts.append(match)
        return " | ".join(valid_parts) if valid_parts else options[0]
    else:
        # Single-select
        match = _find_best_option_match(str(answer), options)
        return match if match else options[0]


def _find_best_option_match(answer: str, options: list[str]) -> str | None:
    """Find the best matching option for the AI's response."""
    # Exact match
    for opt in options:
        if opt.lower().strip() == answer.lower().strip():
            return opt
    # Substring match
    for opt in options:
        if answer.lower() in opt.lower() or opt.lower() in answer.lower():
            return opt
    return None
