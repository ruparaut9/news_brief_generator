import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.fetch_news import fetch_news
from backend.fetch_news import fetch_news
import datetime

categories = ["technology", "business", "sports", "health", "entertainment", "politics"]

today = datetime.date.today().strftime("%Y-%m-%d")

for cat in categories:
    articles = fetch_news(cat, max_items=10, date=today)
    print(f"Fetched {len(articles)} {cat} articles for {today}")
