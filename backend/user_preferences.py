"""
preferences.py
--------------
Purpose:
Manage user preferences (categories, language, reading style).
Stores preferences in a local JSON file for persistence.
"""

import json
import os

PREF_PATH = "data/preferences.json"

# -----------------------------
# Save preferences
# -----------------------------
def save_preferences(user_id: str, prefs: dict):
    """
    Save user preferences to JSON file.
    """
    if os.path.exists(PREF_PATH):
        with open(PREF_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    data[user_id] = prefs

    with open(PREF_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# -----------------------------
# Load preferences
# -----------------------------
def load_preferences(user_id: str):
    """
    Load user preferences from JSON file.
    """
    if not os.path.exists(PREF_PATH):
        return None

    with open(PREF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get(user_id, None)

# -----------------------------
# Update preferences
# -----------------------------
def update_preferences(user_id: str, prefs: dict):
    """
    Update existing preferences.
    """
    save_preferences(user_id, prefs)
