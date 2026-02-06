# 📰 AI-Based Daily News Brief Generator

Your personalized, AI-powered news summaries built with Streamlit and HuggingFace Transformers.

---

## 🚀 Features
- Summarizes daily news articles into **short or detailed briefs**
- Supports **Consolidated** (all categories together) or **Per-Category** summaries
- Language translation (default English, supports others via Google Translate)
- Memory usage monitoring inside the app
- Built with **DistilBART** for efficient summarization

---

## 📂 Project Structure

news_brief_generator/
├── backend/
│   ├── summarizer.py          # Summarization + translation logic
│   ├── fetch_news.py          # Fetch articles from APIs/dataset
│   ├──app.py                   #Backend runner
│   └── user_preferences.py    # Handle user preference storage
├── frontend/
│   └── app.py                 # Streamlit app entry point
├── data/
│   └── bbc_news.csv           # Fallback dataset
├── requirements.txt           # Dependencies
├── runtime.txt                # Python version for deployment
└── README.md                  # Documentation

