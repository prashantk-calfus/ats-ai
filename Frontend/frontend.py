import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, Any, Optional

# Configure page
st.set_page_config(
    page_title="Resume Parser & Evaluator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #A23B72;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .score-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E86AB;
        margin: 1rem 0;
    }
    .skills-container {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .upload-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Backend configuration
BACKEND_URL = "http://localhost:8000"  # Adjust this to docker backend url - 'backend'

# Job Description mappings - Update these paths according to your backend
JD_OPTIONS = {
    "Senior Python Development Engineer": "SrPDE.json",
    "Oracle ERP": "OracleERP.json",
    "Data Architect" : "DataArch.json"
}

import re

def upload_resume(file) -> Optional[Dict[str, Any]]:
    try:
        file.seek(0)
        files = {"resume_file": (file.name, file.getvalue(), file.type)}
        upload_response = requests.post(f"{BACKEND_URL}/upload_resume_file", files=files)

        if upload_response.status_code == 200 and upload_response.json().get("message") == "Resume uploaded successfully":
            st.success("Resume uploaded successfully!")

            stream_url = f"{BACKEND_URL}/resume_parser"
            params = {"resume_path": file.name}

            merged_json = {}
            buffer = ""
            stream_output = st.empty()

            decoder = json.JSONDecoder()

            with requests.get(stream_url, params=params, stream=True, timeout=180) as resp:
                resp.raise_for_status()

                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.strip():
                        continue

                    buffer += line.strip()

                    while buffer:
                        try:
                            parsed_obj, idx = decoder.raw_decode(buffer)
                            buffer = buffer[idx:].lstrip()
                            merged_json.update(parsed_obj)

                            # Live update chunk
                            stream_output.code(json.dumps(parsed_obj, indent=2), language="json")
                        except json.JSONDecodeError:
                            break

            st.write(merged_json)
            return merged_json

        else:
            st.error(f"Upload failed: {upload_response.status_code} - {upload_response.text}")
            return None

    except Exception as e:
        st.error(f"Error during upload/streaming: {str(e)}")
        return None

def evaluate_resume(parsed_data: Dict[str, Any], jd_path: str) -> Optional[Dict[str, Any]]:
    """Send evaluation request to backend"""
    try:
        # print("Parsed Data:", parsed_data)
        payload = {
            "resume_json": parsed_data,
            "jd_path": jd_path
        }

        merged_json = {}
        buffer = ""
        stream_output = st.empty()

        decoder = json.JSONDecoder()

        with requests.get("{BACKEND_URL}/evaluate_resume", json=payload, stream=True, timeout=180) as resp:
            resp.raise_for_status()

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.strip():
                    continue

                buffer += line.strip()

                while buffer:
                    try:
                        parsed_obj, idx = decoder.raw_decode(buffer)
                        buffer = buffer[idx:].lstrip()
                        merged_json.update(parsed_obj)

                        # Live update chunk
                        stream_output.code(json.dumps(parsed_obj, indent=2), language="json")
                    except json.JSONDecodeError:
                        break

        st.write(merged_json)
        return merged_json
    except Exception as e:
        st.error(f"Error during upload/streaming: {str(e)}")
        return None

def display_parsed_resume(data: Dict[str, Any]):
    """Display parsed resume data in a structured format"""
    st.markdown('<div class="section-header">📄 Parsed Resume</div>', unsafe_allow_html=True)

    # Personal Information
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Name:**")
        st.write(data.get("Name", "N/A"))

        st.markdown("**Mobile:**")
        st.write(data.get("Contact_Details", {}).get("Mobile_No", "N/A"))

        st.markdown("**Email:**")
        st.write(data.get("Contact_Details", {}).get("Email", "N/A"))

    with col2:
        st.markdown("**GitHub:**")
        github_url = data.get("Github_Repo", "N/A")
        if github_url != "N/A" and github_url:
            st.markdown(f"[{github_url}]({github_url})")
        else:
            st.write("N/A")

        st.markdown("**LinkedIn:**")
        linkedin_url = data.get("LinkedIn", "N/A")
        if linkedin_url != "N/A" and linkedin_url:
            st.markdown(f"[{linkedin_url}]({linkedin_url})")
        else:
            st.write("N/A")

    # Education
    st.markdown("**Education:**")
    education = data.get("Education", [])
    if education:
        for edu in education:
            st.markdown(f"- **{edu.get('Degree', 'N/A')}** from {edu.get('Institution', 'N/A')}")
            st.markdown(f"  Score: {edu.get('Score', 'N/A')}, Duration: {edu.get('Duration', 'N/A')}")
    else:
        st.write("No education information available")

    # Professional Experience
    st.markdown("**Professional Experience:**")
    experience = data.get("Professional_Experience", [])
    if experience:
        for exp in experience:
            st.markdown(f"- **{exp.get('Role', 'N/A')}** at {exp.get('Company', 'N/A')}")
            st.markdown(f"  Duration: {exp.get('Duration', 'N/A')}")
            st.markdown(f"  Description: {exp.get('Description', 'N/A')}")
    else:
        st.write("No professional experience available")

    # Projects
    st.markdown("**Projects:**")
    projects = data.get("Projects", [])
    if projects:
        for proj in projects:
            st.markdown(f"- **{proj.get('Project_Name', 'N/A')}**")
            st.markdown(f"  {proj.get('Project_Description', 'N/A')}")
    else:
        st.write("No projects available")

    # Certifications
    st.markdown("**Certifications:**")
    certifications = data.get("Certifications", [])
    if certifications:
        for cert in certifications:
            st.markdown(
                f"- {cert.get('Certification_Details', 'N/A')} from {cert.get('Certification_Authority', 'N/A')}")
    else:
        st.write("No certifications available")

    # Skills
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Programming Languages:**")
        prog_langs = data.get("Programming_Language", [])
        if prog_langs:
            for lang in prog_langs:
                st.write(lang+"\n")
        else:
            st.write("None specified")

    with col2:
        st.markdown("**Frameworks:**")
        frameworks = data.get("Frameworks", [])
        if frameworks:
            for framework in frameworks:
                st.write(framework+"\n")
        else:
            st.write("None specified")

    with col3:
        st.markdown("**Technologies:**")
        techs = data.get("Technologies", [])
        if techs:
            for tech in techs:
                st.write(tech+"\n")
        else:
            st.write("None specified")

def display_evaluation_results(data: Dict[str, Any]):
    """Display evaluation results in a structured format"""
    st.markdown('<div class="section-header">📊 Evaluation Results</div>', unsafe_allow_html=True)

    # Score Overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Experience Score", f"{data.get('Experience_Score', 0)}/10")
    with col2:
        st.metric("Skills Score", f"{data.get('Skills_Score', 0)}/10")
    with col3:
        st.metric("Education Score", f"{data.get('Education_Score', 0)}/10")
    with col4:
        st.metric("Overall Score", f"{data.get('Overall_Score', 0)}/10")

    # Match Percentage
    st.markdown('<div class="score-box">', unsafe_allow_html=True)
    st.markdown(
        f'<span style="font-size:24px;"><strong>Match with JD:</strong> {data.get("Match with JD", "0%")}</span>',
        unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Pros and Cons
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Strengths (Pros):**")
        pros = data.get("Pros", [])
        if pros:
            for pro in pros:
                st.markdown(f"✅ {pro}")
        else:
            st.write("No strengths identified")

    with col2:
        st.markdown("**Areas for Improvement (Cons):**")
        cons = data.get("Cons", [])
        if cons:
            for con in cons:
                st.markdown(f"❌ {con}")
        else:
            st.write("No areas for improvement identified")

    # Skills Analysis
    st.markdown("**Skills Analysis:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="skills-container">', unsafe_allow_html=True)
        st.markdown("**Matching Skills:**")
        matching_skills = data.get("Skills Match", [])
        if matching_skills:
            for skill in matching_skills:
                st.markdown(f"🟢 {skill}")
        else:
            st.write("No matching skills")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="skills-container">', unsafe_allow_html=True)
        st.markdown("**Missing Skills:**")
        missing_skills = data.get("Skills not matching with JD", [])
        if missing_skills:
            for skill in missing_skills:
                st.markdown(f"🔴 {skill}")
        else:
            st.write("No missing skills")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="skills-container">', unsafe_allow_html=True)
        st.markdown("**Extra Skills:**")
        extra_skills = data.get("Extra skills", [])
        if extra_skills:
            for skill in extra_skills:
                st.markdown(f"🔵 {skill}")
        else:
            st.write("No extra skills")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f'<span style="font-size:24px;"><strong>Qualification Status (AI-Assist):</strong> {data.get('qualification_status', 'Unable to Fetch. Try Again')}</span>',
        unsafe_allow_html=True)


def main():
    st.markdown('<div class="main-header">Resume Parser & Evaluator</div>', unsafe_allow_html=True)

    # Initialize session state
    if 'parsed_resume' not in st.session_state:
        st.session_state.parsed_resume = None
    if 'evaluation_results' not in st.session_state:
        st.session_state.evaluation_results = None

    # Top section with upload and evaluation controls
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown("**Upload Resume**")
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf'],
            help="Upload your resume in PDF"
        )

        if uploaded_file is not None:
            if st.button("Parse Resume", type="primary"):
                with st.spinner("Parsing resume..."):
                    parsed_data = upload_resume(uploaded_file)
                    if parsed_data:
                        st.session_state.parsed_resume = parsed_data
                        st.success("Resume parsed successfully!")
                        st.rerun()

    with col2:
        st.markdown("**Job Description**")
        selected_jd = st.selectbox(
            "Select Job Description",
            options=list(JD_OPTIONS.keys()),
            help="Choose the job description to evaluate against"
        )

    with col3:
        st.markdown("**Evaluation**")
        if st.button("Evaluate", type="secondary", disabled=st.session_state.parsed_resume is None):
            if st.session_state.parsed_resume:
                with st.spinner("Evaluating resume..."):
                    jd_path = JD_OPTIONS[selected_jd]
                    evaluation_data = evaluate_resume(st.session_state.parsed_resume, jd_path)
                    if evaluation_data:
                        st.session_state.evaluation_results = evaluation_data
                        st.success("Evaluation completed!")
                        st.rerun()
            else:
                st.error("Please upload and parse a resume first!")

    st.markdown('</div>', unsafe_allow_html=True)

    # Display results
    if st.session_state.parsed_resume:
        display_parsed_resume(st.session_state.parsed_resume)

    if st.session_state.evaluation_results:
        display_evaluation_results(st.session_state.evaluation_results)

        # Accept/Reject Buttons — Send decision to backend
        candidate_name = st.session_state.parsed_resume.get("Name", "Unknown")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Accept"):
                response = requests.post(f"{BACKEND_URL}/store_decision", params={
                    "name": candidate_name,
                    "decision": "Accept"
                })
                if response.status_code == 200:
                    st.success(f"{candidate_name} marked as Accepted ✅")
                else:
                    st.error("Failed to store decision.")

        with col2:
            if st.button("❌ Reject"):
                response = requests.post(f"{BACKEND_URL}/store_decision", params={
                    "name": candidate_name,
                    "decision": "Reject"
                })
                if response.status_code == 200:
                    st.warning(f"{candidate_name} marked as Rejected ❌")
                else:
                    st.error("Failed to store decision.")
    # Footer
    st.markdown("---")
    st.markdown("*Resume Parser & Evaluator - Streamlit Frontend*")


if __name__ == "__main__":
    main()