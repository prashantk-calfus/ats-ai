import json
import os
from typing import Any, Dict

import requests
import streamlit as st
from frontend_calls import (
    evaluate_resume_with_backend,
    parse_resume_from_backend,
    upload_resume_file_to_backend,
)

BACKEND_URL = os.getenv("BACKEND_URL", default="http://backend:8000")
JD_OPTIONS = {
    "Select a pre-existing JD": "Select a pre-existing JD",
    "Senior Python Development Engineer": "jd_json/SrPDE.json",
    "Oracle ERP": "jd_json/OracleERP.json",
    "Data Architect": "jd_json/DataArchJD.json",
    "Senior Full Stack Engineer": "jd_json/SeniorFullStackEngineer_Python.json",
}


def display_parsed_resume_in_markdown(parsed_resume_data: Dict[str, Any]):
    """
    Displays the parsed resume information in a user-friendly Markdown format.
    """
    st.markdown("#### Personal Information")
    st.write(f"**Name:** {parsed_resume_data.get('Name', 'N/A')}")

    contact_details = parsed_resume_data.get("Contact_Details", {})
    if contact_details:
        st.write(f"**Mobile No:** {contact_details.get('Mobile_No', 'N/A')}")
        st.write(f"**Email:** {contact_details.get('Email', 'N/A')}")
    else:
        st.write("**Contact Details:** Not provided")

    st.write(f"**GitHub:** {parsed_resume_data.get('Github_Repo', 'N/A')}")
    st.write(f"**LinkedIn:** {parsed_resume_data.get('LinkedIn', 'N/A')}")

    st.markdown("---")
    st.markdown("#### Education")
    education_entries = parsed_resume_data.get("Education", [])
    if education_entries:
        for edu in education_entries:
            st.markdown(f"**{edu.get('Degree', 'N/A')}** at {edu.get('Institution', 'N/A')}")
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Score:* {edu.get('Score', 'N/A')}, *Duration:* {edu.get('Duration', 'N/A')}")
    else:
        st.info("No education details provided.")

    st.markdown("---")
    st.markdown("#### Professional Experience")
    experience_entries = parsed_resume_data.get("Professional_Experience", [])
    if experience_entries:
        for exp in experience_entries:
            st.markdown(f"**{exp.get('Role', 'N/A')}** at **{exp.get('Company', 'N/A')}**")
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Duration:* {exp.get('Duration', 'N/A')}")
            if exp.get("Description", "N/A") != "N/A":
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Description:* {exp.get('Description', 'N/A')}")
    else:
        st.info("No professional experience details provided.")

    st.markdown("---")
    st.markdown("#### Projects")
    project_entries = parsed_resume_data.get("Projects", [])
    if project_entries and project_entries[0].get("Project_Name", "NA").upper() != "NA":
        for proj in project_entries:
            st.markdown(f"**Project Name:** {proj.get('Project_Name', 'N/A')}")
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Description:* {proj.get('Project_Description', 'N/A')}")
    else:
        st.info("No project details provided.")

    st.markdown("---")
    st.markdown("#### Certifications")
    certification_entries = parsed_resume_data.get("Certifications", [])
    if certification_entries and certification_entries[0].get("Certification_Authority", "NA").upper() != "NA":
        for cert in certification_entries:
            st.markdown(f"**Certification:** {cert.get('Certification_Details', 'N/A')}")
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Authority:* {cert.get('Certification_Authority', 'N/A')}")
    else:
        st.info("No certification details provided.")

    st.markdown("---")
    st.markdown("#### Technical Skills")
    prog_lang = parsed_resume_data.get("Programming_Language", [])
    if prog_lang:
        st.write(f"**Programming Languages:** {', '.join(prog_lang)}")
    else:
        st.write("**Programming Languages:** N/A")

    frameworks = parsed_resume_data.get("Frameworks", [])
    if frameworks:
        st.write(f"**Frameworks:** {', '.join(frameworks)}")
    else:
        st.write("**Frameworks:** N/A")

    technologies = parsed_resume_data.get("Technologies", [])
    if technologies:
        st.write(f"**Technologies:** {', '.join(technologies)}")
    else:
        st.write("**Technologies:** N/A")


def display_final_evaluation_results(evaluation_results: Dict[str, Any]):
    """Display the final evaluation results summary"""
    st.subheader("Final Resume Evaluation Results Summary")

    # === Overall Scores ===
    eval_summary = evaluation_results.get("Evaluation_Summary", {})
    match_with_jd = eval_summary.get("Match_Percentage", "N/A").strip()
    qualification_status = eval_summary.get("Qualification_Status", "N/A")
    exp_score = eval_summary.get("Experience_Score", "N/A")
    skills_score = eval_summary.get("Skills_Score", "N/A")
    edu_score = eval_summary.get("Education_Score", "N/A")
    projects_score = eval_summary.get("Projects_Score", "N/A")
    overall_score = eval_summary.get("Overall_Weighted_Score", "N/A")

    col_score1, col_score2, col_score3 = st.columns(3)
    with col_score1:
        st.metric(label=" Overall Score (0-10)", value=overall_score)
    with col_score2:
        st.metric(label=" Match with JD", value=match_with_jd)
    with col_score3:
        if qualification_status == "Qualified":
            st.success(f" Status: {qualification_status}")
        else:
            st.error(f" Status: {qualification_status}")

    # === Individual Scores ===
    st.markdown("---")
    st.markdown("#### Detailed Scores")

    col_ind_score1, col_ind_score2, col_ind_score3, col_ind_score4 = st.columns(4)  # Added a column for projects score
    with col_ind_score1:
        st.metric(label="Experience Score (0-10)", value=exp_score)
    with col_ind_score2:
        st.metric(label="Skills Score (0-10)", value=skills_score)
    with col_ind_score3:
        st.metric(label="Education Score (0-10)", value=edu_score)
    with col_ind_score4:
        st.metric(label="Projects Score (0-10)", value=projects_score)

    # === Pros and Cons ===
    st.markdown("---")
    st.markdown("#### Strengths and Areas for Improvement")

    pros_and_cons = evaluation_results.get("Strengths_and_Weaknesses", {})
    pros = pros_and_cons.get("Pros", [])
    cons = pros_and_cons.get("Cons", [])

    col_pros, col_cons = st.columns(2)
    with col_pros:
        st.success("##### Strengths")
        if pros:
            for p in pros:
                st.write(f"- {p}")
        else:
            st.info("No specific strengths identified.")

    with col_cons:
        st.warning("##### Weaknesses")
        if cons:
            for c in cons:
                st.write(f"- {c}")
        else:
            st.info("No specific weaknesses identified.")

    # === Skills Match ===
    st.markdown("---")
    st.markdown("#### Skills Match Analysis")

    skill_analysis = evaluation_results.get("Skill_Analysis", {})
    skills_match = skill_analysis.get("Skills Match", [])
    skills_not_matching = skill_analysis.get("Required_Skills_Missing_from_Resume", [])
    extra_skills = skill_analysis.get("Extra skills", [])  # This alias is expected from the LLM JSON, so keep it.

    if skills_match:
        st.markdown("**Matching Skills:**")
        st.info(",\n ".join(skills_match))
    else:
        st.warning("No direct skill matches found.")

    if skills_not_matching:
        st.markdown("**Missing Skills (from JD):**")
        st.warning(",\n ".join(skills_not_matching))

    if extra_skills:
        st.markdown("** Extra Skills (beyond JD):**")
        st.info(",\n ".join(extra_skills))
    else:
        st.info("No additional skills beyond JD requirements identified.")

    # === Key Considerations ===
    st.markdown("---")
    st.markdown("####  Key Considerations")

    key_considerations = evaluation_results.get("Key_Considerations", {})
    kpis = key_considerations.get("Quantifiable_Achievements_Identified", [])
    red_flags = key_considerations.get("Red_Flags_Noted", [])
    overall_recommendation = key_considerations.get("Overall_Recommendation", "N/A")

    if kpis:
        st.markdown("** Quantifiable Achievements:**")
        for kpi in kpis:
            st.markdown(f"- {kpi}")
    else:
        st.info("No quantifiable achievements noted.")

    if red_flags:
        st.markdown("** Red Flags:**")
        for flag in red_flags:
            st.warning(f"- {flag}")
    else:
        st.success("No red flags identified.")

    if overall_recommendation and overall_recommendation != "N/A":
        st.markdown("** Final Recommendation:**")
        st.markdown(f"- {overall_recommendation}")


# --- Streamlit Frontend (main app structure) ---
st.set_page_config(layout="wide", page_title="Resume Analyzer")

st.title("Resume Analyzer and Evaluator")

# Initialize session state variables
if "uploaded_resume_filename" not in st.session_state:
    st.session_state.uploaded_resume_filename = None
if "parsed_resume" not in st.session_state:
    st.session_state.parsed_resume = None
if "personal_details" not in st.session_state:
    st.session_state.personal_details = None
if "evaluation_results" not in st.session_state:
    st.session_state.evaluation_results = None
if "show_jd_sections" not in st.session_state:
    st.session_state.show_jd_sections = False
if "decision_made" not in st.session_state:
    st.session_state.decision_made = None
if "temp_jd_path" not in st.session_state:
    st.session_state.temp_jd_path = None


# --- Section 1: Upload and Parse Resume ---
st.header("1. Upload and Parse Resume")
uploaded_file = st.file_uploader("Choose a resume file (PDF)", type=["pdf"])

# Placeholder for messages during upload/parsing
parsing_status_messages = st.empty()

if uploaded_file is not None:
    if st.button("Process Resume", key="process_resume_btn"):
        # Clear states of previous sessions when a new resume is processed
        st.session_state.uploaded_resume_filename = None
        st.session_state.parsed_resume = None
        st.session_state.evaluation_results = None
        st.session_state.show_jd_sections = False
        st.session_state.decision_made = None
        st.session_state.temp_jd_path = None

        with st.spinner("Uploading resume..."):
            uploaded_filename = upload_resume_file_to_backend(uploaded_file, parsing_status_messages)
            st.session_state.uploaded_resume_filename = uploaded_filename

        if st.session_state.uploaded_resume_filename:
            with st.spinner("Parsing resume with LLM..."):
                parsed_data = parse_resume_from_backend(st.session_state.uploaded_resume_filename, parsing_status_messages)
                st.session_state.parsed_resume = parsed_data

                if st.session_state.parsed_resume:
                    st.session_state.show_jd_sections = True
                    parsing_status_messages.success("Resume processed and parsed successfully!")
                else:
                    st.session_state.show_jd_sections = False
                    parsing_status_messages.error("Failed to parse resume after upload.")
        else:
            parsing_status_messages.error("Resume upload failed. Cannot proceed with parsing.")


# --- Collapsible Parsed Resume Section ---
if st.session_state.parsed_resume:
    with st.expander("View Parsed Resume Information (Click to Expand)"):
        display_parsed_resume_in_markdown(st.session_state.parsed_resume)
    st.markdown("---")


# --- Section 2 & 3: Conditional Display ---
if st.session_state.show_jd_sections:
    # --- Section 2: Provide Job Description ---
    st.header("2. Provide Job Description")

    st.info("Please paste a JD or select one from the dropdown to proceed.")

    custom_jd_text = st.text_area(
        "Paste a Job Description here ( Press Cmd+Enter to submit )",
        height=80,
        help="Paste the full job description. If text is entered here, it will be used instead of the dropdown selection.",
    )

    # Create a dropdown for JD options
    selected_jd_display = st.selectbox("Or Select a Job Description:", options=list(JD_OPTIONS.keys()), index=0)

    # Determine the JD path to send to the backend
    jd_content = None
    if custom_jd_text and len(custom_jd_text.strip()) > 50:

        jd_content = {"job_description": custom_jd_text}

        st.info("Using custom JD from text.")

    elif selected_jd_display != "Select a pre-existing JD":
        # For pre-existing JDs, pass the filename. Backend will resolve it from its JD_UPLOAD_FOLDER.
        jd_path_to_use = JD_OPTIONS[selected_jd_display]
        jd_content = json.load(open(jd_path_to_use))
        st.info(f"Selected pre-existing JD: `{jd_path_to_use}`")

    # Placeholder for messages during evaluation
    evaluation_status_messages = st.empty()

    if st.session_state.parsed_resume is not None and jd_content:
        if st.button("Evaluate Resume", key="evaluate_resume_btn"):
            # Clear previous decision when re-evaluating

            # --- Section 3: Evaluate Resume against JD ---
            st.header("3. Evaluate Resume against JD")

            st.session_state.decision_made = None

            with st.spinner("Evaluating..."):
                # Store personal details separately for the report page.
                personal_details_keys = ["Name", "Contact_Details", "Github_Repo", "LinkedIn"]
                st.session_state.personal_details = {key: st.session_state.parsed_resume.get(key) for key in personal_details_keys}

                st.session_state.evaluation_results = evaluate_resume_with_backend(
                    st.session_state.parsed_resume,
                    jd_content,
                    evaluation_status_messages,
                )

                if st.session_state.evaluation_results:
                    evaluation_status_messages.success("Resume evaluation complete!")
                else:
                    evaluation_status_messages.error("Resume evaluation failed. Check backend logs for details.")

    elif st.session_state.parsed_resume is None:
        evaluation_status_messages.warning("Please upload and parse a resume first to proceed with evaluation.")
    else:
        evaluation_status_messages.info("Select a Job Description and click 'Evaluate Resume'.")


# --- Display Final Evaluation Results (Outside of button logic) ---
if st.session_state.evaluation_results:
    display_final_evaluation_results(st.session_state.evaluation_results)

    # Accept/Reject buttons
    candidate_name = (st.session_state.personal_details.get("Name") if st.session_state.personal_details else None) or st.session_state.parsed_resume.get("Name", "Unknown")

    # Display decision status if already made
    if st.session_state.decision_made:
        if st.session_state.decision_made == "Accept":
            st.success(f" **{candidate_name}** has been marked as **Accepted**!")
        else:
            st.warning(f" **{candidate_name}** has been marked as **Rejected**!")
    else:
        # Shown when no decision made yet
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("✅ Accept", key="accept_btn"):
                response = requests.post(f"{BACKEND_URL}/store_decision", params={"name": candidate_name, "decision": "Accept"})
                if response.status_code == 200:
                    st.session_state.decision_made = "Accept"
                    st.rerun()
                else:
                    st.error(f"Failed to store decision: {response.text}")

        with col2:
            if st.button("❌ Reject", key="reject_btn"):
                response = requests.post(f"{BACKEND_URL}/store_decision", params={"name": candidate_name, "decision": "Reject"})
                if response.status_code == 200:
                    st.session_state.decision_made = "Reject"
                    st.rerun()
                else:
                    st.error(f"Failed to store decision: {response.text}")

        with col3:
            # Generate Report Button
            if st.button("Generate Report", key="generate_report_btn"):
                # Store data in session state for the report page
                st.session_state.report_evaluation_results = st.session_state.evaluation_results
                st.session_state.report_parsed_resume = st.session_state.parsed_resume
                # Ensure personal_details is set before navigating
                personal_details_keys = ["Name", "Contact_Details", "Github_Repo", "LinkedIn"]
                st.session_state.report_personal_details = {key: st.session_state.parsed_resume.get(key) for key in personal_details_keys}
                # Navigate to the report page - ensure 'pages/report_page.py'
                st.switch_page("pages/report_page.py")

else:
    st.info("Upload and parse a resume above to unlock Job Description and Evaluation sections.")
