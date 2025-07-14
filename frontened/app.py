import streamlit as st
import requests
import base64
import os

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="ATS Resume Matcher", layout="centered")
st.title("--------- AI Resume Matcher-------------------")

st.sidebar.header("About")
st.sidebar.info(
    "This application uses an AI-powered backend to score resumes against job descriptions, "
    "providing insights into skill and experience matches."

)

# --- Session State Initialization ---
if "uploaded_resume_name" not in st.session_state:
    st.session_state.uploaded_resume_name = None
if "resume_uploaded_successfully" not in st.session_state:
    st.session_state.resume_uploaded_successfully = False
if "match_result" not in st.session_state:
    st.session_state.match_result = None
if "action_status" not in st.session_state:
    st.session_state.action_status = ""
if "selected_jd_name" not in st.session_state:
    st.session_state.selected_jd_name = None

# --- 1. Upload Resume ---
st.header("Upload Resume (PDF)")
uploaded_file = st.file_uploader("Upload your resume", type=["pdf"])

if uploaded_file:
    if st.session_state.uploaded_resume_name != uploaded_file.name or not st.session_state.resume_uploaded_successfully:
        st.session_state.uploaded_resume_name = uploaded_file.name
        st.session_state.resume_uploaded_successfully = False

        file_bytes = uploaded_file.read()
        encoded_file_data = base64.b64encode(file_bytes).decode("utf-8")

        upload_payload = {
            "filename": uploaded_file.name,
            "file_data": encoded_file_data
        }
        try:
            res = requests.post(f"{BACKEND_URL}/upload-resume/", json=upload_payload)
            if res.status_code == 200:
                st.session_state.resume_uploaded_successfully = True
                st.session_state.match_result = None
                st.session_state.action_status = ""
                st.success(f" Resume '{uploaded_file.name}' uploaded successfully.")
            else:
                st.session_state.resume_uploaded_successfully = False
                st.error(f" Resume upload failed (Status: {res.status_code}): {res.text}")
        except requests.exceptions.ConnectionError:
            st.error(f" Could not connect to backend at {BACKEND_URL}")
        except Exception as e:
            st.error(f" Unexpected error during upload: {e}")
    else:
        st.info(f"Resume '{uploaded_file.name}' is already uploaded.")
else:
    if st.session_state.uploaded_resume_name:
        st.session_state.uploaded_resume_name = None
        st.session_state.resume_uploaded_successfully = False
        st.session_state.match_result = None
        st.session_state.action_status = ""

# --- 2. Select Job Description ---
st.header(" Select Job Description")
jd_list = []
try:
    with st.spinner("Fetching job descriptions..."):
        res = requests.get(f"{BACKEND_URL}/list-jds/")
        jd_list = res.json().get("jd_list", [])
        if not jd_list:
            st.warning(" No JDs found in backend. Add files to `jds/`.")
except Exception as e:
    st.error(f"Error fetching JDs: {e}")

selected_jd = st.selectbox("Choose JD", jd_list, key="jd_selector",
                           index=jd_list.index(st.session_state.selected_jd_name) if st.session_state.selected_jd_name in jd_list else (0 if jd_list else None))

if selected_jd != st.session_state.selected_jd_name:
    st.session_state.selected_jd_name = selected_jd
    st.session_state.match_result = None
    st.session_state.action_status = ""

# --- 3. Generate ATS Score ---
st.header(" Generate ATS Score")

if st.session_state.resume_uploaded_successfully and st.session_state.uploaded_resume_name and selected_jd:
    if st.button(" Run ATS Matching"):
        with st.spinner("Analyzing resume against JD..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/match/",
                    json={
                        "jd_filename": selected_jd,
                        "resume_filename": st.session_state.uploaded_resume_name
                    }
                )
                if response.status_code == 200:
                    st.session_state.match_result = response.json()
                    st.success(" Matching complete!")
                else:
                    st.error(f" Backend error: {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f" Failed to match: {e}")
else:
    if not st.session_state.resume_uploaded_successfully:
        st.info("Please upload a resume first.")
    elif not selected_jd:
        st.info("Please select a Job Description.")

# --- Display Results ---
if st.session_state.match_result:
    result = st.session_state.match_result
    candidate_name = result.get("name", "Unknown")

    st.header(" ATS Result")
    st.subheader(f" Candidate: {candidate_name}")

    st.markdown(f"**Resume File:** `{st.session_state.uploaded_resume_name}`")
    st.markdown(f"**Job Description:** `{st.session_state.selected_jd_name}`")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Skill Score", result.get("skill_score", "NA"))
    with col2:
        st.metric("Experience Score", result.get("experience_score", "NA"))
    with col3:
        st.metric("Match Score", result.get("match_score", "0%"))
    with col4:
        st.metric("CGPA", result.get("cgpa", "Not given"))

    col5, col6 = st.columns(2)
    with col5:
        linkedin = result.get("linkedin", "")
        if linkedin:
            st.markdown(f"[ LinkedIn Profile]({linkedin})")
    with col6:
        github = result.get("github", "")
        if github:
            st.markdown(f"[ GitHub Profile]({github})")

    st.markdown("---")
    st.subheader(" Skills Breakdown")
    col1_skills, col2_skills, col3_skills = st.columns(3)
    with col1_skills:
        st.write(" Matched Skills")
        for skill in result.get("matched_skills", []) or ["NA"]:
            st.markdown(f"- {skill}")
    with col2_skills:
        st.write(" Missing Skills")
        for skill in result.get("missing_skills", []) or ["NA"]:
            st.markdown(f"- {skill}")
    with col3_skills:
        st.write(" Extra Skills")
        for skill in result.get("extra_skills", []) or ["NA"]:
            st.markdown(f"- {skill}")

    st.markdown("---")
    st.subheader(" LLM Feedback")
    col_pos, col_neg = st.columns(2)
    with col_pos:
        st.write(" Strengths")
        for point in result.get("positive", []) or ["NA"]:
            st.markdown(f"- {point}")
    with col_neg:
        st.write(" Areas for Improvement")
        for point in result.get("negative", []) or ["NA"]:
            st.markdown(f"- {point}")

    st.markdown("---")
    st.subheader(" Take Action")
    col_select, col_reject = st.columns(2)

    with col_select:
        if st.button("✔ Select Candidate", key="select_button"):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/store-selection/",
                    json={
                        "resume_file": st.session_state.uploaded_resume_name,
                        "jd_file": st.session_state.selected_jd_name,
                        "status": "select",
                        "match_score": result.get("match_score", "0%"),
                        "linkedin": result.get("linkedin", ""),
                        "github": result.get("github", ""),
                        "name": candidate_name
                    }
                )
                if resp.status_code == 200:
                    st.session_state.action_status = f" Candidate `{candidate_name}` has been selected!"
                else:
                    st.session_state.action_status = f" Selection failed: {resp.text}"
            except Exception as e:
                st.session_state.action_status = f" Selection error: {e}"

    with col_reject:
        if st.button(" Reject Candidate", key="reject_button"):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/store-selection/",
                    json={
                        "resume_file": st.session_state.uploaded_resume_name,
                        "jd_file": st.session_state.selected_jd_name,
                        "status": "reject",
                        "match_score": result.get("match_score", "0%"),
                        "name": candidate_name
                    }
                )
                if resp.status_code == 200:
                    st.session_state.action_status = f" Candidate `{candidate_name}` has been rejected."
                else:
                    st.session_state.action_status = f" Rejection failed: {resp.text}"
            except Exception as e:
                st.session_state.action_status = f" Rejection error: {e}"

# --- Status Message ---
if st.session_state.action_status:
    if "selected" in st.session_state.action_status.lower():
        st.success(st.session_state.action_status)
    elif "rejected" in st.session_state.action_status.lower():
        st.warning(st.session_state.action_status)
    else:
        st.error(st.session_state.action_status)
