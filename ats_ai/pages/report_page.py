import time
from typing import Any, Dict

import streamlit as st


# --- Helper functions (copy-pasted from app.py for self-containment and consistency) ---
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


def display_final_evaluation_results(evaluation_results):
    """Display the final evaluation results summary"""
    st.subheader(" Final Resume Evaluation Results Summary")

    # === Overall Scores ===
    eval_summary = evaluation_results.get("Evaluation_Summary", {})
    match_with_jd = eval_summary.get("Match_Percentage", "N/A").strip()
    qualification_status = eval_summary.get("Qualification_Status", "N/A")
    exp_score = eval_summary.get("Experience_Score", "N/A")
    skills_score = eval_summary.get("Skills_Score", "N/A")
    edu_score = eval_summary.get("Education_Score", "N/A")
    projects_score = eval_summary.get("Projects_Score", "N/A")  # Added projects score
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
        st.info(",\n".join(skills_match))
    else:
        st.warning("No direct skill matches found.")

    if skills_not_matching:
        st.markdown("**Missing Skills (from JD):**")
        st.warning(",\n ".join(skills_not_matching))

    if extra_skills:
        st.markdown("**Extra Skills (beyond JD):**")
        st.info(",\n ".join(extra_skills))
    else:
        st.info("No additional skills beyond JD requirements identified.")

    # === Key Considerations ===
    st.markdown("---")
    st.markdown("#### Key Considerations")

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


# --- Report Page Logic ---
st.set_page_config(layout="wide", page_title="Resume Evaluation Report")

st.title("Resume Evaluation Report")

# Retrieve data from session state
# Corrected: Use 'report_personal_details' to get the name consistently
evaluation_results = st.session_state.get("report_evaluation_results")
parsed_resume = st.session_state.get("report_parsed_resume")
personal_details = st.session_state.get("report_personal_details", {})  # Get the personal details dict
candidate_name = personal_details.get("Name", "N/A")  # Extract name from personal_details

if evaluation_results and parsed_resume:
    st.header(f"Report for: {candidate_name}")
    st.markdown("---")

    ## Evaluation Summary
    display_final_evaluation_results(evaluation_results)

    st.markdown("---")

    ## Parsed Resume Details
    st.header("Parsed Resume Details")
    with st.expander("View Full Parsed Resume (Click to Expand)"):
        # Corrected: Directly call display_parsed_resume_in_markdown
        display_parsed_resume_in_markdown(parsed_resume)
else:
    st.warning("No report data available. Please go back to the main page and perform an evaluation.")

st.markdown("---")
if st.button("⬅️ Back to Main Page"):
    st.switch_page("test_frontend.py")
