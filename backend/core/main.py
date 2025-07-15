import os
import base64
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

# Import custom modules
from core.parser import extract_text, extract_hyperlinked_texts
from core.llm_scorer import score_resume_with_gemma
from core.model_store import save_selection

app = FastAPI()

# Directories
RESUME_DIR = "core/data/resumes/"
JD_DIR = "core/data/jd/"
SELECTED_RESUMES_DIR = "core/data/selected_resumes/"
REJECTED_RESUMES_DIR = "core/data/rejected_resumes/"
MATCH_RESULTS_DIR = "core/data/match_results/"

# Ensure required directories exist
for path in [RESUME_DIR, JD_DIR, SELECTED_RESUMES_DIR, REJECTED_RESUMES_DIR, MATCH_RESULTS_DIR]:
    os.makedirs(path, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResumeUploadRequest(BaseModel):
    filename: str
    file_data: str

class MatchRequest(BaseModel):
    jd_filename: str
    resume_filename: str

class SelectionRequest(BaseModel):
    resume_file: str
    jd_file: str
    status: str
    match_score: str
    linkedin: str = ""
    github: str = ""
    name: str = "Unknown"

@app.post("/upload-resume/")
def upload_resume(request: ResumeUploadRequest):
    sanitized_filename = sanitize_filename(request.filename)
    decoded_file = base64.b64decode(request.file_data)

    file_path = os.path.join(RESUME_DIR, sanitized_filename)
    with open(file_path, "wb") as f:
        f.write(decoded_file)

    print(f" Saved resume: {file_path}")  # Debug log
    return {"message": f"Resume '{sanitized_filename}' uploaded and saved successfully."}


@app.get("/list-jds/")
def list_jds():
    try:
        jds = [f for f in os.listdir(JD_DIR) if f.endswith(".pdf")]
        return {"jd_list": jds}
    except Exception as e:
        return JSONResponse(content={"error": "Failed to retrieve JD list."}, status_code=500)


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w_.-]", "_", filename)

@app.post("/match/")
def match_resume(request: MatchRequest):
    sanitized_resume = sanitize_filename(request.resume_filename)
    sanitized_jd = sanitize_filename(request.jd_filename)

    resume_path = os.path.join(RESUME_DIR, sanitized_resume)
    jd_path = os.path.join(JD_DIR, sanitized_jd)

    print(f" Matching: {resume_path} vs {jd_path}")

    if not os.path.exists(resume_path):
        return JSONResponse(content={"error": f"Resume file '{sanitized_resume}' not found."}, status_code=404)
    if not os.path.exists(jd_path):
        return JSONResponse(content={"error": f"JD file '{sanitized_jd}' not found."}, status_code=404)

    safe_resume = sanitized_resume.replace(".pdf", "")
    safe_jd = sanitized_jd.replace(".pdf", "")
    cache_file = os.path.join(MATCH_RESULTS_DIR, f"{safe_resume}_vs_{safe_jd}_result.json")

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except:
            pass

    try:
        resume_text = extract_text(resume_path)
        jd_text = extract_text(jd_path)
        hyperlinks = extract_hyperlinked_texts(resume_path)
        fallback_links = fallback_links_from_text(resume_text)

        linkedin_url = hyperlinks.get("linkedin") or fallback_links.get("linkedin") or ""
        github_url = hyperlinks.get("github") or fallback_links.get("github") or ""

        llm_prompt = f"""
You are an expert ATS (Applicant Tracking System) and resume analyst. Your task is to meticulously compare a given resume with a job description and provide a comprehensive analysis.

Input:
<RESUME_TEXT>
{resume_text}
</RESUME_TEXT>

<JOB_DESCRIPTION_TEXT>
{jd_text}
</JOB_DESCRIPTION_TEXT>

Scoring Instructions:
- skill_score (1-10)
- experience_score (1-10)
- match_score = (0.7 * skill_score + 0.3 * experience_score) * 10 as a string: "87%"

Also extract:
- name: Extract the full name (first and last name) from the resume. If not mentioned, return "Unknown".
- linkedin
- github
- cgpa
- matched_skills
- missing_skills
- extra_skills
- positive
- negative

Return output ONLY in valid JSON format like this:
{{
  "name": "John Doe",
  "skill_score": 8,
  "experience_score": 7,
  "match_score": "79%",
  "linkedin": "https://linkedin.com/in/example",
  "github": "https://github.com/example",
  "cgpa": "8.5",
  "matched_skills": ["Python", "Django"],
  "missing_skills": ["AWS"],
  "extra_skills": ["Photoshop"],
  "positive": ["Strong backend experience"],
  "negative": ["No mention of AWS"]
}}
"""

        result = score_resume_with_gemma(resume_text, jd_text, llm_prompt=llm_prompt)

        if result and "error" not in result:

            if not result.get("name") or result["name"].strip().lower() in ["", "technical skills"]:
                result["name"] = "Unknown"

            if not isinstance(result.get("linkedin"), str) or result.get("linkedin", "").lower() in ["", "linkedin"]:
                result["linkedin"] = linkedin_url
            if not isinstance(result.get("github"), str) or result.get("github", "").lower() in ["", "github"]:
                result["github"] = github_url

            with open(cache_file, "w") as f:
                json.dump(result, f, indent=2)

        return result

    except Exception as e:
        return JSONResponse(content={"error": f"Error during LLM matching: {e}"}, status_code=500)

@app.post("/store-selection/")
def store_selection(request: SelectionRequest):
    try:
        save_selection(
            resume_file=request.resume_file,
            jd_file=request.jd_file,
            status=request.status,
            match_score=request.match_score,
            linkedin=request.linkedin,
            github=request.github,
            name=request.name
        )
        return {"message": f"Selection for {request.name} stored successfully."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


def fallback_links_from_text(text: str) -> dict:

    links = {"linkedin": None, "github": None}

    for match in re.findall(r"https?://[^\s]+", text):
        if "linkedin.com" in match and not links["linkedin"]:
            links["linkedin"] = match
        if "github.com" in match and not links["github"]:
            links["github"] = match

    # Raw mentions without http/https
    if not links["linkedin"]:
        raw = re.search(r"(linkedin\.com/[^\s\)\]]+)", text)
        if raw:
            links["linkedin"] = "https://" + raw.group(1)

    if not links["github"]:
        raw = re.search(r"(github\.com/[^\s\)\]]+)", text)
        if raw:
            links["github"] = "https://" + raw.group(1)

    return links
