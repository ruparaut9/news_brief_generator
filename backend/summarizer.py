"""
summarizer.py
-------------
Summarizer:
- DistilBART (English summarization + translation for other languages)
- Short/detailed length control
- Clean bullet points
- Supports per-category and consolidated daily briefs
- HuggingFace cache limit + memory cleanup
"""

import os
import gc
import streamlit as st
from transformers import pipeline
from googletrans import Translator   # pip install googletrans==4.0.0-rc1
from datetime import datetime
import torch


# -----------------------------
# HuggingFace cache management
# -----------------------------
# Limit HuggingFace cache size to 5 GB
os.environ["HF_HUB_CACHE_LIMIT"] = "5GB"

# Optional: clear cache at startup (comment out if you prefer keeping models cached)
# delete_cache()

# -----------------------------
# Load summarizer with caching
# -----------------------------
@st.cache_resource
def load_summarizer():
    # Force CPU if you want lower memory usage (device=-1)
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", device=-1)

translator = Translator()

# -----------------------------
# Utility: clean summary endings
# -----------------------------
def clean_summary(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    if text.endswith("..."):
        text = text[:-3].strip()
    if not text.endswith((".", "!", "?")):
        text += "."
    return text

# -----------------------------
# Summarize single text
# -----------------------------
def summarize_text(text: str, length: str = "short", language: str = "en") -> str:
    if not text:
        return ""

    # Truncate overly long inputs (>400 words)
    words = text.split()
    if len(words) > 400:
        text = " ".join(words[:400])

    summarizer = load_summarizer()
    input_len = len(text.split())

    if length == "short":
        max_len = min(40, input_len)
        min_len = 10
    else:  # detailed
        max_len = min(120, input_len + 20)
        min_len = 30

    try:
        summary = summarizer(text, max_length=max_len, min_length=min_len, do_sample=False)[0]['summary_text']
        summary = clean_summary(summary)

        # Translate if language != English
        if language != "en":
            summary = translator.translate(summary, dest=language).text

        return summary
    except Exception as e:
        print("Summarization error:", e)
        return clean_summary(text[:150])
    finally:
        # Free memory buffers after each run
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# -----------------------------
# Summarize multiple articles
# -----------------------------
def summarize_articles(articles: list, style: str = "short", language: str = "en") -> list:
    summaries = []
    texts = []
    for article in articles:
        if isinstance(article, dict):
            text = article.get("description", "") or article.get("title", "")
        else:
            text = str(article)
        texts.append(text)

    # Batch summarization (reduces repeated allocations)
    summarizer = load_summarizer()
    try:
        results = summarizer(texts, max_length=60 if style == "short" else 120,
                             min_length=10 if style == "short" else 30,
                             do_sample=False)
        for res in results:
            summary = clean_summary(res['summary_text'])
            if language != "en":
                summary = translator.translate(summary, dest=language).text
            summaries.append(f"• {summary}")
    except Exception as e:
        print("Batch summarization error:", e)
        for text in texts:
            summaries.append(f"• {clean_summary(text[:150])}")
    finally:
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return summaries

# -----------------------------
# Generate daily brief per category
# -----------------------------
def generate_daily_brief(category: str, articles: list, style: str = "short", lang: str = "en",
                         date: str = None, sources: list = None) -> str:
    if not articles:
        return f"No articles available for {category.capitalize()} on {date or datetime.now().strftime('%d %b %Y')}."

    summaries = summarize_articles(articles, style=style, language=lang)

    header_date = date if date else datetime.now().strftime("%d %b %Y")
    brief = f"Your Daily {category.title()} Brief – {header_date}\n"

    for s in summaries:
        brief += f"{s}\n"

    if sources:
        unique_sources = sorted(set(sources))
        brief += "\nSources: " + ", ".join(unique_sources)

    return brief

# -----------------------------
# Generate consolidated daily brief
# -----------------------------
def generate_consolidated_brief(categories: list, articles: list, style: str = "short", lang: str = "en",
                                date: str = None, sources: list = None) -> str:
    if not articles:
        return f"No articles available for {', '.join(categories)} on {date or datetime.now().strftime('%d %b %Y')}."

    header_date = date if date else datetime.now().strftime("%d %b %Y")
    brief = f"Your Consolidated Daily Brief – {header_date}\n"

    grouped = {}
    for cat in categories:
        grouped[cat] = [a for a in articles if a.get("category", "").lower() == cat.lower()]

    for cat, cat_articles in grouped.items():
        if not cat_articles:
            continue

        # Summarize all articles in one batch
        per_article_summaries = summarize_articles(cat_articles, style="short", language=lang)

        narrative_intro = f"{cat.title()} headlines highlight "
        narrative_body = ", ".join([s.lstrip("• ") for s in per_article_summaries])
        stitched_text = narrative_intro + narrative_body

        try:
            consolidated_summary = summarize_text(stitched_text, length="detailed", language=lang)
        except Exception:
            consolidated_summary = stitched_text

        brief += f"\n**{cat.title()}** – {header_date}\n{consolidated_summary}\n---\n"

    if sources:
        unique_sources = sorted(set(sources))
        brief += "\n*Sources:* " + ", ".join(unique_sources)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    brief += f"\n*Generated on: {timestamp}*"

    return brief
