import os
import requests
from dotenv import load_dotenv

load_dotenv()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

AI_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "ML", "neural network",
    "ChatGPT", "OpenAI", "LLM", "GPT", "Claude", "Anthropic", "DeepMind",
    "Hugging Face", "Stability AI", "Generative AI", "NLP"
]

def filter_ai_articles(articles):
    clean = []
    for article in articles:
        title = (article.get("title") or "").lower()
        description = (article.get("description") or "").lower()
        if any(k.lower() in title or k.lower() in description for k in AI_KEYWORDS):
            clean.append(article)
    return clean

def fetch_gnews(query="AI", language="en", max_results=5):
    if not GNEWS_API_KEY:
        raise ValueError("GNews API key not found in .env")

    url = "https://gnews.io/api/v4/search"
    params = {
        "q": query,
        "lang": language,
        "max": max_results,
        "token": GNEWS_API_KEY
    }

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for item in data.get("articles", []):
            articles.append({
                "title": item.get("title"),
                "link": item.get("url"),
                "pubDate": item.get("publishedAt"),
                "text": item.get("description") or ""
            })

        return filter_ai_articles(articles)

    except requests.exceptions.HTTPError as e:
        print(f"GNews API error: {e} | {resp.text}")
        return []
    except Exception as e:
        print(f"Unexpected GNews error: {e}")
        return []
