import os
import shutil
import json

from fastapi import FastAPI, File, UploadFile, HTTPException
from langchain_community.document_loaders import PyMuPDFLoader

from LLM_CHAIN.llm_chain_agent import extract_resume_info, evaluate_resume_against_jd, correct_evaluation_output

from pydantic import BaseModel
from typing import Dict, Any

RESUME_UPLOAD_FOLDER = "data/"

JD_UPLOAD_FOLDER = "jd_json/"

class ResumeEvaluationRequest(BaseModel):
    resume_json: Dict[str, Any]
    jd_path: str

app = FastAPI()

"""
    Create a fastapi server for LLM validation of resumes.
"""

def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()

    return " ".join(page.page_content for page in pages)

@app.post("/upload_resume_file")
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
def resume_parser(resume_path: str):

    """Parse resume with LLM 1"""

    file_path = os.path.join(RESUME_UPLOAD_FOLDER, resume_path)

    raw_resume_text = load_pdf_text(file_path)

    resume_parsed_json = extract_resume_info(raw_resume_text)

    return resume_parsed_json

@app.post("/evaluate_resume")
def evaluate_resume(payload: ResumeEvaluationRequest):

    """Evaluate resume by LLM 2 and validate with LLM3"""
    resume_json = payload.resume_json
    jd_path = payload.jd_path

    jd_filepath = os.path.join(JD_UPLOAD_FOLDER, jd_path)
    jd_json = json.load(open(jd_filepath))

    # Evaluate with LLM 2
    evaluation_response = evaluate_resume_against_jd(jd_json, resume_json)

    # Validate with LLM 3
    final_evaluation = correct_evaluation_output(jd_json, resume_json, evaluation_response)

    return final_evaluation

@app.post("/store_decision")
def store_decision(name: str, decision: str):

    print(f"Storing decision for {name}: {decision}")
    return {"status": "success", "message": f"Decision stored for {name}"}