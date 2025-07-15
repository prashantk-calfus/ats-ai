import os
import shutil
import json

from fastapi import FastAPI, File, UploadFile, HTTPException
from langchain_community.document_loaders import PyMuPDFLoader
from starlette import status
from starlette.responses import StreamingResponse
from pydantic import BaseModel

from typing import Dict, Any, Optional, AsyncGenerator

from llm_chain_agent import extract_resume_info, evaluate_resume_against_jd

RESUME_UPLOAD_FOLDER = "../data/"
JD_UPLOAD_FOLDER = "../jd_json/"

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

app = FastAPI(
    title="Resume Parsing & Evaluation"
)

"""
    Create a fastapi server for LLM validation of resumes.
"""

def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()

    return " ".join(page.page_content for page in pages)

# UPDATED FOR STREAMING RESPONSE CAPABILITY
@app.post("/upload_resume_file", status_code=status.HTTP_200_OK)
async def upload_resume_file(resume_file: UploadFile = File(...)):
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="No file found")
    if not resume_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF format supported")

    file_path = os.path.join(RESUME_UPLOAD_FOLDER, resume_file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(resume_file.file, f)

    try:
        new_chunks = load_pdf_text(file_path) # Check for min text requirement
    except ValueError as e:
        os.remove(file_path) # FILE REMOVED
        return {'message': str(e)}

    return {"message": "Resume uploaded successfully"}

@app.get("/resume_parser")
async def resume_parser(resume_path: str):
    """
    Endpoint to stream LLM responses.
    Calls the LLM service to get the asynchronous generator.
    """
    raw_resume_text = load_pdf_text(RESUME_UPLOAD_FOLDER+resume_path)# READ RAW RESUME TEXT

    try:
        return StreamingResponse(extract_resume_info(raw_resume_text), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start LLM parsing stream: {e}")


@app.post("/evaluate_resume", status_code=status.HTTP_200_OK)
async def evaluate_resume(payload: ResumeEvaluationRequest):

    """
        Evaluate resume by LLM 2
        Expect response in JSON.
    """
    resume_json = payload.resume_json
    jd_path = payload.jd_path

    jd_filepath = os.path.join(JD_UPLOAD_FOLDER, jd_path)
    jd_json = json.load(open(jd_filepath))

    # Calls Evaluation LLM in llm_chain_agent.py
    try:
        return StreamingResponse(evaluate_resume_against_jd(jd_json, resume_json), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start LLM evaluation stream: {e}")


# SCHEMA FOR STORING CANDIDATE ACCEPTANCE DECISION
class Cand_Decision(BaseModel):
    name: str
    contact: Optional[dict] = None
    decision: str
    evaluation_results: Optional[dict]=None


@app.post("/store_decision", status_code=status.HTTP_200_OK)
def store_decision(name: str, decision: str):

    # PLACEHOLDER (REPLACE WITH SQLITE TABLE UPDATE IN FUTURE)
    print(f"Storing decision for {name}: {decision}")
    return {"status": "success", "message": f"Decision stored for {name}"}