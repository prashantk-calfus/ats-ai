import praw

def get_reddit_client():
    return praw.Reddit(
        client_id="6y5NDG4v4A3GjldJPYSrDw",
        client_secret="4zg6A-0Urn1ctqzKFS2VxzWOWOhy6A",
        user_agent="Fetches latest AI-related news and posts from Reddit."
    )
