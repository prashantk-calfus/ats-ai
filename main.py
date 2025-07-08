"""
Resume Ranking System using LangChain and ChromaDB
This script processes resumes and ranks them based on similarity to a job description.
"""
import os
import glob
import shutil
from typing import List, Tuple

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain_core import documents

# Constants
RESUMES_DIR = "data/"
VECTORSTORE_DIR = "resume_vectorstore"
EMBEDDING_MODEL = "all-mpnet-base-v2"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 80
MIN_RESUME_WORD_COUNT = 100

shutil.rmtree(VECTORSTORE_DIR, ignore_errors=True)
print("Removing existing vectorstore...")

class ResumeRanker:

    def __init__(self, vectorstore_dir: str = VECTORSTORE_DIR):

        self.vectorstore_dir = vectorstore_dir
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        self.vectorstore = None

    def load_and_chunk_pdf(self, pdf_path: str, source_name: str = None) -> List[Document]:
        """
            Loads and chunks any provided document.
        """
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        if not source_name:
            source_name = os.path.basename(pdf_path)

        full_text = " ".join([doc.page_content for doc in documents])
        word_count = len(full_text.split())

        # --- New: Minimum content threshold check ---
        if word_count < MIN_RESUME_WORD_COUNT:
            raise ValueError(
                f"Skipping '{source_name}': Extracted text has only {word_count} words, "
                f"which is below the minimum threshold of {MIN_RESUME_WORD_COUNT}. "
                f"This is likely not a complete resume or has poor extraction."
            )

        # Add source information to metadata
        for doc in documents:
            doc.metadata['source'] = source_name
            doc.metadata['file_path'] = pdf_path
            # doc.metadata['uuid'] = uuid

        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        return chunks

    def create_resume_vectorstore(self, resumes_dir: str = RESUMES_DIR) -> bool:
        """
            Creates a new resume vectorstore.
        """

        # Find all PDF files in the resumes directory
        pdf_files = glob.glob(os.path.join(resumes_dir, "*.pdf"))

        if not pdf_files:
            return False

        # Load and chunk all resumes
        all_chunks = []
        for pdf_file in pdf_files:
            resume_name = os.path.basename(pdf_file)
            chunks = self.load_and_chunk_pdf(pdf_file, resume_name)
            all_chunks.extend(chunks)

        if not all_chunks:
            return False

        # Create ChromaDB vector store
        self.vectorstore = Chroma.from_documents(
            documents=all_chunks,
            embedding=self.embeddings,
            persist_directory=self.vectorstore_dir,
            collection_metadata={"hnsw:space": "cosine"}
        )
        # Persist the vector store
        self.vectorstore.persist()
        return True

    def load_existing_vectorstore(self) -> bool:
        """
            Loads existing vectorstore.
        """
        if not os.path.exists(self.vectorstore_dir):
            return False

        self.vectorstore = Chroma(
            persist_directory=self.vectorstore_dir,
            embedding_function=self.embeddings
        )
        return True

    def semantic_search_resumes(self, jd_path: str) -> List[Tuple[str, float]]:

        """
            Lauch semantic search for all candidates acc to i/p JD filepath.
            Returns JSON of all {candidate_filename : similarity score}
        """

        # Load vector store if not already loaded
        if self.vectorstore is None:
            if not self.load_existing_vectorstore():
                return []

        # Load and chunk the job description
        jd_chunks = self.load_and_chunk_pdf(jd_path, "job_description")
        if not jd_chunks:
            return []

        # Combine all JD chunks into one query string
        jd_text = " ".join([chunk.page_content for chunk in jd_chunks])

        # Get all chunks from the vector store
        total_chunks_in_store = self.vectorstore._collection.count()

        # Search for all chunks to evaluate every resume
        search_results = self.vectorstore.similarity_search_with_score( # THIS RETURNS COSINE DISTANCE, 1 - COSINE_SIM
            jd_text,
            k=total_chunks_in_store
        )

        print("\n\nChunks in store", total_chunks_in_store)

        # Group results by resume and use similarity scores
        resume_scores = {}
        for doc, score in search_results:
            resume_name = doc.metadata.get('source', 'unknown')
            # uuid = doc.metadata.get('uuid', 'unknown')  # Fetch file uuid

            # Convert distance to similarity (lower distance = higher similarity)
            similarity = 1 - score/2

            # Keep the best similarity score for each resume
            if resume_name not in resume_scores or similarity > resume_scores[resume_name]:
                resume_scores[resume_name] = similarity

        # Sort ALL resumes by similarity score (descending)
        sorted_resumes = sorted(
            resume_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        # Return top k resumes
        return sorted_resumes

    def top_k_resumes(self, sorted_resumes, k: int) -> List[Tuple[str, float]]:

        """
            Get only top k resumes.
            To be executed only after semantic_search_resumes() function.
        """

        return sorted_resumes[:k]

    def print_results(self, results: List[Tuple[str, float]]):
        """TESTING FUNCTION"""
        print(f"\n{'=' * 60}")
        print(f"RESUME RANKING RESULTS")
        print(f"{'=' * 60}")
        print(f"Total Matches Found: {len(results)}")
        print(f"{'=' * 60}")

        if not results:
            print("No matching resumes found.")
            return
        for i, (resume_name, score) in enumerate(results, 1):
            print(f"{i:2d}. {resume_name:<30} | Similarity: {score:.4f}")
        print(f"{'=' * 60}")


def main():

    # Configuration
    JD_PATH = "jd/JD.pdf"
    TOP_K = 3

    # Initialize the ranker
    ranker = ResumeRanker()

    # Check if vector store exists, create if not
    if not os.path.exists(VECTORSTORE_DIR):
        print("Creating new vector store from resumes...")
        success = ranker.create_resume_vectorstore()
        if not success:
            print("Failed to create vector store. Please check your resume files.")
            return
    else:
        print("Loading existing vector store...")
        success = ranker.load_existing_vectorstore()
        if not success:
            print("Failed to load existing vector store. Creating new one...")
            success = ranker.create_resume_vectorstore()
            if not success:
                print("Failed to create vector store. Please check your resume files.")
                return

    # Check if job description file exists
    if not os.path.exists(JD_PATH):
        print(f"Job description file {JD_PATH} not found.")
        print("Please ensure the job description PDF is in the current directory.")
        return

    # Find top matching resumes
    print(f"Finding top {TOP_K} matching resumes...")
    sorted_resumes = ranker.semantic_search_resumes(JD_PATH)
    top_k  = ranker.top_k_resumes(sorted_resumes, TOP_K)

    # Print results
    ranker.print_results(top_k)
    # Return the results for programmatic use
    return top_k


if __name__ == "__main__":
    # Run the main workflow
    results = main()
    # Example of how to use the results programmatically
    if results:
        print("\nTop resume filenames:")
        for resume_name, score in results:
            print(f"- {resume_name}")