import os
import chromadb
from core.parser import extract_text_from_pdf
from core.embedder import get_embedding

chroma_path = "core/.chroma_db"
resume_folder = "core/data/resumes"

client = chromadb.PersistentClient(path=chroma_path)
collection = client.get_or_create_collection(name="resumes")

def load_resumes_to_db():
    for fname in os.listdir(resume_folder):
        if fname.endswith(".pdf"):
            path = os.path.join(resume_folder, fname)
            text = extract_text_from_pdf(path)
            embedding = get_embedding(text)
            collection.add(
                documents=[text],
                metadatas=[{"filename": fname}],
                ids=[fname]
            )

# def query_vector_db(jd_embedding, top_k=10):
#     return collection.query(query_embeddings=[jd_embedding], n_results=top_k)


def add_to_vector_db(doc_id: str, embedding: list, metadata: dict):
    # Check if file is already in DB
    existing = collection.get(
        where={"filename": metadata["filename"]}
    )
    if existing["ids"]:
        print(f" Already exists in DB: {metadata['filename']}")
        return

    # Add only if not exists
    collection.add(
        embeddings=[embedding],
        metadatas=[metadata],
        ids=[doc_id]
    )
