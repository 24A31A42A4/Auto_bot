# 🤖 AutoForm Bot

<div align="center">
  <img src="assets/hero.png" alt="AutoForm Bot Hero" width="800">
  <br>
  <p><b>An AI-powered automation engine that handles your Google Forms via WhatsApp.</b></p>
  
  ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
  ![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
  ![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
  ![Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)
  ![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
</div>

---

## 🚀 Overview

AutoForm Bot is a robust, end-to-end automation tool designed to help students and professionals automatically fill and submit Google Forms/Quizzes using **Artificial Intelligence**. 

With a simple WhatsApp interface and a premium web dashboard, it handles everything from basic registration details to complex, timed aptitude reasoning.

## ✨ Key Features

- **🧠 Specialized AI Reasoning**: Leverages Google Gemini 2.0+ to solve specialized quiz questions with ultra-high accuracy.
- **📱 WhatsApp Direct Interaction**: No separate app needed! Send links, manage profiles, and get scores directly on WhatsApp.
- **💎 Premium Dashboard**: A glassmorphism-inspired web UI to view submission history, analyze accuracy, and manage your account.
- **🛡️ Secure Persistence**: Your data is yours. Securely stored and managed via Supabase Auth and Database.
- **⚡ Blazing Fast**: Multi-page forms are processed and submitted in ~30 seconds using Playwright.
- **📊 Real-time Stats**: Track your total forms filled and average accuracy visually on the dashboard.

## 📁 Project Structure

```text
Auto_bot/
├── backend/            # Python FastAPI backend
│   ├── main.py         # API & Webhook Entry point
│   ├── src/            # Core logic (AI, DB, WhatsApp, Playwright)
│   └── requirements.txt # Backend dependencies
├── frontend/           # React + Vite frontend
│   ├── src/            # Dashboard & UI components
│   └── package.json    # Frontend dependencies
├── assets/             # Branding & Media
├── Procfile            # Deployment configuration for Railway
└── .env                # Unified Environment Configuration
```

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+ & Node.js 18+
- Meta Developer Account (WhatsApp Cloud API)
- Google Gemini API Key
- Supabase Project

### Installation

1. **Clone the Repo**
   ```bash
   git clone https://github.com/24A31A42A4/Auto_bot.git
   cd Auto_bot
   ```

2. **Setup Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Setup Frontend**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Environment Configuration**
   Create a `.env` in the root directory:
   ```env
   Acess_token="..."
   phone_no_id="..."
   gemini_api_key="..."
   VITE_SUPABASE_URL="..."
   VITE_SUPABASE_ANON_KEY="..."
   VITE_API_URL="http://localhost:8000"
   FRONTEND_URL="http://localhost:5173"
   ```

## 🏎️ Running Locally

1. **Start Backend**: `cd backend && uvicorn main:app --reload`
2. **Start Frontend**: `cd frontend && npm run dev`
3. **Webhook Tunnel**: Use `ngrok http 8000` to expose your local backend to Meta.

## 🚀 Deployment

This project is pre-configured for **Railway**:
1. Connect your GitHub repository.
2. Select the root folder.
3. Railway will auto-detect the `Procfile` for the backend and the static build for the frontend.
4. Ensure all Environment Variables are added to the Railway Dashboard.

---
Built with ❤️ by [24A31A42A4](https://github.com/24A31A42A4)
