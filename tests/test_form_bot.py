"""
test_form_bot.py — Unit tests for profile detection and webhook message routing.
"""

import pytest
from src.profile_detector import detect_personal_field, get_profile_value
from src.webhook_handler import is_google_form_link, is_update_command, parse_registration_data


# ─── Profile Detector Tests ─────────────────────────────────────────


class TestProfileDetector:
    def test_detects_name_field(self):
        assert detect_personal_field("What is your name?") == "name"
        assert detect_personal_field("Enter your full name") == "name"
        assert detect_personal_field("Student Name") == "name"

    def test_detects_roll_number(self):
        assert detect_personal_field("Roll Number") == "roll_number"
        assert detect_personal_field("Enter your register number") == "roll_number"
        assert detect_personal_field("Regd No.") == "roll_number"

    def test_detects_college(self):
        assert detect_personal_field("College Name") == "section"
        assert detect_personal_field("Name of the institution") == "section"

    def test_detects_branch(self):
        assert detect_personal_field("Branch") == "branch"
        assert detect_personal_field("Department") == "branch"

    def test_detects_year(self):
        assert detect_personal_field("Year of Study") == "year"
        assert detect_personal_field("Current Semester") == "year"

    def test_detects_email(self):
        assert detect_personal_field("Email ID") == "email"
        assert detect_personal_field("Your email address") == "email"

    def test_detects_phone(self):
        assert detect_personal_field("Phone Number") == "phone_number"
        assert detect_personal_field("Mobile Number") == "phone_number"

    def test_returns_none_for_quiz_questions(self):
        assert detect_personal_field("What is the capital of France?") is None
        assert detect_personal_field("Explain the concept of OOP") is None
        assert detect_personal_field("Which of the following is correct?") is None

    def test_get_profile_value(self):
        profile = {"name": "Rohit", "roll_number": "22EG1A0501", "section": "A"}
        assert get_profile_value(profile, "name") == "Rohit"
        assert get_profile_value(profile, "roll_number") == "22EG1A0501"
        assert get_profile_value(profile, "missing_field") == ""


# ─── Webhook Handler Tests ──────────────────────────────────────────


class TestWebhookHandler:
    def test_detects_google_form_short_link(self):
        url = is_google_form_link("Check this: https://forms.gle/abc123def")
        assert url == "https://forms.gle/abc123def"

    def test_detects_google_form_long_link(self):
        url = is_google_form_link("https://docs.google.com/forms/d/e/1FAIpQL/viewform")
        assert url == "https://docs.google.com/forms/d/e/1FAIpQL/viewform"

    def test_returns_none_for_non_form_links(self):
        assert is_google_form_link("https://google.com") is None
        assert is_google_form_link("Hello world") is None
        assert is_google_form_link("https://youtube.com/watch?v=123") is None

    def test_is_update_command(self):
        assert is_update_command("UPDATE") is True
        assert is_update_command("UPDATE\nRohit | 22EG | Pragati | CSE | 2nd") is True
        assert is_update_command("update") is True
        assert is_update_command("Hello") is False

    def test_parse_registration_data(self):
        data = parse_registration_data("Rohit | 22EG1A0501 | A | CSE | 2nd Year")
        assert data is not None
        assert data["name"] == "Rohit"
        assert data["roll_number"] == "22EG1A0501"
        assert data["section"] == "A"
        assert data["branch"] == "CSE"
        assert data["year"] == "2nd Year"

    def test_parse_registration_with_email(self):
        data = parse_registration_data("Rohit | 22EG | Pragati | CSE | 2nd | rohit@mail.com")
        assert data["email"] == "rohit@mail.com"

    def test_parse_registration_with_update_prefix(self):
        data = parse_registration_data("UPDATE\nRohit | 22EG | Pragati | CSE | 2nd")
        assert data is not None
        assert data["name"] == "Rohit"

    def test_parse_registration_too_few_parts(self):
        assert parse_registration_data("Rohit | 22EG") is None
        assert parse_registration_data("Just a name") is None
