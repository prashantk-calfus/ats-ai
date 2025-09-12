import os
import praw
import datetime
import time
from dotenv import load_dotenv

load_dotenv()

def get_reddit_client():
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT")
    )


def is_valid_reddit_post(submission, keywords):
    # Skip memes or image-only links
    if submission.url.endswith((".jpg", ".jpeg", ".png", ".gif")) or "i.redd.it" in submission.url:
        return False

    # Title must contain AI-related keywords
    if not any(k.lower() in submission.title.lower() for k in keywords):
        return False

    # Post should not be too short
    if len(submission.title) < 20:
        return False

    # Filter by flair (optional)
    if submission.link_flair_text:
        allowed_flairs = {"research", "paper", "news", "project", "discussion"}
        if submission.link_flair_text.lower() not in allowed_flairs:
            return False

    return True


def fetch_today_ai_posts():
    reddit = get_reddit_client()
    today = datetime.date.today()
    start_of_day = int(time.mktime(datetime.datetime.combine(today, datetime.time()).timetuple()))
    end_of_day = int(time.mktime(datetime.datetime.combine(today + datetime.timedelta(1), datetime.time()).timetuple()))

    ai_subs = ["MachineLearning", "ArtificialIntelligence", "OpenAI"]
    keywords = [
        "AI", "artificial intelligence", "machine learning", "ML", "neural network",
        "ChatGPT", "GPT", "Claude", "Anthropic", "DeepMind", "Hugging Face",
        "Stability AI", "Generative AI", "LLM", "Transformer", "Sora", "Mistral"
    ]

    results = []
    for sub in ai_subs:
        try:
            subreddit = reddit.subreddit(sub)
            for post in subreddit.new(limit=50):
                if start_of_day <= post.created_utc < end_of_day:
                    if is_valid_reddit_post(post, keywords):
                        results.append({
                            "subreddit": sub,
                            "title": post.title,
                            "url": post.url,
                            "created": datetime.datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M"),
                            "selftext": post.selftext if post.selftext else "",
                        })
        except Exception as e:
            print(f"Error fetching from {sub}: {e}")
            continue

    return results
