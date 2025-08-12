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
    * **Institution Reputation:** (Minor factor) Standing of the university/college.
    * **Academic Performance:** GPA or equivalent score if provided and relevant.
    * **Relevant Coursework/Minors:** Specific studies that bolster relevance.

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
            "Technologies": ["Python", "React", ...] // empty array if no projects
          }
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


def calculate_weighted_score_and_status(
    experience_score,
    skills_score,
    education_score,
    projects_score,
    has_valid_projects=True,
    experience_weight=0.3,
    skills_weight=0.4,
    education_weight=0.1,
    projects_weight=0.2,
):
    """
    Calculate weighted score with proper handling of zero weights and project redistribution
    """

    # Dynamic weight calculation based on project validity and custom weights
    if not has_valid_projects or projects_score == 0.0:
        # When projects are invalid, redistribute project weight only if other weights exist
        total_other_weights = experience_weight + skills_weight + education_weight

        if total_other_weights > 0:  # Only redistribute if there are other non-zero weights
            # Redistribute the project weight proportionally
            exp_adjusted = experience_weight + (projects_weight * (experience_weight / total_other_weights))
            skills_adjusted = skills_weight + (projects_weight * (skills_weight / total_other_weights))
            edu_adjusted = education_weight + (projects_weight * (education_weight / total_other_weights))
        else:
            # If all other weights are also zero, something is wrong - use original weights
            exp_adjusted = experience_weight
            skills_adjusted = skills_weight
            edu_adjusted = education_weight

        overall_weighted_score = (experience_score * exp_adjusted) + (skills_score * skills_adjusted) + (education_score * edu_adjusted)
    else:
        # Standard weights when projects are valid
        overall_weighted_score = (experience_score * experience_weight) + (skills_score * skills_weight) + (projects_score * projects_weight) + (education_score * education_weight)

    # Round to one decimal place
    overall_weighted_score = round(overall_weighted_score, 1)

    # Calculate match percentage
    match_percentage = f"{overall_weighted_score * 10.0:.1f}%"

    # Determine qualification status
    match_percentage_numeric = overall_weighted_score * 10.0

    if experience_score < 7.0:
        qualification_status = "Not Qualified - Experience Gap"
    elif overall_weighted_score >= 7.0 and match_percentage_numeric >= 70.0:
        qualification_status = "Qualified"
    else:
        # Determine primary reason for not qualifying based on highest weighted section
        weights_and_scores = [
            (experience_weight, experience_score, "Insufficient Experience"),
            (skills_weight, skills_score, "Skill Gaps"),
            (education_weight, education_score, "Education Requirements"),
        ]

        # Add projects only if they're valid and have weight
        if has_valid_projects and projects_weight > 0:
            weights_and_scores.append((projects_weight, projects_score, "Lack of Project Application"))

        # Find the section with highest weight that's underperforming
        weights_and_scores.sort(key=lambda x: x[0], reverse=True)  # Sort by weight descending

        for weight, score, reason in weights_and_scores:
            if weight > 0 and score < 6.0:  # Only consider sections with non-zero weight
                qualification_status = f"Not Qualified - {reason}"
                break
        else:
            qualification_status = "Not Qualified - Below Standard"

    return {"overall_weighted_score": overall_weighted_score, "match_percentage": match_percentage, "qualification_status": qualification_status}


def get_dynamic_evaluation_prompt(resume_data, job_description, weightage_config, k_runs=3, temperature=0.0, top_p=0.9):
    """Generate evaluation prompt with step-back analysis and enhanced weakness detection"""

    # Calculate display percentages
    exp_pct = weightage_config.experience_weight * 100
    skills_pct = weightage_config.skills_weight * 100
    edu_pct = weightage_config.education_weight * 100
    projects_pct = weightage_config.projects_weight * 100

    weightage_instruction = f"""
    IMPORTANT WEIGHTAGE CONFIGURATION:
    - Experience Weight: {exp_pct:.1f}%
    - Skills Weight: {skills_pct:.1f}%
    - Education Weight: {edu_pct:.1f}%
    - Projects Weight: {projects_pct:.1f}%

    Use these weights when determining the overall assessment. Give more importance to sections with higher weights.
    If projects are invalid, the {projects_pct:.1f}% project weight will be redistributed proportionally among
    Experience ({exp_pct:.1f}%), Skills ({skills_pct:.1f}%), and Education ({edu_pct:.1f}%).
    """

    # Create the enhanced evaluation prompt with step-back analysis
    evaluation_prompt = f"""
        ENHANCED STEP-BACK + SELF-CONSISTENCY EVALUATION (K={k_runs}, temp={temperature}, top_p={top_p})
        {weightage_instruction}
        **INSTRUCTION:**
        You will perform a TWO-PHASE evaluation process:

        **PHASE 1: STEP-BACK ANALYSIS (Internal - Do Not Output)**
        Before evaluating the candidate, perform the following step-back analysis to deeply understand the job requirements:

        1. **Role Context**: Industry (e.g., Tech), seniority (e.g., Lead), and primary function (e.g., DevOps).
        2. **Core Requirements**: List MUST-HAVE vs. NICE-TO-HAVE skills, minimum experience, and key responsibilities.
        3. **Ideal Candidate Profile**: Define critical skills, experience patterns, and deal-breakers (e.g., missing cloud expertise for a Lead DevOps role).
        Use this to guide consistent scoring and skill matching.

        **PHASE 2: ENHANCED SELF-CONSISTENCY EVALUATION**
        After completing the step-back analysis, perform {k_runs} independent evaluations with sampling parameters (temperature={temperature}, top_p={top_p})
         to ensure diversity in reasoning paths. Each evaluation should use slightly different reasoning approaches while maintaining consistency in final judgments.

        1. **Parse JD Experience**: Extract min_required_years from 'Minimum_Experience' (e.g., lower number in ranges like '3-4 years' → 3).
        2. **Calculate Candidate Years**: From Parsed_Resume's Professional_Experience:
           - Sum durations for JD-relevant roles (e.g., involving ETL, SQL).
           - Handle formats: '2022-Present' = (2025 - 2022) + 1 = 4 years (use current year 2025).
           - If ambiguous, estimate conservatively (e.g., '1+ years' = 1 year).
           - Lock candidate_relevant_years after first run for consistency.
        3. **Gap Calculation**: experience_gap = max(0, min_required_years - candidate_relevant_years).
         If candidate's `experience_gap` is greater than 0:
        * Automatically set `"Qualification Status"` to `"Rejected"`.
        * This must be the first item in `"Detailed_Weaknesses"`.
        * Add a clear note in `"Experience_Gaps"` describing the shortfall (e.g., "Has 2 years relevant experience, requires 4").
        * Even if other scores are high, the candidate should not be marked as "Qualified".
        
           **CRITICAL: INTELLIGENT SKILL PARSING & MATCHING**
            Before creating Skills_Match and Required_Skills_Missing lists:

        1. **PARSE JD SKILL PATTERNS DYNAMICALLY:**
           - Analyze the actual language used in each JD skill requirement
           - Identify pattern: "Category (description) tools like Tool1, Tool2"
           - Identify pattern: "Technology stack including X, Y, Z"
           - Identify pattern: "Experience with A or B or similar tools"
           - Extract the actual tools/technologies mentioned as examples

        2. **DYNAMIC TOOL-TO-REQUIREMENT MATCHING:**
           - If JD requirement mentions specific tools as examples, and resume contains those tools → MATCH
           - If JD uses category descriptions with tool examples, match based on the examples found
           - Parse parenthetical explanations and "like/such as/including" phrases to find matchable items

        3. **PREVENT LOGICAL CONTRADICTIONS:**
           - A skill/tool CANNOT be both "matched" and "missing" simultaneously
           - If resume demonstrates a tool/skill mentioned in JD requirements → it's MATCHED, not missing
           - If resume shows broader capability than JD asks for → credit the match, list remainder as extra

        4. **VALIDATION LOGIC:**
           - Before finalizing lists, cross-check for any skill appearing in multiple categories
           - Resolve conflicts by prioritizing matches over misses when evidence exists
           - Apply common sense: if it's in the resume and mentioned in JD → it's a match

        **MANDATORY**: Apply this logic to the actual JD and resume content provided, using the specific tools and requirements mentioned in THIS evaluation.
        **INTELLIGENT SKILL ANALYSIS PROCESS:**
        Before starting the {k_runs} runs, perform this ONE-TIME skill analysis:

        1. **Parse JD Skills**:
           - Identify exact tools (e.g., "Terraform", "Jenkins") and categories (e.g., "IAC tools like Ansible, Terraform").
           - Treat example tools as satisfying the category (e.g., resume mentioning "Terraform" satisfies "IAC tools").
        2. **Resume Skill Extraction**:
           - Extract all skills/tools from skills, experience, and projects sections.
           - Include implied skills: e.g., Terraform implies 70% Linux proficiency; Docker implies 60% containerization knowledge.
        3. **Matching Rules**:
           - Exact match (e.g., "Python" in JD and resume): Full credit.
           - Implied match (e.g., Terraform for "Linux infrastructure"): 70% credit, note as partial.
           - No evidence: List as missing, do NOT infer without clear basis.
           - Example: For JD requirement "Linux-based infrastructure", if resume mentions Terraform but not Linux, mark as partial match with note: "Terraform implies some Linux knowledge."
        4. **Consistency Check**:
           - Lock the Skills_Match, Required_Skills_Missing, and Extra_Skills lists after the first run.
           - Ensure no skill appears in both Matched and Missing lists.
        **CRITICAL RULE:** No skill can appear in both Skills_Match and Required_Skills_Missing simultaneously.

        Lock these lists so they remain IDENTICAL across all {k_runs} evaluations.
        Do NOT add, remove, or modify items in these lists during different runs.

        **SAMPLING DIVERSITY INSTRUCTIONS:**
        * Use temperature={temperature} to introduce controlled randomness in reasoning paths
        * Use top_p={top_p} to maintain high-quality diverse completions
        * Each of the {k_runs} runs should explore different aspects and perspectives
        * Vary the order of evaluation (skills first vs experience first)
        * Consider different weight interpretations within the same framework
        * Explore edge cases and alternative explanations for resume gaps

        **MANDATORY WEAKNESS IDENTIFICATION:**
        In EACH of the {k_runs} internal evaluations, you MUST identify specific weaknesses by analyzing:
        * Experience gaps (years, relevance, seniority level)
        * Missing critical skills from JD requirements
        * Educational mismatches if relevant to role
        * Lack of demonstrated project experience in required areas
        * Industry/domain experience gaps
        * Leadership/management experience if required
        * Certification gaps if specified in JD

        **STRICT EXPERIENCE RULE:**
        - Identify the MINIMUM years of relevant experience required from the JD.
        - Identify the candidate's actual relevant years from the Resume.
        - If candidate's relevant years < required years → 
            - Set "experience_gap" to the shortfall (integer).
            - Set "qualification_status" to "Not Qualified - Experience Gap".
            - Weaknesses must explicitly include: "Experience gap: Requires X years, has Y years."
        - If candidate meets or exceeds required experience → continue normal evaluation.
       
        **WEAKNESS DETECTION RULES:**
        1. **Experience Weakness:** If candidate has fewer years than required, explicitly note: "Requires X years, has Y years."
        2. **Skill Gaps:** Any required skill not demonstrated in resume must be flagged
        3. **Domain Mismatch:** If JD requires specific industry experience not shown in resume
        4. **Level Mismatch:** If JD requires senior-level responsibilities but resume shows junior-level work
        5. **Technical Depth:** If projects/experience lack complexity expected for the role
        6. **Zero Experience Red Flag:** If candidate has no professional experience for roles requiring any, this is a critical weakness

        **AGGREGATION RULES (apply before final output):**
        After generating {k_runs} diverse evaluations using temp={temperature} and top_p={top_p}, aggregate as follows:
        * **Numeric scores** (Experience_Score, Skills_Score, Education_Score, Projects_Score): compute the MEDIAN across the {k_runs} runs, then ROUND to one decimal place. Ensure each score is within [0.0, 10.0].
        * **Match_Percentage**: compute numeric % for each run using the formula in the scoring criteria, take MEDIAN of those numeric percentages, format as string with one decimal place and trailing '%'.
        * **Pros / Cons / Weaknesses**: include items that appear in at least a simple majority (>= {(k_runs // 2) + 1}). If no item reaches majority, include the top-frequency items (up to 5), ordered by frequency then conciseness.
        * **"Skills Match"**: include only skills that are present in the JD (Required or Preferred) AND found in resume across runs. For each skill, pick the MOST COMMON explanation across runs.
        * **"Required_Skills_Missing_from_Resume"** and **"Missing_Requirements"**: include items that are judged missing in the majority of runs.
        * **"Extra skills"**: union of skills found across runs not mentioned in JD.
        * **"Projects"** and **"Parsed_Resume"** arrays: use the union of parsed entries across runs.
        * **Conservative Judgment**: When in doubt, prefer identifying weaknesses rather than overlooking them.
        * **Diversity Benefit**: The varied reasoning paths from sampling should improve robustness of final assessment.

        **CRITICAL REQUIREMENTS:**
        - Use temperature={temperature} and top_p={top_p} for {k_runs} diverse internal evaluations
        - DO NOT output intermediate analysis or evaluations
        - DO NOT include step-back analysis in final output
        - Return exactly one JSON object with comprehensive weakness identification
        - Ensure sampling diversity leads to robust consensus on weaknesses
        - Ensure at least 2-3 specific weaknesses are identified for every candidate unless they are exceptionally qualified

        ---
        **ENHANCED SCORING CRITERIA (Apply ONLY if JD is Valid):**
        Scores are on a scale of 0-10 with STRICTER evaluation standards:
        * **Experience Score (Weight: {exp_pct:.1f}%)**
        * **Years Requirement:** Penalize heavily if minimum not met (subtract 5-7 points for significant gaps)
        * **Zero Experience Penalty:** Score 0-2 if candidate has no professional experience for roles requiring any
        * **Relevance Match:** Industry, domain, and technology alignment critical
        * **Seniority Gap:** Penalize if candidate's level doesn't match JD expectations

        * **Skills Score (Weight: {skills_pct:.1f}%)**
        * **Critical Skills Missing:** Each missing required skill reduces score by 1-2 points
        * **Demonstration Requirement:** Skills must be proven through experience/projects, not just listed
        * **Depth Assessment:** Surface-level knowledge vs deep expertise
        * **Penalties:** Significant penalties for missing core required skills or if skills are listed but not demonstrated.

        * **Projects Score (Weight: {projects_pct:.1f}%)**
        * **Relevance Penalty:** Projects unrelated to JD requirements score low
        * **Complexity Assessment:** Simple projects for complex roles penalized
        * **No Projects Penalty:** Score 0-1 if no relevant projects for technical roles
        * **Impact Evidence:** Projects without measurable outcomes score lower

        * **Education Score (Weight: {edu_pct:.1f}%)**
        * **Degree Relevance:** Alignment of degree(s) and field of study with the technical nature of the JD (e.g., CS, Engineering, Data Science degrees for tech roles)
        * **Academic Performance:** GPA or equivalent score if provided and relevant.
        * **Relevant Coursework/Minors:** Specific studies that bolster relevance.
        ---

        **MATCH PERCENTAGE CALCULATION:**
        * **Match_Percentage represents how much of the JD requirements are covered by the resume**
        * **Stricter Calculation:** Partial matches count as 0.5, not full points
        * Formula: Match_Percentage = (Fully_Matched_Requirements + 0.5*Partially_Matched_Requirements) / Total_JD_Requirements * 100
        * Consider Required_Skills, Minimum_Experience, Qualifications, and key Responsibilities from JD
        * Format as string with one decimal place and "%" sign (e.g., "67.5%")

        ---

        **PROJECTS SECTION PARSING & VALIDATION:**
        * Extract ALL projects from resume in Parsed_Resume
        * For scoring: Projects are INVALID if title is generic, description is minimal, or no clear candidate contribution
        * Penalize heavily for lack of relevant projects in technical roles

        ---

        **CRITICAL INSTRUCTIONS:**
        1. **PRE-EVALUATION JD VALIDATION:** Mark as invalid only if JD is genuinely unusable (empty, single words, obvious test input)
        2. **Weakness Identification is MANDATORY:** Every evaluation must identify specific candidate weaknesses
        3. **Conservative Scoring:** When uncertain, lean toward lower scores and identifying gaps
        4. **Return ONLY VALID JSON** with enhanced structure below
        5. **Handle Missing Information:** Use "NA" for strings, [] for arrays
        6. **Technical Synonymy:** Recognize related technologies but don't over-credit
        7. **Base evaluation ONLY on JD requirements**

        **ENHANCED JSON STRUCTURE:**

        {{
          "Step_Back_Insights": {{
            "JD_Analysis_Summary": "Brief summary of role requirements and ideal candidate profile",
            "Critical_Success_Factors": ["factor1", "factor2", "factor3"],
            "Major_Risk_Areas": ["risk1", "risk2", "risk3"]
          }},
          "Evaluation": {{
            "Experience_Score": <float 0.0-10.0>,
            "Skills_Score": <float 0.0-10.0>,
            "Education_Score": <float 0.0-10.0>,
            "Projects_Score": <float 0.0-10.0>,
            "experience_gap": <integer, number of years candidate is short, 0 if meets or exceeds>,
            "Overall_Weighted_Score": <float 0.0-10.0, DO NOT CALCULATE - just provide individual scores>,
            "Match_Percentage": "<string representing JD requirements coverage, e.g., '67.5%'>",
            "Pros": [
              "specific strength 1",
              "specific strength 2"
            ],
            "Cons": [
              "specific weakness 1",
              "specific weakness 2"
            ],
            "Detailed_Weaknesses": [
              "Critical weakness 1 with impact explanation",
              "Critical weakness 2 with impact explanation",
              "Growth area 1 with development suggestion"
            ],
            "Skills Match": [
                 "ONLY list skills that are present in the JD's Required_Skills or Preferred_Skills arrays AND found in the resume",
                 "For each matched skill, explain how it's demonstrated in the resume",
                 "Do NOT include skills that are not mentioned in the job description"
            ],

            "Required_Skills_Missing_from_Resume": [
              "List only JD-required skills that are not explicitly or implicitly shown in the resume. Do NOT list skills as missing if they are implied through related tools, frameworks, or project experience."
            ],
            "Experience_Gaps": [
              "Specific experience shortfalls relative to JD requirements"
            ],
            "Extra skills": [
               "List additional skills candidate has beyond job requirements (for context, do not factor into main scores)"
            ],
            "Qualification Status": "Qualified or Not Qualified with reason - this will be calculated by the system based on scores and experience gap",
            "Missing_Requirements": [
              "Key JD requirements not met by candidate"
            ],
            "Risk_Assessment": {{
              "High_Risk_Areas": ["area1", "area2"],
              "Medium_Risk_Areas": ["area1", "area2"],
              "Mitigation_Suggestions": ["suggestion1", "suggestion2"]
            }},
            "Comments": "Comprehensive assessment including development recommendations",
            "Summary": "Balanced 2-3 line summary highlighting key strengths AND critical gaps"
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
            "Frameworks": ["list all frameworks, libraries, and significant tools"],
            "Technologies": ["list all underlying technologies, platforms, and databases"],
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
        **MANDATORY: Every evaluation MUST include specific weaknesses in Detailed_Weaknesses array, even for strong candidates. Focus on areas for improvement relative to ideal candidate profile.**
        CANDIDATE RESUME DATA: {resume_data}
        Job Description: {job_description}
    """
    return evaluation_prompt.strip()
