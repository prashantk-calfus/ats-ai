import json
import os

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.llms import Ollama

from ats_ai.agent.llm_agent import extract_json_block
from ats_ai.agent.prompts import JD_EXTRACTION_PROMPT


def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return " ".join(page.page_content for page in pages)


def extract_jd_info(jd_text: str) -> dict:
    llm = Ollama(model="llama3.1:8b")

    prompt = JD_EXTRACTION_PROMPT(jd_text)
    response = llm.invoke(prompt).strip()
    print("Raw JD Output:\n", response)

    response = extract_json_block(response)

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
