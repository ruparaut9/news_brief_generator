
"""
fetch_news.py
-------------
 news fetcher:
- Multiple sources (RSS, NewsAPI/GNews, CSV fallback)
- Robust date filtering
- Multi-source aggregation
- SQLite archiving
- Explicit category tagging for summarizer grouping
"""

import feedparser
import requests
import pandas as pd
from datetime import datetime
from backend.database import save_articles, get_articles, init_db
import streamlit as st

init_db()

RSS_FEEDS = {
    "technology": [
        "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://www.wired.com/feed/rss",
        "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"
    ],
    "business": [
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "https://www.reuters.com/business/rss",
        "https://www.ft.com/rss/home/uk",
        "https://economictimes.indiatimes.com/rssfeedsdefault.cms"
    ],
    "sports": [
        "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
        "https://www.espn.com/espn/rss/news",
        "https://www.skysports.com/rss/12040",
        "https://www.thehindu.com/sport/feeder/default.rss"
    ],
    "health": [
        "http://feeds.bbci.co.uk/news/health/rss.xml",
        "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
        "https://rss.medicalnewstoday.com/featurednews.xml",
        "https://www.thehindu.com/sci-tech/health/feeder/default.rss"
    ],
    "entertainment": [
        "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        "https://variety.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://indianexpress.com/section/entertainment/feed/"
    ],
    "politics": [
        "http://feeds.bbci.co.uk/news/politics/rss.xml",
        "https://www.politico.com/rss/politics.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
        "https://www.thehindu.com/news/national/feeder/default.rss"
    ],
}

CSV_PATH = "backend/data/bbc_news.csv"
NEWSAPI_KEY = st.secrets["NEWSAPI_KEY"]
GNEWS_KEY = st.secrets["GNEWS_KEY"]


# -----------------------------
# RSS Fetch
# -----------------------------
def fetch_from_rss(category: str):
    articles = []
    urls = RSS_FEEDS.get(category.lower(), [])
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                articles.append({
                    "title": entry.get("title", ""),
                    "description": entry.get("summary", ""),
                    "source": feed.feed.get("title", "RSS"),
                    "published": entry.get("published", ""),
                    "link": entry.get("link", ""),
                    "category": category  # ✅ explicit tagging
                })
        except Exception as e:
            print(f"RSS fetch failed for {url}: {e}")
    return articles

# -----------------------------
# NewsAPI Fetch
# -----------------------------
def fetch_from_newsapi(category: str, date: str):
    articles = []
    if not NEWSAPI_KEY or date is None:
        return articles
    try:
        url = "https://newsapi.org/v2/everything"
        params = {"q": category, "from": date, "to": date, "language": "en", "apiKey": NEWSAPI_KEY}
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("articles", []):
                articles.append({
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "source": item.get("source", {}).get("name", "NewsAPI"),
                    "published": item.get("publishedAt", ""),
                    "link": item.get("url", ""),
                    "category": category  # ✅ explicit tagging
                })
    except Exception as e:
        print("NewsAPI fetch failed:", e)
    return articles

# -----------------------------
# GNews Fetch
# -----------------------------
def fetch_from_gnews(category: str, date: str = None):
    articles = []
    if not GNEWS_KEY:
        return articles
    try:
        url = f"https://gnews.io/api/v4/search?q={category}&token={GNEWS_KEY}&lang=en"
        if date:
            url += f"&from={date}&to={date}"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("articles", []):
                articles.append({
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "source": item.get("source", {}).get("name", "GNews"),
                    "published": item.get("publishedAt", ""),
                    "link": item.get("url", ""),
                    "category": category  # ✅ explicit tagging
                })
    except Exception as e:
        print("GNews fetch failed:", e)
    return articles

# -----------------------------
# CSV Fallback
# -----------------------------
def fetch_from_csv(category: str, date: str = None):
    articles = []
    try:
        df = pd.read_csv(CSV_PATH)
        df = df[df["category"].str.lower() == category.lower()]
        if date:
            df = df[df["date"] == date]
        for _, row in df.iterrows():
            articles.append({
                "title": row.get("title", ""),
                "description": row.get("description", ""),
                "source": row.get("source", "Offline Dataset"),
                "published": row.get("published", ""),
                "link": row.get("link", ""),
                "category": category  # ✅ explicit tagging
            })
    except Exception as e:
        print("CSV fetch failed:", e)
    return articles

# -----------------------------
# Unified Fetch
# -----------------------------
def fetch_news(category: str, max_items: int = 5, date: str = None):
    category = category.lower()

    if date:
        stored = get_articles(category, date)
        if stored:
            return stored[:max_items]

        # Prioritize APIs first
        articles = fetch_from_newsapi(category, date)
        if not articles:
            articles = fetch_from_gnews(category, date)
        if not articles:
            articles = fetch_from_rss(category)
        if not articles:
            articles = fetch_from_csv(category, date)

        if articles:
            save_articles(articles, category)
            return articles[:max_items]

    # No date provided → try APIs first
    articles = fetch_from_newsapi(category, datetime.now().strftime("%Y-%m-%d"))
    if not articles:
        articles = fetch_from_gnews(category)
    if not articles:
        articles = fetch_from_rss(category)
    if not articles:
        articles = fetch_from_csv(category)

    # Deduplicate
    seen = set()
    unique_articles = []
    for a in articles:
        key = (a["title"].lower().strip(), a["source"])
        if key not in seen:
            seen.add(key)
            unique_articles.append(a)

    if unique_articles:
        save_articles(unique_articles, category)

    return unique_articles[:max_items]

