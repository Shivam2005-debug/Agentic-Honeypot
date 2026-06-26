# Agentic Honey-Pot for Scam Detection

A finalized AI solution for the India AI Impact Buildathon. This system detects financial scams in real-time, engages the scammer with a "Grandmaster" persona to extract intelligence, and reports findings via secure callback.

## 🚀 Features
- **Real-time Detection:** Llama-3.3-70B analyzes intent (Bank Fraud, Phishing, UPI).
- **Autonomous Honeypot:** "Ramesh", a confused elderly persona, keeps scammers engaged.
- **Intelligence Extraction:** Extracts UPI IDs, Bank Accounts, Emails, and Links.
- **Stateful Memory:** Redis-backed session management.

## 🛠️ Setup
1. Clone repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set `.env` variables (GROQ_API_KEY, REDIS_URL, API_KEY).
4. Run: `uvicorn app.main:app --reload`

## ☁️ Deployment
Deployed on Railway. Protected by `x-api-key`.

## 👥 Authors
- **Shivam Wangikar**
- **Gaurav Yadav**

