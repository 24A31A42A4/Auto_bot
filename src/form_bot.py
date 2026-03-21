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

    # Scrape form title/description for AI context
    form_title = await _scrape_form_title(page)
    print(f"[form_bot] Form title: '{form_title}'")

    while True:
        print(f"[form_bot] Processing page {page_num}...")

        # Scroll down to load all questions on this page
        await _scroll_to_bottom(page)

        # Scrape ONLY VISIBLE questions on current page
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
                # Log what we're sending to AI
                for i, inp in enumerate(ai_input):
                    print(f"[form_bot] AI Input Q{i+1}: '{inp['question'][:60]}' | Options: {inp['options'][:4]}{'...' if len(inp['options']) > 4 else ''}")

                ai_answers = answer_questions(ai_input, user_profile, form_title=form_title)

                # Log what AI returned
                for i, ans in enumerate(ai_answers):
                    print(f"[form_bot] AI Answer Q{i+1}: '{ans}'")

            # Fill personal fields
            for item in personal_fields:
                print(f"[form_bot] Filling personal field '{item['question']['question_text'][:30]}...' with: {item['value']}")
                await _fill_field(page, item["question"], item["value"])

            # Fill AI-answered fields
            for q, answer in zip(ai_questions, ai_answers):
                print(f"[form_bot] Filling AI field '{q['question_text'][:30]}...' with: {answer}")
                await _fill_field(page, q, answer)

        # Check for Next button (multi-page form)
        next_button = await page.query_selector('div[role="button"]:has-text("Next")')
        if next_button:
            await next_button.click()
            await page.wait_for_timeout(2000)
            
            # Check for validation errors preventing page advance
            errors = await page.query_selector_all('div[role="alert"]')
            error_texts = []
            for err in errors:
                err_text = await err.inner_text()
                if err_text.strip():
                    error_texts.append(err_text.strip())
            
            if error_texts:
                print(f"[form_bot] Validation errors prevented advancing to page {page_num + 1}: {', '.join(error_texts)}")
                break
            
            page_num += 1
            continue

        # No Next button — look for Submit button
        submit_button = await page.query_selector(
            'div[role="button"]:has-text("Submit"), '
            'div[role="button"]:has-text("submit")'
        )
        if submit_button:
            await submit_button.click()
            await page.wait_for_timeout(4000)
            break
        else:
            # Try alternative submit selectors
            submit_alt = await page.query_selector(
                'span:has-text("Submit"), '
                'button:has-text("Submit")'
            )
            if submit_alt:
                await submit_alt.click()
                await page.wait_for_timeout(4000)
            break

    # Read the score from the post-submission page
    return await _read_score_safely(page)


async def _read_score_safely(page: Page) -> str:
    """
    Safely read the score after form submission.
    Handles 'View score' button that may open a new tab.
    """
    try:
        # Wait for the confirmation page to fully load
        await page.wait_for_timeout(3000)

        # PRIORITY 1: Look for "View score" link/button FIRST
        # (Confirmation pages often still have leftover form text, so check View Score before anything else)
        view_score_button = await page.query_selector(
            'a:has-text("View score"), '
            'a:has-text("View Score"), '
            'span:has-text("View score"), '
            'div[role="link"]:has-text("View score")'
        )
        if view_score_button:
            print("[form_bot] Found 'View score' button. Clicking...")
            try:
                # Try to get href and navigate in same tab (most reliable)
                href = await view_score_button.get_attribute("href")
                if href:
                    print(f"[form_bot] Navigating to score page: {href[:80]}...")
                    await page.goto(href, wait_until="networkidle", timeout=20000)
                    await page.wait_for_timeout(3000)
                    result = await _read_score(page)
                    print(f"[form_bot] Score result: {result}")
                    return result

                # No href — try clicking directly
                # First try: see if it stays on same page
                await view_score_button.click()
                await page.wait_for_timeout(3000)
                
                # Check if the URL changed (score page loaded in same tab)
                current_url = page.url
                if "viewscore" in current_url.lower() or "viewanalytics" in current_url.lower():
                    result = await _read_score(page)
                    print(f"[form_bot] Score result (same tab): {result}")
                    return result

                # Check if a new page opened
                pages = page.context.pages
                if len(pages) > 1:
                    new_page = pages[-1]  # Get the latest page
                    await new_page.wait_for_load_state("networkidle")
                    await new_page.wait_for_timeout(3000)
                    result = await _read_score(new_page)
                    print(f"[form_bot] Score from new tab: {result}")
                    return result

                # Still on same page — try reading score from current page
                result = await _read_score(page)
                print(f"[form_bot] Score after View Score click: {result}")
                return result

            except Exception as e:
                print(f"[form_bot] Error reading score page: {e}")
                # Fall through to read current page

        # PRIORITY 2: Check if we see a "response recorded" or "thank you" message
        page_text = await page.inner_text("body")
        page_lower = page_text.lower()

        if "your response has been recorded" in page_lower:
            return "Form submitted successfully! (No score — this form is not graded)"

        if "thank" in page_lower or "submitted" in page_lower:
            # Try to find a score on this page anyway
            result = await _read_score(page)
            if "Could not" not in result:
                return result
            return "Form submitted successfully!"

        # PRIORITY 3: Check if still on form page (submission may have failed)
        # Only flag this if there's a visible Submit button still on the page
        submit_still_visible = await page.query_selector(
            'div[role="button"]:visible:has-text("Submit")'
        )
        if submit_still_visible:
            print("[form_bot] WARNING: Submit button still visible — submission may have failed")
            return "Form submission may have failed (still on form page)"

        # Default: try to read score from whatever page we're on
        result = await _read_score(page)
        print(f"[form_bot] Final Analysis: {result}")
        return result

    except Exception as e:
        print(f"[form_bot] Error in score reading: {e}")
        return "Form submitted."


async def _scrape_form_title(page: Page) -> str:
    """Scrape the form title and description for AI context."""
    try:
        # Google Forms title is usually in a heading element
        title_el = await page.query_selector(
            'div[role="heading"][aria-level="1"], '
            'div.freebirdFormviewerViewHeaderTitle, '
            'div[data-item-id] div[role="heading"]'
        )
        if title_el:
            title = (await title_el.inner_text()).strip()
            if title and len(title) > 2:
                # Also try to get description
                desc_el = await page.query_selector(
                    'div.freebirdFormviewerViewHeaderDescription, '
                    'div[role="heading"] + div'
                )
                desc = ""
                if desc_el:
                    desc = (await desc_el.inner_text()).strip()
                return f"{title} — {desc}" if desc else title

        # Fallback: page title
        page_title = await page.title()
        if page_title and "google" not in page_title.lower():
            return page_title
    except Exception as e:
        print(f"[form_bot] Error scraping form title: {e}")

    return ""


async def _scrape_questions(page: Page) -> list[dict]:
    """
    Scrape all VISIBLE question blocks from the current page of a Google Form.
    Filters out hidden questions from previous pages.
    """
    questions = []
    question_blocks = await page.query_selector_all('div[role="listitem"]')

    for i, block in enumerate(question_blocks):
        try:
            # CRITICAL: Skip hidden/invisible question blocks (from previous pages)
            is_visible = await block.is_visible()
            if not is_visible:
                continue

            question_data = await _parse_question_block(page, block)
            if question_data:
                opts_preview = question_data['options'][:3] if question_data['options'] else []
                print(f"[form_bot] Page Question {i+1}: '{question_data['question_text'][:50]}...' | Type: {question_data['type']} | Options: {opts_preview}")
                questions.append(question_data)
        except Exception as e:
            print(f"[form_bot] Error parsing question block {i+1}: {e}")
            continue

    return questions


async def _parse_question_block(page: Page, block: ElementHandle) -> dict | None:
    """Parse a single question block and determine its type and content."""

    # Get the question text — try multiple selectors for robustness
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
            opt_text = await _get_option_text(opt)
            if opt_text:
                options.append(opt_text)

    # Check for checkboxes
    if not options:
        checkbox_options = await block.query_selector_all('div[role="checkbox"]')
        if checkbox_options:
            q_type = "checkbox"
            for opt in checkbox_options:
                opt_text = await _get_option_text(opt)
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
            input_el = await block.query_selector('input[type="text"], input[type="email"], input[type="number"], input[type="url"], input:not([type])')
            if input_el:
                await input_el.scroll_into_view_if_needed()
                await input_el.click()
                await input_el.fill(answer)

        elif q_type == "paragraph":
            textarea = await block.query_selector("textarea")
            if textarea:
                await textarea.scroll_into_view_if_needed()
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
    import re as _re
    answer_lower = answer.lower().strip()
    answer_norm = _re.sub(r'[^\w\s]', '', answer_lower).strip()

    # Try to find the option by role
    options = await block.query_selector_all(f'div[role="{role}"]')

    # First pass: exact match
    for opt in options:
        opt_text = await _get_option_text(opt)
        if opt_text and opt_text.lower() == answer_lower:
            await opt.scroll_into_view_if_needed()
            await opt.click()
            return

    # Second pass: normalized match (ignore punctuation)
    for opt in options:
        opt_text = await _get_option_text(opt)
        if opt_text:
            opt_norm = _re.sub(r'[^\w\s]', '', opt_text.lower()).strip()
            if opt_norm == answer_norm:
                await opt.scroll_into_view_if_needed()
                await opt.click()
                return

    # Third pass: substring containment
    for opt in options:
        opt_text = await _get_option_text(opt)
        if opt_text:
            opt_lower = opt_text.lower().strip()
            if answer_lower in opt_lower or opt_lower in answer_lower:
                await opt.scroll_into_view_if_needed()
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


async def _get_option_text(opt: ElementHandle) -> str:
    """Extract the best text representation of an option element."""
    data_val = await opt.get_attribute("data-value")
    if data_val and data_val.strip():
        return data_val.strip()
    aria_label = await opt.get_attribute("aria-label")
    if aria_label and aria_label.strip():
        return aria_label.strip()
    return (await opt.inner_text()).strip()


async def _read_score(page: Page) -> str:
    """Read the score from the form confirmation/result page."""
    import re
    await page.wait_for_timeout(2000)

    try:
        page_text = await page.inner_text("body")
        
        # DEBUG: Print confirmation page snippet
        print(f"[form_bot] Confirmation page text snippet: {page_text[:500].replace(chr(10), ' ')}")

        # SAFETY CHECK: Detect if we're still on the form page (not results)
        still_on_form = (
            "required question" in page_text.lower()
            and ("next" in page_text.lower() or "submit" in page_text.lower())
        )
        if still_on_form:
            return "Form submitted. Could not navigate to score page."

        # 1. Look for specific Score/Points labels (most reliable)
        total_points_match = re.search(
            r'(?:Total\s+points|Total\s+score|Your\s+score|Score)\s*[:\s]\s*(\d+)\s*/\s*(\d+)',
            page_text, re.IGNORECASE
        )
        if total_points_match:
            return f"Score: {total_points_match.group(1)} / {total_points_match.group(2)}"

        # 2. Look for "X out of Y" pattern
        out_of_match = re.search(r'(\d+)\s+out\s+of\s+(\d+)', page_text, re.IGNORECASE)
        if out_of_match:
            return f"Score: {out_of_match.group(1)} / {out_of_match.group(2)}"

        # 3. Look for "X / Y points" or "X/Y" near score-related words
        score_fraction = re.search(
            r'(?:scored?|points?|marks?|grade|result).*?(\d+)\s*/\s*(\d+)',
            page_text[:1000], re.IGNORECASE
        )
        if score_fraction:
            return f"Score: {score_fraction.group(1)} / {score_fraction.group(2)}"

        # 4. Look for fraction patterns but filter dates aggressively
        fractions = re.findall(r'(\d+)\s*/\s*(\d+)', page_text)
        for num, total in fractions:
            num_int, total_int = int(num), int(total)

            # Skip date-like patterns (DD/MM/YYYY or MM/DD)
            date_pattern = rf'{num}\s*/\s*{total}\s*/\s*\d{{2,4}}'
            if re.search(date_pattern, page_text):
                continue

            # Skip if preceded by another number/slash (part of date)
            pre_date = rf'\d+\s*/\s*{num}\s*/\s*{total}'
            if re.search(pre_date, page_text):
                continue

            # Skip unreasonable scores (total > 200 or num > total*2)
            if total_int > 200 or total_int == 0:
                continue
            if num_int > total_int * 2:
                continue

            # Skip likely year numbers
            if total_int >= 1900 or num_int >= 1900:
                continue

            return f"Score: {num} / {total}"

        # 5. Look for "X points" or "X marks"
        points_match = re.search(r'(\d+)\s*(?:points?|marks?)', page_text, re.IGNORECASE)
        if points_match:
            return f"Score: {points_match.group(0)}"

        # 6. Check status messages
        if "your response has been recorded" in page_text.lower():
            return "Form submitted successfully! (No score — this form is not graded)"

        if "thank" in page_text.lower() or "submitted" in page_text.lower():
            return "Form submitted successfully!"

        return "Form submitted. Could not read score."

    except Exception as e:
        print(f"[form_bot] Error reading score: {e}")
        return "Form submitted."
