import os
import json
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyMuPDFLoader
from Backend.llm_chain_agent import extract_json_from_response

def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return " ".join(page.page_content for page in pages)

def extract_jd_info(jd_text: str) -> dict:
    llm = Ollama(model="llama3.1:8b")

    prompt = f"""
        You are a job description parser.
        
        Extract structured information from the following JD text. Return valid JSON only.
        
        Format:
        {{
          "Job_Title": "Senior Backend Engineer",
          "Required_Skills": ["Python", "FastAPI", "Docker"],
          "Preferred_Skills": ["LangChain", "ML", "AWS"],
          "Minimum_Experience": "3+ years",
          "Location": "Bangalore",
          "Responsibilities": [
            "Develop REST APIs",
            "Maintain microservices architecture"
          ],
          "Qualifications": [
            "B.Tech in CS or related field"
          ],
          "Domain": "Software Development"
        }}
        
        JD Text:
        \"\"\"
        {jd_text}
        \"\"\"
        
        Only return valid JSON. No comments or explanation.
    """.strip()

    response = llm.invoke(prompt).strip()
    print("Raw JD Output:\n", response)

    response = extract_json_from_response(response)

    try:
        return response
    except json.JSONDecodeError as e:
        print("Failed to parse JD JSON:", e)
        return {}

def save_json(data: dict, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Structured JD saved to: {output_path}")

if __name__ == "__main__":
    jd_pdf_path = "../jd/SrPythonDev.pdf"
    output_json_path = "../jd_json/SrPDE.json"

    print(f"Loading JD from: {jd_pdf_path}")
    jd_text = load_pdf_text(jd_pdf_path)

    print("Extracting structured JD info...")
    jd_structured = extract_jd_info(jd_text)

    if jd_structured:
        save_json(jd_structured, output_json_path)
