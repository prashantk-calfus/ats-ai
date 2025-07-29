JD_EXTRACTION_PROMPT = """
You are an expert HR analyst AI with the ability to distinguish between valid job descriptions and random text.

TASK 1: First, determine if the provided text is a legitimate job description.
TASK 2: If it's a valid JD, extract structured information. If not, return empty structure.

VALIDATION CRITERIA for a legitimate job description:
- Contains job-related terminology and context
- Has information about role responsibilities, requirements, or qualifications  
- Mentions skills, experience, education, or job-related details
- Is substantive enough to be a real job posting (not just greetings, names, or random words)
- Written in a professional/business context

CRITICAL RULES:
1. Respond ONLY in valid JSON. Do NOT include commentary, explanations, or anything outside the JSON object.
2. If the text is NOT a legitimate job description (e.g., casual messages, random text, greetings, single words), return the empty structure with all arrays as [] and strings as "".
3. If it IS a legitimate job description, extract the information as specified.
4. Use the exact structure and keys as specified below.

RETURN FORMAT (strictly follow this):
{{
  "is_valid_jd": true/false,
  "Job_Title": "Job title as mentioned or empty string if invalid",
  "Required_Skills": ["list of must-have skills, tools, or technologies or empty array if invalid"],
  "Preferred_Skills": ["list of nice-to-have skills or tools or empty array if invalid"],
  "Minimum_Experience": "minimum experience required (e.g., '3+ years') or empty string if invalid",
  "Location": "location mentioned (or 'Remote', 'Hybrid') or empty string if invalid",
  "Responsibilities": ["key responsibilities extracted as list items or empty array if invalid"],
  "Qualifications": ["required degrees, certifications, or qualifications or empty array if invalid"],
  "Domain": "industry/domain (e.g., 'Technology', 'Healthcare') or empty string if invalid"
}}


JD TEXT:
\"\"\"
{jd_text}
\"\"\"

Return only the structured JSON output.
""".strip()

RESUME_PARSE_PROMPT = """
        You are an expert resume parser in HR and recruitment. Your task is to extract structured information from resume text.

        CRITICAL INSTRUCTIONS:
        1. **Return ONLY VALID JSON.** No explanations, no commentary, no additional text outside the JSON structure.
        2. **Use the EXACT JSON structure provided below.** Adhere strictly to all keys, data types, and nesting.
        3. **Handle Missing Information:**
        * For **single string fields** (e.g., "Name", "Mobile_No", "Github_Repo"), if information is missing, use the string value "NA".
        * For **lists/arrays** (e.g., "Education", "Professional_Experience", "Projects", "Certifications", "Programming_Language", "Frameworks", "Technologies"), if no relevant entries are found, return an **empty array []**. 
          Do not return an object with "NA" values inside an empty array.
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

EVALUATION_PROMPT = """
    You are a **highly experienced Senior HR Professional and Technical Recruiter** with 15+ years of experience in technical hiring. 
    Your primary objective is to **accurately and reliably evaluate a candidate's resume against a given Job Description (JD)**. Provide a comprehensive, nuanced assessment that directly aids in critical hiring decisions.

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


EVALUATION_AND_PARSING_PROMPT = """
    You are a multi-stage evaluation AI. Your job is to:

    1. **Evaluate the candidate’s resume** against a provided job description.
    2. **Return a detailed and structured JSON** where the evaluation comes first, followed by the parsed resume data.

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
    * Match_Percentage: How much of the JD is covered by the resume. Format as a string with one decimal place and a "%" sign.
    * Qualification_Status:
    * "Qualified" IF Overall_Weighted_Score >= 7.0 AND Match_Percentage (as a numerical value, e.g., 70.0) >= 70.0.
    * "Not Qualified - [Specific Reason]" (e.g., "Skill Gaps", "Insufficient Experience", "Lack of Project Application"). If multiple reasons, pick the most significant.


    CRITICAL INSTRUCTIONS:
    1. **Return ONLY VALID JSON.** No explanations, no commentary, no additional text outside the JSON structure.
    2. **Use the EXACT JSON structure provided below.** Adhere strictly to all keys, data types, and nesting.
    3. **Handle Missing Information:**
    * For **single string fields** (e.g., "Name", "Mobile_No", "Github_Repo"), if information is missing, use the string value "NA".
    * For **lists/arrays** (e.g., "Education", "Professional_Experience", "Projects", "Certifications", "Programming_Language", "Frameworks", "Technologies"), if no relevant entries are found, return an **empty array []**.
      Do not return an object with "NA" values inside an empty array.
    4. **All JSON keys must be in double quotes.**
    5. **Be thorough and accurate** - don't invent information that isn't there.
    6. **Pay special attention to technical skills, programming languages, and frameworks.**
    7. **The resume and JD may express skills, tools, and frameworks differently.** Do not expect exact word matches.**
    8. **Use reasoning and industry knowledge to infer relationships between tools and core skills.** Examples:
       * If the JD asks for **"Python"**, and the resume includes **"FastAPI"** or **"LangChain"**, infer the candidate likely knows Python.
       * If the JD requires **"DevOps"**, and the resume lists tools like **"Terraform"**, **"GitHub Actions"**, or **"CI/CD pipelines"**, consider it aligned.
       * If the JD mentions **"Cloud Platforms"**, and the resume includes **"AWS"**, **"GCP"**, or **"Azure"**, treat it as a match.**
    9. **Avoid marking a skill as "missing" if it is clearly demonstrated or implied through tools, frameworks, or project context.**
    10.**You must reason about technical synonymy.** Related tools or domains should contribute toward skills match, even if not worded identically.
    11.**Award partial or full credit for implied or demonstrated knowledge** based on:
       * Tools used in projects
       * Responsibilities or achievements
       * Specific technologies mentioned in context**
    12.**Recognize synonyms and related technologies** (e.g., "Flask" relates to Python; "Kubernetes" relates to DevOps/cloud).
   13.**Only report a skill as missing if it's listed in the JD's Required_Skills but has no clear evidence in the resume. Do not evaluate skills not mentioned in the JD.**
    14.**CRITICAL: Base your evaluation ONLY on the skills listed in the job description. Ignore any resume skills that are not mentioned in the JD's requirements.**

    "Evaluation" must contain the following fields:

    {{
      "Evaluation": {{
        "Experience_Score": <float 0.0-10.0>,
        "Skills_Score": <float 0.0-10.0>,
        "Education_Score": <float 0.0-10.0>,
        "Projects_Score": <float 0.0-10.0>,
        "Overall_Weighted_Score": <float 0.0-10.0, rounded to one decimal place>,
        "Match_Percentage": "<string, e.g., '75.5%'>",
        "Pros": [
          "bullet point 1",
          "bullet point 2"
        ],
        "Cons": [
          "bullet point 1",
          "bullet point 2"
        ],
        "Skills Match": [
            "ONLY list skills that are present in the JD's Required_Skills or Preferred_Skills arrays AND found in the resume",
            "For each matched skill, explain how it's demonstrated in the resume",
            "Do NOT include skills that are not mentioned in the job description"
        ],
        "Required_Skills_Missing_from_Resume": [
          "List only JD-required skills that are not explicitly or implicitly shown in the resume. Do NOT list skills as missing if they are implied through related tools, frameworks, or project experience."
        ],

        "Extra skills": [
            "List additional skills candidate has beyond job requirements (for context, do not factor into main scores)"
        ],
        "Qualification Status": "Qualified / Not Qualified",
        "Missing_Requirements": [
          "list of key requirements from JD that are not met"
        ],
        "Comments": "general suggestions or red flags",
        "Summary": "short summary of fitment (2-3 lines)"
      }},
      "Parsed_Resume": {{
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
        ],
        "Professional_Experience": [
          {{
            "Company": "company name",
            "Role": "job title/position",
            "Duration": "employment period",
            "Description": "brief role description or achievements"
          }}
        ],
        "Programming_Language": ["list all programming languages mentioned"],
        "Frameworks": ["list all frameworks, libraries, and significant tools (e.g., React, Express, Pandas, NumPy, Bootstrap, Spring Boot)"],
        "Technologies": ["list all underlying technologies, platforms, and databases (e.g., AWS, Azure, Docker, Kubernetes, SQL, MongoDB, Git, Jenkins, Tableau, Salesforce, SharePoint)"],
        "Certifications": ["certification 1", "certification 2"],
        "Projects": [
          {{
            "Title": "project name",
            "Description": "summary of the project",
            "Technologies": ["Python", "React", ...]
          }}
        ]
      }}
    }}

    CANDIDATE RESUME DATA: {resume_data}

    Job Description: {job_description}

""".strip()

JD_VALIDATION_AND_EXTRACTION_PROMPT = """
You are an AI assistant that analyzes text to determine if it's a valid job description and extracts structured information.

First, analyze if the following text is a legitimate job description or just random text/greeting/name.

Text to analyze:
{{JD_TEXT}}

If this is NOT a valid job description (like "see u", "hello", random text, just a name, etc.), respond with:
{
    "is_valid_jd": false,
    "Job_Title": "",
    "Required_Skills": [],
    "Preferred_Skills": [],
    "Minimum_Experience": "",
    "Location": "",
    "Responsibilities": [],
    "Qualifications": [],
    "Domain": ""
}

If this IS a valid job description, extract and structure the information as JSON:
{
    "is_valid_jd": true,
    "Job_Title": "extracted job title",
    "Required_Skills": ["skill1", "skill2"],
    "Preferred_Skills": ["skill1", "skill2"],
    "Minimum_Experience": "X years",
    "Location": "location",
    "Responsibilities": ["responsibility1", "responsibility2"],
    "Qualifications": ["qualification1", "qualification2"],
    "Domain": "domain/industry"
}

Respond ONLY with valid JSON, no additional text.
"""
