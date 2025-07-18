"""Testing out the new frontend changes."""
import os
import uuid

import streamlit as st
import requests
import json
from typing import Optional, Dict, Any
import time
from streamlit.runtime.scriptrunner import add_script_run_ctx

# Assuming these are defined in your project or passed as environment variables
BACKEND_URL = "http://localhost:8000"

JD_OPTIONS = {
    "Select a pre-existing JD": "Select a pre-existing JD",
    "Senior Python Development Engineer": "SrPDE.json",
    "Oracle ERP": "OracleERP.json",
    "Data Architect" : "DataArchJD.json",
    "Senior Full Stack Engineer": "SeniorFullStackEngineer_Python.json"
}


# --- Helper function for structured display of parsed resume chunks ---
def display_parsed_resume_chunk(chunk_data: Dict[str, Any], chunk_id: int):
    """
        This helper now accepts the full parsed_resume_data and extracts relevant parts
        based on the chunk_id for structured display.
    """

    if chunk_id == 1:
        # Expected: Name, Contact_Details, Github_Repo, LinkedIn
        name = chunk_data.get("Name", "N/A")
        contact = chunk_data.get("Contact_Details", {})
        mobile = contact.get("Mobile_No", "N/A")
        email = contact.get("Email", "N/A")
        github = chunk_data.get("Github_Repo", "N/A")
        linkedin = chunk_data.get("LinkedIn", "N/A")

        st.markdown(f"<h4>{name}</h4", unsafe_allow_html=True)
        st.markdown(f"**Contact:** Mobile: {mobile}, </br>Email: {email}", unsafe_allow_html=True)
        st.markdown(f"**Profiles:** GitHub: {github}, </br>LinkedIn: {linkedin}", unsafe_allow_html=True)

    elif chunk_id == 2:
        # Expected: Education
        education_list = chunk_data.get("Education", [])
        if education_list:
            st.markdown("<h4>Education:</h4>", unsafe_allow_html=True)
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
            st.markdown("<h4>Professional Experience:</h4>", unsafe_allow_html=True)
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
            st.markdown("<h4>Projects:</h4>", unsafe_allow_html=True)
            for proj in projects_list:
                st.markdown(f"- **Project Name:** {proj.get('Project_Name', 'N/A')}")
                st.markdown(f"  **Description:** {proj.get('Project_Description', 'N/A')}")
        else:
            st.info("No projects found.")

    elif chunk_id == 5:
        # Expected: Certifications
        certifications_list = chunk_data.get("Certifications", [])
        if certifications_list:
            st.markdown("<h4>Certifications:</h4>", unsafe_allow_html=True)
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

        st.markdown("<h4>Skills & Technologies:</h4>", unsafe_allow_html=True)
        if prog_langs:
            st.markdown(f"- **Programming Languages:** {', '.join(prog_langs)}")
        if frameworks:
            st.markdown(f"- **Frameworks/Tools:** {', '.join(frameworks)}")
        if technologies:
            st.markdown(f"- **Other Technologies:** {', '.join(technologies)}")
        if not (prog_langs or frameworks or technologies):
            st.info("No specific skills/technologies found.")
    else:
        st.write("CHUNK ID", chunk_id)
        st.warning(f"Unknown resume chunk type (ID: {chunk_id}).")

    # st.markdown("---")


# --- Helper function for structured display of evaluation chunks ---
def display_evaluation_chunk(chunk_data: Dict[str, Any], chunk_id: int):

    if chunk_id == 1:
        # Expected: Scores and Qualification Status
        exp_score = chunk_data.get("Experience_Score", "N/A")
        skills_score = chunk_data.get("Skills_Score", "N/A")
        edu_score = chunk_data.get("Education_Score", "N/A")
        overall_score = chunk_data.get("Overall_Score", "N/A")
        match_jd = chunk_data.get("Match with JD", "N/A").strip()
        status = chunk_data.get("qualification_status", "N/A")


        if not match_jd or match_jd is "NA" or match_jd is "0%":
            exp_score = skills_score = edu_score = overall_score = "N/A"


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
            st.markdown(f"- **Matching Skills:** {',  '.join(skills_match)}")
        if skills_not_matching:
            st.markdown(f"- **Missing JD Skills:** {',  '.join(skills_not_matching)}")
        if extra_skills:
            st.markdown(f"- **Additional Skills:** {',  '.join(extra_skills)}")
        if not (skills_match or skills_not_matching or extra_skills):
            st.info("No detailed skill analysis available.")
    else:
        st.warning(f"Unknown evaluation chunk type (ID: {chunk_id}).")

    st.markdown("---")
    time.sleep(0.5)


# --- Function to display final evaluation results ---
def display_final_evaluation_results(evaluation_results):
    """Display the final evaluation results summary"""
    st.subheader("Final Resume Evaluation Results Summary")

    # Display Overall Scores
    # overall_score = evaluation_results.get('Overall_Score', None)
    match_with_jd = evaluation_results.get('Match with JD', None).strip()
    qualification_status = evaluation_results.get('qualification_status', None)

    exp_score = evaluation_results.get('Experience_Score', 'N/A')
    skills_score = evaluation_results.get('Skills_Score', 'N/A')
    edu_score = evaluation_results.get('Education_Score', 'N/A')

    if not match_with_jd or match_with_jd is "NA" or match_with_jd is "0%":
        exp_score = skills_score = edu_score = 'N/A'
        overall_score = 'N/A'

    overall_score = evaluation_results.get('Overall_Score', 'N/A')

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
        st.metric(label="Experience Score (0-10)", value=exp_score)
    with col_ind_score2:
        st.metric(label="Skills Score (0-10)", value=skills_score)
    with col_ind_score3:
        st.metric(label="Education Score (0-10)", value=edu_score)


    # Display Pros and Cons
    st.markdown("---")
    st.markdown("#### Strengths and Areas for Improvement ")
    pros = evaluation_results.get('Pros', [])
    cons = evaluation_results.get('Cons', [])

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
    skills_match = evaluation_results.get('Skills Match', [])
    skills_not_matching = evaluation_results.get('Skills not matching with JD', [])
    extra_skills = evaluation_results.get('Extra skills', [])
    no_skill_match_flag = 0

    if skills_match:
        st.markdown("**Matching Skills:**")
        st.write(", ".join(skills_match))
    else:
        st.info("No direct skill matches found.")
        no_skill_match_flag = 1

    if skills_not_matching:
        st.markdown("**Skills Required by JD but Missing:**")
        st.warning(", ".join(skills_not_matching))
    elif no_skill_match_flag:
        st.success("No skill matches found.")

    if extra_skills:
        st.markdown("**Additional Skills Candidate Has:**")
        st.info(", ".join(extra_skills))
    else:
        st.info("No additional skills beyond JD requirements identified.")


# --- Modified backend communication functions ---
def upload_resume(file, live_parsing_status_placeholder) -> Optional[Dict[str, Any]]:
    st.session_state.parsed_resume_chunks = {} # Initialize to store chunks for expander display
    try:
        file.seek(0)
        files = {"resume_file": (file.name, file.getvalue(), file.type)}
        upload_response = requests.post(f"{BACKEND_URL}/upload_resume_file", files=files)

        if upload_response.status_code == 200 and upload_response.json().get("message") == "Resume uploaded successfully":
            live_parsing_status_placeholder.success("Resume uploaded successfully! Parsing in progress...")

            stream_url = f"{BACKEND_URL}/resume_parser"
            params = {"resume_path": file.name}

            merged_json = {}
            decoder = json.JSONDecoder()
            buffer = ""
            chunk_count = 0

            # Create an empty placeholder to update live parsing. This is where chunks will appear and then be cleared.
            live_parsing_display_placeholder = st.empty()


            with requests.get(stream_url, params=params, stream=True, timeout=180) as resp:
                resp.raise_for_status()

                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.strip():
                        continue

                    buffer += line.strip()
                    # st.write(buffer)

                    while "---END_OF_JSON_CHUNK--" in buffer:
                        buffer, _, remaining_buffer = buffer.partition("---END_OF_JSON_CHUNK--")

                    while buffer:
                        try:
                            parsed_obj, idx = decoder.raw_decode(buffer)
                            merged_json.update(parsed_obj)
                            buffer = buffer[idx:].lstrip()
                            chunk_count += 1

                            st.session_state.parsed_resume_chunks[chunk_count] = parsed_obj

                            # --- Display live parsing progress within the placeholder ---
                            with live_parsing_display_placeholder.container():
                                # st.subheader("Parsing results...")
                                # st.info("Displaying parsed resume sections as they arrive from the backend...")
                                display_parsed_resume_chunk(parsed_obj, chunk_count)
                            time.sleep(0.5)

                        except json.JSONDecodeError:
                            break
                        except Exception as e:
                            live_parsing_status_placeholder.warning(f"Error decoding JSON chunk during parsing: {e} - Line: '{line.strip()}'")
                            buffer = ""
                            break

            live_parsing_display_placeholder.empty() # Clear the live display after all chunks are received
            live_parsing_status_placeholder.success("Resume parsing complete! View details in the dropdown below.")
            return merged_json

        else:
            live_parsing_status_placeholder.error(f"Upload failed: {upload_response.status_code} - {upload_response.text}")
            return None

    except requests.exceptions.RequestException as req_err:
        live_parsing_status_placeholder.error(f"Network or backend error during upload/parsing: {req_err}")
        return None
    except Exception as e:
        live_parsing_status_placeholder.error(f"An unexpected error occurred during upload/parsing: {str(e)}")
        return None


def evaluate_resume(parsed_data: Dict[str, Any], jd_path: str, evaluation_status_placeholder) -> Optional[Dict[str, Any]]:
    """Send evaluation request to backend"""
    try:
        if not parsed_data:
            evaluation_status_placeholder.warning("No parsed resume data available for evaluation.")
            return None

        payload = {
            "resume_json": parsed_data,
            "jd_path": jd_path
        }

        evaluation_status_placeholder.info(f"Sending evaluation request with JD: `{jd_path}`....")

        # with st.expander("Payload sent to Backend (for debugging)"):
        #     st.json(payload)


        merged_json = {}
        decoder = json.JSONDecoder()
        buffer = ""
        chunk_count = 0

        live_evaluation_display_placeholder = st.empty()

        with requests.post(f"{BACKEND_URL}/evaluate_resume", json=payload, stream=True, timeout=180) as resp:
            resp.raise_for_status()

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.strip():
                    continue

                buffer += line.strip()

                while "---END_OF_JSON_CHUNK--" in buffer:
                    buffer, _, remaining_buffer = buffer.partition("---END_OF_JSON_CHUNK--")


                while buffer:
                    try:
                        parsed_obj, idx = decoder.raw_decode(buffer)
                        merged_json.update(parsed_obj)
                        buffer = buffer[idx:].lstrip()
                        chunk_count += 1

                        # --- Call helper function to display evaluation chunk ---
                        with live_evaluation_display_placeholder.container():
                            st.subheader("Live Evaluation Progress:")
                            st.info("Displaying evaluation results as they arrive from the backend...")
                            display_evaluation_chunk(parsed_obj, chunk_count)
                        time.sleep(0.5)

                    except json.JSONDecodeError:
                        break
                    except Exception as e:
                        evaluation_status_placeholder.warning(f"Error decoding JSON chunk during evaluation: {e} - Line: '{line.strip()}'")
                        buffer = ""
                        break

            if st.session_state.temp_jd_path and os.path.exists(st.session_state.temp_jd_path):
                try:
                    os.remove(st.session_state.temp_jd_path)
                    evaluation_status_placeholder.success(
                        f"Cleaned up temporary JD file: `{os.path.basename(st.session_state.temp_jd_path)}`")
                    st.session_state.temp_jd_path = None
                except Exception as e:
                    evaluation_status_placeholder.warning(
                        f"Could not delete temporary JD file `{st.session_state.temp_jd_path}`: {e}")

        # Clear live evaluation display after completion
        live_evaluation_display_placeholder.empty()
        evaluation_status_placeholder.success("Resume evaluation complete!")

        return merged_json
    except requests.exceptions.RequestException as req_err:
        evaluation_status_placeholder.error(f"Network or backend error during evaluation: {req_err}")
        return None
    except Exception as e:
        evaluation_status_placeholder.error(f"An unexpected error occurred during evaluation: {str(e)}")
        return None

# --- Streamlit Frontend (main app structure remains the same) ---
st.set_page_config(layout="wide", page_title="Resume Analyzer")

st.title("Resume Analyzer and Evaluator")

# Session state to store parsed and evaluated data
if 'parsed_resume' not in st.session_state:
    st.session_state.parsed_resume = None
if 'parsed_resume_chunks' not in st.session_state:
    st.session_state.parsed_resume_chunks = {}
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = None
if 'show_jd_sections' not in st.session_state:
    st.session_state.show_jd_sections = False
if 'decision_made' not in st.session_state:
    st.session_state.decision_made = None
if 'temp_jd_path' not in st.session_state:
    st.session_state.temp_jd_path = None


# --- Section 1: Upload Resume ---
st.header("1. Upload Resume")
uploaded_file = st.file_uploader("Choose a resume file (PDF, DOCX)", type=["pdf", "docx"])

# Placeholder for messages during upload/parsing
parsing_status_messages = st.empty()

if uploaded_file is not None:
    if st.button("Display Resume"):
        # Clear states of previous sessions
        st.session_state.parsed_resume = None
        st.session_state.evaluation_results = None
        st.session_state.show_jd_sections = False
        st.session_state.parsed_resume_chunks = {}
        st.session_state.decision_made = None

        with st.spinner("Parsing for display..."):
            # Pass the placeholder to the upload_resume function
            parsed_data = upload_resume(uploaded_file, parsing_status_messages)
            st.session_state.parsed_resume = parsed_data

            if st.session_state.parsed_resume:
                st.session_state.show_jd_sections = True
            else:
                st.session_state.show_jd_sections = False


# --- Collapsible Parsed Resume Section ---
if st.session_state.parsed_resume:
    with st.expander("View Resume Information (Click to Expand)"):
        if st.session_state.parsed_resume_chunks:
            # Display chunks in order they were received for precise rendering
            for i in sorted(st.session_state.parsed_resume_chunks.keys()):
                display_parsed_resume_chunk(st.session_state.parsed_resume_chunks[i], i)

        # THIS PART WONT BE NEEDED
        else:
            st.warning("No detailed chunks stored, displaying full parsed resume JSON structure.")
            # Fallback if chunks weren't stored (e.g., direct assign for testing)
            # This part displays the full JSON structure by iterating over common sections.
            if st.session_state.parsed_resume.get("Name") or st.session_state.parsed_resume.get("Contact_Details"):
                display_parsed_resume_chunk(st.session_state.parsed_resume, 1)
            if st.session_state.parsed_resume.get("Education"):
                display_parsed_resume_chunk(st.session_state.parsed_resume, 2)
            if st.session_state.parsed_resume.get("Professional_Experience"):
                display_parsed_resume_chunk(st.session_state.parsed_resume, 3)
            if st.session_state.parsed_resume.get("Projects"):
                display_parsed_resume_chunk(st.session_state.parsed_resume, 4)
            if st.session_state.parsed_resume.get("Certifications"):
                display_parsed_resume_chunk(st.session_state.parsed_resume, 5)

            # For skills, combine and pass them as one logical chunk
            skills_data_for_display = {
                "Programming_Language": st.session_state.parsed_resume.get("Programming_Language", []),
                "Frameworks": st.session_state.parsed_resume.get("Frameworks", []),
                "Technologies": st.session_state.parsed_resume.get("Technologies", [])
            }
            if skills_data_for_display["Programming_Language"] or \
               skills_data_for_display["Frameworks"] or \
               skills_data_for_display["Technologies"]:
                 display_parsed_resume_chunk(skills_data_for_display, 6)

        st.markdown("---")


# --- Section 2 & 3: Conditional Display ---
if st.session_state.show_jd_sections:
    # --- Section 2: Provide Job Description ---
    st.header("2. Provide Job Description")

    custom_jd_text = st.text_area(
        "Paste a Job Description here:",
        height=80,
        help="Paste the full job description. If text is entered here, it will be used instead of the dropdown selection."
    )

    # Create a dropdown for JD options
    selected_jd_display = st.selectbox(
        "Or Select a Job Description:",
        options=list(JD_OPTIONS.keys()),
        index=0  # Default to the first option
    )

    # Map the selected display option to its actual JD path
    jd_path = JD_OPTIONS[selected_jd_display]
    st.session_state.temp_jd_path = None

    # st.info(f"Selected JD path: `{jd_path}`")

    if custom_jd_text is not None and len(custom_jd_text.strip()) > 50:
        # WE NEED TO SAVE THE ADDED JD IN TEXT FORMAT TO PROPER JSON FILE FOR EVALUATION
        # THIS STEP DOES NOT REQUIRE CHANGES TO BE MADE AT THE BACKEND.
        rand_filename = str(uuid.uuid4())[:8] + ".json"

        jd_path = "../jd_json/"+rand_filename

        temp_jd_content = {'job_description': custom_jd_text}
        with open(jd_path, 'w') as f:
            json.dump(temp_jd_content, f, indent=4)

        st.session_state.temp_jd_path = jd_path
        st.info("Detected JD in Text Format...")

    elif selected_jd_display != "Select a pre-existing JD":
        jd_path = JD_OPTIONS[selected_jd_display]
        st.info(f"Selected JD path: `{jd_path}`")
    else:
        st.info("Please paste a JD or select one in the dropdown.")

    # --- Section 3: Evaluate Resume against JD ---
    st.header("3. Evaluate Resume against JD")

    # Placeholder for messages during evaluation
    evaluation_status_messages = st.empty()

    if st.session_state.parsed_resume is not None and jd_path and jd_path != "Select a pre-existing JD":
        if st.button("Evaluate Resume"):
            # Clear previous decision when re-evaluating
            st.session_state.decision_made = None

            with st.spinner("Evaluating..."):
                # Pass the placeholder to the evaluate_resume function
                st.session_state.evaluation_results = evaluate_resume(st.session_state.parsed_resume, jd_path, evaluation_status_messages)

    elif st.session_state.parsed_resume is None:
        evaluation_status_messages.warning("Please upload and parse a resume first to proceed with evaluation.")
    else:
        evaluation_status_messages.info("Select a Job Description and click 'Evaluate Resume'.")


# --- Display Final Evaluation Results (Outside of button logic) ---
if st.session_state.evaluation_results:
    display_final_evaluation_results(st.session_state.evaluation_results)
    # st.json(st.session_state.parsed_resume)

    # Accept/Reject buttons
    candidate_name = st.session_state.parsed_resume.get("Name", "Unknown")

    # Display decision status if already made
    if st.session_state.decision_made:
        if st.session_state.decision_made == "Accept":
            st.success(f"✅ {candidate_name} has been marked as Accepted")
        else:
            st.warning(f"❌ {candidate_name} has been marked as Rejected")
    else:

        #SHOWN WHEN NO DECISION MADE YET
        col1, col2, col3 = st.columns([1, 1, 2]) # Added a third column for the report button

        with col1:
            if st.button("✅ Accept"):
                response = requests.post(f"{BACKEND_URL}/store_decision", params={
                    "name": candidate_name,
                    "decision": "Accept"
                })
                if response.status_code == 200:
                    st.session_state.decision_made = "Accept"
                    st.rerun()

        with col2:
            if st.button("❌ Reject"):
                response = requests.post(f"{BACKEND_URL}/store_decision", params={
                    "name": candidate_name,
                    "decision": "Reject"
                })
                if response.status_code == 200:
                    st.session_state.decision_made = "Reject"
                    st.rerun()

        with col3:
            # Generate Report Button
            if st.button("Generate Report 📄"):
                # Store data in session state for the report page
                st.session_state.report_evaluation_results = st.session_state.evaluation_results
                st.session_state.report_parsed_resume = st.session_state.parsed_resume
                st.session_state.report_candidate_name = candidate_name
                # Navigate to the report page
                st.switch_page("pages/report_page.py")

else:
    st.info("Upload and parse a resume above to unlock Job Description and Evaluation sections.")