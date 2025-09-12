# # news_fetcher/newsdata_client.py
# import os
# import requests
# from dotenv import load_dotenv
# import re
# from datetime import datetime
#
# load_dotenv()
#
# NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
#
# AI_KEYWORDS = [
#     "AI", "artificial intelligence", "machine learning", "ML", "neural network",
#     "ChatGPT", "OpenAI", "LLM", "GPT", "Claude", "Anthropic", "DeepMind",
#     "Hugging Face", "Stability AI", "Generative AI", "NLP"
# ]
#
# def filter_ai_articles(articles):
#     clean = []
#     ai_patterns = [re.compile(rf"\b{k.lower()}\b") for k in AI_KEYWORDS]
#
#     for article in articles:
#         text = f"{article.get('title', '')} {article.get('description', '')}".lower()
#         if any(p.search(text) for p in ai_patterns):
#             clean.append(article)
#     return clean
#
# def fetch_newsdata(query="AI", language="en", page=1, page_size=5):
#     if not NEWSDATA_API_KEY:
#         raise ValueError("NewsData.io API key not found in .env")
#
#     url = "https://newsdata.io/api/1/news"
#
#
#     params = {
#         "apikey": NEWSDATA_API_KEY,
#         "q": query,
#         "language": language,
#         "page": page,
#         "page_size": page_size,
#
#     }
#
#     try:
#         resp = requests.get(url, params=params)
#         resp.raise_for_status()
#         data = resp.json()
#
#         articles = []
#         for item in data.get("results", []):
#             articles.append({
#                 "title": item.get("title"),
#                 "link": item.get("link"),
#                 "pubDate": item.get("pubDate"),
#                 "text": item.get("description") or ""
#             })
#
#         return filter_ai_articles(articles)
#
#     except requests.exceptions.HTTPError as e:
#         print(f"NewsData.io error: {e} | {resp.text}")
#         return []
#     except Exception as e:
#         print(f"Unexpected NewsData.io error: {e}")
#         return []



# newsdata_client.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class NewsDataClient:
    def __init__(self):
        self.api_key = os.getenv("NEWSDATA_API_KEY")
        self.base_url = "https://newsdata.io/api/1/news"

    def fetch_latest_news(self, query, language="en", category=None, country=None, page=1):
        params = {
            "apikey": self.api_key,
            "q": query,
            "language": language,
            "category": category,
            "country": country,
            "page": page
        }
        # Remove None or empty string values
        params = {k: v for k, v in params.items() if v}
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()

    def fetch_archive_news(self, query, from_date, to_date, language="en", category=None, country=None, page=1):
        params = {
            "apikey": self.api_key,
            "q": query,
            "from_date": from_date,
            "to_date": to_date,
            "language": language,
            "category": category,
            "country": country,
            "page": page
        }
        params = {k: v for k, v in params.items() if v}
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()
