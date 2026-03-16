# 🤖 AutoForm Bot

AutoForm Bot is a powerful, interactive WhatsApp bot designed to help college students automatically fill and submit Google Forms using AI. It leverages **FastAPI**, **Playwright**, **Gemini AI**, and **Supabase** to provide 100% accurate field filling and specialized aptitude reasoning.

## 🚀 Key Features

- **Expert AI Reasoning**: Powered by Gemini 1.5/2.0 with an "Elite Aptitude Expert" persona for high-accuracy answers.
- **Interactive WhatsApp UI**: Uses official interactive buttons for onboarding, profile management, and navigation.
- **Profile Persistence**: Saves your data (Name, Roll No, Section, Branch, Year, Email) in Supabase so you only register once.
- **Automated Form Filling**: Navigates multi-page forms, handles text inputs, radio buttons, checkboxes, and dropdowns.
- **Score Extraction**: Automatically extracts and returns your score from the form's confirmation page.
- **Profile Management**: Easy interactive "Update" and "Delete" actions with secondary confirmation.

## 📋 Prerequisites

- Python 3.10+
- Meta WhatsApp Cloud API credentials
- Google Gemini API Key
- Supabase Project (Table: `Auto_bot`)
- ngrok (for local webhook tunneling)

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd Auto_bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   Acess_token="your_meta_whatsapp_token"
   phone_no_id="your_whatsapp_phone_number_id"
   gemini_api_key="your_google_gemini_api_key"
   SUPABASE_URL="your_supabase_project_url"
   supabase_key="your_supabase_anon_key"
   VERIFY_TOKEN="your_webhook_verify_token"
   ```

4. **Prepare Database**:
   Create a table named `Auto_bot` in Supabase with the following columns:
   - `phone_number` (text, primary key)
   - `name` (text)
   - `roll_number` (text)
   - `section` (text)
   - `branch` (text)
   - `year` (text)
   - `email` (text)
   - `forms_filled` (int)

## 🏎️ Running the Bot

1. **Start the FastAPI server**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Start the ngrok tunnel**:
   ```bash
   ngrok http 8000
   ```

3. **Configure Webhook**:
   - Go to Meta App Dashboard > WhatsApp > Configuration.
   - Callback URL: `https://your-ngrok-url.ngrok-free.app/webhook`
   - Verify Token: Same as `VERIFY_TOKEN` in `.env`.

## 📱 How to Use

1. **Register**: Send "Hi" to your bot on WhatsApp. Click **"How to Register?"** and send your details:
   `Name | Roll No | Section | Branch | Year | Email`
2. **Fill Form**: Forward any Google Form link to the bot.
3. **Wait**: The bot will process the form in ~30 seconds and reply with your result/score.
4. **Manage**: Use the interactive menu to **Update Profile** or **Delete Profile**.

## 🏗️ Architecture

- **`main.py`**: Webhook entry point and API routes.
- **`src/webhook_handler.py`**: Bot logic, message routing, and button interaction handling.
- **`src/form_bot.py`**: Playwright automation engine for form filling.
- **`src/ai_helper.py`**: Google Gemini SDK integration for expert-level answering.
- **`src/profile_detector.py`**: Logic to identify personal fields vs. quiz questions.
- **`src/database.py`**: Supabase storage interaction.
- **`src/whatsapp.py`**: Meta Graph API integration for sending messages and buttons.

---
Built with ❤️ for students.
