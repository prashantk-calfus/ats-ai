"""
Using LLM chaining workflow to parse, evaluate, and validate resume and given job description
to create a robust and accurate assessment of a candidate.
1. extract_resume_info : Parsing Agent
2. evaluate_resume_against_jd : Evaluation Agent
"""

import json
import re
from typing import Any, AsyncGenerator

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.llms import Ollama

llm = Ollama(model="llama3.1:8b")
# base_url="http://host.docker.internal:11434")

JSON_CHUNK_DELIMITER = "---END_OF_JSON_CHUNK---"


def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()

    return " ".join(page.page_content for page in pages)


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
          "Github_Repo": "github profile url, use NA if not provided",
          "LinkedIn": "linkedin profile url, use NA if not provided"
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

    try:
        async for chunk in llm.astream(prompt):
            try:
                print(chunk)
                yield chunk

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
        You are a senior HR professional and technical recruiter. You specialize in evaluating candidates against job requirements and providing detailed, actionable feedback.

        EVALUATION TASK:
        Carefully evaluate the candidate's resume against the job description provided. Give a comprehensive assessment that will help in making hiring decisions.
        Also evaluate if the job description is meaningful to the task, Mark all scores (experience, skills, education), pros, cons, skills fields to NA otherwise.

        SCORING CRITERIA:
        - Experience Score (0-10): Relevance and depth of work experience to job requirements consider only professional experience
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
          "Match with JD": "<similarity with JD in percentage (0% - 90%)>",
          "qualification_status": "<if overall_score>=7 AND Match with JD >=70% then Qualified else Not Qualified>"
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
        - If JD is empty or something that doesnt not match a Job Description, mark experience score, skill score, education score as 0.
        - Key considerations mentioned in the JD are critical, if any of them fail then mark candidate as Not Qualified.
        - Be strict and realistic in scoring - don't inflate scores.
        - Penalise scores if resume skills, experience, education do not match JD.
        - Try to analyse if they have used the mentioned skills in their projects, especially somewhere, otherwise penalise the score.
        - Reject candidate if minimum experience requirement is not met.
        - Be specific and evidence-based in your assessment.
        - Pros should highlight concrete achievements and relevant experience.
        - Cons should be constructive with improvement suggestions.
        - Skills matching should be precise and job-relevant.
        - Base your assessment on actual resume content vs actual job requirement.
        - Look for red flags like job hopping, skill gaps, or overqualification.

        CANDIDATE RESUME DATA:
        {json.dumps(resume_data, indent=2)}

        JOB DESCRIPTION:
        {jd_json}

        Return ONLY the JSON evaluation:
    """.strip()

    print(jd_json)

    try:
        async for chunk in llm.astream(prompt):
            try:
                print(chunk)
                yield chunk

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
