from pydantic import BaseModel
from typing import Optional, Dict, Any

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
                        "experience": [
                            {"title": "Software Engineer", "company": "Tech Corp", "years": "2020-Present"}
                        ],
                        "skills": ["Python", "FastAPI", "Docker"]
                    },
                    "jd_path": "software_engineer_v1.json"
                }
            ]
        }
    }

# SCHEMA FOR STORING CANDIDATE ACCEPTANCE DECISION
class Cand_Decision(BaseModel):
    name: str
    contact: Optional[dict] = None
    decision: str
    evaluation_results: Optional[dict]=None