import fitz  # PyMuPDF

def extract_text(file_path: str) -> str:
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception as e:
        print(f"[Parser Error] Failed to extract text from {file_path}: {e}")
        return ""

def extract_hyperlinked_texts(file_path: str) -> dict:

    hyperlinks = {"linkedin": None, "github": None}
    try:
        doc = fitz.open(file_path)
        for page in doc:
            for link in page.get_links():
                uri = link.get("uri")
                if uri:
                    if "linkedin.com" in uri.lower():
                        hyperlinks["linkedin"] = uri
                    elif "github.com" in uri.lower():
                        hyperlinks["github"] = uri
    except Exception as e:
        print(f"[Parser Error] Failed to extract hyperlinks: {e}")
    return hyperlinks
