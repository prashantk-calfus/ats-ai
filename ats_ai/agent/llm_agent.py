import json
import os
import re

from dotenv import load_dotenv
from google import genai
from langchain_community.document_loaders import PyMuPDFLoader
from pydantic import BaseModel

from ats_ai.agent.prompts import (
    EVALUATION_AND_PARSING_PROMPT,
    EVALUATION_PROMPT,
    RESUME_PARSE_PROMPT,
)

"""
    Using LLM chaining workflow to parse, evaluate, and validate resume and given job description
    to create a robust and accurate assessment of a candidate.
    1. extract_resume_info : Parsing Agent
    2. evaluate_resume_against_jd : Evaluation Agent
"""

load_dotenv()
genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.Client()


# Define structured schema for parsed resume info
class ParsedResume(BaseModel):
    Name: str
    Contact_Details: dict
    Github_Repo: str
    LinkedIn: str
    Education: list
    Professional_Experience: list
    Projects: list
    Certifications: list
    Programming_Language: list[str]
    Frameworks: list[str]
    Technologies: list[str]


class ResumeEvaluation(BaseModel):
    Evaluation_Summary: dict
    Strengths_and_Weaknesses: dict
    Skill_Analysis: dict
    Key_Considerations: dict


def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return " ".join(page.page_content for page in pages)


def extract_json_block(text: str) -> dict:
    """
    Extracts the first JSON block from a string (removes ```json ... ``` if present),
    and returns it as a Python dictionary.
    """
    pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(pattern, text, re.DOTALL)

    try:
        if match:
            cleaned_json = match.group(1).strip()
        else:
            cleaned_json = text.strip()

        return json.loads(cleaned_json)

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}\nRaw content: {text}")


async def extract_resume_info(raw_resume_text: str):
    """
    Parsing Agent LLM.
    Parse information from resume into JSON
    """
    prompt = RESUME_PARSE_PROMPT.format(raw_resume_text=raw_resume_text)
    response = gemini_model.models.generate_content(model="gemini-2.0-flash", contents=prompt)

    return extract_json_block(response.text)


async def evaluate_resume_against_jd(jd_json: dict, resume_data: dict):
    """
    Evaluation Agent LLM.
    Evaluate parsed information from resume from JD
    """
    prompt = EVALUATION_PROMPT.format(resume_data=resume_data, jd_json=jd_json)
    response = gemini_model.models.generate_content(model="gemini-2.0-flash", contents=prompt)

    return extract_json_block(response.text)


async def combined_parse_evaluate(resume_data: str, job_description: str):
    """
    Parse and Evaluate Candidate resume with Job Description
    - returns Dict[str, Any]: JSON object containing evaluation and parsed result
    """
    prompt = EVALUATION_AND_PARSING_PROMPT.format(resume_data=resume_data, job_description=job_description)
    response = gemini_model.models.generate_content(model="gemini-2.0-flash", contents=prompt)

    return extract_json_block(response.text)
