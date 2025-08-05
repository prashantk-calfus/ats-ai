import json
import os
import re

from dotenv import load_dotenv
from google import genai
from langchain_community.document_loaders import PyMuPDFLoader
from pydantic import BaseModel

from ats_ai.agent.prompts import (
    EVALUATION_AND_PARSING_PROMPT,
    RESUME_PARSE_PROMPT,
    calculate_weighted_score_and_status,
)

"""
    Using LLM chaining workflow to parse, evaluate, and validate resume and given job description
    to create a robust and accurate assessment of a candidate.
    1. extract_resume_info : extract_resume_info()
    2. evaluate_resume_against_jd : evaluate_resume_against_jd()
    3. Combined Evaluation Agent: combined_parse_evaluate()
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
    # Find JSON-like object
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise json.JSONDecodeError("No JSON object found", text, 0)

    raw_json = match.group()
    return json.loads(raw_json)


async def extract_resume_info(raw_resume_text: str):
    """
    Parsing Agent LLM.
    Parse information from resume into JSON
    """
    prompt = RESUME_PARSE_PROMPT.format(raw_resume_text=raw_resume_text)
    response = gemini_model.models.generate_content(model="gemini-2.0-flash", contents=prompt)

    return extract_json_block(response.text)


# async def evaluate_resume_against_jd(jd_json: dict, resume_data: dict):
#     """
#     Evaluation Agent LLM.
#     Evaluate parsed information from resume from JD
#     """
#     prompt = EVALUATION_PROMPT.format(resume_data=resume_data, jd_json=jd_json)
#     response = gemini_model.models.generate_content(model="gemini-2.0-flash", contents=prompt)
#
#     return extract_json_block(response.text)


# async def combined_parse_evaluate(resume_data: str, job_description: str):
#     """
#     Parse and Evaluate Candidate resume with Job Description
#     - returns Dict[str, Any]: JSON object containing evaluation and parsed result
#     """
#     prompt = EVALUATION_AND_PARSING_PROMPT.format(resume_data=resume_data, job_description=job_description)
#     response = gemini_model.models.generate_content(model="gemini-2.0-flash", contents=prompt)
#
#     return extract_json_block(response.text)


async def combined_parse_evaluate(resume_data: str, job_description: str):
    """
    Parse and Evaluate Candidate resume with Job Description
    - returns Dict[str, Any]: JSON object containing evaluation and parsed result
    """
    prompt = EVALUATION_AND_PARSING_PROMPT.format(resume_data=resume_data, job_description=job_description)
    response = gemini_model.models.generate_content(model="gemini-2.0-flash", contents=prompt)

    # Parse the initial response to get individual scores
    parsed_response = extract_json_block(response.text)

    # Extract individual scores from LLM response
    experience_score = parsed_response["Evaluation"]["Experience_Score"]
    skills_score = parsed_response["Evaluation"]["Skills_Score"]
    education_score = parsed_response["Evaluation"]["Education_Score"]
    projects_score = parsed_response["Evaluation"]["Projects_Score"]

    # Determine if projects are valid based on parsed resume data
    projects = parsed_response["Parsed_Resume"]["Projects"]
    has_valid_projects = len(projects) > 0 and projects[0]["Title"] not in ["NA", "N/A", "", None] and projects[0]["Description"] not in ["NA", "N/A", "", None] and len(projects[0]["Description"]) > 10

    # Calculate weighted scores using the function
    calculation_result = calculate_weighted_score_and_status(experience_score=experience_score, skills_score=skills_score, education_score=education_score, projects_score=projects_score, has_valid_projects=has_valid_projects)

    # Update the response with calculated values
    parsed_response["Evaluation"]["Overall_Weighted_Score"] = calculation_result["overall_weighted_score"]
    parsed_response["Evaluation"]["Match_Percentage"] = calculation_result["match_percentage"]
    parsed_response["Evaluation"]["Qualification Status"] = calculation_result["qualification_status"]

    return parsed_response
