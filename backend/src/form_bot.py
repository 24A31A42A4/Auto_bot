"""
form_bot.py — Playwright form automation engine.
Opens a Google Form, scrapes questions, fills answers (from profile or Gemini AI),
submits the form, and reads the score from the confirmation page.

Based on the original working logic, with targeted improvements:
- status_callback for WhatsApp status updates
- Top-of-form email detection
- Image-based question handling (vision AI)
- Fallback fills for unanswered questions (never skip required fields)
- Retry logic on validation errors
- Consistent return types
"""

import asyncio
from playwright.async_api import async_playwright, Page, ElementHandle
from src.profile_detector import detect_personal_field, get_profile_value
from src.ai_helper import answer_questions, answer_with_image


async def fill_form(url: str, user_profile: dict, status_callback: callable = None) -> dict:
    """
    Main entry point: fills and submits a Google Form.

    Args:
        url: The Google Form URL
        user_profile: Dict with user profile data from Supabase
        status_callback: Optional callback for live status updates

    Returns:
        Dict with {"score": str, "title": str}
    """
    def log_status(msg: str):
        print(f"[form_bot] {msg}")
        if status_callback:
            status_callback(msg)

    log_status(f"Starting form-fill for {url}")
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

            # Scrape form title early for tracking
            form_title = await _scrape_form_title(page)

            result = await _process_form_pages(page, user_profile, log_status, form_title)
            
            # _process_form_pages can return a dict with score and score_url, or a string error
            if isinstance(result, dict):
                return {
                    "score": result.get("score"),
                    "title": form_title,
                    "score_url": result.get("score_url")
                }
            return {"score": result, "title": form_title}

        except Exception as e:
            log_status(f"Error: {e}")
            return {"score": f"Error: {str(e)}", "title": "Unknown Form"}

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


async def _process_form_pages(page: Page, user_profile: dict, log_status: callable, form_title: str) -> str:
    """
    Process all pages of a form (handles multi-page forms).
    ALWAYS returns a plain string — never a dict.
    """
    page_num = 1

    print(f"[form_bot] Form title: '{form_title}'")

    while True:
        log_status(f"Processing page {page_num}...")

        # Scroll down to load all questions on this page
        await _scroll_to_bottom(page)

        # Check for mandatory email field at top (outside main question list)
        top_email = await page.query_selector(
            'input[type="email"][name="emailAddress"], '
            'input[aria-label="Email"], input[aria-label="email"]'
        )
        if top_email:
            email_val = get_profile_value(user_profile, "email")
            if email_val:
                log_status(f"Filling email field: {email_val}")
                await top_email.click()
                await top_email.fill(email_val)
                await top_email.press("Tab")

        # Scrape ONLY VISIBLE questions on current page
        questions = await _scrape_questions(page)
        log_status(f"Found {len(questions)} questions on page {page_num}")

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
                # Pre-fill with fallback defaults
                ai_answers = [""] * len(ai_questions)
                text_qs = []
                text_indices = []

                for i, q in enumerate(ai_questions):
                    if q.get("has_image"):
                        print(f"[form_bot] Image question detected: '{q['question_text'][:30]}...'")
                        try:
                            block = q["element"]
                            await block.scroll_into_view_if_needed()
                            await page.wait_for_timeout(500)
                            image_bytes = await block.screenshot()
                            ans = answer_with_image(q["question_text"], image_bytes, q.get("options", []))
                            ai_answers[i] = ans
                            print(f"[form_bot] AI Vision Answer Q{i+1}: '{ans}'")
                        except Exception as e:
                            print(f"[form_bot] Error capturing image for Q{i+1}: {e}")
                    else:
                        text_qs.append(q)
                        text_indices.append(i)

                if text_qs:
                    ai_input = [
                        {
                            "question": q["question_text"],
                            "type": q["type"],
                            "options": q.get("options", []),
                        }
                        for q in text_qs
                    ]
                    # Log what we're sending to AI
                    for i, inp in enumerate(ai_input):
                        print(f"[form_bot] AI Input Q{text_indices[i]+1}: '{inp['question'][:60]}' | Options: {inp['options'][:4]}")

                    text_answers = answer_questions(ai_input, user_profile, form_title=form_title)

                    for idx, ans in zip(text_indices, text_answers):
                        ai_answers[idx] = ans
                        print(f"[form_bot] AI Answer Q{idx+1}: '{ans}'")

            # Fill personal fields
            for item in personal_fields:
                log_status(f"Filling: '{item['question']['question_text'][:30]}...' -> {item['value']}")
                await _fill_field(page, item["question"], item["value"])

            # Fill AI-answered fields — NEVER skip, use fallback if no answer
            for q, answer in zip(ai_questions, ai_answers):
                if not answer or answer == "Unable to determine answer":
                    # Fallback: pick first option for MCQ, "N/A" for text
                    if q["type"] in ("radio", "dropdown", "checkbox") and q.get("options"):
                        answer = q["options"][0]
                        log_status(f"⚠️ No AI answer for '{q['question_text'][:30]}...' → using first option: '{answer}'")
                    elif q["type"] in ("short_text", "paragraph"):
                        answer = "N/A"
                        log_status(f"⚠️ No AI answer for '{q['question_text'][:30]}...' → filling 'N/A'")
                    else:
                        log_status(f"⚠️ No answer and no fallback for: '{q['question_text'][:30]}...'")
                        continue

                log_status(f"Filling Answer: '{q['question_text'][:30]}...'")
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
                print(f"[form_bot] Validation errors on page {page_num}: {', '.join(error_texts)}")
                # RETRY: Try to fill missed required fields with fallback answers
                log_status(f"Retrying missed required fields on page {page_num}...")
                missed_blocks = await page.query_selector_all(
                    'div[role="listitem"]:has(div[role="alert"]), '
                    'div[role="listitem"]:has(font:has-text("This is a required question"))'
                )
                for missed_block in missed_blocks:
                    if not await missed_block.is_visible():
                        continue
                    q_data = await _parse_question_block(page, missed_block)
                    if q_data:
                        fallback = q_data["options"][0] if q_data.get("options") else "N/A"
                        print(f"[form_bot] Retry-filling: '{q_data['question_text'][:30]}...' with '{fallback}'")
                        await _fill_field(page, q_data, fallback)

                # Retry clicking Next after filling missed fields
                await page.wait_for_timeout(500)
                await next_button.click()
                await page.wait_for_timeout(2000)

                # If still errors, give up on this page
                errors2 = await page.query_selector_all('div[role="alert"]')
                still_errors = any((await e.inner_text()).strip() for e in errors2)
                if still_errors:
                    print(f"[form_bot] Still have validation errors after retry on page {page_num}. Giving up.")
                    return "⚠️ Form could not advance past page " + str(page_num) + " (required fields missing)"

            page_num += 1
            continue

        # No Next button — look for Submit button
        submit_button = await page.query_selector(
            'div[role="button"]:has-text("Submit"), '
            'div[role="button"]:has-text("submit"), '
            'span:has-text("Submit"), '
            'button:has-text("Submit"), '
            'div[jsname="M2S78d"]'
        )
        if submit_button:
            log_status("Submitting form...")
            await submit_button.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            await submit_button.click(force=True)
            log_status("Submit clicked. Finalizing...")
            await page.wait_for_timeout(5000)

            # Post-submit check: are we still on the form?
            is_still_on_form = await page.query_selector('div[role="list"]')
            if is_still_on_form:
                # Try to find which fields have errors
                error_containers = await page.query_selector_all(
                    'div[role="listitem"]:has(font:has-text("This is a required question")), '
                    'div[role="listitem"]:has(div[role="alert"])'
                )
                error_labels = []
                for container in error_containers:
                    label_el = await container.query_selector('div[role="heading"], label, .M7VMe')
                    if label_el:
                        txt = await label_el.inner_text()
                        error_labels.append(txt.strip().split('\n')[0])

                if error_labels:
                    final_err = f"⚠️ Fields Missed: {', '.join(set(error_labels))}"
                    log_status(final_err)
                    return final_err  # Always return string
                else:
                    log_status("⚠️ Submission stuck. Please check manually.")
                    return "⚠️ Check Required Fields"  # Always return string
            break
        else:
            break

    # Read the score from the post-submission page
    score_text, score_url = await _read_score_safely(page)
    return {"score": score_text, "title": form_title, "score_url": score_url}


async def _read_score_safely(page: Page) -> tuple[str, str | None]:
    """
    Safely read the score after form submission.
    Handles 'View score' button that may open a new tab.
    Returns (score_text, score_url)
    """
    try:
        # Wait for the confirmation page to fully load
        await page.wait_for_timeout(3000)
        score_url = None

        # PRIORITY 1: Look for "View score" link/button FIRST
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
                    if not href.startswith("http"):
                        # Handle relative URLs if any
                        import urllib.parse
                        href = urllib.parse.urljoin(page.url, href)
                    
                    print(f"[form_bot] Navigating to score page: {href[:80]}...")
                    score_url = href
                    await page.goto(href, wait_until="networkidle", timeout=20000)
                    await page.wait_for_timeout(3000)
                    result = await _read_score(page)
                    print(f"[form_bot] Score result: {result}")
                    return result, score_url

                # No href — try clicking directly
                await view_score_button.click()
                await page.wait_for_timeout(3000)

                # Check if the URL changed (score page loaded in same tab)
                current_url = page.url
                if "viewscore" in current_url.lower() or "viewanalytics" in current_url.lower():
                    score_url = current_url
                    result = await _read_score(page)
                    print(f"[form_bot] Score result (same tab): {result}")
                    return result, score_url

                # Check if a new page opened
                pages = page.context.pages
                if len(pages) > 1:
                    new_page = pages[-1]
                    await new_page.wait_for_load_state("networkidle")
                    await new_page.wait_for_timeout(3000)
                    score_url = new_page.url
                    result = await _read_score(new_page)
                    print(f"[form_bot] Score from new tab: {result}")
                    return result, score_url

                # Still on same page — try reading score from current page
                result = await _read_score(page)
                print(f"[form_bot] Score after View Score click: {result}")
                return result, score_url

            except Exception as e:
                print(f"[form_bot] Error reading score page: {e}")

        # PRIORITY 2: Check if we see a "response recorded" or "thank you" message
        page_text = await page.inner_text("body")
        page_lower = page_text.lower()

        if "your response has been recorded" in page_lower:
            return "Form submitted successfully! (No score — this form is not graded)", None

        if "thank" in page_lower or "submitted" in page_lower:
            result = await _read_score(page)
            if "Could not" not in result:
                return result, None
            return "Form submitted successfully!", None

        # PRIORITY 3: Check if still on form page (submission may have failed)
        submit_still_visible = await page.query_selector(
            'div[role="button"]:visible:has-text("Submit")'
        )
        if submit_still_visible:
            print("[form_bot] WARNING: Submit button still visible — submission may have failed")
            return "⚠️ Submission Needed (Check manually)", None

        # Default: try to read score from whatever page we're on
        result = await _read_score(page)
        print(f"[form_bot] Final Analysis: {result}")
        return result, score_url

    except Exception as e:
        print(f"[form_bot] Error in score reading: {e}")
        return "Form submitted.", None


async def _scrape_form_title(page: Page) -> str:
    """Scrape the form title and description for AI context."""
    try:
        title_el = await page.query_selector(
            'div[role="heading"][aria-level="1"], '
            'div.freebirdFormviewerViewHeaderTitle, '
            'div[data-item-id] div[role="heading"]'
        )
        if title_el:
            title = (await title_el.inner_text()).strip()
            if title and len(title) > 2:
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
    Uses ONLY div[role="listitem"] — the reliable Google Forms question container.
    """
    questions = []
    question_blocks = await page.query_selector_all('div[role="listitem"]')

    # Fallback: if no listitem blocks found, try data-item-id (older form versions)
    if not question_blocks:
        question_blocks = await page.query_selector_all('div[data-item-id]')

    for i, block in enumerate(question_blocks):
        try:
            # Skip hidden/invisible question blocks (from previous pages)
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
    import re

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
    option_map = {}  # Maps letter labels to full option text (e.g., {"A": "Rs. 3266.75"})

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

    # CRITICAL: Detect if options are just single-letter labels (A, B, C, D, E)
    # If so, try to extract the FULL option values from the question text.
    # Many Google Forms embed options like "A. Rs. 3266.75  B. Rs. 3165.75" in the question itself.
    if options and all(len(o.strip()) <= 2 for o in options):
        # Try to parse "A. value", "A) value", "A: value" patterns from question text
        embedded_options = re.findall(
            r'(?:^|\n|\s)([A-Ea-e])[.):\s]+\s*(.+?)(?=\s*[A-Ea-e][.):\s]|\s*\*|\s*$)',
            question_text, re.MULTILINE
        )
        if embedded_options and len(embedded_options) >= len(options):
            option_map = {}
            full_options = []
            for letter, value in embedded_options:
                letter_upper = letter.upper().strip()
                value_clean = value.strip().rstrip('.')
                option_map[letter_upper] = value_clean
                full_options.append(f"{letter_upper}. {value_clean}")
            
            print(f"[form_bot] Extracted option map from question text: {option_map}")
            
            # Replace bare letter options with full "A. value" options for AI
            options = full_options
            
            # Clean the question text: remove the embedded options so AI sees only the question
            for letter, value in embedded_options:
                pattern = rf'\s*{re.escape(letter)}[.):\s]+\s*{re.escape(value.strip())}'
                question_text = re.sub(pattern, '', question_text).strip()

    return {
        "question_text": question_text,
        "type": q_type,
        "options": options,
        "option_map": option_map,  # Letter -> full value mapping
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
            input_el = await block.query_selector(
                'input[type="text"], input[type="email"], input[type="number"], '
                'input[type="url"], input[type="tel"], input[type="date"], '
                'input:not([type]), .whsOnd'
            )
            if input_el:
                await input_el.scroll_into_view_if_needed()
                await input_el.click()
                await page.wait_for_timeout(100)
                await input_el.focus()
                await input_el.fill(answer)
                await input_el.press("Tab")
            else:
                # Fallback: find ANY input in the block
                fallback = await block.query_selector("input")
                if fallback:
                    await fallback.fill(answer)
                    await fallback.press("Tab")
                else:
                    # Fallback: contenteditable divs
                    editable = await block.query_selector('[contenteditable="true"], [contenteditable="plaintext-only"]')
                    if editable:
                        await editable.click()
                        await page.wait_for_timeout(100)
                        await page.keyboard.type(answer)
                    else:
                        print(f"[form_bot] ⚠️ Could not find input for '{question['question_text'][:30]}...'")

        elif q_type == "paragraph":
            textarea = await block.query_selector("textarea, .KH7Ywe")
            if textarea:
                await textarea.scroll_into_view_if_needed()
                await textarea.click()
                await page.wait_for_timeout(100)
                await textarea.focus()
                await textarea.fill(answer)
                await textarea.press("Tab")

        elif q_type == "radio":
            option_map = question.get("option_map", {})
            await _select_option(block, answer, "radio", option_map)

        elif q_type == "checkbox":
            # Handle multiple selections (answers separated by ' | ')
            option_map = question.get("option_map", {})
            selected_answers = [a.strip() for a in answer.split("|")]
            for ans in selected_answers:
                await _select_option(block, ans, "checkbox", option_map)

        elif q_type == "dropdown":
            dropdown = await block.query_selector('div[role="listbox"]')
            if dropdown:
                await dropdown.click()
                await page.wait_for_timeout(500)
                option = await page.query_selector(f'div[role="option"]:has-text("{answer}")')
                if option:
                    await option.click()
                    await page.wait_for_timeout(300)

        await page.wait_for_timeout(200)  # Small delay between fields

    except Exception as e:
        print(f"[form_bot] Error filling field '{question['question_text'][:30]}...': {e}")


async def _select_option(block: ElementHandle, answer: str, role: str, option_map: dict = None) -> None:
    """
    Select a radio or checkbox option by matching answer text.
    If option_map is provided, maps AI answer values back to letter labels.
    """
    import re as _re
    answer_lower = answer.lower().strip()
    answer_norm = _re.sub(r'[^\w\s]', '', answer_lower).strip()

    # If we have an option_map (letter -> value), try to find the matching letter
    # AI might return "A. Rs. 3365.75" or "Rs. 3365.75" or just "A"
    if option_map:
        target_letter = None
        
        # Check if AI returned something like "A. Rs. 3365.75" — extract the letter
        letter_match = _re.match(r'^([A-Ea-e])[.)\s]', answer.strip())
        if letter_match:
            target_letter = letter_match.group(1).upper()
        else:
            # Check if the answer matches any VALUE in the option_map
            for letter, value in option_map.items():
                value_lower = value.lower().strip()
                value_norm = _re.sub(r'[^\w\s]', '', value_lower).strip()
                if (answer_lower == value_lower or
                    answer_norm == value_norm or
                    answer_lower in value_lower or
                    value_lower in answer_lower):
                    target_letter = letter
                    break
        
        if target_letter:
            print(f"[form_bot] Mapped answer '{answer}' to letter '{target_letter}' via option_map")
            # Click the radio/checkbox with this letter label
            options = await block.query_selector_all(f'div[role="{role}"]')
            for opt in options:
                data_val = await opt.get_attribute("data-value")
                aria_label = await opt.get_attribute("aria-label")
                opt_inner = (await opt.inner_text()).strip()
                opt_id = (data_val or aria_label or opt_inner or "").strip().upper()
                if opt_id == target_letter:
                    await opt.scroll_into_view_if_needed()
                    await opt.click()
                    return
            # If letter matching failed, fall through to normal matching below

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

    # Fallback: match labels ONLY inside option containers (avoid question text, "Required" etc.)
    option_containers = await block.query_selector_all(f'div[role="{role}"], label[data-value]')
    for container in option_containers:
        labels = await container.query_selector_all("label, span")
        for label in labels:
            label_text = (await label.inner_text()).strip().lower()
            if label_text and (label_text == answer_lower or answer_lower in label_text):
                await container.scroll_into_view_if_needed()
                await container.click()
                return

    # Last resort: click first option (better than leaving a required field blank)
    if options:
        print(f"[form_bot] Could not match option '{answer}', clicking first available")
        await options[0].scroll_into_view_if_needed()
        await options[0].click()


async def _get_option_text(opt: ElementHandle) -> str:
    """
    Extract the best text representation of an option element.
    IMPORTANT: Prefer the full readable text over data-value,
    because data-value is often just a letter label like 'A', 'B'.
    """
    # First try: get the FULL visible text (most reliable for actual option content)
    # Try finding an internal span or label with the option text
    inner_label = await opt.query_selector('span, div[dir="auto"], label')
    if inner_label:
        txt = (await inner_label.inner_text()).strip()
        if txt and len(txt) > 1:  # Skip single-char labels like "A", "B"
            return txt

    # Second try: full inner text of the option element
    full_text = (await opt.inner_text()).strip()
    if full_text and len(full_text) > 1:
        return full_text

    # Third try: aria-label (often has the full option text)
    aria_label = await opt.get_attribute("aria-label")
    if aria_label and aria_label.strip() and len(aria_label.strip()) > 1:
        return aria_label.strip()

    # Fourth try: data-value (often just a letter, but use as last resort)
    data_val = await opt.get_attribute("data-value")
    if data_val and data_val.strip():
        return data_val.strip()

    # Absolute fallback
    return full_text if full_text else ""


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

            # Skip date-like patterns
            date_pattern = rf'{num}\s*/\s*{total}\s*/\s*\d{{2,4}}'
            if re.search(date_pattern, page_text):
                continue

            pre_date = rf'\d+\s*/\s*{num}\s*/\s*{total}'
            if re.search(pre_date, page_text):
                continue

            if total_int > 200 or total_int == 0:
                continue
            if num_int > total_int * 2:
                continue
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
