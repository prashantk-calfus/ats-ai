import trafilatura

# def extract_full_text(url: str) -> str:
#     """
#     Extracts main article text from a URL using trafilatura.
#     """
#     try:
#         downloaded = trafilatura.fetch_url(url)
#         if downloaded:
#             extracted = trafilatura.extract(downloaded)
#             if extracted:
#                 return extracted
#         return ""
#     except Exception as e:
#         print(f"Error extracting {url}: {e}")
#         return ""
#
#

import trafilatura

def extract_full_text(url):
    """Extract main article text using Trafilatura"""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            return text if text else ""
        return ""
    except Exception as e:
        print(f"Error extracting {url}: {e}")
        return ""
