import asyncio
import json
import logging
import os
import re
import shutil
import threading
from typing import Any, Dict

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
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


# @app.post("/evaluate_resume", status_code=status.HTTP_200_OK)
# async def evaluate_resume(payload: ResumeEvaluationRequest):
#     """
#     Evaluate resume with JD
#     """
#     try:
#         response = await evaluate_resume_against_jd(payload.jd_json, payload.resume_json)
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to start LLM evaluation stream: {e}")


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


@app.post("/generate_pdf_report", status_code=status.HTTP_200_OK)
async def generate_pdf_report_endpoint(report_data: Dict[str, Any]):
    """Generate PDF report and return file path"""
    try:
        evaluation_results = report_data.get("evaluation_results")
        parsed_resume = report_data.get("parsed_resume")
        candidate_name = report_data.get("candidate_name")
        jd_source = report_data.get("jd_source", "Unknown JD")

        # Generate PDF
        pdf_filename = generate_pdf_report(evaluation_results, parsed_resume, candidate_name, jd_source)

        return {"status": "success", "pdf_path": pdf_filename, "message": "PDF report generated successfully"}

    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF report: {str(e)}")


@app.get("/download_report/{filename}")
async def download_report(filename: str):
    """Download the generated PDF report"""
    file_path = f"reports/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=filename)
    else:
        raise HTTPException(status_code=404, detail="Report file not found")


# ---- Run ----
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
