import os
import shutil
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
from starlette import status
from starlette.responses import RedirectResponse

from ats_ai.agent.llm_agent import (
    combined_parse_evaluate,
    evaluate_resume_against_jd,
    extract_resume_info,
)
from ats_ai.models.server_models_schema import ResumeEvaluationRequest

RESUME_UPLOAD_FOLDER = "data/"
JD_UPLOAD_FOLDER = "jd_json/"
RESUME_FILE_UPLOAD = File(...)

app = FastAPI(title="Resume Parsing & Evaluation")


def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()

    return " ".join(page.page_content for page in pages)


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

    print(f"Uploading {resume_file.filename} to {file_path}")

    with open(file_path, "wb") as f:
        shutil.copyfileobj(resume_file.file, f)

    return {"message": "Resume uploaded successfully"}


@app.get("/resume_parser")
async def resume_parser(resume_path: str):
    """
    Parse resume file
    Expect response in JSON.
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
    Evaluate resume with JD
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


@app.post("/parse_and_evaluate", status_code=status.HTTP_200_OK)
async def parse_and_evaluate(combined_json: Dict[str, Any]):
    resume_data = combined_json.get("resume_data")
    jd_json = combined_json.get("jd_json")

    return await combined_parse_evaluate(resume_data, jd_json)


@app.post("/store_candidate_evaluation", status_code=status.HTTP_200_OK)
async def store_candidate_evaluation(eval_json: Dict[str, Any]):
    # name = eval_json.get("name")
    # overall_score = eval_json.get("Overall_Weighted_Score")
    # match_jd = eval_json.get("Match_Percentage")

    return {"message": "Evaluation saved successfully"}


@app.get("/")
async def docs():
    return RedirectResponse("/docs")


# For local debug purpose
if __name__ == "__main__":
    uvicorn.run(app)
