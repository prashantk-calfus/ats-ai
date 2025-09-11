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

def filter_ai_articles(articles):
    clean = []
    for article in articles:
        title = (article.get("title") or "").lower()
        description = (article.get("description") or "").lower()
        if any(k.lower() in title or k.lower() in description for k in AI_KEYWORDS):
            clean.append(article)
    return clean

def fetch_thenewsapi(query="AI", language="en", page_size=5):
    if not THENEWSAPI_API_KEY:
        raise ValueError("TheNewsAPI key not found in .env")

    url = "https://api.thenewsapi.com/v1/news/all"
    params = {
        "q": query,
        "language": language,
        "page_size": page_size,
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
