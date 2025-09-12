import os
import requests
from dotenv import load_dotenv

load_dotenv()

THENEWSAPI_API_KEY = os.getenv("THENEWSAPI_API_KEY")

AI_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "ML", "neural network",
    "ChatGPT", "OpenAI", "LLM", "GPT", "Claude", "Anthropic", "DeepMind",
    "Hugging Face", "Stability AI", "Generative AI", "NLP"
]

import re

def filter_ai_articles(articles):
    clean = []
    # compile regex patterns for all keywords
    ai_patterns = [re.compile(rf"\b{k.lower()}\b") for k in AI_KEYWORDS]

    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        if any(p.search(text) for p in ai_patterns):
            clean.append(article)
    return clean


def fetch_thenewsapi(query="AI", language="en", page_size=5):
    if not THENEWSAPI_API_KEY:
        raise ValueError("TheNewsAPI key not found in .env")

    url = "https://api.thenewsapi.com/v1/news/all"
    from datetime import datetime

    today = datetime.utcnow().date()  # UTC date
    params = {
        "q": query,
        "language": language,
        "page_size": page_size,
        "from": today.isoformat(),
        "to": today.isoformat(),
        "api_token": THENEWSAPI_API_KEY
    }

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for item in data.get("data", []):
            articles.append({
                "title": item.get("title"),
                "link": item.get("url"),
                "pubDate": item.get("published_at"),
                "text": item.get("description") or ""
            })

        return filter_ai_articles(articles)

    except requests.exceptions.HTTPError as e:
        print(f"TheNewsAPI error: {e} | {resp.text}")
        return []
    except Exception as e:
        print(f"Unexpected TheNewsAPI error: {e}")
        return []
