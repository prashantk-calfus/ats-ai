# reddit_content.py
from reddit_client import get_reddit_client

# Get Reddit client once
reddit = get_reddit_client()

def get_reddit_post_text(url: str) -> str:
    """
    Fetch the content of a Reddit post from its URL.
    Returns title + selftext if available.
    """
    try:
        submission = reddit.submission(url=url)
        if submission.selftext:
            return submission.title + "\n\n" + submission.selftext
        else:
            return submission.title
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""
