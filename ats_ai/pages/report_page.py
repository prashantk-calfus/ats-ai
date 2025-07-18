import streamlit as st
from typing import Dict, Any
import time

# --- Helper functions (copy-pasted from app.py for self-containment) ---
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
        st.warning(f"Unknown resume chunk type (ID: {chunk_id}).")


def display_final_evaluation_results(evaluation_results):
    """Display the final evaluation results summary"""
    st.subheader("Final Resume Evaluation Results Summary")

    # Display Overall Scores
    overall_score = evaluation_results.get('Overall_Score', None)
    match_with_jd = evaluation_results.get('Match with JD', None)
    qualification_status = evaluation_results.get('qualification_status', None)

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
        st.metric(label="Experience Score (0-10)", value=evaluation_results.get('Experience_Score', 'N/A'))
    with col_ind_score2:
        st.metric(label="Skills Score (0-10)", value=evaluation_results.get('Skills_Score', 'N/A'))
    with col_ind_score3:
        st.metric(label="Education Score (0-10)", value=evaluation_results.get('Education_Score', 'N/A'))

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

# --- Report Page Logic ---
st.set_page_config(layout="wide", page_title="Resume Evaluation Report")

st.title("Resume Evaluation Report")

# Retrieve data from session state
evaluation_results = st.session_state.get('report_evaluation_results')
parsed_resume = st.session_state.get('report_parsed_resume')
candidate_name = st.session_state.get('report_candidate_name', 'N/A')

if evaluation_results and parsed_resume:
    st.header(f"Report for: {candidate_name}")
    st.markdown("---")

    ## Evaluation Summary
    display_final_evaluation_results(evaluation_results)

    st.markdown("---")

    ## Parsed Resume Details
    st.header("Parsed Resume Details")
    with st.expander("View Full Parsed Resume (Click to Expand)"):
        # Display chunks in order they were received for precise rendering
        if 'parsed_resume_chunks' in st.session_state and st.session_state.parsed_resume_chunks:
            for i in sorted(st.session_state.parsed_resume_chunks.keys()):
                display_parsed_resume_chunk(st.session_state.parsed_resume_chunks[i], i)
        else:
            st.warning("No detailed chunks stored, displaying full parsed resume JSON structure.")
            # Fallback if chunks weren't stored (e.g., direct assign for testing)
            if parsed_resume.get("Name") or parsed_resume.get("Contact_Details"):
                display_parsed_resume_chunk(parsed_resume, 1)
            if parsed_resume.get("Education"):
                display_parsed_resume_chunk(parsed_resume, 2)
            if parsed_resume.get("Professional_Experience"):
                display_parsed_resume_chunk(parsed_resume, 3)
            if parsed_resume.get("Projects"):
                display_parsed_resume_chunk(parsed_resume, 4)
            if parsed_resume.get("Certifications"):
                display_parsed_resume_chunk(parsed_resume, 5)

            skills_data_for_display = {
                "Programming_Language": parsed_resume.get("Programming_Language", []),
                "Frameworks": parsed_resume.get("Frameworks", []),
                "Technologies": parsed_resume.get("Technologies", [])
            }
            if skills_data_for_display["Programming_Language"] or \
               skills_data_for_display["Frameworks"] or \
               skills_data_for_display["Technologies"]:
                 display_parsed_resume_chunk(skills_data_for_display, 6)

else:
    st.warning("No report data available. Please go back to the main page and perform an evaluation.")

st.markdown("---")
if st.button("⬅️ Back to Main Page"):
    st.switch_page("test_frontend.py")