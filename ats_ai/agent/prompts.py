JD_EXTRACTION_PROMPT = """
You are an expert HR analyst AI.

Your task is to extract structured information from the provided job description (JD) text. Focus only on what is explicitly or strongly implied in the JD. Do not make assumptions or fabricate information.

CRITICAL RULES:
1. Respond ONLY in valid JSON. Do NOT include commentary, explanations, or anything outside the JSON object.
2. If a field is missing in the JD, return "NA" or an empty list as appropriate.
3. Use the exact structure and keys as specified below.
4. Be comprehensive, but avoid duplication or invented content.
5. Extract information from ANY text provided - do not validate if it's a proper JD or not.

RETURN FORMAT (strictly follow this):
{{
  "Job_Title": "Job title as mentioned or inferred from the text",
  "Required_Skills": ["list of must-have skills, tools, or technologies mentioned"],
  "Preferred_Skills": ["list of nice-to-have skills or tools mentioned"],
  "Minimum_Experience": "minimum experience required (e.g., '3+ years') or 'NA'",
  "Location": "location mentioned (or 'Remote', 'Hybrid', or 'NA')",
  "Responsibilities": ["key responsibilities extracted as list items"],
  "Qualifications": ["required degrees, certifications, or qualifications"],
  "Domain": "industry or domain mentioned or inferred",
  "Key_considerations_for_hiring": ["list down very important factors detrimental for hiring"]
}}
 JD TEXT:
\"\"\"
{jd_text}
\"\"\"
Return only the structured JSON output.
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
    * **Academic Performance:** GPA or equivalent score if provided and relevant.


    ---

    **CALCULATIONS (Perform ONLY if JD is Valid):**

    * Overall_Weighted_Score = (Experience_Score * 0.3) + (Skills_Score * 0.4) + (Projects_Score * 0.2) + (Education_Score * 0.1)
    * All scores (0-10) should be floats for this calculation.
    **MATCH PERCENTAGE CALCULATION:**
    * **Match_Percentage represents how much of the JD requirements are covered by the resume, NOT the performance score.**
    * Calculate based on:
      * Required Skills Coverage: Count how many required skills from JD are present/demonstrated in resume
      * Experience Match: Does candidate meet minimum experience requirement? (Yes=100%, Partial=50%, No=0%)
      * Qualification Match: Does candidate meet education/certification requirements?
      * Responsibility Alignment: How well does candidate's experience align with key responsibilities?
    * Formula: Match_Percentage = (Matched_Requirements / Total_JD_Requirements) * 100

    * Consider Required_Skills, Minimum_Experience, Qualifications, and key Responsibilities from JD
    * Format as string with one decimal place and "%" sign (e.g., "67.5%")
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
            "Match_Percentage": "<string representing JD requirements coverage, e.g., '67.5%'>",
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

        7. **Atomic Skill Extraction**: Always split multi-skill mentions connected by commas, slashes (/), ampersands (&), or conjunctions (e.g., "and") into separate standalone skills.
          Example: "Terraform, GitHub and Git" → ["Terraform", "GitHub", "Git"]
        - **Normalization**: Ensure each extracted skill is returned in its simplest atomic form without grouping words.
        - **De-Duplication**: If a skill appears multiple times across resume, list it only once.


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
          {
            "Title": "project name or NA if no projects",
            "Description": "summary of the project or NA if no projects",
            "Technologies": ["list ALL underlying technologies, platforms, databases, and infrastructure tools found ANYWHERE in resume
             including dedicated skills sections (e.g., AWS, Azure, Docker, Kubernetes, SQL, MongoDB, Git, Jenkins, Terraform, Ansible)"]

        ],
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
        - For LinkedIn: Search for patterns like "linkedin.com/in/", "LinkedIn:", "🔗 LinkedIn", or any text containing linkedin
        - For GitHub: Search for patterns like "github.com/", "GitHub:", "🔗 GitHub", or any text containing github
        - Extract **ALL educational qualifications**.
        - Include **ALL work experience, internships, and relevant positions**.
        - Capture **ALL projects** (personal, academic, professional).
        - List **ALL technical skills**, ensuring proper categorization into Programming_Language, Frameworks, or Technologies.
        - Be comprehensive but **do not duplicate information**.
        - **Order of Lists:** For 'Education', 'Professional_Experience', and 'Projects', list all entries in **reverse chronological order** (most recent first).
        - **Description Conciseness:** Summarize 'Professional_Experience' descriptions concisely, aiming for 2-3 sentences to highlight key responsibilities and quantifiable achievements.

     **ENHANCED SKILL PARSING RULES:**
    - **Dedicated Skills Section Priority**: Always scan for standalone "Skills", "Technical Skills", or "Technologies" sections and extract ALL items listed there
    - **Comma-Separated List Processing**: When encountering lists like "Terraform, GitHub and Git", parse each item individually - do NOT lose items during comma splitting
    - **Multi-Format Skill Detection**: Extract skills from bullet points (- item), numbered lists, comma-separated strings, and paragraph mentions
    - **Comprehensive Section Scanning**: Search the entire resume text for technology mentions, not just experience descriptions - skills can appear in summary, skills sections, or project descriptions
    - **Validation Check**: Before finalizing JSON, verify that prominent technologies visible in raw text (like "Terraform") appear in the appropriate extracted arrays

        RESUME TEXT TO PARSE:
        {raw_resume_text}

        Return ONLY the JSON structure:
""".strip()


def calculate_weighted_score_and_status(
    experience_score, skills_score, education_score, projects_score, candidate_total_experience_years, jd_required_experience_years, has_valid_projects=True, experience_weight=0.3, skills_weight=0.4, education_weight=0.1, projects_weight=0.2
):
    """
    Enhanced calculation with explicit experience years comparison
    """

    # CRITICAL: Check experience requirement FIRST
    if jd_required_experience_years > 0 and candidate_total_experience_years < jd_required_experience_years:
        # If candidate doesn't meet minimum experience, they are disqualified
        qualification_status = f"Not Qualified - Experience Gap (Required: {jd_required_experience_years}+ years, Has: {candidate_total_experience_years} years)"

        # Still calculate the weighted score for completeness
        if not has_valid_projects or projects_score == 0.0:
            total_other_weights = experience_weight + skills_weight + education_weight
            if total_other_weights > 0:
                exp_adjusted = experience_weight + (projects_weight * (experience_weight / total_other_weights))
                skills_adjusted = skills_weight + (projects_weight * (skills_weight / total_other_weights))
                edu_adjusted = education_weight + (projects_weight * (education_weight / total_other_weights))
            else:
                exp_adjusted = experience_weight
                skills_adjusted = skills_weight
                edu_adjusted = education_weight

            overall_weighted_score = (experience_score * exp_adjusted) + (skills_score * skills_adjusted) + (education_score * edu_adjusted)
        else:
            overall_weighted_score = (experience_score * experience_weight) + (skills_score * skills_weight) + (projects_score * projects_weight) + (education_score * education_weight)

        overall_weighted_score = round(overall_weighted_score, 1)
        match_percentage = f"{overall_weighted_score * 10.0:.1f}%"

        return {
            "overall_weighted_score": overall_weighted_score,
            "match_percentage": match_percentage,
            "qualification_status": qualification_status,
            "experience_gap": True,
            "required_experience": jd_required_experience_years,
            "candidate_experience": candidate_total_experience_years,
        }

    # Dynamic weight calculation based on project validity and custom weights
    if not has_valid_projects or projects_score == 0.0:
        total_other_weights = experience_weight + skills_weight + education_weight

        if total_other_weights > 0:
            exp_adjusted = experience_weight + (projects_weight * (experience_weight / total_other_weights))
            skills_adjusted = skills_weight + (projects_weight * (skills_weight / total_other_weights))
            edu_adjusted = education_weight + (projects_weight * (education_weight / total_other_weights))
        else:
            exp_adjusted = experience_weight
            skills_adjusted = skills_weight
            edu_adjusted = education_weight

        overall_weighted_score = (experience_score * exp_adjusted) + (skills_score * skills_adjusted) + (education_score * edu_adjusted)
    else:
        overall_weighted_score = (experience_score * experience_weight) + (skills_score * skills_weight) + (projects_score * projects_weight) + (education_score * education_weight)

    overall_weighted_score = round(overall_weighted_score, 1)
    match_percentage = f"{overall_weighted_score * 10.0:.1f}%"
    match_percentage_numeric = overall_weighted_score * 10.0

    # Determine qualification status based on overall score
    if overall_weighted_score >= 7.0 and match_percentage_numeric >= 70.0:
        qualification_status = "Qualified"
    else:
        # Find the section with highest weight that's underperforming
        weights_and_scores = [
            (experience_weight, experience_score, "Insufficient Experience"),
            (skills_weight, skills_score, "Skill Gaps"),
            (education_weight, education_score, "Education Requirements"),
        ]

        if has_valid_projects and projects_weight > 0:
            weights_and_scores.append((projects_weight, projects_score, "Lack of Project Application"))

        weights_and_scores.sort(key=lambda x: x[0], reverse=True)

        for weight, score, reason in weights_and_scores:
            if weight > 0 and score < 6.0:
                qualification_status = f"Not Qualified - {reason}"
                break
        else:
            qualification_status = "Not Qualified - Below Standard"

    return {
        "overall_weighted_score": overall_weighted_score,
        "match_percentage": match_percentage,
        "qualification_status": qualification_status,
        "experience_gap": False,
        "required_experience": jd_required_experience_years,
        "candidate_experience": candidate_total_experience_years,
    }


def get_dynamic_evaluation_prompt(resume_data, job_description, weightage_config):
    """Generate enhanced evaluation prompt with robust skill extraction and grouping fix"""
    import json

    exp_pct = weightage_config.experience_weight * 100
    skills_pct = weightage_config.skills_weight * 100
    edu_pct = weightage_config.education_weight * 100
    projects_pct = weightage_config.projects_weight * 100

    return f"""
You are an expert resume evaluator. Analyze the resume against the job description with detailed explanations.

    WEIGHTS: Experience {exp_pct}%, Skills {skills_pct}%, Education {edu_pct}%, Projects {projects_pct}%

    **STEP-BACK ANALYSIS (Internal – Do Not Output):**
    1. Parse the ENTIRE resume (Skills section, Professional Experience, Education, Certifications, and Projects).
    2. Extract ALL technical skills, tools, frameworks, and technologies mentioned ANYWHERE in the resume.
       - Include explicitly listed skills (Skills section) even if not tied to work experience.
       - Include skills/technologies mentioned inside project descriptions.
       - Include tools/skills from job responsibilities and achievements in Professional Experience.
    3. Do NOT filter out skills based on years of experience or duration — if the candidate has mentioned a skill anywhere, treat it as part of their skill set.
    4. Normalize the skill list (remove duplicates, unify synonyms like "JS" → "JavaScript").
    5. Lock this consolidated resume skill set for the evaluation phase.
    6. Use this locked skill set to perform all skill matching against the JD requirements.

    CRITICAL INSTRUCTIONS:
    1. **DO NOT CALCULATE EXPERIENCE YEARS**: Leave Total_Experience_Years and JD_Required_Experience_Years as 0.0 - the system will calculate separately.
    2. Focus on the QUALITY and RELEVANCE of experience, skills, education, and projects.
    3. For matched skills, explain HOW they're demonstrated in the resume (either in skills section, projects, or work experience).
    4. Do NOT use placeholder/example values – extract only from resume and JD.
    5. Education must be directly relevant to the job field (e.g., CS/IT/Data for tech roles). Score based on field relevance + degree level, not just presence.
    6. **Intelligent Skill Matching**: Match JD categories to resume by extracting category–tool mappings (e.g., “CI/CD tools like Jenkins, GitLab”),
       and mark the category satisfied if any listed tool is found. Handle variations like “such as”, “including”, or parentheses.
    7. When extracting skills, normalize all text (ignore case differences).
    8. Always split skill groups correctly:
        - Treat commas (`,`), slashes (`/`), semicolons (`;`), and conjunctions like "and", "or", "&" as separators.
        - Example: "Terraform, GitHub and Git" → ["Terraform", "GitHub", "Git"].
        - Example: "SQL Server / PostgreSQL" → ["SQL Server", "PostgreSQL"].
    9. Capture every skill explicitly mentioned in the resume (in Skills section, Projects, Experience, Certifications, or anywhere else),
        even if grouped with others.
    10. Do not drop skills that are not in the JD — list them under "Extra skills".
    11. Ensure no skill gets lost due to grouping (e.g., "Terraform, GitHub and Git" must capture Terraform separately).
    12. If a grouped skill includes both JD-required and non-required skills, correctly separate them and place each in the right category.
    
    **SEMANTIC CATEGORY SKILL MAPPING:**
     **Intelligent Category Recognition**: When matching skills, use domain knowledge to map resume skills to JD categories:
       - If resume mentions infrastructure/deployment tools and JD has DevOps/Infrastructure categories, automatically cross-reference
       - If resume mentions programming languages and JD has Development/Programming categories, automatically cross-reference  
       - If resume mentions databases and JD has Database/Storage categories, automatically cross-reference
     **Skill-to-Category Intelligence**: 
       - Analyze the semantic meaning of resume skills to determine which JD categories they would logically fulfill
       - A resume skill matches a JD category if that skill type typically belongs to that domain area
       - Use technical domain knowledge to bridge the gap between specific tools mentioned in resume and broader categories in JD
     **Reverse Category Matching**: 
       - When JD specifies broad categories (DevOps, Frontend, Backend, etc.) but resume lists specific tools
       - Automatically determine if the specific resume tools fall under those broad JD categories
       - Count as matches when there's logical domain alignment

    **PARSED_RESUME EXTRACTION REQUIREMENTS:**
    - **Comprehensive Skills Section Parsing**: Scan the entire "Skills" or "Technical Skills" section and extract EVERY mentioned technology
    - **Handle Mixed Skill Lists**: Parse entries like "Terraform, GitHub and Git" as separate items: ["Terraform", "GitHub", "Git"]
    - **Multi-line Skills Processing**: Extract from bullet points, comma-separated lists, and paragraph mentions in Skills section
    - **Complete Technology Capture**: Include ALL tools mentioned in Skills section (Terraform, Jenkins, Jira, Confluence, etc.) in appropriate Parsed_Resume arrays
    - **Cross-Section Validation**: Ensure Technologies array in Parsed_Resume includes ALL infrastructure/DevOps tools from Skills section, not just from experience descriptions
    - **Knowledge Areas**: Include conceptual skills (NLP, Computer Vision, etc.) in Technologies array as they represent technical knowledge

    RETURN ONLY THIS EXACT JSON STRUCTURE:
    {{
      "Evaluation": {{
        "Total_Experience_Years": 0.0,
        "JD_Required_Experience_Years": 0.0,
        "Experience_Score": <float>,   # 0–10 (quality/relevance only)
        "Skills_Score": <float>,       # 0–10
        "Education_Score": <float>,    # 0–10
        "Projects_Score": <float>,     # 0–10
        "Overall_Weighted_Score": <float>,
        "Match_Percentage": "<float>%",
        "Qualification Status": "<string>",
        "Pros": [ "<string>", ... ],
        "Cons": [ "<string>", ... ],
        "Skills Match": [
          "List skills where resume tools/technologies semantically match JD categories",
          "Format: 'Resume_Skill → JD_Category (Domain Logic: explanation)'", 
          "Include both exact matches and semantic category matches"
        ],
        "Required_Skills_Missing_from_Resume": [
          "List JD-required skills that are NOT in the consolidated resume skill set"
        ],
        "Extra skills": [
          "List additional skills candidate has beyond JD requirements"
        ],
        "Summary": "<string>"
      }},
      "Parsed_Resume": {{
        "Name": "<Candidate Name>",
        "Contact_Details": {{
          "Mobile_No": "<string>",
          "Email": "<string>"
        }},
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
            "Company": "<Company Name>",
            "Role": "<Job Title>",
            "Duration": "<Start - End (X years)>",
            "Description": "<Work details>"
          }}
        ],
        "Programming_Language": ["list all programming languages from skills, projects, and experience"],
        "Frameworks": ["list all frameworks/libraries/tools"],
        "Technologies": ["list all platforms, databases, cloud, infra, devops tools"],
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

    **CRITICAL:**
    - Do NOT calculate experience years – always set both fields to 0.0
    - Capture ALL skills mentioned in the resume (Skills section, Projects, Experience, Certifications) regardless of duration
    - Focus on evaluating quality and relevance, not quantity or years
    - Education relevance is mandatory for scoring
    - Skills must come from the consolidated skill set, not just projects
    - Handle grouped skills carefully: split them correctly and ensure none are lost.

    RESUME: {resume_data}
    JOB DESCRIPTION: {json.dumps(job_description)}
    """
