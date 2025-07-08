from fastapi import FastAPI, UploadFile, File, Query, HTTPException
import uuid, os
from core.parser import extract_text_from_pdf
from core.embedder import get_embedding
from core.vector_db import  add_to_vector_db
from core.sqlite_db import insert_candidate, fetch_all_candidates
from core.llm_commenter import generate_comment
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json

app = FastAPI()
JD_FOLDER = "core/data/jd/"
RESUME_FOLDER = "core/data/resumes/"

@app.get("/generate-comments/")
def generate_comments_for_all_resumes(
    jd_filename: str = Query(..., description="JD PDF file name"),
    top_k: int = Query(10, description="How many top resumes to return")
):
    jd_path = os.path.join(JD_FOLDER, jd_filename)

    if not os.path.exists(jd_path):
        raise HTTPException(status_code=404, detail="JD file not found.")

    jd_text = extract_text_from_pdf(jd_path)
    jd_embedding = get_embedding(jd_text)

    temp_results = []

    resume_files = [f for f in os.listdir(RESUME_FOLDER) if f.endswith(".pdf")]
    if not resume_files:
        raise HTTPException(status_code=404, detail="No resumes found in folder.")

    MIN_RESUME_WORDS = 100  # Define your minimum word count here

    for resume_filename in resume_files:
        resume_path = os.path.join(RESUME_FOLDER, resume_filename)
        try:
            resume_text = extract_text_from_pdf(resume_path)

            # Check resume length
            if len(resume_text.split()) < MIN_RESUME_WORDS:
                print(f"Skipping {resume_filename}: Resume too short for ATS processing.")
                temp_results.append({
                    "name": resume_filename.replace("_", " ").replace(".pdf", ""),
                    "resume": resume_filename,
                    "ats_score": "N/A",
                    "llm_comment": " Skipped: Resume content is too short for meaningful ATS analysis. Please upload a more comprehensive resume."
                })
                continue # Skip to the next resume

            resume_embedding = get_embedding(resume_text)

            similarity = cosine_similarity(
                np.array(resume_embedding).reshape(1, -1),
                np.array(jd_embedding).reshape(1, -1)
            )[0][0]
            ats_score = round(similarity * 100, 2)

            raw_comment = generate_comment(resume_text, jd_text, ats_score)

            # Parse LLM output
            try:
                parsed = json.loads(raw_comment)
            except:
                try:
                    parsed = json.loads(raw_comment.strip().strip('"').replace('\\"', '"'))
                except:
                    parsed = {}

            name = parsed.get("name")
            if not name or not isinstance(name, str):
                name = "Name not mentioned"

            if "positive" in parsed and "negative" in parsed:
                comment = f" {parsed['positive']}  {parsed['negative']}"
            else:
                comment = raw_comment

            resume_id = str(uuid.uuid4())

            insert_candidate(
                uuid=resume_id,
                name=name,
                ats_score=ats_score,
                llm_comment=comment,
                jd_name=jd_filename
            )

            result = {
                "name": name,
                "resume": resume_filename,
                "ats_score": ats_score,
                "llm_comment": comment
            }
            temp_results.append(result)

            print(f" Name: {name} | ATS: {ats_score}%\nComment: {comment}\n")

        except Exception as e:
            print(f" Failed on {resume_filename}: {e}")
            temp_results.append({
                "name": resume_filename.replace("_", " ").replace(".pdf", ""),
                "resume": resume_filename,
                "ats_score": "Error",
                "llm_comment": f" Processing failed: {str(e)}"
            })


    # Sort only the valid ATS scores. Keep skipped/error entries at the bottom or handle as preferred.
    # For simplicity, sorting only based on numeric ATS scores and putting others at the end.
    sorted_results = sorted(temp_results, key=lambda x: x["ats_score"] if isinstance(x["ats_score"], (int, float)) else -1, reverse=True)
    return {
        "jd_used": jd_filename,
        "top_k": top_k,
        "results": sorted_results[:top_k]
    }


@app.post("/upload-resume/")
def upload_resume(file: UploadFile = File(...)):
    file_path = os.path.join(RESUME_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    resume_text = extract_text_from_pdf(file_path)
    resume_embedding = get_embedding(resume_text)
    resume_id = str(uuid.uuid4())
    name = file.filename.replace("_", " ").replace(".pdf", "")

    add_to_vector_db(resume_id, resume_embedding, {"filename": file.filename})
    insert_candidate(resume_id, name, None, None, None)

    return {
        "message": "Resume uploaded.",
        "name": name
    }

@app.get("/candidates/all")
def get_all():
    return fetch_all_candidates()

