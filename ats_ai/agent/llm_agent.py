import json
import os
import re

from dotenv import load_dotenv
from google import genai
from langchain_community.document_loaders import PyMuPDFLoader
from pydantic import BaseModel

"""
    Using LLM chaining workflow to parse, evaluate, and validate resume and given job description
    to create a robust and accurate assessment of a candidate.
    1. extract_resume_info : Parsing Agent
    2. evaluate_resume_against_jd : Evaluation Agent

"""

load_dotenv()
genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.Client()


# Define structured schema for parsed resume info (optional but illustrative)
class ParsedResume(BaseModel):
    Name: str
    Contact_Details: dict
    Github_Repo: str
    LinkedIn: str
    Education: list
    Professional_Experience: list
    Projects: list
    Certifications: list
    Programming_Language: list[str]
    Frameworks: list[str]
    Technologies: list[str]


class ResumeEvaluation(BaseModel):
    Evaluation_Summary: dict
    Strengths_and_Weaknesses: dict
    Skill_Analysis: dict
    Key_Considerations: dict


def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return " ".join(page.page_content for page in pages)


def extract_json_block(text: str) -> dict:
    """
    Extracts the first JSON block from a string (removes ```json ... ``` if present),
    and returns it as a Python dictionary.
    """
    pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(pattern, text, re.DOTALL)

    try:
        if match:
            cleaned_json = match.group(1).strip()
        else:
            cleaned_json = text.strip()

        return json.loads(cleaned_json)

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}\nRaw content: {text}")


async def extract_resume_info(raw_resume_text: str):
    """
    Parsing Agent LLM.
    Parse information from resume into JSON
    """
    prompt = f"""
        You are an expert resume parser in HR and recruitment. Your task is to extract structured information from resume text.
    
        CRITICAL INSTRUCTIONS:
        1. **Return ONLY VALID JSON.** No explanations, no commentary, no additional text outside the JSON structure.
        2. **Use the EXACT JSON structure provided below.** Adhere strictly to all keys, data types, and nesting.
        3. **Handle Missing Information:**
        * For **single string fields** (e.g., "Name", "Mobile_No", "Github_Repo"), if information is missing, use the string value "NA".
        * For **lists/arrays** (e.g., "Education", "Professional_Experience", "Projects", "Certifications", "Programming_Language", "Frameworks", "Technologies"),
         if no relevant entries are found, return an **empty array []**. Do not return an object with "NA" values inside an empty array.
        4. **All JSON keys must be in double quotes.**
        5. **Be thorough and accurate** - don't invent information that isn't there.
        6. **Pay special attention to technical skills, programming languages, and frameworks.**
    
        REQUIRED JSON STRUCTURE (use exactly this format):
        {{
          "Name": "candidate full name",
          "Contact_Details": {{
            "Mobile_No": "phone number",
            "Email": "email address"
          }},
          "Github_Repo": "github profile url, use NA if not provided",
          "LinkedIn": "linkedin profile url, use NA if not provided",
          "Education": [
            {{
              "Degree": "degree name and field of study",
              "Institution": "university/college name",
              "Score": "GPA/percentage/grade",
              "Duration": "study period or graduation year"
            }}
            // Add more education entries as separate objects if present.
          ],
          "Professional_Experience": [
            {{
              "Company": "company name",
              "Role": "job title/position",
              "Duration": "employment period",
              "Description": "summarize in 2-3 sentences key responsibilities and achievements"
            }}
            // Add more professional experience entries as separate objects if present.
          ],
          "Projects": [
            {{
              "Project_Name": "project title",
              "Project_Description": "brief description including technologies used"
            }}
            // Add more project entries as separate objects if present.
          ],
          "Certifications": [
            {{
              "Certification_Authority": "issuing organization",
              "Certification_Details": "certification name and details"
            }}
            // Add more certification entries as separate objects if present.
          ],
          "Programming_Language": ["list all programming languages mentioned"],
          "Frameworks": ["list all frameworks, libraries, and significant tools (e.g., React, Express, Pandas, NumPy, Bootstrap, Spring Boot)"],
          "Technologies": ["list all underlying technologies, platforms, and databases (e.g., AWS, Azure, Docker, Kubernetes, SQL, MongoDB, Git, Jenkins, Tableau, Salesforce, SharePoint)"]
        }}
    
        EXTRACTION GUIDELINES:
        - Look carefully for **contact information** (phone, email, GitHub, LinkedIn).
        - Extract **ALL educational qualifications**.
        - Include **ALL work experience, internships, and relevant positions**.
        - Capture **ALL projects** (personal, academic, professional).
        - List **ALL technical skills**, ensuring proper categorization into Programming_Language, Frameworks, or Technologies.
        - Be comprehensive but **do not duplicate information**.
        - **Order of Lists:** For 'Education', 'Professional_Experience', and 'Projects', list all entries in **reverse chronological order** (most recent first).
        - **Description Conciseness:** Summarize 'Professional_Experience' descriptions concisely, aiming for 2-3 sentences to highlight key responsibilities and quantifiable achievements.
    
        RESUME TEXT TO PARSE:
        {raw_resume_text}
    
        Return ONLY the JSON structure:
    """.strip()

    response = gemini_model.models.generate_content(model="gemini-2.0-flash", contents=prompt)

    return extract_json_block(response.text)


async def evaluate_resume_against_jd(jd_json: dict, resume_data: dict):
    """
    Evaluation Agent LLM.
    Evaluate parsed information from resume from JD
    """
    prompt = f"""
        You are a **highly experienced Senior HR Professional and Technical Recruiter** with 15+ years of experience in technical hiring. 
        Your primary objective is to **accurately and reliably evaluate a candidate's resume against a given Job Description (JD)**.
        Provide a comprehensive, nuanced assessment that directly aids in critical hiring decisions.
    
        **CRITICAL INSTRUCTIONS FOR EVALUATION:**
    
        1. **Return ONLY VALID JSON.** No explanations, no commentary, no additional text outside the JSON structure.
        2. **Use the EXACT JSON structure provided below.** Adhere strictly to all keys, data types, and nesting.
        3. **Strictly Evidence-Based:** Every score, pro, con, and skill match MUST be directly supported by explicit content in the CANDIDATE RESUME DATA and JOB DESCRIPTION. Do not infer or invent.
        4. **Handle Invalid JD Gracefully:**
        * **If the JOB DESCRIPTION is empty, appears to be gibberish, is clearly not a job description (e.g., just a name or random text), or is too short/vague to be meaningful:**
        * Set Experience_Score, Skills_Score, Education_Score, Projects_Score, and Overall_Weighted_Score to 0.0.
        * Set Match_Percentage to "0.0%".
        * Set Qualification_Status to "Not Qualified - Invalid Job Description".
        * Set Pros, Cons, Skills_Matching_JD, Required_Skills_Missing_from_Resume, Extra_Skills_on_Resume_Not_in_JD, Quantifiable_Achievements_Identified, and Red_Flags_Noted to empty lists ([]).
        * Set Overall_Recommendation to "Cannot evaluate due to invalid/meaningless Job Description.".
    
        5. **Quantifiable Impact (KPIs):** Actively search for and prioritize quantifiable achievements (Key Performance Indicators - KPIs, metrics, percentages, numbers indicating impact) in the resume that align with the JD. 
            Integrate these into scores and explicitly list them in "Quantifiable_Achievements_Identified" and "Pros". 
            If the JD mentions KPIs, cross-reference and look for similar achievements in the resume.
        6. Maximum 3 pros and 3 cons are expected. 
        
        ---
    
        **SCORING CRITERIA (Apply ONLY if JD is Valid):**
    
        Scores are on a scale of 0-10. The Overall_Weighted_Score will be a calculated float.
    
        * **Experience Score (Weight: 30%)**
        * **Years of Experience:** Directly compare against JD's requirement. Penalize heavily if minimum is not met.
        * **Relevance:** How closely does past experience (industry, domain, tech stack) align with the JD?
        * **Depth & Breadth:** Level of responsibility, complexity of roles, exposure to full SDLC.
        * **Impact/Achievements:** Look for quantifiable results (KPIs) in past roles (e.g., "reduced latency by X%", "managed projects exceeding Y budget").
        * **Career Progression:** Evidence of growth, promotions, increasing responsibility.
        * **Company Reputation:** (Minor factor) Relevance of past companies to the role/industry.
    
        * **Skills Score (Weight: 40%)**
        * **Core Skills Match (Must-Haves):** Exact match and demonstrated proficiency for essential skills listed in the JD. This is the most critical factor.
        * **Demonstrated Application:** **Crucially, skills listed must be shown to be used effectively in "Professional_Experience" and/or "Projects" sections.** A skill merely listed but not applied in context receives minimal points.
        * **Depth of Proficiency:** Is the candidate an expert, proficient, or merely familiar? (Infer from descriptions).
        * **Secondary/Desirable Skills:** Match for nice-to-have skills.
        * **Penalties:** Significant penalties for missing core required skills or if skills are listed but not demonstrated.
    
        * **Projects Score (Weight: 20%)**
        * **Relevance to JD:** How directly do projects relate to the job's technical requirements and domain?
        * **Technical Complexity:** Difficulty and sophistication of the technologies and problems solved.
        * **Skill Application:** Explicit demonstration of required skills (from JD) within projects.
        * **Impact/Results:** Quantifiable outcomes or real-world application of projects (e.g., "achieved X accuracy," "handled Y users").
        * **Role in Project:** Clearly define candidate's contribution and ownership.
    
        * **Education Score (Weight: 10%)**
        * **Degree Relevance:** Alignment of degree(s) and field of study with the technical nature of the JD (e.g., CS, Engineering, Data Science degrees for tech roles).
        * **Institution Reputation:** (Minor factor) Standing of the university/college.
        * **Academic Performance:** GPA or equivalent score if provided and relevant.
        * **Relevant Coursework/Minors:** Specific studies that bolster relevance.
    
        ---
    
        **CALCULATIONS (Perform ONLY if JD is Valid):**
    
        * Overall_Weighted_Score = (Experience_Score * 0.3) + (Skills_Score * 0.4) + (Projects_Score * 0.2) + (Education_Score * 0.1)
        * All scores (0-10) should be floats for this calculation.
        * Round the final Overall_Weighted_Score to **one decimal place**.
        * Match_Percentage: Derived from Overall_Weighted_Score relative to 10.0, e.g., an Overall_Weighted_Score of 8.0 would be "80.0%". Format as a string with one decimal place and a "%" sign.
        * Qualification_Status:
        * "Qualified" IF Overall_Weighted_Score >= 7.0 AND Match_Percentage (as a numerical value, e.g., 70.0) >= 70.0.
        * "Not Qualified - [Specific Reason]" (e.g., "Skill Gaps", "Insufficient Experience", "Lack of Project Application"). If multiple reasons, pick the most significant.
    
        ---
    
        **RETURN ONLY THIS JSON STRUCTURE (as a single JSON object):**
        {{
            "Evaluation_Summary": {{
                "Experience_Score": <float 0.0-10.0>,
                "Skills_Score": <float 0.0-10.0>,
                "Education_Score": <float 0.0-10.0>,
                "Projects_Score": <float 0.0-10.0>,
                "Overall_Weighted_Score": <float 0.0-10.0, rounded to one decimal place>,
                "Match_Percentage": "<string, e.g., '75.5%'>",
                "Qualification_Status": "<string, e.g., 'Qualified' or 'Not Qualified'>"
            }},
            "Strengths_and_Weaknesses": {{
                "Pros": [
                "Specific strength 1 (e.g., 'Strong Python skills demonstrably used in Project X, leading to Y% efficiency gain')",
                "Specific strength 2 (e.g., '5 years of relevant full-stack experience aligning with JD requirements')",
                "Specific strength 3"
                ],
                "Cons": [
                "Specific weakness 1 (e.g., 'Missing required skill: [Skill Name]')",
                "Specific weakness 2 (e.g., 'Skills like [Skill Name] listed but no evidence of practical application in projects')",
                "Specific weakness 3 (e.g., 'Experience duration of 2 years falls short of the JD's 5+ years requirement')"
            ]
            }},
            "Skill_Analysis": {{
                "Skills Match": [
                    "List specific skills explicitly mentioned in JD and found/used in resume (e.g., 'Node.js: used in API Gateway development, Enphase Energy')",
                    "List quantifiable outcomes tied to skills where possible (e.g., 'BiLSTM: achieved 92% accuracy in Phonocardiogram Project')"
                ],
                "Required_Skills_Missing_from_Resume": [
                    "List REQUIRED skills from JD that are absent or not demonstrated in the resume"
                ],
                "Extra skills": [
                    "List additional skills candidate has beyond job requirements (for context, do not factor into main scores)"
                ]
            }},
            "Key_Considerations": {{
                "Quantifiable_Achievements_Identified": [
                    "List all specific metrics, KPIs, or quantified impacts found in the resume (e.g., 'Reduced system load by 20%', 'Increased user engagement by 15%')",
                    "Include achievements from Professional Experience and Projects."
                ],
                "Red_Flags_Noted": [
                    "List any concerns: e.g., 'Job hopping (multiple short stints)', 'Overqualified for this role', 'Lack of recent relevant experience'",
                    "If no red flags, list []."
                ],
                "Overall_Recommendation": "A concise, objective summary (1-2 sentences) of the evaluation and a clear recommendation (e.g., 'Strong fit, recommend for interview' or 'Not suitable due to skill gaps in X and Y, consider other candidates.')."
            }}
        }}
        CANDIDATE RESUME DATA:
        {resume_data}
        JOB DESCRIPTION:
        {jd_json}
    """.strip()

    print(jd_json)

    response = gemini_model.models.generate_content(model="gemini-2.0-flash", contents=prompt)

    return extract_json_block(response.text)
