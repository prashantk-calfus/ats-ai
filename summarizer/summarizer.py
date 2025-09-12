import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import time
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()


class NewsSummarizer:
    def __init__(self):
        """Initialize the Gemini 2.0 Flash summarizer"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # 1 second between requests

    def _rate_limit(self):
        """Simple rate limiting to avoid hitting API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def summarize_article(self, article: Dict) -> str:
        """
        Summarize a single article using Gemini 2.0 Flash

        Args:
            article (Dict): Article data with title, text/content fields

        Returns:
            str: Summarized text (3-5 sentences)
        """
        try:
            # Extract content from different possible fields
            content = ""
            title = article.get('title', '')

            # Check various content fields based on your JSON structure
            if article.get('text'):
                content = article['text']
            elif article.get('content'):
                content = article['content']
            elif article.get('full_text'):
                content = article['full_text']
            elif article.get('selftext'):
                content = article['selftext']
            elif article.get('description'):
                content = article['description']

            # Skip if no meaningful content
            if not content or content.strip() == "" or "ONLY AVAILABLE IN PAID PLANS" in content:
                return f"Summary not available - insufficient content for: {title}"

            # Create prompt for summarization
            prompt = f"""
            Please summarize the following news article in 3-5 clear, concise sentences. 
            Focus on the key facts and main points. Make it informative and easy to understand.

            Title: {title}
            Content: {content}

            Summary:
            """

            # Rate limiting
            self._rate_limit()

            # Generate summary using Gemini
            response = self.model.generate_content(prompt)
            summary = response.text.strip()

            return summary

        except Exception as e:
            print(f"Error summarizing article '{article.get('title', 'Unknown')}': {str(e)}")
            return f"Summary unavailable due to processing error: {article.get('title', 'Unknown title')}"

    def summarize_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Summarize a batch of articles and add summary field

        Args:
            articles (List[Dict]): List of article dictionaries

        Returns:
            List[Dict]: Articles with added 'summary' field
        """
        summarized_articles = []

        for i, article in enumerate(articles):
            print(f"Summarizing article {i + 1}/{len(articles)}: {article.get('title', 'No title')[:50]}...")

            # Generate summary
            summary = self.summarize_article(article)

            # Add summary to article
            article_copy = article.copy()
            article_copy['summary'] = summary
            article_copy['summarized_at'] = time.strftime('%Y-%m-%d %H:%M:%S')

            summarized_articles.append(article_copy)

        return summarized_articles

    def add_summaries(self, articles: List[Dict]) -> List[Dict]:
        """
        Add summaries to your exact JSON format articles

        Args:
            articles (List[Dict]): Your news articles with title/text

        Returns:
            List[Dict]: Same articles + summary field added
        """
        print(f"Adding summaries to {len(articles)} articles...")

        for i, article in enumerate(articles):
            print(f"Processing {i + 1}/{len(articles)}: {article.get('title', '')[:50]}...")

            # Add summary to each article
            summary = self.summarize_article(article)
            article['summary'] = summary

        print("All summaries added!")
        return articles


# Usage example function
def main():
    """Example usage of the summarizer"""
    try:
        # Initialize summarizer
        summarizer = NewsSummarizer()

        # Load your fetched news JSON (replace with your actual data loading)
        # For testing, you can load from a file:
        # with open('news_data.json', 'r') as f:
        #     news_data = json.load(f)

        # Or use sample data for testing
        sample_news = [
            {
                "title": "Test Article",
                "text": "This is a sample news article content for testing the summarization functionality.",
                "source": "Test Source"
            }
        ]

        # Process and summarize
        summarized_news = summarizer.process_news_json(sample_news)

        # Print results
        for article in summarized_news:
            print(f"\nTitle: {article['title']}")
            print(f"Summary: {article['summary']}")
            print("-" * 50)

        # Save summarized data
        with open('summarized_news.json', 'w') as f:
            json.dump(summarized_news, f, indent=2)

        print(f"\nSummarized {len(summarized_news)} articles and saved to 'summarized_news.json'")

    except Exception as e:
        print(f"Error in main: {str(e)}")


if __name__ == "__main__":
    main()