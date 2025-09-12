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
from http.client import HTTPException

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




# TheNewsApi
# from fastapi import FastAPI
# from news_fetcher.thenewsapi_client import fetch_thenewsapi
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
# @app.get("/today-news")
# def get_thenewsapi_articles(query: str = "AI"):
#     """
#     Fetch AI-related news from TheNewsAPI.com (first 5),
#     extract full text using trafilatura.
#     """
#     thenewsapi_articles = fetch_thenewsapi(query=query, page_size=5)
#
#     clean_articles = []
#     for article in thenewsapi_articles:
#         text = extract_full_text(article.get("link", ""))
#         if text:
#             article["text"] = text
#             clean_articles.append(article)
#
#     return {"count": len(clean_articles), "articles": clean_articles}



# # NewsData
# from fastapi import FastAPI, Query, HTTPException
# from news_fetcher.newsdata_client import NewsDataClient
# from typing import Optional
# import trafilatura
#
# app = FastAPI(title="AI News API", version="1.0")
# client = NewsDataClient()
#
#
# def extract_full_text(url: str) -> str:
#     """
#     Fetch and extract full text from the article URL using Trafilatura
#     """
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
#
# @app.get("/today-news")
# def get_latest_news(
#     query: str = Query("artificial intelligence", description="Search keyword"),
#     language: str = Query("en", description="Language code"),
#     category: Optional[str] = Query(None, description="News category"),
#     country: Optional[str] = Query(None, description="Country code"),
#     page: int = Query(0, ge=0, description="Pagination page number"),
#     fetch_full_text: bool = Query(True, description="Whether to fetch full article text")
# ):
#     """
#     Fetch latest news from NewsData.io and optionally extract full text using Trafilatura
#     """
#     try:
#         news_data = client.fetch_latest_news(
#             query=query,
#             language=language,
#             category=category,
#             country=country,
#             page=page
#         )
#
#         articles = news_data.get("results", [])
#
#         if fetch_full_text:
#             for article in articles:
#                 link = article.get("link")
#                 if link:
#                     article["full_text"] = extract_full_text(link)
#
#         return {"count": len(articles), "articles": articles}
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @app.get("/archive-news")
# def get_archive_news(
#     query: str = Query(..., description="Search keyword"),
#     from_date: str = Query(..., description="Start date YYYY-MM-DD"),
#     to_date: str = Query(..., description="End date YYYY-MM-DD"),
#     language: str = Query("en", description="Language code"),
#     category: Optional[str] = Query(None, description="News category"),
#     country: Optional[str] = Query(None, description="Country code"),
#     page: int = Query(0, ge=0, description="Pagination page number"),
#     fetch_full_text: bool = Query(True, description="Whether to fetch full article text")
# ):
#     """
#     Fetch archive/historical news and optionally extract full text using Trafilatura
#     """
#     try:
#         news_data = client.fetch_archive_news(
#             query=query,
#             from_date=from_date,
#             to_date=to_date,
#             language=language,
#             category=category,
#             country=country,
#             page=page
#         )
#
#         articles = news_data.get("results", [])
#
#         if fetch_full_text:
#             for article in articles:
#                 link = article.get("link")
#                 if link:
#                     article["full_text"] = extract_full_text(link)
#
#         return {"count": len(articles), "articles": articles}
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



# Mediastack
# from fastapi import FastAPI, Query
# from news_fetcher.mediastack_client import fetch_ai_news
#
# app = FastAPI(title="AI News API - Mediastack + Trafilatura")
#
# @app.get("/today-news")
# def get_ai_news(limit_per_keyword: int = Query(5, ge=1, le=10)):
#     try:
#         articles = fetch_ai_news(limit_per_keyword=limit_per_keyword)
#         return {"count": len(articles), "articles": articles}
#     except Exception as e:
#         return {"error": str(e)}
#


from fastapi import FastAPI, Query, HTTPException
from typing import Optional, List, Dict
import trafilatura


from summarizer.summarizer import NewsSummarizer
# === IMPORT CLIENTS ===
from news_fetcher.newsapi_client import fetch_ai_news as fetch_newsapi_ai
from news_fetcher.gnews_client import fetch_gnews
from news_fetcher.thenewsapi_client import fetch_thenewsapi
from news_fetcher.newsdata_client import NewsDataClient
from news_fetcher.mediastack_client import fetch_ai_news as fetch_mediastack_ai
from news_fetcher.reddit_client import fetch_today_ai_posts

# Create app
app = FastAPI(title="AI News API", version="2.0")
summarizer = NewsSummarizer()
# Trafilatura helper
def extract_full_text(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            return text if text else ""
        return ""
    except Exception as e:
        print(f"Error extracting {url}: {e}")
        return ""


# ===================== Individual Sources =====================

@app.get("/newsapi-articles")
def get_newsapi_articles(query: str = "AI"):
    news_items = fetch_newsapi_ai(query=query)
    clean_news = []
    for n in news_items:
        text = extract_full_text(n.get("link", ""))
        if text:
            n["text"] = text
            clean_news.append(n)
    return {"count": len(clean_news), "articles": clean_news}


@app.get("/gnews-articles")
def get_gnews_articles(query: str = "AI"):
    gnews_articles = fetch_gnews(query=query, max_results=5)
    clean_articles = []
    for article in gnews_articles:
        text = extract_full_text(article.get("link", ""))
        if text:
            article["text"] = text
            clean_articles.append(article)
    return {"count": len(clean_articles), "articles": clean_articles}


@app.get("/thenewsapi-articles")
def get_thenewsapi_articles(query: str = "AI"):
    thenewsapi_articles = fetch_thenewsapi(query=query, page_size=5)
    clean_articles = []
    for article in thenewsapi_articles:
        text = extract_full_text(article.get("link", ""))
        if text:
            article["text"] = text
            clean_articles.append(article)
    return {"count": len(clean_articles), "articles": clean_articles}


client = NewsDataClient()

@app.get("/newsdata-latest")
def get_latest_news(
    query: str = Query("artificial intelligence"),
    language: str = Query("en"),
    category: Optional[str] = None,
    country: Optional[str] = None,
    page: int = Query(0, ge=0),
    fetch_full_text: bool = True
):
    try:
        news_data = client.fetch_latest_news(
            query=query,
            language=language,
            category=category,
            country=country,
            page=page
        )
        articles = news_data.get("results", [])
        if fetch_full_text:
            for article in articles:
                link = article.get("link")
                if link:
                    article["full_text"] = extract_full_text(link)
        return {"count": len(articles), "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/newsdata-archive")
def get_archive_news(
    query: str,
    from_date: str,
    to_date: str,
    language: str = "en",
    category: Optional[str] = None,
    country: Optional[str] = None,
    page: int = Query(0, ge=0),
    fetch_full_text: bool = True
):
    try:
        news_data = client.fetch_archive_news(
            query=query,
            from_date=from_date,
            to_date=to_date,
            language=language,
            category=category,
            country=country,
            page=page
        )
        articles = news_data.get("results", [])
        if fetch_full_text:
            for article in articles:
                link = article.get("link")
                if link:
                    article["full_text"] = extract_full_text(link)
        return {"count": len(articles), "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mediastack-news")
def get_ai_news(limit_per_keyword: int = Query(5, ge=1, le=10)):
    try:
        articles = fetch_mediastack_ai(limit_per_keyword=limit_per_keyword)
        return {"count": len(articles), "articles": articles}
    except Exception as e:
        return {"error": str(e)}


# ===================== Combined Endpoint =====================
@app.get("/all-news")
def get_all_sources(
    query: str = Query("artificial intelligence", description="Search keyword"),
    language: str = Query("en", description="Language code"),
    category: Optional[str] = Query(None, description="News category"),
    country: Optional[str] = Query(None, description="Country code"),
    page: int = Query(0, ge=0, description="Pagination page number"),
    fetch_full_text: bool = Query(True, description="Whether to fetch full article text")
) -> Dict:
    """
    Fetch news from all sources and merge them with deduplication.
    """
    all_articles: List[Dict] = []
    seen_links = set()

    # --- NewsAPI ---
    try:
        newsapi_articles = fetch_newsapi_ai(query=query)
        for n in newsapi_articles:
            link = n.get("link")
            if link and link not in seen_links:
                n["source"] = "NewsAPI"
                n["text"] = extract_full_text(link) if fetch_full_text else ""
                all_articles.append(n)
                seen_links.add(link)
    except Exception as e:
        print("NewsAPI error:", e)
        print("Error",e)
    # --- GNews ---
    try:
        gnews_articles = fetch_gnews(query=query, max_results=5)
        for n in gnews_articles:
            link = n.get("link")
            if link and link not in seen_links:
                n["source"] = "GNews"
                n["text"] = extract_full_text(link) if fetch_full_text else ""
                all_articles.append(n)
                seen_links.add(link)
    except Exception as e:
        print("GNews error:", e)

    # --- TheNewsAPI ---
    try:
        thenewsapi_articles = fetch_thenewsapi(query=query, page_size=5)
        for n in thenewsapi_articles:
            link = n.get("link")
            if link and link not in seen_links:
                n["source"] = "TheNewsAPI"
                n["text"] = extract_full_text(link) if fetch_full_text else ""
                all_articles.append(n)
                seen_links.add(link)
    except Exception as e:
        print("TheNewsAPI error:", e)

    # --- NewsData ---
    try:
        newsdata_articles = client.fetch_latest_news(
            query=query,
            language=language,
            category=category,
            country=country,
            page=page
        ).get("results", [])

        for n in newsdata_articles:
            link = n.get("link")
            if link and link not in seen_links:
                n["source"] = "NewsData"
                n["full_text"] = extract_full_text(link) if fetch_full_text else ""
                all_articles.append(n)
                seen_links.add(link)
    except Exception as e:
        print("NewsData error:", e)

    # --- Mediastack ---
    try:
        mediastack_articles = fetch_mediastack_ai(limit_per_keyword=5)
        for n in mediastack_articles:
            link = n.get("url") or n.get("link")
            if link and link not in seen_links:
                n["source"] = "Mediastack"
                n["text"] = extract_full_text(link) if fetch_full_text else ""
                all_articles.append(n)
                seen_links.add(link)
    except Exception as e:
        print("Mediastack error:", e)



 # --- Reddit ---
    # --- Reddit ---
    try:
        reddit_articles = fetch_today_ai_posts()
        for n in reddit_articles:
            link = n.get("url")
            if link and link not in seen_links:
                n["source"] = f"Reddit ({n['subreddit']})"
                n["text"] = n.get("selftext", "")
                all_articles.append(n)
                seen_links.add(link)
    except Exception as e:
        print("Reddit error:", e)



    # === ADD THIS SECTION - SUMMARIZATION ===
    try:
        print(f"Adding summaries to {len(all_articles)} articles...")
        all_articles = summarizer.add_summaries(all_articles)

        print("Summaries added successfully!")
    except Exception as e:
        print(f"Summarization error: {e}")
        # Continue without summaries if there's an error

    return {"count": len(all_articles), "articles": all_articles}