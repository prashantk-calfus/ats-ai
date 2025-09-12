# mediastack_client.py
import os
import time
import requests
import trafilatura
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

API_KEY = os.getenv("MEDIASTACK_API_KEY")

AI_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "ML", "neural network",
    "ChatGPT", "OpenAI", "LLM", "GPT", "Claude", "Anthropic", "DeepMind",
    "Hugging Face", "Stability AI", "Generative AI", "NLP"
]

BASE_URL = "http://api.mediastack.com/v1/news"


def fetch_mediastack_news(query: str, limit: int = 5) -> List[Dict]:
    params = {
        "access_key": API_KEY,
        "keywords": query,
        "languages": "en",
        "limit": limit,
        "sort": "published_desc"
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("data", [])


def extract_full_text(url: str) -> str:
    """
    Fetch article HTML via requests, then extract text with Trafilatura.
    """
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code == 200:
            downloaded = resp.text
            text = trafilatura.extract(downloaded)
            return text if text else ""
    except Exception as e:
        print(f"Trafilatura extraction failed for {url}: {e}")
    return ""


def fetch_ai_news(limit_per_keyword: int = 5) -> List[Dict]:
    all_articles = []
    seen_links = set()

    for keyword in AI_KEYWORDS:
        try:
            articles = fetch_mediastack_news(keyword, limit=limit_per_keyword)
            for article in articles:
                link = article.get("url")
                if link and link not in seen_links:
                    text = extract_full_text(link)
                    if text:
                        article["text"] = text
                        article["keyword"] = keyword
                        all_articles.append(article)
                        seen_links.add(link)
            # avoid 429 rate limit
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching news for {keyword}: {e}")

    return all_articles
