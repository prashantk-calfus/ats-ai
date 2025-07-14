
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

def extract_resume_info(raw_resume_text: str) -> dict:

    """
        Parsing Agent LLM.
        Parse information from resume into JSON
    """

    llm = Ollama(model="gemma3:12b")

    prompt = f"""
        You are an expert resume parser in HR and recruitment. Your task is to extract structured information from resume text.
    
        CRITICAL INSTRUCTIONS:
        1. Return ONLY valid JSON - no explanations, no commentary, no additional text
        2. Use the EXACT structure provided below
        3. If information is missing, use "NA" as the value
        4. All JSON keys must be in double quotes
        5. Be thorough and accurate - don't invent information that isn't there
        6. Pay special attention to technical skills, programming languages, and frameworks
    
        REQUIRED JSON STRUCTURE (use exactly this format):
        {{
          "Name": "candidate full name",
          "Contact_Details": {{
            "Mobile_No": "phone number",
            "Email": "email address"
          }},
          "Github_Repo": "github profile url",
          "LinkedIn": "linkedin profile url",
          "Education": [
            {{
              "Degree": "degree name and field of study",
              "Institution": "university/college name",
              "Score": "GPA/percentage/grade",
              "Duration": "study period or graduation year"
            }}
          ],
          "Professional_Experience": [
            {{
              "Company": "company name",
              "Role": "job title/position",
              "Duration": "employment period",
              "Description": "key responsibilities and achievements"
            }}
          ],
          "Projects": [
            {{
              "Project_Name": "project title",
              "Project_Description": "brief description including technologies used"
            }}
          ],
          "Certifications": [
            {{
              "Certification_Authority": "issuing organization",
              "Certification_Details": "certification name and details"
            }}
          ],
          "Programming_Language": ["list all programming languages mentioned"],
          "Frameworks": ["list all frameworks, tools, libraries, and technologies"]
        }}
    
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

    response = llm.invoke(prompt).strip()

    cleaned = extract_json_from_response(response)

    print("Function response: ",cleaned)

    return cleaned

def evaluate_resume_against_jd(jd_text: str, resume_data: dict) -> dict:

    """
        Evaluation Agent LLM.
        Evaluate parsed information from resume from JD
    """

    llm = Ollama(model="gemma3:12b")

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
        - 0-2: Very poor match, major gaps
        - 3-4: Poor match, significant gaps
        - 5-6: Fair match, some relevant experience
        - 7-8: Good match, most requirements met
        - 9-10: Excellent match, exceeds requirements
    
        RETURN ONLY THIS JSON STRUCTURE:
        {{
          "Experience_Score": <integer 0-10>,
          "Skills_Score": <integer 0-10>,
          "Education_Score": <integer 0-10>,
          "Overall_Score": <integer average of above three>,
          "Match with JD": "<percentage>%",
          "Pros": [
            "Specific strength 1 with evidence from resume",
            "Specific strength 2 with evidence from resume",
            "Specific strength 3 with evidence from resume"
          ],
          "Cons": [
            "Specific weakness 1 with improvement suggestion",
            "Specific weakness 2 with improvement suggestion", 
            "Specific weakness 3 with improvement suggestion"
          ],
          "Skills Match": [
            "List specific skills that match job requirements"
          ],
          "Skills not matching with JD": [
            "List required skills that candidate lacks"
          ],
          "Extra skills": [
            "List additional skills candidate has beyond job requirements"
          ]
        }}
    
        EVALUATION GUIDELINES:
        - Be specific and evidence-based in your assessment
        - Pros should highlight concrete achievements and relevant experience
        - Cons should be constructive with improvement suggestions
        - Skills matching should be precise and job-relevant
        - Consider both technical and soft skills
        - Base your assessment on actual resume content
    
        JOB DESCRIPTION:
        {jd_text}
    
        CANDIDATE RESUME DATA:
        {json.dumps(resume_data, indent=2)}
    
        Return ONLY the JSON evaluation:
    """.strip()

    response = llm.invoke(prompt).strip()

    cleaned = extract_json_from_response(response)

    return cleaned

def correct_evaluation_output(jd_text: str, resume_data: dict, evaluation_data: dict) -> dict:

    """
        Validation Agent LLM.
        Validate evaluation from LLM 2
    """

    llm = Ollama(model="gemma3:12b")

    prompt = f"""
        You are a quality assurance specialist for resume evaluation systems. Your job is to review evaluations for accuracy, consistency, and fairness.
    
        VALIDATION TASK:
        Review the evaluation below and ensure it meets quality standards. Make corrections if needed.
    
        VALIDATION CHECKLIST:
        1. Are scores integers between 0-10?
        2. Is overall score the correct average of Experience, Skills, Education scores?
        3. Is match percentage realistic and consistent with overall score?
        4. Are pros specific and evidence-based?
        5. Are cons constructive with actionable suggestions?
        6. Is skills matching accurate based on job requirements?
        7. Are all lists relevant and non-repetitive?
    
        CORRECTION RULES:
        - If evaluation is accurate: return the same JSON unchanged
        - If scores are wrong: recalculate and fix them
        - If pros/cons are vague: make them more specific and actionable
        - If skills matching is incorrect: fix based on actual job requirements
        - Keep all feedback professional and constructive
    
        RETURN THE CORRECTED EVALUATION IN THE SAME JSON FORMAT:
        {{
          "Experience_Score": <integer 0-10>,
          "Skills_Score": <integer 0-10>,
          "Education_Score": <integer 0-10>,
          "Overall_Score": <integer average>,
          "Match with JD": "<percentage>%",
          "Pros": ["specific strength 1", "specific strength 2", "specific strength 3"],
          "Cons": ["weakness 1", "weakness 2", "weakness 3"],
          "Skills Match": ["matching skills list"],
          "Skills not matching with JD": ["missing skills list"],
          "Extra skills": ["additional skills list"]
        }}
    
        JOB DESCRIPTION:
        {jd_text}
    
        CANDIDATE RESUME DATA:
        {json.dumps(resume_data, indent=2)}
    
        EVALUATION TO VALIDATE:
        {json.dumps(evaluation_data, indent=2)}
    
        Return the corrected JSON:
    """.strip()

    response = llm.invoke(prompt).strip() # CHECK FOR JSON ERRORS

    try:
        return json.loads(response)

    except json.JSONDecodeError as e:
        print("Validation LLM returned invalid JSON:", e)
        print("Raw response:\n", response[:500])
        return evaluation_data

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

    print("\nRunning validation and correction...")
    validated_evaluation = correct_evaluation_output(jd_text, extracted_data, evaluation)

    print("\nFinal Validated Evaluation:")
    print(json.dumps(validated_evaluation, indent=2))

    with open("../evaluation_results/test_results.json", "w") as f:
        json.dump(evaluation, f, indent=2)

if __name__ == "__main__":
    resume_pdf = "../data/resume_ashvin_bhutekar 1.pdf"
    jd_pdf = "../jd_json/SrPDE.json"

    run_llm_chain(resume_pdf, jd_pdf)
