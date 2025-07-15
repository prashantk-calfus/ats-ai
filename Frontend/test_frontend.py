
"""Testing out the new frontend changes."""

import streamlit as st
import requests
import json
from typing import Optional, Dict, Any
import time # Import time for adding delays

# Assuming these are defined in your project or passed as environment variables
BACKEND_URL = "http://localhost:8000"

JD_OPTIONS = {
    "Senior Python Development Engineer": "SrPDE.json",
    "Oracle ERP": "OracleERP.json",
    "Data Architect" : "DataArch.json"
}

# --- Helper function for structured display of parsed resume chunks ---
def display_parsed_resume_chunk(chunk_data: Dict[str, Any], chunk_id: int):

    if chunk_id == 1:
        # Expected: Name, Contact_Details, Github_Repo, LinkedIn
        name = chunk_data.get("Name", "N/A")
        contact = chunk_data.get("Contact_Details", {})
        mobile = contact.get("Mobile_No", "N/A")
        email = contact.get("Email", "N/A")
        github = chunk_data.get("Github_Repo", "N/A")
        linkedin = chunk_data.get("LinkedIn", "N/A")

        st.markdown(f"**Name:** {name}")
        st.markdown(f"**Contact:** Mobile: {mobile},\n\tEmail: {email}")
        st.markdown(f"**Profiles:** GitHub: {github},\n\tLinkedIn: {linkedin}")

    elif chunk_id == 2:
        # Expected: Education
        education_list = chunk_data.get("Education", [])
        if education_list:
            st.markdown("**Education:**")
            for edu in education_list:
                st.markdown(f"- **Degree:** {edu.get('Degree', 'N/A')}")
                st.markdown(f"  **Institution:** {edu.get('Institution', 'N/A')}")
                st.markdown(f"  **Score:** {edu.get('Score', 'N/A')}")
                st.markdown(f"  **Duration:** {edu.get('Duration', 'N/A')}")
        else:
            st.info("No education details found.")

    elif chunk_id == 3:
        # Expected: Professional_Experience
        experience_list = chunk_data.get("Professional_Experience", [])
        if experience_list:
            st.markdown("**Professional Experience:**")
            for exp in experience_list:
                st.markdown(f"- **Company:** {exp.get('Company', 'N/A')}")
                st.markdown(f"  **Role:** {exp.get('Role', 'N/A')}")
                st.markdown(f"  **Duration:** {exp.get('Duration', 'N/A')}")
                st.markdown(f"  **Description:** {exp.get('Description', 'N/A')}")
        else:
            st.info("No professional experience found.")

    elif chunk_id == 4:
        # Expected: Projects
        projects_list = chunk_data.get("Projects", [])
        if projects_list:
            st.markdown("**Projects:**")
            for proj in projects_list:
                st.markdown(f"- **Project Name:** {proj.get('Project_Name', 'N/A')}")
                st.markdown(f"  **Description:** {proj.get('Project_Description', 'N/A')}")
        else:
            st.info("No projects found.")

    elif chunk_id == 5:
        # Expected: Certifications
        certifications_list = chunk_data.get("Certifications", [])
        if certifications_list:
            st.markdown("**Certifications:**")
            for cert in certifications_list:
                st.markdown(f"- **Authority:** {cert.get('Certification_Authority', 'N/A')}")
                st.markdown(f"  **Details:** {cert.get('Certification_Details', 'N/A')}")
        else:
            st.info("No certifications found.")

    elif chunk_id == 6:
        # Expected: Programming_Language, Frameworks, Technologies
        prog_langs = chunk_data.get("Programming_Language", [])
        frameworks = chunk_data.get("Frameworks", [])
        technologies = chunk_data.get("Technologies", [])

        st.markdown("**Skills & Technologies:**")
        if prog_langs:
            st.markdown(f"- **Programming Languages:** {', '.join(prog_langs)}")
        if frameworks:
            st.markdown(f"- **Frameworks/Tools:** {', '.join(frameworks)}")
        if technologies:
            st.markdown(f"- **Other Technologies:** {', '.join(technologies)}")
        if not (prog_langs or frameworks or technologies):
            st.info("No specific skills/technologies found.")
    else:
        st.warning(f"Unknown resume chunk type (ID: {chunk_id}).")

    st.markdown("---") # Separator for clarity
    time.sleep(0.5) # Small delay to make chunks visible


# --- Helper function for structured display of evaluation chunks ---
def display_evaluation_chunk(chunk_data: Dict[str, Any], chunk_id: int):

    if chunk_id == 1:
        # Expected: Scores and Qualification Status
        exp_score = chunk_data.get("Experience_Score", "N/A")
        skills_score = chunk_data.get("Skills_Score", "N/A")
        edu_score = chunk_data.get("Education_Score", "N/A")
        overall_score = chunk_data.get("Overall_Score", "N/A")
        match_jd = chunk_data.get("Match with JD", "N/A")
        status = chunk_data.get("qualification_status", "N/A")

        st.markdown("**Evaluation Scores:**")
        st.write(f"- Experience Score: **{exp_score}/10**")
        st.write(f"- Skills Score: **{skills_score}/10**")
        st.write(f"- Education Score: **{edu_score}/10**")
        st.write(f"- Overall Score: **{overall_score}/10**")
        st.write(f"- Match with JD: **{match_jd}**")
        if status == "Qualified":
            st.success(f"**Qualification Status:** {status}")
        else:
            st.error(f"**Qualification Status:** {status}")

    elif chunk_id == 2:
        # Expected: Pros, Cons
        pros = chunk_data.get("Pros", [])
        cons = chunk_data.get("Cons", [])

        col_pros, col_cons = st.columns(2)
        with col_pros:
            st.success("##### Strengths (Pros)")
            if pros:
                for p in pros:
                    st.write(f"- {p}")
            else:
                st.info("No specific strengths identified.")
        with col_cons:
            st.warning("##### Areas for Improvement (Cons)")
            if cons:
                for c in cons:
                    st.write(f"- {c}")
            else:
                st.info("No specific weaknesses identified.")

    elif chunk_id == 3:
        # Expected: Skills Match, Skills not matching with JD, Extra skills
        skills_match = chunk_data.get("Skills Match", [])
        skills_not_matching = chunk_data.get("Skills not matching with JD", [])
        extra_skills = chunk_data.get("Extra skills", [])

        st.markdown("**Detailed Skill Analysis:**")
        if skills_match:
            st.markdown(f"- **Matching Skills:** {', '.join(skills_match)}")
        if skills_not_matching:
            st.markdown(f"- **Missing JD Skills:** {', '.join(skills_not_matching)}")
        if extra_skills:
            st.markdown(f"- **Additional Skills:** {', '.join(extra_skills)}")
        if not (skills_match or skills_not_matching or extra_skills):
            st.info("No detailed skill analysis available.")
    else:
        st.warning(f"Unknown evaluation chunk type (ID: {chunk_id}).")

    st.markdown("---") # Separator for clarity
    time.sleep(0.5) # Small delay to make chunks visible


# --- Modified backend communication functions ---

def upload_resume(file) -> Optional[Dict[str, Any]]:
    try:
        file.seek(0)
        files = {"resume_file": (file.name, file.getvalue(), file.type)}
        upload_response = requests.post(f"{BACKEND_URL}/upload_resume_file", files=files)

        if upload_response.status_code == 200 and upload_response.json().get("message") == "Resume uploaded successfully":
            st.success("Resume uploaded successfully!")
            st.subheader("Live Resume Parsing Progress:")
            st.info("Displaying parsed resume sections as they arrive from the backend...")

            stream_url = f"{BACKEND_URL}/resume_parser"
            params = {"resume_path": file.name}

            merged_json = {}
            decoder = json.JSONDecoder()
            buffer = ""
            chunk_count = 0

            with requests.get(stream_url, params=params, stream=True, timeout=180) as resp:
                resp.raise_for_status()

                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.strip():
                        continue

                    buffer += line.strip()

                    while buffer:
                        try:
                            parsed_obj, idx = decoder.raw_decode(buffer)
                            merged_json.update(parsed_obj)
                            buffer = buffer[idx:].lstrip()
                            chunk_count += 1

                            # --- Call helper function to display parsed resume chunk ---
                            display_parsed_resume_chunk(parsed_obj, chunk_count)

                        except json.JSONDecodeError:
                            break
                        except Exception as e:
                            st.warning(f"Error decoding JSON chunk during parsing: {e} - Line: '{line.strip()}'")
                            buffer = ""
                            break

            st.success("Resume parsing complete!")
            return merged_json

        else:
            st.error(f"Upload failed: {upload_response.status_code} - {upload_response.text}")
            return None

    except requests.exceptions.RequestException as req_err:
        st.error(f"Network or backend error during upload/parsing: {req_err}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during upload/parsing: {str(e)}")
        return None

def evaluate_resume(parsed_data: Dict[str, Any], jd_path: str) -> Optional[Dict[str, Any]]:
    """Send evaluation request to backend"""
    try:
        if not parsed_data:
            st.warning("No parsed resume data available for evaluation.")
            return None

        payload = {
            "resume_json": parsed_data,
            "jd_path": jd_path
        }

        st.subheader("Live Evaluation Progress:")
        st.info("Displaying evaluation results as they arrive from the backend...")

        merged_json = {}
        decoder = json.JSONDecoder()
        buffer = ""
        chunk_count = 0

        with requests.post(f"{BACKEND_URL}/evaluate_resume", json=payload, stream=True, timeout=180) as resp:
            resp.raise_for_status()

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.strip():
                    continue

                buffer += line.strip()

                while buffer:
                    try:
                        parsed_obj, idx = decoder.raw_decode(buffer)
                        merged_json.update(parsed_obj)
                        buffer = buffer[idx:].lstrip()
                        chunk_count += 1

                        # --- Call helper function to display evaluation chunk ---
                        display_evaluation_chunk(parsed_obj, chunk_count)

                    except json.JSONDecodeError:
                        break
                    except Exception as e:
                        st.warning(f"Error decoding JSON chunk during evaluation: {e} - Line: '{line.strip()}'")
                        buffer = ""
                        break

        st.success("Resume evaluation complete!")
        return merged_json
    except requests.exceptions.RequestException as req_err:
        st.error(f"Network or backend error during evaluation: {req_err}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during evaluation: {str(e)}")
        return None

# --- Streamlit Frontend (main app structure remains the same) ---
st.set_page_config(layout="wide", page_title="Resume Analyzer")

st.title("Resume Analyzer and Evaluator")

# Session state to store parsed and evaluated data
if 'parsed_resume' not in st.session_state:
    st.session_state.parsed_resume = None
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = None

# --- Section 1: Upload Resume ---
st.header("1. Upload Resume")
uploaded_file = st.file_uploader("Choose a resume file (PDF, DOCX)", type=["pdf", "docx"])

if uploaded_file is not None:
    if st.button("Upload and Parse Resume"):
        with st.spinner("Uploading and parsing..."):
            st.session_state.parsed_resume = upload_resume(uploaded_file)
            st.session_state.evaluation_results = None # Clear previous evaluation if new resume uploaded


# --- Section 2: Provide Job Description ---
st.header("2. Provide Job Description")
jd_path = st.text_input("Enter Job Description Path (e.g., 'data/jds/software_engineer.txt')", value="data/jds/software_engineer.txt")


# --- Section 3: Evaluate Resume against JD ---
st.header("3. Evaluate Resume against JD")
if st.session_state.parsed_resume is not None and jd_path:
    if st.button("Evaluate Resume"):
        with st.spinner("Evaluating..."):
            st.session_state.evaluation_results = evaluate_resume(st.session_state.parsed_resume, jd_path)

            if st.session_state.evaluation_results:
                st.subheader("Final Resume Evaluation Results Summary")
                # Removed the "View Raw Evaluation JSON" expander
                # If you want to keep it for debugging, you can re-add it:
                # with st.expander("View Full Evaluation JSON (for debugging)"):
                #    st.json(st.session_state.evaluation_results)

                # Display Overall Scores
                overall_score = st.session_state.evaluation_results.get('Overall_Score', None)
                match_with_jd = st.session_state.evaluation_results.get('Match with JD', None)
                qualification_status = st.session_state.evaluation_results.get('qualification_status', None)

                if overall_score is not None and match_with_jd is not None:
                    col_score1, col_score2, col_score3 = st.columns(3)
                    with col_score1:
                        st.metric(label="Overall Score (0-10)", value=overall_score)
                    with col_score2:
                        st.metric(label="Match with JD", value=match_with_jd)
                    with col_score3:
                        if qualification_status == "Qualified":
                            st.success(f"**Status:** {qualification_status}")
                        else:
                            st.error(f"**Status:** {qualification_status}")

                # Display individual scores
                st.markdown("---")
                st.markdown("#### Detailed Scores ")
                col_ind_score1, col_ind_score2, col_ind_score3 = st.columns(3)
                with col_ind_score1:
                    st.metric(label="Experience Score (0-10)", value=st.session_state.evaluation_results.get('Experience_Score', 'N/A'))
                with col_ind_score2:
                    st.metric(label="Skills Score (0-10)", value=st.session_state.evaluation_results.get('Skills_Score', 'N/A'))
                with col_ind_score3:
                    st.metric(label="Education Score (0-10)", value=st.session_state.evaluation_results.get('Education_Score', 'N/A'))

                # Display Pros and Cons
                st.markdown("---")
                st.markdown("#### Strengths and Areas for Improvement ")
                pros = st.session_state.evaluation_results.get('Pros', [])
                cons = st.session_state.evaluation_results.get('Cons', [])

                col_pros, col_cons = st.columns(2)
                with col_pros:
                    st.success("##### Strengths (Pros)")
                    if pros:
                        for p in pros:
                            st.write(f"- {p}")
                    else:
                        st.info("No specific strengths identified.")
                with col_cons:
                    st.warning("##### Areas for Improvement (Cons)")
                    if cons:
                        for c in cons:
                            st.write(f"- {c}")
                    else:
                        st.info("No specific weaknesses identified.")

                # Display Skills Match
                st.markdown("---")
                st.markdown("#### Skills Match Analysis ")
                skills_match = st.session_state.evaluation_results.get('Skills Match', [])
                skills_not_matching = st.session_state.evaluation_results.get('Skills not matching with JD', [])
                extra_skills = st.session_state.evaluation_results.get('Extra skills', [])

                if skills_match:
                    st.markdown("**Matching Skills:**")
                    st.write(", ".join(skills_match))
                else:
                    st.info("No direct skill matches found.")

                if skills_not_matching:
                    st.markdown("**Skills Required by JD but Missing:**")
                    st.warning(", ".join(skills_not_matching))
                else:
                    st.success("Candidate possesses all required skills (based on analysis).")

                if extra_skills:
                    st.markdown("**Additional Skills Candidate Has:**")
                    st.info(", ".join(extra_skills))
                else:
                    st.info("No additional skills beyond JD requirements identified.")

            else:
                st.session_state.evaluation_results = None
elif st.session_state.parsed_resume is None:
    st.warning("Please upload and parse a resume first to proceed with evaluation.")
else:
    st.info("Enter a Job Description path and click 'Evaluate Resume'.")