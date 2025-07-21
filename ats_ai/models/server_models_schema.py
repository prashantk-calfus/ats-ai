from typing import Any, Dict, Optional
from pydantic import BaseModel


class ResumeEvaluationRequest(BaseModel):
    resume_json: Dict[str, Any]
    jd_path: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "resume_json": {
                        "name": "John Doe",
                        "email": "john.doe@example.com",
                        "experience": [{"title": "Software Engineer", "company": "Tech Corp", "years": "2020-Present"}],
                        "skills": ["Python", "FastAPI", "Docker"],
                    },
                    "jd_path": "software_engineer_v1.json",
                }
            ]
        }
    }


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


# SCHEMA FOR STORING CANDIDATE ACCEPTANCE DECISION
class Cand_Decision(BaseModel):
    name: str
    contact: Optional[dict] = None
    decision: str
    evaluation_results: Optional[dict] = None
