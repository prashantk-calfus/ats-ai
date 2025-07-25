import json
import logging
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.llms import Ollama
from ats_ai.agent.llm_agent import extract_json_block
from ats_ai.agent.prompts import JD_EXTRACTION_PROMPT
from ats_ai.agent.prompts import JD_VALIDATION_AND_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

def create_empty_jd_structure() -> dict:
    """Create an empty JD structure for invalid inputs"""
    return {
        "is_valid_jd": False,
        "Job_Title": "",
        "Required_Skills": [],
        "Preferred_Skills": [],
        "Minimum_Experience": "",
        "Location": "",
        "Responsibilities": [],
        "Qualifications": [],
        "Domain": ""
    }



def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return " ".join(page.page_content for page in pages)


def extract_jd_info(jd_text: str) -> dict:
    """
    Enhanced function that validates if text is a JD and extracts info accordingly.
    Uses LLM intelligence instead of hardcoded keywords.
    """
    try:
        # Initialize the LLM
        llm = Ollama(model="llama3.1:8b")

        # Create the enhanced prompt with validation
        prompt = JD_VALIDATION_AND_EXTRACTION_PROMPT.replace("{{JD_TEXT}}", jd_text.strip())

        # Get response from LLM
        response = llm.invoke(prompt).strip()
        logger.info(f"Raw JD Validation Output:\n{response}")

        # Extract and parse JSON
        parsed_response = extract_json_block(response)

        # Check if LLM determined this is a valid JD
        is_valid = parsed_response.get("is_valid_jd", False)

        if not is_valid:
            logger.info("LLM determined text is not a valid job description")
            return create_empty_jd_structure()

        # Remove the validation flag from the final output to match your expected format
        final_response = {k: v for k, v in parsed_response.items() if k != "is_valid_jd"}

        logger.info("Successfully extracted JD information")
        return final_response

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JD JSON: {e}")
        logger.error(f"Raw response: {response}")
        return create_empty_jd_structure()
    except Exception as e:
        logger.error(f"Error in extract_jd_info: {e}")
        return create_empty_jd_structure()


def save_json(data: dict, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Structured JD saved to: {output_path}")



if __name__ == "__main__":

    jd_pdf_path = "../jd/Calfus - SSE PythonFS - JD.pdf"
    output_json_path = "../../jd_json/SeniorFullStackEngineer_Python.json"

    if os.path.exists(jd_pdf_path):
        print(f"Loading JD from: {jd_pdf_path}")
        jd_text = load_pdf_text(jd_pdf_path)

        print("Extracting structured JD info...")
        jd_structured = extract_jd_info(jd_text)

        if jd_structured and jd_structured.get("Job_Title"):
            save_json(jd_structured, output_json_path)
        else:
            print("No valid JD content found in the PDF")