import json
import os
import shutil
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
from pydantic import BaseModel
from starlette import status

from ats_ai.agent.llm_agent import evaluate_resume_against_jd, extract_resume_info

RESUME_UPLOAD_FOLDER = "data/"
JD_UPLOAD_FOLDER = "jd_json/"


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


app = FastAPI(title="Resume Parsing & Evaluation")

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

    if os.path.exists(RESUME_UPLOAD_FOLDER):
        file_path = os.path.join(RESUME_UPLOAD_FOLDER, resume_file.filename)
    else:
        os.makedirs(RESUME_UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(RESUME_UPLOAD_FOLDER, resume_file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(resume_file.file, f)

    try:
        new_chunks = load_pdf_text(file_path)  # Check for min text requirement
    except ValueError as e:
        os.remove(file_path)  # FILE REMOVED
        return {"message": str(e)}

    return {"message": "Resume uploaded successfully"}


@app.get("/resume_parser")
async def resume_parser(resume_path: str):
    """
    Endpoint to stream LLM responses.
    Calls the LLM service to get the asynchronous generator.
    """
    raw_resume_text = load_pdf_text(RESUME_UPLOAD_FOLDER + resume_path)

    try:
        response = await extract_resume_info(raw_resume_text)

        return response
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
        response = await evaluate_resume_against_jd(jd_json, resume_json)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start LLM evaluation stream: {e}")
