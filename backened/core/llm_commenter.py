import requests
import json

def generate_comment(resume_text: str, jd_text: str, score: float = 0.0) -> str:
    prompt = f"""
You are an AI recruiter assistant.

Given the following resume and job description, and an ATS score of {score}%, respond ONLY in the following valid JSON format:

{{
  "name": "<Extracted candidate name from resume, or write 'Name not mentioned'>",
  "positive": "<One short strong point>",
  "negative": "<One short missing point>"
}}

Do not invent a name like John Doe. If no name is present in the resume text, just write "Name not mentioned".

### JOB DESCRIPTION:
{jd_text}

### RESUME:
{resume_text}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral", "prompt": prompt.strip(), "stream": False}
        )
        return response.json()["response"].strip()
    except Exception as e:
        fallback = {
            "name": "Name not mentioned",
            "positive": "LLM failed to respond properly.",
            "negative": f"LLM error: {str(e)}"
        }
        return json.dumps(fallback)
