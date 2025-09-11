import os
import requests
from dotenv import load_dotenv

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# AI keywords filter
AI_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "ML", "neural network",
    "ChatGPT", "OpenAI", "LLM", "GPT", "Claude", "Anthropic", "DeepMind",
    "Hugging Face", "Stability AI", "Generative AI", "NLP"
]

def filter_ai_articles(articles):
    clean = []
    for article in articles:
        title = (article.get("title") or "").lower()
        text = (article.get("text") or "").lower()
        if any(k.lower() in title or k.lower() in text for k in AI_KEYWORDS):
            clean.append(article)
    return clean

def fetch_ai_news(query="artificial intelligence", language="en"):
    if not NEWS_API_KEY:
        raise ValueError("API key not found. Check your .env file.")

    url = f"https://newsdata.io/api/1/news"
    params = {
        "apikey": NEWS_API_KEY,
        "q": query,
        "language": language,
    }

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "pubDate": item.get("pubDate"),
                "text": item.get("description") or ""
            })

        return filter_ai_articles(results)

    except requests.exceptions.HTTPError as e:
        print(f"Error fetching news: {e} | {resp.text}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []
