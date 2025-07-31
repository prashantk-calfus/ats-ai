import json
import logging
import os
from pathlib import Path

import mammoth
from dotenv import load_dotenv
from google import genai
from langchain_community.document_loaders import PyMuPDFLoader

from ats_ai.agent.llm_agent import extract_json_block
from ats_ai.agent.prompts import JD_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_model = genai.Client()


def create_empty_jd_structure() -> dict:
    """Create a default JD structure with meaningful defaults instead of empty values"""
    return {
        "Job_Title": "Position Available",
        "Required_Skills": ["To be determined"],
        "Preferred_Skills": [],
        "Minimum_Experience": "NA",
        "Location": "NA",
        "Responsibilities": ["To be determined"],
        "Qualifications": [],
        "Domain": "General",
        "Key_considerations_for_hiring": [],
    }


def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return " ".join(page.page_content for page in pages)


def extract_jd_info(jd_text: str) -> dict:

    try:
        # Create the prompt
        prompt = JD_EXTRACTION_PROMPT.format(jd_text=jd_text.strip())

        # Get response from Gemini
        response = gemini_model.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        raw_response = response.text.strip()

        logger.info(f"Raw JD Extraction Output:\n{raw_response}")

        # Extract and parse JSON
        parsed_response = extract_json_block(raw_response)

        # Ensure all required fields exist with default values if missing
        default_structure = {"Job_Title": "NA", "Required_Skills": [], "Preferred_Skills": [], "Minimum_Experience": "NA", "Location": "NA", "Responsibilities": [], "Qualifications": [], "Domain": "NA", "Key_considerations_for_hiring": []}

        # Merge with defaults to ensure no missing fields
        final_response = {**default_structure, **parsed_response}
        print(final_response)
        logger.info("Successfully extracted JD information")
        return final_response

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JD JSON: {e}")
        logger.error(f"Raw response: {raw_response}")
        # Return default structure instead of empty
        return {
            "Job_Title": "Extracted from Text",
            "Required_Skills": ["To be determined"],
            "Preferred_Skills": [],
            "Minimum_Experience": "NA",
            "Location": "NA",
            "Responsibilities": ["To be determined"],
            "Qualifications": [],
            "Domain": "General",
            "Key_considerations_for_hiring": [],
        }
    except Exception as e:
        logger.error(f"Error in extract_jd_info: {e}")
        # Return default structure instead of empty
        return {
            "Job_Title": "Extracted from Text",
            "Required_Skills": ["To be determined"],
            "Preferred_Skills": [],
            "Minimum_Experience": "NA",
            "Location": "NA",
            "Responsibilities": ["To be determined"],
            "Qualifications": [],
            "Domain": "General",
            "Key_considerations_for_hiring": [],
        }


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


def save_json(data: dict, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Structured JD saved to: {output_path}")


def process_jd_folder_to_json():
    """
    Process all DOC/DOCX files in jd_folder and convert to JSON
    """
    jd_folder = Path("jd_folder")
    jd_json_folder = Path("jd_json")

    # Create jd_json folder if it doesn't exist
    jd_json_folder.mkdir(exist_ok=True)

    if not jd_folder.exists():
        logger.warning("jd_folder does not exist")
        return 0

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

                # Extract JD info using LLM (without validation)
                jd_structured = extract_jd_info(jd_text)

                # Always save the result (no validation check)
                json_filename = file_path.stem + ".json"
                json_path = jd_json_folder / json_filename

                # Save JSON
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(jd_structured, f, indent=2, ensure_ascii=False)

                logger.info(f"✅ Saved: {json_filename}")
                processed_count += 1

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

        if jd_structured:
            save_json(jd_structured, output_json_path)
        else:
            print("No JD content found in the PDF")
