"""
frontend/app.py
---------------
Streamlit frontend:
- Pastel light blue theme
- Preferences sidebar
- Separate buttons: Save Preferences + Generate Brief
- Toggle: Consolidated vs Per-Category briefs
- Clean markdown output
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import datetime
import streamlit as st
import psutil

from backend.fetch_news import fetch_news
from backend.summarizer import generate_daily_brief, generate_consolidated_brief

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="AI-Based Daily News Brief Generator",
    page_icon="📰",
    layout="wide"
)

# -----------------------------
# Custom CSS
# -----------------------------
st.markdown(
    """
    <style>
    body { background-color: #e6f2ff; font-family: "Segoe UI", sans-serif; }
    .stButton>button {
        background-color: #4da6ff;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5em 1em;
        font-weight: bold;
    }
    h1, h2, h3 { color: #004080; }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Title
# -----------------------------
st.title("📰 AI-Based Daily News Brief Generator")
st.write("Your personalized, AI-powered news summaries.")

# -----------------------------
# Sidebar Preferences
# -----------------------------
st.sidebar.header("⚙️ Preferences")
categories = ["Technology", "Business", "Sports", "Health", "Entertainment", "Politics"]

selected_categories = st.sidebar.multiselect(
    "Select News Segments",
    categories,
    default=st.session_state.get("categories", ["Technology", "Business"])
)

summary_length = st.sidebar.radio(
    "Summary Length",
    ["Short", "Detailed"],
    index=0 if st.session_state.get("summary_length", "short") == "short" else 1
)

selected_date = st.sidebar.date_input(
    "Select Date",
    value=st.session_state.get("date", datetime.date.today())
)
date_str = selected_date.strftime("%Y-%m-%d")

language = st.sidebar.selectbox(
    "Language",
    ["en", "hi", "fr", "es"],
    index=["en", "hi", "fr", "es"].index(st.session_state.get("language", "en"))
)

# Toggle for brief type
brief_type = st.sidebar.radio(
    "Choose Brief Type",
    ["Consolidated", "Per-Category"],
    index=0
)

# Save Preferences
if st.sidebar.button("💾 Save Preferences"):
    st.session_state["categories"] = selected_categories
    st.session_state["summary_length"] = summary_length.lower()
    st.session_state["date"] = selected_date
    st.session_state["language"] = language
    st.session_state["brief_type"] = brief_type
    st.sidebar.success("Preferences saved!")

# Generate Brief
if st.sidebar.button("📰 Generate Daily Brief"):
    st.session_state["generate"] = True

# -----------------------------
# Home Page Experience
# -----------------------------
if st.session_state.get("generate", False):

    if brief_type == "Consolidated":
        # Consolidated Daily Brief
        st.subheader("📰 Daily Consolidated Brief")
        all_articles, all_sources = [], []
        for category in selected_categories:
            articles = fetch_news(category.lower(), max_items=2, date=date_str)  # limit to 2
            all_articles.extend(articles)
            all_sources.extend([a.get("source", "") for a in articles])

        consolidated = generate_consolidated_brief(
            selected_categories,
            all_articles,
            style=summary_length.lower(),
            lang=language,
            date=date_str,
            sources=all_sources
        )

        st.markdown(consolidated)

    else:  # Per-Category
        st.subheader("Category Highlights")
        for category in selected_categories:
            articles = fetch_news(category.lower(), max_items=2, date=date_str)  # limit to 2
            sources = [a.get("source", "") for a in articles]
            brief = generate_daily_brief(
                category,
                articles,
                style=summary_length.lower(),
                lang=language,
                date=date_str,
                sources=sources
            )

            st.markdown(f"**{category} Highlights – {date_str}**")
            for line in brief.split("\n"):
                if line.strip().startswith("•"):
                    st.markdown(line.strip())
            if sources:
                st.caption(f"Sources: {', '.join(sorted(set(sources)))}")

    st.session_state["generate"] = False

# -----------------------------
# Memory Usage Display
# -----------------------------
process = psutil.Process(os.getpid())
mem_usage_mb = process.memory_info().rss / (1024 * 1024)
st.sidebar.write(f"💾 Current memory usage: {mem_usage_mb:.2f} MB")
import psutil, os
process = psutil.Process(os.getpid())
print("Memory usage MB:", process.memory_info().rss / (1024 * 1024))
