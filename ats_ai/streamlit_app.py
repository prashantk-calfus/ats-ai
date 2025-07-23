import json
import os

import pymupdf
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "http://localhost:8000"

JD_OPTIONS = {
    "Select a pre-existing JD": "Select a pre-existing JD",
    "Senior Python Development Engineer": "SrPDE.json",
    "Oracle ERP": "OracleERP.json",
    "Data Architect": "DataArchJD.json",
    "Senior Full Stack Engineer": "SeniorFullStackEngineer_Python.json",
}

st.set_page_config(layout="wide", page_title="ATS AI")
st.title("ATS AI : Resume Analyzer and Evaluator")

if "parsed_data_combined" not in st.session_state:
    st.session_state.parsed_data_combined = None
if "decision_made" not in st.session_state:
    st.session_state.decision_made = None
if "uploaded_resume_name" not in st.session_state:
    st.session_state.uploaded_resume_name = None
if "selected_jd_display_value" not in st.session_state:
    st.session_state.selected_jd_display_value = "Select a pre-existing JD"

if "report_evaluation_results" not in st.session_state:
    st.session_state.report_evaluation_results = None
if "report_parsed_resume" not in st.session_state:
    st.session_state.report_parsed_resume = None
if "report_cand_name" not in st.session_state:
    st.session_state.report_cand_name = None


uploaded_resume = st.file_uploader("Upload resume file (PDF)", type=["pdf"])

if uploaded_resume is not None:
    if st.session_state.uploaded_resume_name != uploaded_resume.name:
        st.session_state.uploaded_resume_name = uploaded_resume.name
        st.session_state.parsed_data_combined = None
        st.session_state.decision_made = None
else:
    if st.session_state.uploaded_resume_name is not None:
        st.session_state.uploaded_resume_name = None
        st.session_state.parsed_data_combined = None
        st.session_state.decision_made = None


selected_jd_display = st.selectbox("Select a Job Description:", options=list(JD_OPTIONS.keys()), key="jd_selectbox", index=list(JD_OPTIONS.keys()).index(st.session_state.selected_jd_display_value))

if st.session_state.selected_jd_display_value != selected_jd_display:
    st.session_state.selected_jd_display_value = selected_jd_display
    st.session_state.parsed_data_combined = None
    st.session_state.decision_made = None


jd_path = None
if selected_jd_display != "Select a pre-existing JD":
    jd_path = JD_OPTIONS[selected_jd_display]
    st.info(f"Selected JD: `{jd_path}`")

if st.session_state.uploaded_resume_name and jd_path:
    evaluate_button_disabled = st.session_state.parsed_data_combined is not None
    if st.button("Upload & Evaluate", disabled=evaluate_button_disabled):
        with st.spinner("Uploading and evaluating..."):
            try:
                resume_pdf_reader = pymupdf.open(stream=uploaded_resume.getvalue(), filetype="pdf")
                resume_text = ""
                for i in range(resume_pdf_reader.page_count):
                    page = resume_pdf_reader.load_page(i)
                    resume_text += page.get_text()

                files = {"resume_file": (uploaded_resume.name, uploaded_resume.getvalue(), uploaded_resume.type)}
                upload_response = requests.post(f"{BACKEND_URL}/upload_resume_file", files=files)

                if upload_response.status_code != 200:
                    st.error(f"Failed to upload resume to backend: {upload_response.status_code} - {upload_response.text}")
                    st.session_state.parsed_data_combined = None
                    st.session_state.decision_made = None
                else:
                    with open(os.path.join("jd_json/", jd_path), "r") as f:
                        jd_json = json.load(f)

                    combined_json = {"resume_data": resume_text, "jd_json": jd_json}

                    response = requests.post(f"{BACKEND_URL}/parse_and_evaluate", json=combined_json)

                    if response.status_code == 200:
                        st.session_state.parsed_data_combined = response.json()
                        st.success("Evaluation Complete")
                    else:
                        st.error(f"Evaluation failed: {response.status_code} - {response.text}")
                        st.session_state.parsed_data_combined = None
                        st.session_state.decision_made = None
            except Exception as e:
                st.error(f"An error occurred during evaluation: {e}")
                st.session_state.parsed_data_combined = None
                st.session_state.decision_made = None
elif st.session_state.uploaded_resume_name is None:
    st.info("Please upload a resume (PDF) file.")
elif jd_path is None:
    st.info("Please select a Job Description.")


if st.session_state.parsed_data_combined:
    parsed_resume_data = st.session_state.parsed_data_combined.get("Parsed_Resume")
    eval_results = st.session_state.parsed_data_combined.get("Evaluation")

    candidate_name = parsed_resume_data.get("Name", "Candidate")
    st.header(f"Evaluation Report for: {candidate_name}")

    st.markdown("---")
    st.subheader("Overall Evaluation")

    exp_score = eval_results.get("Experience_Score")
    skill_score = eval_results.get("Skills_Score")
    edu_score = eval_results.get("Education_Score")
    projects_score = eval_results.get("Projects_Score")
    overall_score = eval_results.get("Overall_Weighted_Score")
    match_jd = eval_results.get("Match_Percentage")
    qual_status = eval_results.get("Qualification Status")

    col_score1, col_score2, col_score3 = st.columns(3)
    with col_score1:
        st.metric(label="Overall Score (0-10)", value=overall_score)
    with col_score2:
        st.metric(label="Match with JD", value=match_jd)
    with col_score3:
        if qual_status == "Qualified":
            st.success(f"Status: {qual_status}")
        else:
            st.error(f"Status: {qual_status}")

    st.markdown("---")
    st.subheader("Detailed Scores")

    col_ind_score1, col_ind_score2, col_ind_score3, col_ind_score4 = st.columns(4)
    with col_ind_score1:
        st.metric(label="Experience Score (0-10)", value=exp_score)
    with col_ind_score2:
        st.metric(label="Skills Score (0-10)", value=skill_score)
    with col_ind_score3:
        st.metric(label="Education Score (0-10)", value=edu_score)
    with col_ind_score4:
        st.metric(label="Projects Score (0-10)", value=projects_score)

    st.markdown("---")
    st.subheader("Strengths and Areas for Improvement")

    pros = eval_results.get("Pros")
    cons = eval_results.get("Cons")

    col_pros, col_cons = st.columns(2)

    with col_pros:
        st.success("##### Strengths")
        if pros:
            for p in pros:
                st.markdown(f"- {p}")
        else:
            st.info("No specific strengths identified.")

    with col_cons:
        st.warning("##### Weaknesses")
        if cons:
            for c in cons:
                st.markdown(f"- {c}")
        else:
            st.info("No specific weaknesses identified.")

    # Displaying Skills Match
    skills_match = eval_results.get("Skills Match")
    if skills_match and len(skills_match) > 0:
        st.markdown("---")
        st.markdown("#### Skills Matched with JD")
        for skill_item in skills_match:
            st.markdown(f"- {skill_item}")
    else:
        st.markdown("---")
        st.info("No specific skills match details provided.")

    # Displaying Missing Skills from Resume
    missing_skills_from_resume = eval_results.get("Required_Skills_Missing_from_Resume")
    if missing_skills_from_resume and len(missing_skills_from_resume) > 0:
        st.markdown("---")
        st.markdown("#### Required Skills Missing from Resume (from JD)")
        st.warning(", ".join(missing_skills_from_resume))
    else:
        st.markdown("---")
        st.info("No required skills missing from resume identified.")

    # Displaying Extra Skills
    extra_skills = eval_results.get("Extra skills")
    if extra_skills and len(extra_skills) > 0:
        st.markdown("---")
        st.markdown("#### Extra Skills (not required by JD, but present)")
        st.info(", ".join(extra_skills))
    else:
        st.markdown("---")
        st.info("No extra skills identified.")

    summary_eval = eval_results.get("Summary")
    if summary_eval:
        st.markdown("---")
        st.markdown("**Summary**")
        st.markdown(f"- {summary_eval}")

    st.markdown("---")
    st.subheader("Parsed Resume Information")

    if parsed_resume_data:
        with st.expander("View Full Parsed Resume Data"):

            st.write(f"**Name:** {candidate_name}")

            contact_details = parsed_resume_data.get("Contact_Details", {})
            st.markdown(f"**Mobile No:** {contact_details.get('Mobile_No', 'N/A')}")
            st.markdown(f"**Email:** {contact_details.get('Email', 'N/A')}")

            github_repo = parsed_resume_data.get("Github_Repo", "N/A")
            if github_repo and github_repo.strip().lower() != "na":
                st.markdown(f"**GitHub:** {github_repo}")
            else:
                st.markdown("**GitHub:** Not provided")

            linkedin = parsed_resume_data.get("LinkedIn", "N/A")
            if linkedin and linkedin.strip().lower() != "na":
                st.markdown(f"**LinkedIn:** {linkedin}")
            else:
                st.markdown("**LinkedIn:** Not provided")

            st.markdown("---")
            st.markdown("#### Education")
            education_entries = parsed_resume_data.get("Education", [])
            if education_entries:
                for edu in education_entries:
                    st.markdown(f"**{edu.get('Degree', 'N/A')}** at {edu.get('Institution', 'N/A')}")
                    score = edu.get("Score", "N/A")
                    duration = edu.get("Duration", "N/A")
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Score:* {score}, *Duration:* {duration}")
            else:
                st.info("No education details provided.")

            st.markdown("---")
            st.markdown("#### Professional Experience")
            experience_entries = parsed_resume_data.get("Professional_Experience", [])
            if experience_entries:
                for exp in experience_entries:
                    st.markdown(f"**{exp.get('Role', 'N/A')}** at **{exp.get('Company', 'N/A')}**")
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Duration:* {exp.get('Duration', 'N/A')}")
                    description = exp.get("Description", "N/A")
                    if description and description.strip().lower() not in ["na", "n/a"]:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Description:* {description}")
            else:
                st.info("No professional experience details provided.")

            st.markdown("---")
            st.markdown("#### Projects")
            project_entries = parsed_resume_data.get("Projects", [])
            if project_entries and project_entries[0].get("Project_Name", "NA").upper() not in ["NA", "N/A"]:
                for proj in project_entries:
                    st.markdown(f"**Project Name:** {proj.get('Project_Name', 'N/A')}")
                    description = proj.get("Project_Description", "N/A")
                    if description and description.strip().lower() not in ["na", "n/a"]:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Description:* {description}")
            else:
                st.info("No project details provided.")

            st.markdown("---")
            st.markdown("#### Certifications")
            certification_entries = parsed_resume_data.get("Certifications", [])
            if certification_entries and len(certification_entries) > 0:
                for cer in certification_entries:
                    st.markdown(f"- {cer}")
            else:
                st.info("No certifications provided.")

            st.markdown("---")
            st.markdown("#### Technical Skills")
            programming_languages = parsed_resume_data.get("Programming_Language", [])
            frameworks = parsed_resume_data.get("Frameworks", [])
            technologies = parsed_resume_data.get("Technologies", [])

            all_skills = []
            if programming_languages:
                all_skills.append("##### Programming Languages")
                all_skills.extend([f"⦿ {s}" for s in programming_languages])
            if frameworks:
                all_skills.append("##### Frameworks")
                all_skills.extend([f"⦿ {s}" for s in frameworks])
            if technologies:
                all_skills.append("##### Technologies")
                all_skills.extend([f"⦿ {s}" for s in technologies])

            if all_skills:
                for skill_item in all_skills:
                    st.markdown(skill_item)
            else:
                st.info("No technical skills provided.")

    st.markdown("---")
    st.subheader("Decision Actions")

    combine_eval_results = eval_results
    combine_eval_results["name"] = candidate_name

    if st.session_state.decision_made:
        if st.session_state.decision_made == "Accept":
            st.success(f" **{candidate_name}** has been marked as **Accepted**!")
        else:
            st.warning(f" **{candidate_name}** has been marked as **Rejected**!")

    else:
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ Accept", key="accept_btn"):
                response = requests.post(f"{BACKEND_URL}/store_candidate_evaluation", json=combine_eval_results)
                if response.status_code == 200:
                    st.session_state.decision_made = "Accept"
                    st.rerun()
                else:
                    st.error(f"Failed to store decision: {response.text}")

        with col2:
            if st.button("❌ Reject", key="reject_btn"):
                response = requests.post(f"{BACKEND_URL}/store_candidate_evaluation", json=combine_eval_results)
                if response.status_code == 200:
                    st.session_state.decision_made = "Reject"
                    st.rerun()
                else:
                    st.error(f"Failed to store decision: {response.text}")

        with col3:
            if st.button("Generate Report", key="generate_report_btn"):
                st.session_state.report_evaluation_results = eval_results
                st.session_state.report_parsed_resume = parsed_resume_data
                st.session_state.report_cand_name = candidate_name
                st.switch_page("pages/report_page.py")
