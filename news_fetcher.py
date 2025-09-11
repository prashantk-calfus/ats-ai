# import urllib
#
# import requests
# import xml.etree.ElementTree as ET
#
#
# def fetch_google_news(query="artificial intelligence", lang="en", region="US"):
#     encoded_query = urllib.parse.quote(query)
#     url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={region}&ceid={region}:{lang}"
#
#     resp = requests.get(url)
#     root = ET.fromstring(resp.content)
#
#     results = []
#     for item in root.findall(".//item"):
#         results.append({
#             "title": item.find("title").text,
#             "link": item.find("link").text,
#             "published": item.find("pubDate").text,
#         })
#     return results

#
# import requests
# import os
# from dotenv import load_dotenv
#
# # Load variables from .env file
# load_dotenv()
#
# NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
#
# def fetch_ai_news(query="artificial intelligence", language="en"):
#     url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={query}&language={language}"
#
#     try:
#         resp = requests.get(url)
#         resp.raise_for_status()
#         data = resp.json()
#
#         results = []
#         for item in data.get("results", []):
#             results.append({
#                 "title": item.get("title"),
#                 "link": item.get("link"),
#                 "pubDate": item.get("pubDate")
#             })
#         return results
#     except Exception as e:
#         print(f"Error fetching news: {e}")
#         return []

#
# import requests
# import os
# from dotenv import load_dotenv
#
# # Load variables from .env file
# load_dotenv()
#
# NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
#
# # 🔑 Keywords to filter only AI-related news
# AI_KEYWORDS = [
#     "AI", "artificial intelligence", "machine learning", "ML", "neural network",
#     "ChatGPT", "OpenAI", "LLM", "GPT", "Claude", "Anthropic", "DeepMind",
#     "Hugging Face", "Stability AI", "Generative AI", "NLP"
# ]
#
# def filter_ai_articles(articles):
#     clean = []
#     for article in articles:
#         title = (article.get("title") or "").lower()
#         text = (article.get("text") or "").lower()
#         if any(k.lower() in title or k.lower() in text for k in AI_KEYWORDS):
#             clean.append(article)
#     return clean
#
#
# def fetch_ai_news(query="artificial intelligence OR AI OR machine learning OR ChatGPT OR OpenAI OR generative AI",
#                   language="en"):
#     url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={query}&language={language}"
#
#     try:
#         resp = requests.get(url)
#         resp.raise_for_status()
#         data = resp.json()
#
#         results = []
#         for item in data.get("results", []):
#             results.append({
#                 "title": item.get("title"),
#                 "link": item.get("link"),
#                 "pubDate": item.get("pubDate"),
#                 "text": item.get("description") or ""  # sometimes NewsData gives short text in description
#             })
#
#         # ✅ filter results here
#         return filter_ai_articles(results)
#
#     except Exception as e:
#         print(f"Error fetching news: {e}")
#         return []
