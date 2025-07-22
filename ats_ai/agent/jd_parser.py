import json
import os

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.llms import Ollama
from llm_agent import extract_json_from_response


def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return " ".join(page.page_content for page in pages)


def extract_jd_info(jd_text: str) -> dict:
    llm = Ollama(model="llama3.1:8b")

    prompt = f"""
    You are an expert HR analyst AI.

    Your task is to extract structured information from the provided job description (JD) text. Focus only on what is explicitly or strongly implied in the JD. Do not make assumptions or fabricate information.

    CRITICAL RULES:
    1. Respond ONLY in valid JSON. Do NOT include commentary, explanations, or anything outside the JSON object.
    2. If a field is missing in the JD, return "NA" or an empty list as appropriate.
    3. Use the exact structure and keys as specified below.
    4. Be comprehensive, but avoid duplication or invented content.

    RETURN FORMAT (strictly follow this):
    {{
      "Job_Title": "Job title as mentioned",
      "Required_Skills": ["list of must-have skills, tools, or technologies"],
      "Preferred_Skills": ["list of nice-to-have skills or tools"],
      "Minimum_Experience": "minimum experience required (e.g., '3+ years')",
      "Location": "location mentioned (or 'Remote', 'Hybrid', or 'NA')",
      "Responsibilities": ["key responsibilities extracted as list items"],
      "Qualifications": ["required degrees, certifications, or qualifications"],
      "Key considerations for hiring" : ["list down very important factors detrimental for hiring"]
    }}

    JD TEXT:
    \"\"\"
    {jd_text}
    \"\"\"

    Return only the structured JSON output.
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
    jd_pdf_path = "../jd/Calfus - SSE PythonFS - JD.pdf"
    output_json_path = "../../jd_json/SeniorFullStackEngineer_Python.json"

    print(f"Loading JD from: {jd_pdf_path}")
    jd_text = load_pdf_text(jd_pdf_path)

    print("Extracting structured JD info...")
    jd_structured = extract_jd_info(jd_text)

    if jd_structured:
        save_json(jd_structured, output_json_path)
