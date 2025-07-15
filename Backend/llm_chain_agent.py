
"""
    Using LLM chaining workflow to parse, evaluate, and validate resume and given job description
    to create a robust and accurate assessment of a candidate.
    1. extract_resume_info : Parsing Agent
    2. evaluate_resume_against_jd : Evaluation Agent
    3. correct_evaluation_output : Validation Agent
"""

import json
import re
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyMuPDFLoader

from typing import AsyncGenerator, Any

llm = Ollama(model="llama3.1:8b")
             # base_url="http://host.docker.internal:11434")

JSON_CHUNK_DELIMITER = "---END_OF_JSON_CHUNK---"

def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()

    return " ".join(page.page_content for page in pages)

def extract_json_from_response(response: str) -> dict:

    """Helper function to extract JSON data from response"""

    match = re.search(r"```json(.*?)```", response, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
    else:
        json_str = response.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        print("Raw string was:\n", json_str[:500])
        return {}

async def extract_resume_info(raw_resume_text: str) -> AsyncGenerator[Any, Any]:
    """
        Parsing Agent LLM.
        Parse information from resume into JSON
    """

    prompt = f"""
        You are an expert resume parser in HR and recruitment. Your task is to extract structured information from resume text.

        CRITICAL INSTRUCTIONS:
        1. Return ONLY valid JSON - no explanations, no commentary, no additional text.
        2. Use the EXACT structure provided below
        3. If information is missing, use "NA" as the value
        4. All JSON keys must be in double quotes
        5. Be thorough and accurate - don't invent information that isn't there
        6. Pay special attention to technical skills, programming languages, and frameworks
        7. The JSON has to be returned in valid JSON chunks to support streaming responses.

        REQUIRED JSON STRUCTURE CHUNKS(use exactly this format):
        {{
          "Name": "candidate full name",
          "Contact_Details": {{
            "Mobile_No": "phone number",
            "Email": "email address"
          }},
          "Github_Repo": "github profile url",
          "LinkedIn": "linkedin profile url"
        }}{JSON_CHUNK_DELIMITER}
        {{
          "Education": [
            {{
              "Degree": "degree name and field of study",
              "Institution": "university/college name",
              "Score": "GPA/percentage/grade",
              "Duration": "study period or graduation year"
            }}
          ]
        }}{JSON_CHUNK_DELIMITER}
        {{
          "Professional_Experience": [
            {{
              "Company": "company name",
              "Role": "job title/position",
              "Duration": "employment period",
              "Description": "summarise in 2 lines key responsibilities and achievements"
            }}
          ]
        }}{JSON_CHUNK_DELIMITER}
        {{
          "Projects": [
            {{
              "Project_Name": "project title",
              "Project_Description": "brief description including technologies used"
            }}
          ]
        }}{JSON_CHUNK_DELIMITER}
        {{
          "Certifications": [
            {{
              "Certification_Authority": "issuing organization",
              "Certification_Details": "certification name and details"
            }}
          ]
        }}{JSON_CHUNK_DELIMITER}
        {{
          "Programming_Language": ["list all programming languages mentioned"],
          "Frameworks": ["list all frameworks, tools, libraries, and technologies"],
          "Technologies": ["list all technologies mentioned"]
        }}{JSON_CHUNK_DELIMITER}

        EXTRACTION GUIDELINES:
        - Look carefully for contact information (phone, email)
        - Extract ALL educational qualifications
        - Include ALL work experience, internships, and relevant positions
        - Capture ALL projects (personal, academic, professional)
        - List ALL technical skills, programming languages, and frameworks
        - Be comprehensive but don't duplicate information

        RESUME TEXT TO PARSE:
        {raw_resume_text}

        Return ONLY the JSON structure:
    """.strip()
    buffer = ""
    chunk_no = 1
    try:
        async for chunk in llm.astream(prompt):
            buffer += chunk

            while JSON_CHUNK_DELIMITER in buffer:
                # Split the buffer at the first occurrence of the delimiter
                json_candidate, _, remaining_buffer = buffer.partition(JSON_CHUNK_DELIMITER)
                # print("JSON CHUNK BEFORE DELIMITER: \n", json_candidate)
                # print("REMAINING BUFFER: \n", remaining_buffer)
                buffer = remaining_buffer

                try:
                    parsed_json = json_candidate
                    print(f"PARSED JSON CHUNK {chunk_no}: \n", parsed_json)
                    chunk_no = chunk_no + 1
                    yield parsed_json # THIS SHOULD ALWAYS SEND A STRING

                except json.JSONDecodeError as e:
                    print("Failed to parse JSON:", e)
    except Exception as e:
        raise
    print("Stream Finished....")

async def evaluate_resume_against_jd(jd_json: str, resume_data: dict) -> AsyncGenerator[Any, Any]:

    """
        Evaluation Agent LLM.
        Evaluate parsed information from resume from JD
    """

    prompt = f"""
        You are a senior HR professional and technical recruiter with 15+ years of experience. You specialize in evaluating candidates against job requirements and providing detailed, actionable feedback.
    
        EVALUATION TASK:
        Carefully evaluate the candidate's resume against the job description provided. Give a comprehensive assessment that will help in making hiring decisions.
    
        SCORING CRITERIA:
        - Experience Score (0-10): Relevance and depth of work experience to job requirements
        - Skills Score (0-10): Technical skills match with job requirements  
        - Education Score (0-10): Educational background relevance to the role
        - Overall Score: Simple mathematical average of the three scores above
        - Match Percentage: Overall candidate-job fit percentage
    
        SCORING SCALE:
        - 0-2: Very poor match, major gaps (0-20% match)
        - 3-4: Poor match, significant gaps (21-40% match)
        - 5-6: Fair match, some relevant experience (41-60% match)
        - 7-8: Good match, most requirements met (61-80% match)
        - 9-10: Excellent match, exceeds requirements (81-100% match)
    
        RETURN ONLY THIS JSON STRUCTURE:
        {{
          "Experience_Score": <integer 0-10>,
          "Skills_Score": <integer 0-10>,
          "Education_Score": <integer 0-10>,
          "Overall_Score": <integer average of above three>,
          "Match with JD": "<percentage>%",
          "qualification_status": "<if overall_score>=7 or Match with JD >=70% then Qualified else Not Qualified>"
        }}{JSON_CHUNK_DELIMITER}
        {{
          "Pros": [
            "Specific strength 1 with evidence from resume",
            "Specific strength 2 with evidence from resume",
            "Specific strength 3 with evidence from resume"
          ],
          "Cons": [
            "Specific weakness 1 with improvement suggestion",
            "Specific weakness 2 with improvement suggestion", 
            "Specific weakness 3 with improvement suggestion"
          ]
        }}{JSON_CHUNK_DELIMITER}
        {{
          "Skills Match": [
            "List specific skills that match job requirements"
          ],
          "Skills not matching with JD": [
            "List required skills that candidate lacks"
          ],
          "Extra skills": [
            "List additional skills candidate has beyond job requirements"
          ]
        }}{JSON_CHUNK_DELIMITER}
    
        EVALUATION GUIDELINES:
        - Be strict and realistic in scoring - don't inflate scores
        - Be specific and evidence-based in your assessment
        - Pros should highlight concrete achievements and relevant experience
        - Cons should be constructive with improvement suggestions
        - Skills matching should be precise and job-relevant
        - Consider both technical and soft skills
        - Base your assessment on actual resume content vs actual job requirements
        - Look for red flags like job hopping, skill gaps, or overqualification
    
        JOB DESCRIPTION:
        {jd_json}
    
        CANDIDATE RESUME DATA:
        {json.dumps(resume_data, indent=2)}
    
        Return ONLY the JSON evaluation:
    """.strip()
    buffer = ""
    chunk_no = 1
    try:
        async for chunk in llm.astream(prompt):
            buffer += chunk

            while JSON_CHUNK_DELIMITER in buffer:
                # Split the buffer at the first occurrence of the delimiter
                json_eval, _, remaining_buffer = buffer.partition(JSON_CHUNK_DELIMITER)

                buffer = remaining_buffer

                try:
                    parsed_json = json_eval
                    print(f"EVALUATED JSON CHUNK {chunk_no}: \n", parsed_json)
                    # print("JSON CHUNK BEFORE DELIMITER: \n", json_eval)
                    # print("REMAINING BUFFER: \n", remaining_buffer)
                    chunk_no = chunk_no + 1
                    yield parsed_json  # THIS SHOULD ALWAYS SEND A STRING

                except json.JSONDecodeError as e:
                    print("Failed to parse JSON:", e)
    except Exception as e:
        raise
    print("Stream Finished....")

# DO NOT RUN THIS FUNCTION
def run_llm_chain(resume_path: str, jd_path: str):
    print(f"Loading resume: {resume_path}")
    resume_text = load_pdf_text(resume_path)

    print(f"Loading JD: {jd_path}")
    jd_text = json.load(open(jd_path))

    print("Extracting structured data from resume...")
    extracted_data = extract_resume_info(resume_text)
    if not extracted_data:
        print("Extraction failed. Aborting.")
        return

    print("Evaluating resume against JD...")
    evaluation = evaluate_resume_against_jd(jd_text, extracted_data)

    print("\nFinal Validated Evaluation:")
    print(json.dumps(evaluation, indent=2))

    with open("../evaluation_results/test_results.json", "w") as f:
        json.dump(evaluation, f, indent=2)

if __name__ == "__main__":
    resume_pdf = "../data/resume_ashvin_bhutekar 1.pdf"
    jd_pdf = "../jd_json/SrPDE.json"

    run_llm_chain(resume_pdf, jd_pdf)
