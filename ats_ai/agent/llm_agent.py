import json
import os
import re

from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from openai import OpenAI
from pydantic import BaseModel

from ats_ai.agent.prompts import (
    RESUME_PARSE_PROMPT,
    calculate_weighted_score_and_status,
    get_dynamic_evaluation_prompt,
)

"""
    Using LLM chaining workflow to parse, evaluate, and validate resume and given job description
    to create a robust and accurate assessment of a candidate.
    1. extract_resume_info : extract_resume_info()
    2. evaluate_resume_against_jd : evaluate_resume_against_jd()
    3. Combined Evaluation Agent: combined_parse_evaluate()
"""

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
    """Parse information from resume into JSON"""
    prompt = RESUME_PARSE_PROMPT.format(raw_resume_text=raw_resume_text)

    response = openai_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.0)

    return extract_json_block(response.choices[0].message.content)


async def combined_parse_evaluate(resume_data: str, job_description: dict, weightage_config=None):
    """
    Parse and Evaluate Candidate resume with Job Description with custom weightage
    Enhanced with experience years calculation and qualification logic
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

    # Generate enhanced prompt with experience calculation
    prompt = get_dynamic_evaluation_prompt(resume_data, job_description, weightage_config)

    response = openai_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.0, top_p=0.9)

    print("=== RAW RESPONSE ===")
    print(response.choices[0].message.content)
    print("=== END RAW RESPONSE ===")

    # Parse the initial response to get individual scores and experience data
    parsed_response = extract_json_block(response.choices[0].message.content)

    print("=== PARSED RESPONSE ===")
    print(json.dumps(parsed_response, indent=2))
    print("=== END PARSED RESPONSE ===")
    # After line where you get parsed_response, add this:
    if "Parsed_Resume" in parsed_response:
        professional_exp = parsed_response["Parsed_Resume"].get("Professional_Experience", [])
        calculated_total_exp = 0.0

        for exp in professional_exp:
            if isinstance(exp, dict):
                duration_str = exp.get("Duration", "")
                # Look for pattern like "(0.5 years)" in duration string
                if "(" in duration_str and "years)" in duration_str:
                    try:
                        start_idx = duration_str.find("(") + 1
                        end_idx = duration_str.find(" years)")
                        years_value = float(duration_str[start_idx:end_idx])
                        calculated_total_exp += years_value
                    except (ValueError, IndexError):
                        continue
        calculated_total_exp = round(calculated_total_exp, 1)
        print(f"Calculated total experience: {calculated_total_exp}")

    # Extract experience information from LLM response and validate with our functions
    try:
        if "Evaluation" in parsed_response:
            evaluation = parsed_response["Evaluation"]

            # GET LLM'S DIRECT MATCH PERCENTAGE - ADD THIS LINE
            llm_match_percentage = evaluation.get("Match_Percentage", None)

            # Get LLM's calculation
            # evaluation.get("Total_Experience_Years", 0.0)
            # llm_jd_required_experience = evaluation.get("JD_Required_Experience_Years", 0.0)

            experience_score = evaluation["Experience_Score"]
            skills_score = evaluation["Skills_Score"]
            education_score = evaluation["Education_Score"]
            projects_score = evaluation["Projects_Score"]

            # Use LLM calculated experience values directly
            # candidate_total_experience = evaluation.get("Total_Experience_Years", 0.0)
            # With this:
            candidate_total_experience = calculated_total_exp if calculated_total_exp > 0 else evaluation.get("Total_Experience_Years", 0.0)
            jd_required_experience = evaluation.get("JD_Required_Experience_Years", 0.0)

        else:
            # Fallback to our own calculations if LLM didn't provide experience data
            print("LLM didn't provide experience data, calculating ourselves...")
            llm_match_percentage = None  # ADD THIS LINE
            candidate_total_experience = 0.0
            # jd_required_experience = extract_jd_required_experience(job_description)
            experience_score = parsed_response.get("Experience_Score", 0.0)
            skills_score = parsed_response.get("Skills_Score", 0.0)
            education_score = parsed_response.get("Education_Score", 0.0)
            projects_score = parsed_response.get("Projects_Score", 0.0)

            # Try to calculate from parsed resume if available
            if "Parsed_Resume" in parsed_response:
                parsed_response["Parsed_Resume"].get("Professional_Experience", [])
                # candidate_total_experience = calculate_total_experience_years(resume_experience)

    except KeyError as e:
        print(f"KeyError accessing scores: {e}")
        print(f"Available keys in parsed_response: {list(parsed_response.keys())}")

        # Fallback values with our own calculations
        llm_match_percentage = None  # ADD THIS LINE
        candidate_total_experience = 0.0
        # jd_required_experience = get_experience_from_jd_json(job_description)
        experience_score = 0.0
        skills_score = 0.0
        education_score = 0.0
        projects_score = 0.0
    # Determine if projects are valid based on parsed resume data
    try:
        if "Parsed_Resume" in parsed_response:
            projects = parsed_response["Parsed_Resume"].get("Projects", [])
        else:
            projects = parsed_response.get("Projects", [])
    except (KeyError, TypeError):
        projects = []

    # Check if projects are valid
    has_valid_projects = False
    if projects and len(projects) > 0:
        if isinstance(projects[0], dict):
            # Dictionary format: {"Title": "...", "Description": "..."}
            first_project = projects[0]
            title = first_project.get("Title", first_project.get("Project_Name", ""))
            description = first_project.get("Description", first_project.get("Project_Description", ""))
            has_valid_projects = title not in ["NA", "N/A", "", None] and description not in ["NA", "N/A", "", None] and len(str(description)) > 10
        elif isinstance(projects[0], str):
            # String format: direct project names
            has_valid_projects = projects[0] not in ["NA", "N/A", "", None] and len(projects[0]) > 10

    # Use enhanced calculation that includes experience years comparison
    calculation_result = calculate_weighted_score_and_status(
        experience_score=experience_score,
        skills_score=skills_score,
        education_score=education_score,
        projects_score=projects_score,
        candidate_total_experience_years=candidate_total_experience,
        jd_required_experience_years=jd_required_experience,
        has_valid_projects=has_valid_projects,
        experience_weight=weightage_config.experience_weight,
        skills_weight=weightage_config.skills_weight,
        education_weight=weightage_config.education_weight,
        projects_weight=weightage_config.projects_weight,
        llm_match_percentage=llm_match_percentage,
    )
    # Create a standardized response structure
    if "Evaluation" not in parsed_response:
        # If the response doesn't have the nested structure, create it
        evaluation_data = {
            "Total_Experience_Years": candidate_total_experience,
            "JD_Required_Experience_Years": jd_required_experience,
            "Experience_Score": experience_score,
            "Skills_Score": skills_score,
            "Education_Score": education_score,
            "Projects_Score": projects_score,
            "Overall_Weighted_Score": calculation_result["overall_weighted_score"],
            "Match_Percentage": calculation_result["match_percentage"],
            "Qualification Status": calculation_result["qualification_status"],
            "Pros": parsed_response.get("Pros", []),
            "Cons": parsed_response.get("Cons", []),
            "Skills Match": parsed_response.get("Skills Match", parsed_response.get("Skills_Match", [])),
            "Required_Skills_Missing_from_Resume": parsed_response.get("Required_Skills_Missing_from_Resume", []),
            "Extra skills": parsed_response.get("Extra skills", parsed_response.get("Extra_Skills", [])),
            "Summary": parsed_response.get("Summary", ""),
        }

        # Create the standardized response structure
        standardized_response = {"Evaluation": evaluation_data, "Parsed_Resume": parsed_response.get("Parsed_Resume", {})}

        return standardized_response
    else:
        # Update the existing nested structure with calculated values and experience info
        parsed_response["Evaluation"]["Total_Experience_Years"] = candidate_total_experience
        parsed_response["Evaluation"]["JD_Required_Experience_Years"] = jd_required_experience
        parsed_response["Evaluation"]["Overall_Weighted_Score"] = calculation_result["overall_weighted_score"]
        parsed_response["Evaluation"]["Match_Percentage"] = calculation_result["match_percentage"]
        parsed_response["Evaluation"]["Qualification Status"] = calculation_result["qualification_status"]

        return parsed_response
