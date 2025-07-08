# import pdfplumber
#
# def extract_text_from_pdf(pdf_path):
#     with pdfplumber.open(pdf_path) as pdf:
#         text = ''
#         for page in pdf.pages:
#             text += page.extract_text() or ''
#     return text.strip()


# core/parser.py

from langchain_community.document_loaders import PyPDFLoader

def extract_text_from_pdf(pdf_path: str) -> str:
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    # Combine all pages into a single string
    full_text = "\n".join([page.page_content for page in pages])
    return full_text.strip()
