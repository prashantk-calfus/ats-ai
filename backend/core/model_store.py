import os
import shutil
import json
import datetime
import re

# Paths
RESUME_DIR = "core/data/resumes/"
SELECTED_DIR = "core/data/selected_resumes/"
REJECTED_DIR = "core/data/rejected_resumes/"
MATCH_RESULTS_DIR = "core/data/match_results/"
SELECTION_LOG = "core/data/selection_log.json"

# --- Helper: sanitize filenames ---
def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w_.-]", "_", filename)

def save_selection(resume_file: str, jd_file: str, status: str, match_score: str, linkedin: str = "", github: str = "", name: str = "Unknown"):
    status = status.lower()
    if status not in ["select", "reject"]:
        raise ValueError(f"Invalid status provided: {status}")

    # Sanitize filenames
    safe_resume_file = sanitize_filename(resume_file)
    safe_jd_file = sanitize_filename(jd_file)

    # Validate resume exists
    src_path = os.path.join(RESUME_DIR, safe_resume_file)
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Resume file not found: {resume_file}")

    # Determine destination directory
    dest_dir = SELECTED_DIR if status == "select" else REJECTED_DIR
    dest_path = os.path.join(dest_dir, safe_resume_file)
    shutil.copy2(src_path, dest_path)

    # Fallback: If name not passed, try from cache
    if name == "Unknown":
        cache_file = os.path.join(MATCH_RESULTS_DIR, f"{safe_resume_file.replace('.pdf', '')}_vs_{safe_jd_file.replace('.pdf', '')}_result.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    result = json.load(f)
                    name = result.get("name", "Unknown")
            except Exception:
                pass

    # Create record
    record = {
        "timestamp": str(datetime.datetime.now()),
        "name": name,
        "resume_file": resume_file,   # Original name (not sanitized) for readability
        "jd_file": jd_file,
        "status": status,
        "match_score": match_score,
        "linkedin": linkedin,
        "github": github
    }

    # Append to log
    existing = []
    if os.path.exists(SELECTION_LOG):
        try:
            with open(SELECTION_LOG, "r") as f:
                existing = json.load(f)
        except:
            existing = []

    existing.append(record)
    with open(SELECTION_LOG, "w") as f:
        json.dump(existing, f, indent=2)


