from reddit_client import get_reddit_client

reddit = get_reddit_client()
subreddit = reddit.subreddit("AI","Artificial Intelligence", "ChatGPT", "Generative AI",)

try:
    for post in subreddit.hot(limit=3):
        print(post.title)
except Exception as e:
    print("Reddit fetch error:", e)
