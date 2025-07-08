import os
import uuid
import json
from core.parser import extract_text_from_pdf
from core.embedder import get_embedding
from core.vector_db import add_to_vector_db
from core.sqlite_db import insert_candidate
from core.llm_commenter import generate_comment
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

RESUME_DIR = "core/data/resumes"
JD_PATH = "core/data/jd/py.pdf"  # Default JD file to match

# Extract JD text and embedding once
jd_text = extract_text_from_pdf(JD_PATH)
jd_embedding = get_embedding(jd_text)

def bulk_load():
    files = [f for f in os.listdir(RESUME_DIR) if f.endswith(".pdf")]
    for file in files:
        path = os.path.join(RESUME_DIR, file)
        print(f"Processing: {file}")
        try:
            resume_text = extract_text_from_pdf(path)
            embedding = get_embedding(resume_text)
            resume_id = str(uuid.uuid4())

            similarity = cosine_similarity(
                np.array(embedding).reshape(1, -1),
                np.array(jd_embedding).reshape(1, -1)
            )[0][0]
            ats_score = round(similarity * 100, 2)

            raw_comment = generate_comment(resume_text, jd_text, ats_score)

            try:
                parsed = json.loads(raw_comment)
                comment = f" {parsed['positive']}  {parsed['negative']}"
                name = parsed.get("name") or file.replace("_", " ").replace(".pdf", "")
            except Exception as e:
                comment = raw_comment
                name = file.replace("_", " ").replace(".pdf", "")

            add_to_vector_db(resume_id, embedding, {"filename": file})
            insert_candidate(resume_id, name, ats_score, comment, os.path.basename(JD_PATH))

            print(f" {name} - {ats_score}% ")

        except Exception as e:
            print(f" Failed: {file} — {e}")

if __name__ == "__main__":
    bulk_load()
