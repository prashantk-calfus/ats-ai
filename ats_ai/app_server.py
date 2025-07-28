import json
import logging
import os
import re
import shutil
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
from pydantic import BaseModel
from starlette import status
from starlette.responses import JSONResponse, RedirectResponse

from ats_ai.agent.jd_parser import create_empty_jd_structure, extract_jd_info

# ---- Import your agent functions ----
from ats_ai.agent.llm_agent import (
    combined_parse_evaluate,
    evaluate_resume_against_jd,
    extract_resume_info,
)

# ---- Constants ----
RESUME_UPLOAD_FOLDER = "data/"
JD_UPLOAD_FOLDER = "jd_json/"
RESUME_FILE_UPLOAD = File(...)

# ---- FastAPI app ----
app = FastAPI(title="Resume Parsing & Evaluation")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---- Models ----
class ResumeEvaluationRequest(BaseModel):
    resume_json: Dict[str, Any]
    jd_json: Dict[str, Any]


class JDTextRequest(BaseModel):
    jd_text: str
    jd_name: str


# ---- Helpers ----
def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return " ".join(page.page_content for page in pages)


# ---- Endpoints ----
@app.post("/upload_resume_file", status_code=status.HTTP_200_OK)
async def upload_resume_file(resume_file: UploadFile = RESUME_FILE_UPLOAD):
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="No file found")
    if not resume_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF format supported")

    os.makedirs(RESUME_UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(RESUME_UPLOAD_FOLDER, resume_file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(resume_file.file, f)

    return {"message": "Resume uploaded successfully", "file_path": file_path}


@app.get("/resume_parser")
async def resume_parser(resume_path: str):
    raw_resume_text = load_pdf_text(os.path.join(RESUME_UPLOAD_FOLDER, resume_path))

    try:
        response = await extract_resume_info(raw_resume_text)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start LLM parsing stream: {e}")


@app.post("/evaluate_resume", status_code=status.HTTP_200_OK)
async def evaluate_resume(payload: ResumeEvaluationRequest):
    """
    Evaluate resume with JD
    """
    try:
        response = await evaluate_resume_against_jd(payload.jd_json, payload.resume_json)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start LLM evaluation stream: {e}")


@app.post("/parse_and_evaluate", status_code=status.HTTP_200_OK)
async def parse_and_evaluate(combined_json: Dict[str, Any]):
    resume_data = combined_json.get("resume_data")
    jd_json = combined_json.get("jd_json")

    if not resume_data or not jd_json:
        raise HTTPException(status_code=422, detail="Missing resume_data or jd_json")

    return await combined_parse_evaluate(resume_data, jd_json)


@app.post("/store_candidate_evaluation", status_code=status.HTTP_200_OK)
async def store_candidate_evaluation(eval_json: Dict[str, Any]):
    # Stub for DB saving logic
    return {"message": "Evaluation saved successfully"}


@app.get("/list_jds", status_code=status.HTTP_200_OK)
async def list_jds():

    try:
        os.makedirs(JD_UPLOAD_FOLDER, exist_ok=True)  # Ensure folder exists

        jd_files = [f[:-5] for f in os.listdir(JD_UPLOAD_FOLDER) if f.endswith(".json")]  # Remove `.json` extension

        return {"jds": jd_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list JDs: {str(e)}")


@app.post("/save_jd_raw_text/")
async def save_jd_raw_text(request: JDTextRequest):
    """Enhanced endpoint with intelligent JD validation - only saves valid JDs"""
    jd_text = request.jd_text.strip()
    jd_name = request.jd_name.strip()

    if not jd_text or not jd_name:
        raise HTTPException(status_code=400, detail="Missing JD text or JD name.")

    try:
        # Use the enhanced extraction function with AI validation
        jd_structured = extract_jd_info(jd_text)

        # Check if it's a valid JD - extract_jd_info now returns empty structure for invalid text
        is_valid_jd = bool(jd_structured.get("Job_Title", "").strip() or jd_structured.get("Required_Skills", []) or jd_structured.get("Responsibilities", []))

        if is_valid_jd:
            # Only save if it's a valid JD
            os.makedirs("jd_json", exist_ok=True)

            # Sanitize filename
            safe_filename = re.sub(r"[^\w\s-]", "", jd_name)
            safe_filename = re.sub(r"[-\s]+", "_", safe_filename)
            output_path = os.path.join("jd_json", f"{safe_filename}.json")

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(jd_structured, f, indent=2, ensure_ascii=False)

            return {"status": "success", "message": f"JD saved as {safe_filename}.json", "file": f"{safe_filename}.json", "is_valid_jd": True, "parsed_data": jd_structured, "validation_method": "AI-powered analysis"}
        else:
            # Don't save file for invalid JD
            return {"status": "invalid", "message": "Text is not a valid job description - no file saved", "file": None, "is_valid_jd": False, "parsed_data": {}, "validation_method": "AI-powered analysis"}

    except Exception as e:
        logger.error(f"Error in save_jd_raw_text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving JD: {str(e)}")


@app.post("/process_jd_folder", status_code=status.HTTP_200_OK)
async def process_jd_folder():
    """Process all DOC/DOCX files in jd_folder and convert to JSON"""
    try:
        from ats_ai.agent.jd_parser import process_jd_folder_to_json

        processed_count = process_jd_folder_to_json()

        return {"status": "success", "message": f"Processed {processed_count} JD files successfully", "processed_count": processed_count}

    except Exception as e:
        logger.error(f"Error in process_jd_folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing JD folder: {str(e)}")


@app.get("/")
async def docs():
    return RedirectResponse("/docs")


# ---- Run ----
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
