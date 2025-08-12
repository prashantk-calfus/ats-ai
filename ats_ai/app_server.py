import asyncio
import json
import logging
import os
import re
import shutil
import threading
from pathlib import Path
from typing import Any, Dict

import mammoth
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from langchain_community.document_loaders import PyMuPDFLoader
from pydantic import BaseModel
from starlette import status
from starlette.responses import RedirectResponse

from ats_ai.agent.jd_parser import extract_jd_info

# ---- Import your agent functions ----
from ats_ai.agent.llm_agent import (  # evaluate_resume_against_jd,
    combined_parse_evaluate,
    extract_resume_info,
)
from ats_ai.pdf_generator import generate_pdf_report
from ats_ai.scraper import CalfusJobScraper

# ---- Constants ----
RESUME_UPLOAD_FOLDER = "data/"
JD_UPLOAD_FOLDER = "jd_json/"
RESUME_FILE_UPLOAD = File(...)

# ---- FastAPI app ----
app = FastAPI(title="Resume Parsing & Evaluation")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
    """Save JD text without validation - always process and save"""
    jd_text = request.jd_text.strip()
    jd_name = request.jd_name.strip()

    if not jd_text or not jd_name:
        raise HTTPException(status_code=400, detail="Missing JD text or JD name.")

    try:
        # Extract JD info without validation
        jd_structured = extract_jd_info(jd_text)

        # Always save the JD (no validation check)
        os.makedirs("jd_json", exist_ok=True)

        # Sanitize filename
        safe_filename = re.sub(r"[^\w\s-]", "", jd_name)
        safe_filename = re.sub(r"[-\s]+", "_", safe_filename)
        output_path = os.path.join("jd_json", f"{safe_filename}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(jd_structured, f, indent=2, ensure_ascii=False)

        return {"status": "success", "message": f"JD saved as {safe_filename}.json", "file": f"{safe_filename}.json", "is_valid_jd": True, "parsed_data": jd_structured}  # Always return True since we're not validating

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


class JDTempRequest(BaseModel):
    jd_text: str


@app.post("/parse_jd_temp/")
async def parse_jd_temp(request: JDTempRequest):
    """
    Parse JD text temporarily without saving anywhere - purely for temporary evaluation
    """
    try:
        # jd_text = request.get("jd_text", "").strip()
        jd_text = request.jd_text.strip()

        if not jd_text:
            raise HTTPException(status_code=400, detail="JD text is required")

        # Parse JD text without any validation or saving
        jd_structured = extract_jd_info(jd_text)

        # Return parsed data directly - no saving, no validation
        return {"status": "success", "message": "JD parsed temporarily (not saved)", "parsed_data": jd_structured}

    except Exception as e:
        logger.error(f"Error in parse_jd_temp: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error parsing JD temporarily: {str(e)}")


@app.get("/")
async def docs():
    return RedirectResponse("/docs")


@app.post("/trigger_scraper", status_code=status.HTTP_200_OK)
async def trigger_scraper():
    try:
        # Run in background thread to avoid blocking
        thread = threading.Thread(target=run_scraper_job)
        thread.start()

        return {"message": "Scraper job triggered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger scraper: {e}")


def run_scraper_and_convert_job():
    try:
        logger.info("Starting scraper and conversion job...")

        # Step 1: Run the scraper
        scraper = CalfusJobScraper()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(scraper.run())
        loop.close()

        logger.info("Scraper completed - now converting JDs to JSON...")

        # Step 2: Automatically convert DOCX files to JSON
        from ats_ai.agent.jd_parser import process_jd_folder_to_json

        processed_count = process_jd_folder_to_json()

        logger.info(f"Complete job finished: Scraped JDs and converted {processed_count} files to JSON")

    except Exception as e:
        logger.error(f"Scraper and conversion job failed: {e}")


def run_scraper_job():
    run_scraper_and_convert_job()


def start_scheduler():
    """Initialize and start the background scheduler"""
    scheduler = BackgroundScheduler()

    # Schedule to run daily at 2:30 AM - now includes automatic JSON conversion
    scheduler.add_job(run_scraper_and_convert_job, "cron", hour=1, minute=00, id="daily_scraper_and_converter", replace_existing=True)  # Use the enhanced function

    scheduler.start()
    logger.info("Background scheduler started - scraper + JSON conversion will run daily at 2:30 AM")
    return scheduler


@app.post("/trigger_scraper_with_conversion", status_code=status.HTTP_200_OK)
async def trigger_scraper_with_conversion():
    """Manually trigger the scraper job WITH automatic JSON conversion"""
    try:
        # Run in background thread to avoid blocking
        thread = threading.Thread(target=run_scraper_and_convert_job)
        thread.start()

        return {"message": "Scraper job with automatic JSON conversion triggered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger scraper with conversion: {e}")


# Global scheduler variable
scheduler = None

# @app.on_event("startup")
# def startup_event():
#
#     start_scheduler()
#
#
# @app.on_event("shutdown")
# def shutdown_event():
#
#     if scheduler:
#         scheduler.shutdown()
#         logger.info("Background scheduler stopped")

#
# @app.post("/generate_pdf_report", status_code=status.HTTP_200_OK)
# async def generate_pdf_report_endpoint(report_data: Dict[str, Any]):
#     """Generate PDF report and return file path"""
#     try:
#         evaluation_results = report_data.get("evaluation_results")
#         parsed_resume = report_data.get("parsed_resume")
#         candidate_name = report_data.get("candidate_name")
#         jd_source = report_data.get("jd_source", "Unknown JD")
#         weightage_config = report_data.get("weightage_config")  # ADD THIS LINE
#
#         # Generate PDF with weightage config
#         pdf_filename = generate_pdf_report(evaluation_results, parsed_resume, candidate_name, jd_source, weightage_config)  # ADD THIS PARAMETER
#
#         return {"status": "success", "pdf_path": pdf_filename, "message": "PDF report generated successfully"}
#
#     except Exception as e:
#         logger.error(f"Error generating PDF report: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error generating PDF report: {str(e)}")
#

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")  # set to prod URL in deployment


@app.post("/generate_pdf_report", status_code=status.HTTP_200_OK)
async def generate_pdf_report_endpoint(report_data: Dict[str, Any]):
    try:
        evaluation_results = report_data.get("evaluation_results")
        parsed_resume = report_data.get("parsed_resume")
        candidate_name = report_data.get("candidate_name")
        jd_source = report_data.get("jd_source", "Unknown JD")
        weightage_config = report_data.get("weightage_config")

        pdf_filename = generate_pdf_report(evaluation_results, parsed_resume, candidate_name, jd_source, weightage_config)

        filename = os.path.basename(pdf_filename)

        return {"status": "success", "pdf_path": pdf_filename, "download_url": f"{BASE_URL}/download_report/{filename}", "message": "PDF report generated successfully"}

    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF report: {str(e)}")


@app.get("/download_report/{filename}")
async def download_report(filename: str):
    file_path = f"reports/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=filename)
    else:
        raise HTTPException(status_code=404, detail="Report file not found")


# Add this helper function in app_server.py
def extract_text_from_document(file_path: str) -> str:
    file_extension = Path(file_path).suffix.lower()

    if file_extension == ".pdf":
        loader = PyMuPDFLoader(file_path)
        pages = loader.load()
        return " ".join(page.page_content for page in pages)

    elif file_extension in [".doc", ".docx"]:
        try:
            with open(file_path, "rb") as doc_file:
                result = mammoth.extract_raw_text(doc_file)
                return result.value
        except Exception as e:
            logger.error(f"Error reading {file_extension} file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading {file_extension} file: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_extension}")


# 2. Modify the upload_resume_file endpoint in app_server.py
@app.post("/upload_resume_file", status_code=status.HTTP_200_OK)
async def upload_resume_file(resume_file: UploadFile = RESUME_FILE_UPLOAD):
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="No file found")

    # Updated to accept PDF, DOC, and DOCX files
    allowed_extensions = [".pdf", ".doc", ".docx"]
    file_extension = Path(resume_file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only PDF, DOC, and DOCX formats are supported")

    os.makedirs(RESUME_UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(RESUME_UPLOAD_FOLDER, resume_file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(resume_file.file, f)

    return {"message": "Resume uploaded successfully", "file_path": file_path}


# 3. Modify the resume_parser endpoint in app_server.py
@app.get("/resume_parser")
async def resume_parser(resume_path: str):
    file_path = os.path.join(RESUME_UPLOAD_FOLDER, resume_path)

    # Use the new universal text extraction function
    try:
        raw_resume_text = extract_text_from_document(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text from file: {e}")

    try:
        response = await extract_resume_info(raw_resume_text)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start LLM parsing stream: {e}")


# ---- Add these new models after existing models ----
class WeightageConfig(BaseModel):
    experience_weight: float = 0.3
    skills_weight: float = 0.4
    education_weight: float = 0.1
    projects_weight: float = 0.2


class ParseAndEvaluateRequest(BaseModel):
    resume_data: str
    jd_json: Dict[str, Any]
    weightage_config: WeightageConfig = WeightageConfig()


# ---- Replace the existing parse_and_evaluate endpoint ----
@app.post("/parse_and_evaluate", status_code=status.HTTP_200_OK)
async def parse_and_evaluate(request: ParseAndEvaluateRequest):
    if not request.resume_data or not request.jd_json:
        return PlainTextResponse(content="Missing resume_data or jd_json", status_code=422)

    # Validate weights sum to 1.0
    total_weight = request.weightage_config.experience_weight + request.weightage_config.skills_weight + request.weightage_config.education_weight + request.weightage_config.projects_weight

    if abs(total_weight - 1.0) > 0.01:  # Allow small floating point differences
        return PlainTextResponse(content=f"Weightage must sum to 100% (1.0). Current sum: {total_weight:.2f}", status_code=400)

    try:
        resp = await combined_parse_evaluate(request.resume_data, request.jd_json, request.weightage_config)
        return resp
    except Exception as e:
        error_str = str(e)
        if "The model is overloaded" in error_str:
            msg = "The model is overloaded. Please try after sometime."
        else:
            msg = error_str
        return PlainTextResponse(content=msg, status_code=500)
