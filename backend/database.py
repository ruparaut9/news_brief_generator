"""
database.py
-----------
Purpose:
Handles both user preferences and article storage using SQLite.
Supports:
- Saving multiple categories per user, along with summary style and language
- Storing fetched articles daily for dynamic date retrieval
"""

import sqlite3
import json
from typing import List, Dict
from datetime import datetime

DB_NAME = "backend/appdata.db"


# -----------------------------
# Initialize database
# -----------------------------
def init_db() -> None:
    """
    Initialize the database.
    Creates preferences and articles tables if they do not exist.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Preferences table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS preferences (
                    user_id TEXT PRIMARY KEY,
                    categories TEXT,       -- stored as JSON list
                    style TEXT,            -- "short" or "detailed"
                    language TEXT          -- e.g., "en", "hi", "fr", "es"
                )
                """
            )
            # Articles table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    source TEXT,
                    published TEXT,
                    category TEXT,
                    date_fetched DATE
                )
                """
            )
            conn.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")


# -----------------------------
# Preferences Management
# -----------------------------
def save_preferences(user_id: str, categories: List[str], style: str = "short", language: str = "en") -> None:
    """Save user preferences."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute(
                """
                REPLACE INTO preferences (user_id, categories, style, language)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, json.dumps(categories), style, language),
            )
            conn.commit()
    except Exception as e:
        print(f"Error saving preferences for {user_id}: {e}")


def load_preferences(user_id: str) -> Dict[str, str]:
    """Load preferences for a given user_id. Returns defaults if none saved."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT categories, style, language FROM preferences WHERE user_id = ?",
                (user_id,),
            )
            row = c.fetchone()

        if row:
            return {
                "categories": json.loads(row[0]),
                "summary_length": row[1],
                "language": row[2],
            }
        else:
            return {
                "categories": ["technology"],
                "summary_length": "short",
                "language": "en",
            }
    except Exception as e:
        print(f"Error loading preferences for {user_id}: {e}")
        return {
            "categories": ["technology"],
            "summary_length": "short",
            "language": "en",
        }


# -----------------------------
# Articles Management
# -----------------------------
def save_articles(articles: List[Dict], category: str) -> None:
    """Save fetched articles into the database with today's date."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            for art in articles:
                c.execute(
                    """
                    INSERT INTO articles (title, description, source, published, category, date_fetched)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        art.get("title", ""),
                        art.get("description", ""),
                        art.get("source", ""),
                        art.get("published", ""),
                        category,
                        datetime.now().date()
                    )
                )
            conn.commit()
    except Exception as e:
        print(f"Error saving articles for {category}: {e}")


def get_articles(category: str, date: str) -> List[Dict]:
    """Retrieve articles for a given category and date."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT title, description, source, published FROM articles WHERE category=? AND date_fetched=?",
                (category, date),
            )
            rows = c.fetchall()
        return [{"title": r[0], "description": r[1], "source": r[2], "published": r[3]} for r in rows]
    except Exception as e:
        print(f"Error retrieving articles for {category} on {date}: {e}")
        return []
