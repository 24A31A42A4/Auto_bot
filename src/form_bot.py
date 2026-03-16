"""
form_bot.py — Playwright form automation engine.
Opens a Google Form, scrapes questions, fills answers (from profile or Gemini AI),
submits the form, and reads the score from the confirmation page.
"""

import asyncio
from playwright.async_api import async_playwright, Page, ElementHandle
from src.profile_detector import detect_personal_field, get_profile_value
from src.ai_helper import answer_questions, answer_with_image


async def fill_form(url: str, user_profile: dict) -> str:
    """
    Main entry point: fills and submits a Google Form.

    Args:
        url: The Google Form URL
        user_profile: Dict with user profile data from Supabase

    Returns:
        Result string (e.g. "Score: 9 / 10" or "Form submitted successfully")
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)  # Let the form fully render

            result = await _process_form_pages(page, user_profile)
            return result

        except Exception as e:
            print(f"[form_bot] Error: {e}")
            return f"Error filling form: {str(e)}"

        finally:
            await browser.close()


async def _scroll_to_bottom(page: Page) -> None:
    """Scroll down the page gradually to ensure all questions are loaded & visible."""
    previous_height = 0
    for _ in range(20):  # Max 20 scroll steps
        current_height = await page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            break
        await page.evaluate("window.scrollBy(0, 400)")
        await page.wait_for_timeout(300)
        previous_height = current_height
    # Scroll back to top so we fill fields from the beginning
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)


async def _process_form_pages(page: Page, user_profile: dict) -> str:
    """Process all pages of a form (handles multi-page forms)."""
    page_num = 1

    while True:
        print(f"[form_bot] Processing page {page_num}...")

        # Scroll down to load all questions on this page
        await _scroll_to_bottom(page)

        # Scrape questions on current page
        questions = await _scrape_questions(page)
        print(f"[form_bot] Found {len(questions)} questions on page {page_num}")

        if questions:
            # Separate personal fields from quiz questions
            personal_fields = []
            ai_questions = []

            for q in questions:
                profile_field = detect_personal_field(q["question_text"])
                if profile_field:
                    value = get_profile_value(user_profile, profile_field)
                    personal_fields.append({"question": q, "value": value})
                else:
                    ai_questions.append(q)

            # Get AI answers for non-personal questions
            ai_answers = []
            if ai_questions:
                ai_input = [
                    {
                        "question": q["question_text"],
                        "type": q["type"],
                        "options": q.get("options", []),
                    }
                    for q in ai_questions
                ]
                ai_answers = answer_questions(ai_input, user_profile)

            # Fill personal fields
            for item in personal_fields:
                print(f"[form_bot] Filling personal field '{item['question']['question_text'][:20]}...' with: {item['value']}")
                await _fill_field(page, item["question"], item["value"])

            # Fill AI-answered fields
            for q, answer in zip(ai_questions, ai_answers):
                print(f"[form_bot] Filling AI field '{q['question_text'][:20]}...' with: {answer}")
                await _fill_field(page, q, answer)

        # Check for Next button (multi-page form)
        next_button = await page.query_selector('div[role="button"]:has-text("Next")')
        if next_button:
            await next_button.click()
            await page.wait_for_timeout(2000)
            page_num += 1
            continue

        # No Next button — look for Submit button
        submit_button = await page.query_selector(
            'div[role="button"]:has-text("Submit"), '
            'div[role="button"]:has-text("submit")'
        )
        if submit_button:
            await submit_button.click()
            await page.wait_for_timeout(3000)
            break
        else:
            # Try alternative submit selectors
            submit_alt = await page.query_selector(
                'span:has-text("Submit"), '
                'button:has-text("Submit")'
            )
            if submit_alt:
                await submit_alt.click()
                await page.wait_for_timeout(3000)
            break

    # After submission, look for "View score" button
    # This often opens in a new tab
    view_score_button = await page.query_selector('a:has-text("View score"), span:has-text("View score")')
    if view_score_button:
        print("[form_bot] Found 'View score' button. Clicking...")
        # Listen for the new page (tab) being opened
        async with page.context.expect_page() as new_page_info:
            await view_score_button.click()
        
        new_page = await new_page_info.value
        await new_page.wait_for_load_state("networkidle")
        await new_page.wait_for_timeout(2000)
        
        # Read score from the new page
        result = await _read_score(new_page)
        print(f"[form_bot] Score from new tab: {result}")
        return result

    # Otherwise read from current page
    result = await _read_score(page)
    print(f"[form_bot] Final Analysis: {result}")
    return result


async def _scrape_questions(page: Page) -> list[dict]:
    """
    Scrape all question blocks from the current page of a Google Form.
    """
    questions = []
    question_blocks = await page.query_selector_all('div[role="listitem"]')

    for i, block in enumerate(question_blocks):
        try:
            question_data = await _parse_question_block(page, block)
            if question_data:
                print(f"[form_bot] Page Question {i+1}: '{question_data['question_text'][:40]}...' | Type: {question_data['type']}")
                questions.append(question_data)
        except Exception as e:
            print(f"[form_bot] Error parsing question block {i+1}: {e}")
            continue

    return questions


async def _parse_question_block(page: Page, block: ElementHandle) -> dict | None:
    """Parse a single question block and determine its type and content."""

    # Get the question text
    question_text_el = await block.query_selector(
        'div[role="heading"] span, '
        'div[data-params] > div > div > span'
    )

    if not question_text_el:
        return None

    question_text = (await question_text_el.inner_text()).strip()

    if not question_text or len(question_text) < 2:
        return None

    # Check for images in the question
    images = await block.query_selector_all("img")
    has_image = len(images) > 0

    # Determine question type and get options
    q_type = "short_text"
    options = []

    # Check for radio buttons (multiple choice)
    radio_options = await block.query_selector_all('div[role="radio"], label[data-value]')
    if radio_options:
        q_type = "radio"
        for opt in radio_options:
            opt_text = (await opt.inner_text()).strip()
            if opt_text:
                options.append(opt_text)

    # Check for checkboxes
    if not options:
        checkbox_options = await block.query_selector_all('div[role="checkbox"]')
        if checkbox_options:
            q_type = "checkbox"
            for opt in checkbox_options:
                opt_text = (await opt.inner_text()).strip()
                if opt_text:
                    options.append(opt_text)

    # Check for dropdown
    if not options:
        dropdown = await block.query_selector('div[role="listbox"]')
        if dropdown:
            q_type = "dropdown"
            dropdown_options = await block.query_selector_all('div[role="option"], div[data-value]')
            for opt in dropdown_options:
                opt_text = (await opt.inner_text()).strip()
                if opt_text and opt_text.lower() != "choose":
                    options.append(opt_text)

    # Check for paragraph (long answer)
    if not options:
        textarea = await block.query_selector('textarea')
        if textarea:
            q_type = "paragraph"

    return {
        "question_text": question_text,
        "type": q_type,
        "options": options,
        "element": block,
        "has_image": has_image,
    }


async def _fill_field(page: Page, question: dict, answer: str) -> None:
    """Fill a single form field with the given answer."""
    block = question["element"]
    q_type = question["type"]

    try:
        # Scroll the question into view before filling
        await block.scroll_into_view_if_needed()
        await page.wait_for_timeout(200)

        if q_type == "short_text":
            input_el = await block.query_selector('input[type="text"], input:not([type])')
            if input_el:
                await input_el.scroll_into_view_if_needed()
                await input_el.click()
                await input_el.fill(answer)

        elif q_type == "paragraph":
            textarea = await block.query_selector("textarea")
            if textarea:
                await textarea.click()
                await textarea.fill(answer)

        elif q_type == "radio":
            # Click the matching radio option
            await _select_option(block, answer, "radio")

        elif q_type == "checkbox":
            # Handle multiple selections (answers separated by ' | ')
            selected_answers = [a.strip() for a in answer.split("|")]
            for ans in selected_answers:
                await _select_option(block, ans, "checkbox")

        elif q_type == "dropdown":
            # Click dropdown, then select the option
            dropdown = await block.query_selector('div[role="listbox"]')
            if dropdown:
                await dropdown.click()
                await page.wait_for_timeout(500)
                # Find and click the matching option
                option = await page.query_selector(f'div[role="option"]:has-text("{answer}")')
                if option:
                    await option.click()
                    await page.wait_for_timeout(300)

        await page.wait_for_timeout(200)  # Small delay between fields

    except Exception as e:
        print(f"[form_bot] Error filling field '{question['question_text'][:30]}...': {e}")


async def _select_option(block: ElementHandle, answer: str, role: str) -> None:
    """Select a radio or checkbox option by matching answer text."""
    answer_lower = answer.lower().strip()

    # Try to find the option by role
    options = await block.query_selector_all(f'div[role="{role}"]')

    for opt in options:
        opt_text = (await opt.inner_text()).strip().lower()
        if opt_text == answer_lower or answer_lower in opt_text or opt_text in answer_lower:
            await opt.click()
            return

    # Fallback: try clicking by label text
    labels = await block.query_selector_all("label, span")
    for label in labels:
        label_text = (await label.inner_text()).strip().lower()
        if label_text == answer_lower or answer_lower in label_text:
            await label.click()
            return

    # Last resort: click first option
    if options:
        print(f"[form_bot] Could not match option '{answer}', clicking first available")
        await options[0].click()


async def _read_score(page: Page) -> str:
    """Read the score from the form confirmation/result page."""
    import re
    await page.wait_for_timeout(2000)

    try:
        page_text = await page.inner_text("body")
        lines = [line.strip() for line in page_text.split("\n") if line.strip()]
        
        # DEBUG: Print confirmation page snippet
        print(f"[form_bot] Confirmation page text snippet: {page_text[:300].replace('\n', ' ')}")

        # 1. Look for specific Score/Points labels
        total_points_match = re.search(r'(?:Total points|Score|Your score)[:\s]*(\d+)\s*/\s*(\d+)', page_text, re.IGNORECASE)
        if total_points_match:
            return f"Score: {total_points_match.group(1)} / {total_points_match.group(2)}"

        # 2. General fraction match but avoid date-like patterns (DD/MM/YYYY)
        # We look for X / Y where Y is usually small or matches total questions
        fractions = re.findall(r'(\d+)\s*/\s*(\d+)', page_text)
        for num, total in fractions:
            # Simple heuristic: If it looks like a date (e.g. 16/03/2026), skip it
            # Dates usually have a 4-digit number right after or before
            date_pattern = rf'{num}\s*/\s*{total}\s*/\s*\d{{4}}'
            if re.search(date_pattern, page_text):
                continue
            
            # If total is something like "03", it's very likely a month from a date
            if total in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]:
                if re.search(rf'{num}\s*/\s*{total}\s*/', page_text): # and followed by another slash
                    continue
            
            # If we passed date checks, return the first valid-looking fraction
            return f"Score: {num} / {total}"

        # 3. Look for "X points"
        points_match = re.search(r'(\d+)\s*(?:points?|marks?)', page_text, re.IGNORECASE)
        if points_match:
            return f"Score: {points_match.group(0)}"

        # 4. Check status messages
        if "your response has been recorded" in page_text.lower():
            return "Form submitted successfully! (No score — this form is not graded)"

        if "thank" in page_text.lower() or "submitted" in page_text.lower():
            return "Form submitted successfully!"

        return "Form submitted. Could not read score."

    except Exception as e:
        print(f"[form_bot] Error reading score: {e}")
        return "Form submitted."
