# NewsApi
# from fastapi import FastAPI
# from news_fetcher.newsapi_client import fetch_ai_news
# import trafilatura
#
# app = FastAPI(title="AI News API")
#
# def extract_full_text(url: str):
#     try:
#         downloaded = trafilatura.fetch_url(url)
#         if downloaded:
#             text = trafilatura.extract(downloaded)
#             return text if text else ""
#         return ""
#     except Exception as e:
#         print(f"Error extracting {url}: {e}")
#         return ""
#
# @app.get("/today-articles")
# def get_today_articles(query: str = "AI"):
#     news_items = fetch_ai_news(query=query)
#     clean_news = []
#
#     for n in news_items:
#         text = extract_full_text(n.get("link", ""))
#         if text:
#             n["text"] = text
#             clean_news.append(n)
#
#     return {"count": len(clean_news), "articles": clean_news}




# GNews
# from fastapi import FastAPI
# from news_fetcher.gnews_client import fetch_gnews
# import trafilatura
#
# app = FastAPI(title="AI News API")
#
# def extract_full_text(url: str):
#     try:
#         downloaded = trafilatura.fetch_url(url)
#         if downloaded:
#             text = trafilatura.extract(downloaded)
#             return text if text else ""
#         return ""
#     except Exception as e:
#         print(f"Error extracting {url}: {e}")
#         return ""
#
# @app.get("/today-articles")
# def get_today_articles(query: str = "AI"):
#     """
#     Fetch AI-related news from GNews (first 5),
#     extract full text using trafilatura.
#     """
#     # Fetch only 5 articles from GNews
#     gnews_articles = fetch_gnews(query=query, max_results=5)
#
#     clean_articles = []
#     for article in gnews_articles:
#         text = extract_full_text(article.get("link", ""))
#         if text:
#             article["text"] = text
#             clean_articles.append(article)
#
#     return {"count": len(clean_articles), "articles": clean_articles}





from fastapi import FastAPI
from news_fetcher.thenewsapi_client import fetch_thenewsapi
import trafilatura

app = FastAPI(title="AI News API")

def extract_full_text(url: str):
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            return text if text else ""
        return ""
    except Exception as e:
        print(f"Error extracting {url}: {e}")
        return ""

@app.get("/today-articles")
def get_thenewsapi_articles(query: str = "AI"):
    """
    Fetch AI-related news from TheNewsAPI.com (first 5),
    extract full text using trafilatura.
    """
    thenewsapi_articles = fetch_thenewsapi(query=query, page_size=5)

    clean_articles = []
    for article in thenewsapi_articles:
        text = extract_full_text(article.get("link", ""))
        if text:
            article["text"] = text
            clean_articles.append(article)

    return {"count": len(clean_articles), "articles": clean_articles}
