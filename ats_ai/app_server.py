import os
import shutil
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
from pydantic import BaseModel
from starlette import status
from starlette.responses import RedirectResponse

from ats_ai.agent.llm_agent import evaluate_resume_against_jd, extract_resume_info

RESUME_UPLOAD_FOLDER = "data/"
JD_UPLOAD_FOLDER = "jd_json/"
RESUME_FILE_UPLOAD = File(...)


class ResumeEvaluationRequest(BaseModel):
    resume_json: Dict[str, Any]
    jd_json: Dict[str, Any]

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
                    "jd_json": "{Job Description}",
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
async def upload_resume_file(resume_file: UploadFile = RESUME_FILE_UPLOAD):
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
    jd_json = payload.jd_json

    # Calls Evaluation LLM in llm_chain_agent.py
    try:
        response = await evaluate_resume_against_jd(jd_json, resume_json)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start LLM evaluation stream: {e}")


@app.get("/")
async def docs():
    return RedirectResponse("/docs")


# For local debug purpose
if __name__ == "__main__":
    uvicorn.run(app)
