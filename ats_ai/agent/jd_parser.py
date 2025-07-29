import json
import logging
import os
from pathlib import Path

import mammoth
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.llms import Ollama

from ats_ai.agent.llm_agent import extract_json_block
from ats_ai.agent.prompts import JD_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


def create_empty_jd_structure() -> dict:
    """Create an empty JD structure for invalid inputs"""
    return {"is_valid_jd": False, "Job_Title": "", "Required_Skills": [], "Preferred_Skills": [], "Minimum_Experience": "", "Location": "", "Responsibilities": [], "Qualifications": [], "Domain": ""}


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
        prompt = JD_EXTRACTION_PROMPT.replace("{{JD_TEXT}}", jd_text.strip())

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


def load_docx_text(file_path: str) -> str:
    """Load text from DOCX file"""
    try:
        with open(file_path, "rb") as docx_file:
            result = mammoth.extract_raw_text(docx_file)
            return result.value
    except Exception as e:
        logger.error(f"Error reading DOCX file {file_path}: {e}")
        return ""


def load_document_text(file_path: str) -> str:
    """Universal document loader for PDF, DOC, DOCX"""
    file_extension = Path(file_path).suffix.lower()

    if file_extension == ".docx":
        return load_docx_text(file_path)

    else:
        raise ValueError(f"Unsupported file format: {file_extension}")


def process_jd_folder_to_json():
    """
    NEW FUNCTION: Process all DOC/DOCX files in jd_folder and convert to JSON
    """
    jd_folder = Path("jd_folder")
    jd_json_folder = Path("jd_json")

    # Create jd_json folder if it doesn't exist
    jd_json_folder.mkdir(exist_ok=True)

    if not jd_folder.exists():
        logger.warning("jd_folder does not exist")
        return

    # Process all DOC/DOCX files
    supported_extensions = [".doc", ".docx", ".pdf"]
    processed_count = 0

    for file_path in jd_folder.iterdir():
        if file_path.suffix.lower() in supported_extensions:
            try:
                logger.info(f"Processing: {file_path.name}")

                # Load document text
                jd_text = load_document_text(str(file_path))

                if not jd_text.strip():
                    logger.warning(f"No text extracted from {file_path.name}")
                    continue

                # Extract JD info using LLM
                jd_structured = extract_jd_info(jd_text)

                # Check if it's a valid JD
                is_valid_jd = bool(jd_structured.get("Job_Title", "").strip() or jd_structured.get("Required_Skills", []) or jd_structured.get("Responsibilities", []))

                if is_valid_jd:
                    # Create JSON filename
                    json_filename = file_path.stem + ".json"
                    json_path = jd_json_folder / json_filename

                    # Save JSON
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(jd_structured, f, indent=2, ensure_ascii=False)

                    logger.info(f"✅ Saved: {json_filename}")
                    processed_count += 1
                else:
                    logger.warning(f"❌ Invalid JD: {file_path.name}")

            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                continue

    logger.info(f"Processed {processed_count} JD files successfully")
    return processed_count


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
