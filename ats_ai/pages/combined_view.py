import json
import os

import pymupdf
import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"
JD_OPTIONS = {
    "Select a pre-existing JD": "Select a pre-existing JD",
    "Senior Python Development Engineer": "SrPDE.json",
    "Oracle ERP": "OracleERP.json",
    "Data Architect": "DataArchJD.json",
    "Senior Full Stack Engineer": "SeniorFullStackEngineer_Python.json",
}

st.title("Combined View for faster results")
st.session_state.parsed_resume = None
st.session_state.evaluation_results = None

uploaded_resume = st.file_uploader("Upload resume file (PDF)", type=["pdf"])

selected_jd_display = st.selectbox("Select a Job Description:", options=list(JD_OPTIONS.keys()))
jd_path = None
if selected_jd_display != "Select a pre-existing JD":
    jd_path = JD_OPTIONS[selected_jd_display]
    st.info(f"Selected JD: `{jd_path}`")

if uploaded_resume is not None and jd_path:
    if st.button("Upload & Evaluate"):
        with st.spinner("Uploading and evaluating..."):
            # Upload resume
            files = {"resume_file": (uploaded_resume.name, uploaded_resume.getvalue(), uploaded_resume.type)}
            upload_response = requests.post(f"{BACKEND_URL}/upload_resume_file", files=files)

            if upload_response.status_code != 200:
                st.error("Failed to upload resume")
            else:
                text = ""
                resume_data = pymupdf.open("data/" + uploaded_resume.name)
                for i in range(0, resume_data.page_count):
                    page = resume_data.load_page(i)
                    text += page.get_text()

                with open(os.path.join("jd_json/", jd_path), "r") as f:
                    jd_json = json.load(f)

                combined_json = {"resume_data": text, "jd_json": jd_json}

                response = requests.post(f"{BACKEND_URL}/parse_and_evaluate", json=combined_json)
                st.session_state.parsed_data = response.json()

                # st.session_state.evaluation_results = st.session_state.parsed_data.get("Evaluation")
                # st.session_state.parsed_resume = st.session_state.parsed_data.get("Parsed_Resume")

                if response.status_code == 200:
                    st.success("Evaluation Complete")
                    # st.json(response.json())
                else:
                    st.error(f"Evaluation failed: {response.status_code}")

parsed_resume_data = st.session_state.parsed_data.get("Parsed_Resume")
eval_results = st.session_state.parsed_data.get("Evaluation")
candidate_name = parsed_resume_data.get("Name")
st.header(f"Evaluation Report for: {candidate_name}")

"""EVALUATION REPORT IN MARKDOWN"""

exp_score = eval_results.get("Experience_Score")
skill_score = eval_results.get("Skills_Score")
edu_score = eval_results.get("Education_Score")
projects_score = eval_results.get("Projects_Score")
overall_score = eval_results.get("Overall_Weighted_Score")
match_jd = eval_results.get("Match_Percentage")
qual_status = eval_results.get("Qualification Status")

col_score1, col_score2, col_score3 = st.columns(3)
with col_score1:
    st.metric(label=" Overall Score (0-10)", value=overall_score)
with col_score2:
    st.metric(label=" Match with JD", value=match_jd)
with col_score3:
    if qual_status == "Qualified":
        st.success(f" Status: {qual_status}")
    else:
        st.error(f" Status: {qual_status}")

# === Individual Scores ===
st.markdown("---")
st.markdown("#### Detailed Scores")

col_ind_score1, col_ind_score2, col_ind_score3, col_ind_score4 = st.columns(4)  # Added a column for projects score
with col_ind_score1:
    st.metric(label="Experience Score (0-10)", value=exp_score)
with col_ind_score2:
    st.metric(label="Skills Score (0-10)", value=skill_score)
with col_ind_score3:
    st.metric(label="Education Score (0-10)", value=edu_score)
with col_ind_score4:
    st.metric(label="Projects Score (0-10)", value=projects_score)


st.markdown("---")
st.markdown("#### Strengths and Areas for Improvement")

pros = eval_results.get("Pros")
cons = eval_results.get("Cons")

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

missing_req = eval_results.get("Missing_Requirements")
if missing_req:
    st.markdown("**Missing Skills (from JD):**")
    st.warning(",\n ".join(missing_req))

summary_eval = eval_results.get("Summary")
if summary_eval:
    st.markdown("**Summary**")
    st.markdown(f"- {summary_eval}")

if parsed_resume_data:
    with st.expander("Parsed Resume Information"):

        st.write(f"**Name:** {candidate_name}")

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
        if certification_entries:
            for cer in certification_entries:
                st.markdown(f"{cer}")

        st.markdown("#### Technical Skills")
        skills = parsed_resume_data.get("Skills", [])
        if skills:
            for skill in skills:
                st.markdown(f"⦿ {skill}")
