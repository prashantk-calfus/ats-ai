# import datetime
# import time
# from reddit_client import get_reddit_client
#
# def fetch_today_ai_posts():
#     reddit = get_reddit_client()
#
#     # Today's time range
#     today = datetime.date.today()
#     start_of_day = int(time.mktime(datetime.datetime.combine(today, datetime.time()).timetuple()))
#     end_of_day = int(time.mktime(datetime.datetime.combine(today + datetime.timedelta(1), datetime.time()).timetuple()))
#
#     # Only valid AI-related subreddits
#     ai_subs = ["MachineLearning", "ArtificialIntelligence", "OpenAI"]
#
#     keywords = ["AI", "ChatGPT", "Generative AI", "LLaMA", "GPT-4", "GPT-5"]
#
#     results = []
#
#     for sub in ai_subs:
#         try:
#             subreddit = reddit.subreddit(sub)
#             for post in subreddit.new(limit=50):
#                 if start_of_day <= post.created_utc < end_of_day:
#                     # Filter posts by keywords
#                     if any(k.lower() in post.title.lower() for k in keywords):
#                         results.append({
#                             "subreddit": sub,
#                             "title": post.title,
#                             "url": post.url,
#                             "created": datetime.datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M")
#                         })
#         except Exception as e:
#             print(f"Error fetching from {sub}: {e}")
#             continue
#
#     return results



import datetime
import time
from reddit_client import get_reddit_client

def fetch_today_ai_posts():
    reddit = get_reddit_client()

    # Today's time range
    today = datetime.date.today()
    start_of_day = int(time.mktime(datetime.datetime.combine(today, datetime.time()).timetuple()))
    end_of_day = int(time.mktime(datetime.datetime.combine(today + datetime.timedelta(1), datetime.time()).timetuple()))

    # Only valid AI-related subreddits
    ai_subs = ["MachineLearning", "ArtificialIntelligence", "OpenAI"]

    keywords = [
        # General AI / ML
        "AI", "artificial intelligence", "machine learning", "ML", "neural network",
        "deep learning", "reinforcement learning", "computer vision", "NLP",

        # Generative AI
        "generative AI", "generative", "diffusion", "stable diffusion", "midjourney",
        "dall-e", "dalle", "imagen", "text-to-image", "image generation",
        "video generation", "music generation", "AI art", "synthetic media",

        # Language models
        "ChatGPT", "GPT-4", "GPT-5", "GPT", "LLM", "large language model",
        "Claude", "Bard", "Gemini", "LLaMA", "Llama", "Mistral", "Alpaca",
        "transformer", "BERT", "T5", "PaLM", "LaMDA",

        # AI companies / tools
        "OpenAI", "Anthropic", "Google AI", "DeepMind", "Hugging Face",
        "Stability AI", "Runway", "Pika Labs", "ElevenLabs", "Replicate",
        "Cohere", "AI21", "Inflection",

        # Specific AI applications
        "code generation", "copilot", "cursor", "replit", "ghostwriter",
        "voice synthesis", "speech synthesis", "TTS", "voice cloning",
        "autonomous", "robotics", "AGI", "superintelligence",

        # Technical terms
        "fine-tuning", "RAG", "embedding", "vector database", "prompt engineering",
        "few-shot", "zero-shot", "chain of thought", "RLHF", "alignment",
        "hallucination", "multimodal", "vision-language", "CLIP",

        # Recent developments
        "o1", "reasoning model", "chain-of-thought", "GPT-4o", "Sora",
        "video diffusion", "3D generation", "NeRF", "gaussian splatting"
    ]
    def is_relevant_post(submission):
        # If post has no text and no keywords, skip
        if not submission.title:
            return False

        # Check keywords in title
        if any(k.lower() in submission.title.lower() for k in keywords):
            return True

        # Check flair if available
        if submission.link_flair_text and submission.link_flair_text.lower() in [
            "research", "paper", "news", "release", "project"
        ]:
            return True

        return False
    results = []

    for sub in ai_subs:
        try:
            subreddit = reddit.subreddit(sub)
            for post in subreddit.new(limit=50):
                if start_of_day <= post.created_utc < end_of_day:
                    # Filter posts by keywords
                    if any(k.lower() in post.title.lower() for k in keywords):
                        if is_relevant_post(post):
                            results.append({
                                "subreddit": sub,
                                "title": post.title,
                                "url": post.url,
                                "created": datetime.datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M")
                            })
        except Exception as e:
            print(f"Error fetching from {sub}: {e}")
            continue

    return results
