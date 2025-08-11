import json
import os
import re

from dotenv import load_dotenv
from google import genai
from langchain_community.document_loaders import PyMuPDFLoader
from pydantic import BaseModel

from ats_ai.agent.prompts import (
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


async def combined_parse_evaluate(resume_data: str, job_description: str, weightage_config=None):
    """
    Parse and Evaluate Candidate resume with Job Description with custom weightage
    - returns Dict[str, Any]: JSON object containing evaluation and parsed result
    """
    # Use default weightage if not provided
    if weightage_config is None:
        from pydantic import BaseModel

        class DefaultWeightageConfig(BaseModel):
            experience_weight: float = 0.3
            skills_weight: float = 0.4
            education_weight: float = 0.1
            projects_weight: float = 0.2

        weightage_config = DefaultWeightageConfig()

    # Import the dynamic prompt function
    from ats_ai.agent.prompts import get_dynamic_evaluation_prompt

    # Generate dynamic prompt with custom weightage
    prompt = get_dynamic_evaluation_prompt(resume_data, job_description, weightage_config, k_runs=3, temperature=0.0, top_p=0.9)
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

    # Calculate weighted scores using the function with custom weights
    calculation_result = calculate_weighted_score_and_status(
        experience_score=experience_score,
        skills_score=skills_score,
        education_score=education_score,
        projects_score=projects_score,
        has_valid_projects=has_valid_projects,
        experience_weight=weightage_config.experience_weight,
        skills_weight=weightage_config.skills_weight,
        education_weight=weightage_config.education_weight,
        projects_weight=weightage_config.projects_weight,
    )

    # Update the response with calculated values
    parsed_response["Evaluation"]["Overall_Weighted_Score"] = calculation_result["overall_weighted_score"]
    parsed_response["Evaluation"]["Match_Percentage"] = calculation_result["match_percentage"]
    parsed_response["Evaluation"]["Qualification Status"] = calculation_result["qualification_status"]

    return parsed_response
