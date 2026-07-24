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
    "gemini-flash-latest",        # Always latest Flash model
    "gemini-flash-lite-latest",   # Always latest Flash Lite model
    "gemini-pro-latest",          # Always latest Pro model
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
        "SYSTEM DIRECTIVE: You are an Elite Grandmaster Competitive Exam Genius with 100% precision in Logical Reasoning, Quantitative Aptitude, Data Interpretation, Mathematics, Verbal Ability, Science, and General Knowledge.\n\n"
        "YOUR MISSION: Solve EVERY question with HIGHEST POSSIBLE ACCURACY and ZERO mistakes.\n\n"
        "EXPERT PROBLEM-SOLVING RULES:\n"
        "1. SEATING ARRANGEMENTS & PUZZLES: Trace relative positions, facing directions (inside/outside), and seating orders step-by-step.\n"
        "2. BLOOD RELATIONS: Build family trees generation-by-generation to deduce exact relations.\n"
        "3. SYLLOGISMS: Strictly test conclusions using formal Venn diagram logic.\n"
        "4. MATHEMATICS & SERIES: Solve exact algebraic equations, double-check arithmetic calculations, and verify number series patterns.\n"
        "5. OPTION MATCHING: Select the option string from the provided 'Options' array that EXACTLY matches your calculated solution.\n\n"
        "STRICT OUTPUT FORMAT:\n"
        "- Return ONLY a valid JSON array of answer strings, one per question.\n"
        "- Example format: [\"A. Sister\", \"42\", \"Option X | Option Y\"]\n"
        f"{profile_context}"
        f"{form_context}\n"
        "QUESTIONS TO SOLVE WITH 100% ACCURACY:"
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

    def try_deepseek():
        ds_client = get_deepseek_client()
        if not ds_client:
            return None
        for ds_model in DEEPSEEK_MODELS:
            try:
                print(f"[ai_helper] Querying DeepSeek model '{ds_model}'...")
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
            except Exception as e:
                err_str = str(e)
                if "402" in err_str or "Insufficient Balance" in err_str:
                    print(f"[ai_helper] ⚠️ DeepSeek API Notice: Insufficient Balance (402). Falling back to Gemini...")
                else:
                    print(f"[ai_helper] ⚠️ DeepSeek error ({ds_model}): {e}")
                return None

    def try_gemini():
        api_key = os.getenv("gemini_api_key")
        if not api_key:
            return None
        try:
            client = get_client()
            for model_name in MODELS_TO_TRY:
                print(f"[ai_helper] Querying Gemini model '{model_name}'...")
                for attempt in range(3):  # 3 fast attempts
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
                        print(f"[ai_helper] ⚠️ Gemini model '{model_name}' attempt {attempt+1} error: {e}")
                        if "429" in error_msg or "rate" in error_msg or "resource_exhausted" in error_msg:
                            if attempt < 2:
                                time.sleep(2)
                                continue
                        break # Next model
        except Exception as e:
            print(f"[ai_helper] ⚠️ Gemini client error: {e}")
        return None

    # Check preference in .env (defaults to Gemini first, then DeepSeek fallback)
    preferred_provider = os.getenv("PREFERRED_AI_PROVIDER", "gemini").lower()

    if preferred_provider == "deepseek":
        res = try_deepseek()
        if res:
            return res
        res = try_gemini()
        if res:
            return res
    else:
        res = try_gemini()
        if res:
            return res
        res = try_deepseek()
        if res:
            return res

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
