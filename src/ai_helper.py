import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return genai.Client(api_key=os.getenv("gemini_api_key"))

# Models to try in order of preference
# Models to try in order of preference (based on current working quota)
MODELS_TO_TRY = [
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemma-3-12b-it",
    "gemma-3-4b-it"
]


# Note: The new SDK uses a Client-based approach, so get_model is no longer needed in its old form.
# We will use get_client() and pass model names directly.


def answer_questions(questions: list[dict], user_profile: dict = None) -> list[str]:
    """
    Send a batch of quiz questions to Gemini and get answers.

    Args:
        questions: List of dicts with question data
        user_profile: Optional user profile to provide context (Name, Roll, etc.)

    Returns:
        List of answer strings.
    """
    if not questions:
        return []

    # Build the prompt
    profile_context = ""
    if user_profile:
        profile_context = f"\nUSER CONTEXT (Use these for personal questions):\n"
        for k, v in user_profile.items():
            profile_context += f"- {k.replace('_', ' ').title()}: {v}\n"

    prompt_parts = [
        "You are an elite Aptitude and Verbal Ability expert with 100+ years of combined teaching, exam-setting, and problem-solving experience. "
        "You have trained students for the world's toughest competitive exams such as CAT, GMAT, GRE, UPSC, SSC, Bank PO, and other high-level aptitude assessments.\n\n"
        "Your task is to solve questions with extreme accuracy and deep reasoning.\n\n"
        "Follow these rules strictly:\n"
        "1. Carefully read and analyze the question before solving.\n"
        "2. Identify all conditions, constraints, and hidden assumptions.\n"
        "3. Break the problem into logical steps.\n"
        "4. Show the reasoning clearly but keep it concise and structured.\n"
        "5. For aptitude problems: Identify the concept, apply the most efficient method, and verify calculations.\n"
        "6. For verbal ability: Analyze grammar rules, vocabulary, tone, and context.\n"
        "7. Double-check the final answer by validating it against the question conditions.\n"
        "8. If multiple interpretations are possible, choose the most logical answer.\n"
        "9. If the question is tricky or ambiguous, resolve it logically.\n"
        "10. For the final output, you MUST follow these formatting rules for the bot to process:\n"
        "    - Return your answers as a JSON array of strings, one per question.\n"
        "    - For multiple choice (radio/dropdown): provide ONLY the exact option text.\n"
        "    - For checkboxes: provide the correct option(s) separated by ' | '.\n"
        "    - For short text/paragraph: provide only the final verified answer.\n"
        f"{profile_context}\n"
        "QUESTIONS TO SOLVE:"
    ]

    for i, q in enumerate(questions, 1):
        prompt_parts.append(f"\nQ{i}: {q['question']}")
        if q.get("options"):
            prompt_parts.append(f"   Options: {', '.join(q['options'])}")
        prompt_parts.append(f"   Type: {q['type']}")

    prompt_parts.append(
        "\n\nRespond with ONLY a JSON array of answer strings. "
        "Example: [\"Answer 1\", \"Answer 2\", \"Answer 3\"]"
    )

    prompt = "\n".join(prompt_parts)

    # Try models in order loop
    client = get_client()

    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            response_text = response.text.strip()

            # Clean up response — remove markdown code fences if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            answers = json.loads(response_text)

            if len(answers) < len(questions):
                answers.extend([""] * (len(questions) - len(answers)))

            return answers[:len(questions)]
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                print(f"[ai_helper] Model {model_name} rate limited, trying next...")
                continue
            else:
                print(f"[ai_helper] Error with {model_name}: {e}")
                continue

    # Fallback if all fail
    return ["Unable to determine answer"] * len(questions)


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
    prompt = f"Look at this Google Form question screenshot and answer it.\n\nQuestion: {question_text}"
    if options:
        prompt += f"\nOptions: {', '.join(options)}"
    prompt += "\n\nGive ONLY the answer, nothing else. If there are options, return exactly one of the given options."

    client = get_client()

    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                ]
            )
            return response.text.strip()
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                print(f"[ai_helper] Model {model_name} rate limited, trying next...")
                continue
            else:
                print(f"[ai_helper] Vision error with {model_name}: {e}")
                continue

    return "Unable to determine answer"
