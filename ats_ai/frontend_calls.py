import requests
from typing import Optional, Dict, Any

BACKEND_URL = "http://localhost:8000"

"""
    Functions used by frontend streamlit to call server.
"""

def upload_resume_file_to_backend(file, status_placeholder) -> Optional[str]:
    """
    Uploads the resume PDF to the backend and returns the filename if successful.
    The backend saves the file and does NOT return parsed data here.
    """
    try:
        file.seek(0)  # Ensure file pointer is at the beginning
        files = {"resume_file": (file.name, file.getvalue(), file.type)}
        status_placeholder.info(f"Uploading `{file.name}` to backend...")
        upload_response = requests.post(f"{BACKEND_URL}/upload_resume_file", files=files)

        if upload_response.status_code == 200:
            response_data = upload_response.json()
            if response_data.get("message") == "Resume uploaded successfully":
                status_placeholder.success(f"Resume uploaded: `{file.name}`")
                return file.name
            else:
                status_placeholder.error(f"Upload failed: {response_data.get('message', 'Unknown error')}")
                return None
        else:
            status_placeholder.error(f"Backend upload error: Status {upload_response.status_code} - {upload_response.text}")
            return None
    except requests.exceptions.RequestException as req_err:
        status_placeholder.error(f"Network or backend connection error during upload: {req_err}")
        return None
    except Exception as e:
        status_placeholder.error(f"An unexpected error occurred during upload: {str(e)}")
        return None


def parse_resume_from_backend(resume_filename: str, status_placeholder) -> Optional[Dict[str, Any]]:
    """
    Sends a request to the backend's /resume_parser endpoint to get the parsed resume JSON.
    """
    try:
        status_placeholder.info(f"Requesting parsing for `{resume_filename}` from backend...")
        # Note: The backend's /resume_parser expects the filename as a query parameter
        parse_response = requests.get(f"{BACKEND_URL}/resume_parser", params={"resume_path": resume_filename})

        if parse_response.status_code == 200:
            parsed_data = parse_response.json()
            status_placeholder.success(f"Resume parsed successfully for `{resume_filename}`.")
            return parsed_data
        else:
            status_placeholder.error(f"Backend parsing error: Status {parse_response.status_code} - {parse_response.text}")
            return None
    except requests.exceptions.RequestException as req_err:
        status_placeholder.error(f"Network or backend connection error during parsing: {req_err}")
        return None
    except Exception as e:
        status_placeholder.error(f"An unexpected error occurred during parsing: {str(e)}")
        return None


def evaluate_resume_with_backend(parsed_data: Dict[str, Any], jd_json: Dict[str, Any], evaluation_status_placeholder) -> Optional[Dict[str, Any]]:
    """Sends evaluation request to backend"""
    try:
        if not parsed_data:
            evaluation_status_placeholder.warning("No parsed resume data available for evaluation.")
            return None
        payload = {
            "resume_json": parsed_data,
            "jd_json": jd_json,
        }
        # st.json(payload)

        evaluation_status_placeholder.info(f"Sending evaluation request with JD....")
        eval_response = requests.post(f"{BACKEND_URL}/evaluate_resume", json=payload)

        if eval_response.status_code == 200:
            return eval_response.json()
        else:
            evaluation_status_placeholder.error(
                f"Backend responded with an error during evaluation: Status {eval_response.status_code} - {eval_response.text}"
            )
            return None

    except requests.exceptions.RequestException as req_err:
        evaluation_status_placeholder.error(f"Network or backend error during evaluation: {req_err}")
        return None
    except Exception as e:
        evaluation_status_placeholder.error(f"An unexpected error occurred during evaluation: {str(e)}")
        return None