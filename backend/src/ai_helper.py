import os
import json
import re
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def get_client():
    return genai.Client(api_key=os.getenv("gemini_api_key"))

# Models to try in order of preference (verified March 2026 Gemini models)
MODELS_TO_TRY = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

# How many times to retry a rate-limited model before moving to next
RATE_LIMIT_RETRIES = 2
RATE_LIMIT_DELAY = 5  # seconds to wait before retrying


def answer_questions(questions: list[dict], user_profile: dict = None, form_title: str = "") -> list[str]:
    """
    Send a batch of quiz questions to Gemini and get answers.

    Args:
        questions: List of dicts with question data
        user_profile: Optional user profile to provide context (Name, Roll, etc.)
        form_title: Optional form title/description for subject context

    Returns:
        List of answer strings.
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
        "You are an elite expert with mastery across ALL academic subjects: Aptitude, Verbal Ability, "
        "Mathematics, Science, Engineering, Computer Science, General Knowledge, Current Affairs, "
        "Reasoning, and all competitive exam topics (CAT, GMAT, GRE, UPSC, SSC, Bank PO, GATE, etc.).\n\n"
        "YOUR #1 GOAL: Get EVERY answer CORRECT. Accuracy is everything.\n\n"
        "STRICT RULES:\n"
        "1. READ each question VERY CAREFULLY. Identify what is being asked.\n"
        "2. For MULTIPLE CHOICE questions:\n"
        "   - Your answer MUST be the EXACT text of one of the given options.\n"
        "   - Note: Option prefixes like 'A)', 'B.' have been STRIPPED from the options list to help you focus on the actual content.\n"
        "   - Return ONLY the exact content string of the option you choose (e.g., '10.5%'). Do NOT return just 'A' or 'Option A'.\n"
        "   - Copy the option text EXACTLY — same spelling, capitalization, and punctuation.\n"
        "   - Do NOT paraphrase or rewrite the option.\n"
        "   - Eliminate wrong options first, then pick the best remaining one.\n"
        "3. For CHECKBOX questions (multiple correct answers):\n"
        "   - Select ALL correct options separated by ' | '\n"
        "   - Each answer must be the EXACT option text.\n"
        "4. For SHORT TEXT / PARAGRAPH questions:\n"
        "   - Provide ONLY the final answer (a word, number, or brief phrase).\n"
        "   - Do NOT explain your reasoning in the answer.\n"
        "5. THINK STEP-BY-STEP internally before choosing:\n"
        "   a) What subject/topic is this?\n"
        "   b) What concept or formula applies?\n"
        "   c) Work through the solution.\n"
        "   d) Verify: Does my answer match the question's conditions?\n"
        "   e) For MCQ: Is my answer EXACTLY one of the listed options?\n"
        "6. If ambiguous, choose the most commonly accepted/standard answer.\n"
        "7. DOUBLE-CHECK numerical calculations.\n"
        "8. For 'All of the above' / 'None of the above' options — verify ALL other options first.\n"
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
        "For MCQ/checkbox, use the EXACT option text. "
        "Example: [\"Option A text\", \"Option X | Option Y\", \"42\"]"
    )

    prompt = "\n".join(prompt_parts)

    # Try models in order, with retry on rate limit
    client = get_client()

    for model_name in MODELS_TO_TRY:
        for attempt in range(RATE_LIMIT_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,  # Deterministic — most probable answer
                    )
                )
                response_text = response.text.strip()

                # Clean up response — remove markdown code fences if present
                if response_text.startswith("```"):
                    lines = response_text.split("\n")
                    lines = [l for l in lines if not l.strip().startswith("```")]
                    response_text = "\n".join(lines)

                # Try to extract JSON array from response even if there's extra text
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)

                answers = json.loads(response_text)

                # Validate: for MCQ/checkbox, ensure the answer matches an option
                validated_answers = []
                for idx, ans in enumerate(answers):
                    if idx < len(questions):
                        q = questions[idx]
                        validated_ans = _validate_answer(ans, q)
                        validated_answers.append(validated_ans)
                    else:
                        validated_answers.append(ans)

                if len(validated_answers) < len(questions):
                    validated_answers.extend([""] * (len(questions) - len(validated_answers)))

                return validated_answers[:len(questions)]
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                    if attempt < RATE_LIMIT_RETRIES:
                        wait_time = RATE_LIMIT_DELAY * (attempt + 1)
                        print(f"[ai_helper] Model {model_name} rate limited, retrying in {wait_time}s (attempt {attempt+1}/{RATE_LIMIT_RETRIES})...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"[ai_helper] Model {model_name} rate limited after {RATE_LIMIT_RETRIES} retries, trying next model...")
                        break
                elif "404" in error_msg or "NOT_FOUND" in error_msg:
                    print(f"[ai_helper] Model {model_name} not found, trying next...")
                    break  # Don't retry, move to next model
                else:
                    print(f"[ai_helper] Error with {model_name}: {e}")
                    break  # Don't retry unknown errors

    # Fallback if all fail
    return ["Unable to determine answer"] * len(questions)


def _validate_answer(answer: str, question: dict) -> str:
    """
    Validate that an AI answer matches one of the available options.
    For MCQ/dropdown, find the closest matching option if exact match fails.
    """
    options = question.get("options", [])
    q_type = question.get("type", "short_text")

    if not options or q_type in ("short_text", "paragraph"):
        return answer  # No validation needed for free-text

    if q_type == "checkbox":
        # Multiple answers separated by ' | '
        selected = [a.strip() for a in answer.split("|")]
        matched = []
        for sel in selected:
            best = _find_best_option_match(sel, options)
            if best:
                matched.append(best)
        return " | ".join(matched) if matched else answer

    # Radio / dropdown — single answer
    best = _find_best_option_match(answer, options)
    return best if best else answer


def _find_best_option_match(answer: str, options: list[str]) -> str | None:
    """Find the best matching option for a given answer string."""
    answer_clean = answer.strip().lower()

    # 1. Exact match
    for opt in options:
        if opt.strip().lower() == answer_clean:
            return opt

    # 2. One contains the other
    for opt in options:
        opt_lower = opt.strip().lower()
        if answer_clean in opt_lower or opt_lower in answer_clean:
            return opt

    # 3. Normalized match (remove punctuation and extra whitespace)
    answer_norm = re.sub(r'[^\w\s]', '', answer_clean).strip()
    for opt in options:
        opt_norm = re.sub(r'[^\w\s]', '', opt.strip().lower()).strip()
        if answer_norm == opt_norm:
            return opt

    return None


def answer_with_image(question_text: str, image_bytes: bytes, options: list[str] = None) -> str:
    """
    Send a question with an image to Gemini Vision for answering.

    Args:
        question_text: The question text
        image_bytes: The screenshot of the question block as bytes
        options: Optional list of answer options

    Returns:
        Answer string
    """
    prompt = (
        "Look at this Google Form question screenshot and answer it accurately.\n\n"
        f"Question: {question_text}"
    )
    if options:
        prompt += f"\nOptions: {json.dumps(options)}"
    prompt += (
        "\n\nGive ONLY the answer, nothing else. "
        "If there are options, return EXACTLY one of the given option texts (copy it verbatim)."
    )

    client = get_client()

    for model_name in MODELS_TO_TRY:
        for attempt in range(RATE_LIMIT_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        prompt,
                        types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                    )
                )
                answer = response.text.strip()

                # Validate against options if provided
                if options:
                    best = _find_best_option_match(answer, options)
                    if best:
                        return best

                return answer
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                    if attempt < RATE_LIMIT_RETRIES:
                        wait_time = RATE_LIMIT_DELAY * (attempt + 1)
                        print(f"[ai_helper] Vision model {model_name} rate limited, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"[ai_helper] Vision model {model_name} rate limited after retries, trying next...")
                        break
                elif "404" in error_msg or "NOT_FOUND" in error_msg:
                    print(f"[ai_helper] Vision model {model_name} not found, trying next...")
                    break
                else:
                    print(f"[ai_helper] Vision error with {model_name}: {e}")
                    break

    return "Unable to determine answer"
