from fastapi import FastAPI, UploadFile, HTTPException, File
from langchain_community.document_loaders import PyPDFLoader

import requests
import shutil
import os
import json

from database import CandidateDB
from main import ResumeRanker

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "mistral"

jd_dir = "jd/"
VECTORSTORE_DIR = "chroma_db"
resume_dir = "data/"

obj = ResumeRanker()
sql_db = CandidateDB()

shutil.rmtree(VECTORSTORE_DIR, ignore_errors=True) # Clear and build vectorstore

if obj.vectorstore is None:
    obj.create_resume_vectorstore(resume_dir)

app = FastAPI()

@app.get("/semantic_search_resumes")
def semantic_search_resumes(jd_path):
    """
    This function should give semantic similarity scores and add them to the sqlite database.
    """
    sorted_resumes = obj.semantic_search_resumes(jd_dir+jd_path)

    for filename, score in sorted_resumes:
        candidate_record = sql_db.get_candidate_by_resume_filename(filename)

        if candidate_record:
            candidate_uuid = candidate_record[0]
            sql_db.update_candidate(candidate_uuid, similarity_score=score)
            print(filename + " score for: " + str(score))

    return sorted_resumes

@app.get("/ask_llm")
def ask_llm(resume_filename: str, jd_path: str):

    """
    Query a single candidate with the LLM along with the Job Description of their Applied position.
    Retrieved results are saved to sqlite database.
    """

    loader = PyPDFLoader(jd_dir + jd_path)
    JD = loader.load()

    loader = PyPDFLoader(resume_dir+resume_filename)
    resume = loader.load()

    prompt = f"""
        JD: {JD}
        Resume: {resume} 
    """

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": """You are a hiring expert. Given a JD and a resume, 
            find out if the candidate is suitable for the job role by listing out their pros and cons. 
            Format for reply is this, list at max 3 pros and 3 cons, and then grade it out of 100 -  
            {
                "pros": {...},
                "cons": {...},
                "score": {score}
            }
            """ },
            {"role": "user", "content": prompt}
        ],
        "stream": False
    })

    response_data = response.json()

    # Step 2: Extract and parse the content (which is a stringified JSON)
    raw_content = response_data["message"]["content"]

    try:
        content_json = json.loads(raw_content)
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing content JSON: {e}\nRaw Content:\n{raw_content}")

    # Step 3: Extract values
    pros = content_json.get("pros", [])
    cons = content_json.get("cons", [])
    score = content_json.get("score", None)

    # Step 4: Combine into a new structured dict
    summary = {
        "pros": pros,
        "cons": cons,
        "score": score
    }

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    summary = json.dumps(summary)
    candidate_record = sql_db.get_candidate_by_resume_filename(resume_filename)
    cand_uuid = candidate_record[0]
    sql_db.update_candidate(cand_uuid, candidate_name=None, resume_filename=None, position_applied=None,
                            similarity_score=None, ai_comments=summary)

    return summary

@app.post("/append_resume")
def append_resume(candidate_name:str, position_applied:str, file : UploadFile = File(...)):
    # This adds to both chromaDB and sqlite3

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=404, detail="Only .pdf files supported.")

    file_path = os.path.join(resume_dir, file.filename)
    print(f"File path: {file_path}")

    exist_source = {
        meta.get("source") for meta in obj.vectorstore.get()["metadatas"]
    }

    if file.filename in exist_source:
        print("Duplication error.")
        raise HTTPException(status_code=404, detail="File already exists.")

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        new_chunks = obj.load_and_chunk_pdf(file_path) # Check for min text requirement
    except ValueError as e:
        os.remove(file_path) # FILE REMOVED
        return {'message': str(e)}

    sql_db.add_candidate(candidate_name, file.filename, position_applied) # adding to sqlite database

    obj.vectorstore.add_documents(new_chunks)
    obj.vectorstore.persist()

    return {"message": f"Resume '{file.filename}' uploaded successfully."}
