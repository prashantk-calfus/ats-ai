import requests
import xml.etree.ElementTree as ET
import urllib.parse


def fetch_google_news(query="artificial intelligence", lang="en", region="US"):
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={region}&ceid={region}:{lang}"

    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    root = ET.fromstring(resp.content)

    articles = []
    for item in root.findall(".//item"):
        title = item.find("title").text if item.find("title") is not None else ""
        link = item.find("link").text if item.find("link") is not None else ""
        pubDate = item.find("pubDate").text if item.find("pubDate") is not None else ""
        description = item.find("description").text if item.find("description") is not None else ""

        if title and link:
            articles.append({
                "title": title,
                "link": link,
                "pubDate": pubDate,
                "description": description
            })
    return articles


def resolve_real_url(google_link):
    """Follow redirect to get real article URL"""
    try:
        resp = requests.get(google_link, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return resp.url
    except Exception as e:
        print(f"Error resolving URL {google_link}: {e}")
        return google_link
