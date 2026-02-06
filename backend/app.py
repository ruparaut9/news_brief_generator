
"""
backend/app.py
---------------
FastAPI backend for Daily News Brief Generator.
Competition-ready: integrates preferences, article storage, summarization,
multi-source aggregation, and dynamic date retrieval.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from datetime import datetime
from typing import List, Optional
from backend.fetch_news import fetch_news
from backend.summarizer import generate_daily_brief
from backend.database import init_db, load_preferences, save_preferences
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Daily News Brief Generator")

# Initialize unified database (preferences + articles)
init_db()

# Mount static directory for favicon
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("backend", "static", "favicon.ico"))


# -----------------------------
# Single-category brief endpoint
# -----------------------------
@app.get("/brief/{category}")
def get_brief(
    category: str,
    summary_length: str = "short",
    date: Optional[str] = None,
    language: str = "en"
):
    # Fetch articles dynamically (DB → NewsAPI/GNews → RSS → CSV)
    articles = fetch_news(category, max_items=5, date=date)
    sources = [a.get("source", "") for a in articles]

    # Generate formatted brief
    brief_text = generate_daily_brief(
        category=category,
        articles=articles,
        style=summary_length,
        lang=language,
        date=date,
        sources=sources
    )

    display_date = date if date else datetime.now().strftime("%d %b %Y")
    return {
        "date": display_date,
        "category": category,
        "articles": articles,
        "daily_brief": brief_text,
        "sources": list(sorted(set(sources)))  # deduplicated
    }


# -----------------------------
# Multi-category personalized daily brief endpoint
# -----------------------------
@app.get("/daily_brief/")
def get_daily_brief(
    user_id: str,
    summary_length: str = "short",
    date: Optional[str] = None,
    language: str = "en"
):
    # Load user preferences
    prefs = load_preferences(user_id)
    categories = prefs.get("categories", ["technology"])
    language = prefs.get("language", language)

    briefs = []
    all_sources = set()

    # Generate briefs for each category
    for cat in categories:
        articles = fetch_news(cat, max_items=5, date=date)
        sources = [a.get("source", "") for a in articles]
        all_sources.update(sources)

        brief_text = generate_daily_brief(
            category=cat,
            articles=articles,
            style=summary_length,
            lang=language,
            date=date,
            sources=sources
        )
        briefs.append(brief_text)

    display_date = date if date else datetime.now().strftime("%d %b %Y")
    return {
        "user_id": user_id,
        "date": display_date,
        "daily_brief": "\n\n".join(briefs),
        "sources": list(sorted(all_sources))  # deduplicated
    }


# -----------------------------
# Preferences endpoints
# -----------------------------
@app.get("/preferences")
def get_preferences(user_id: str = "demo"):
    return load_preferences(user_id)


@app.post("/preferences/save")
def set_preferences(
    user_id: str,
    categories: List[str],
    style: str = "short",
    language: str = "en"
):
    save_preferences(user_id, categories, style, language)
    return {"message": "Preferences saved successfully"}
