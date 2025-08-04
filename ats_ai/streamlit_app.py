import json
import os
import time

import pymupdf
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/")

st.set_page_config(layout="wide", page_title="ATS AI")
st.title("ATS AI : Intelligent Resume Screening")

# Initialize all session state variables
if "parsed_data_combined" not in st.session_state:
    st.session_state.parsed_data_combined = None
if "decision_made" not in st.session_state:
    st.session_state.decision_made = None
if "uploaded_resume_name" not in st.session_state:
    st.session_state.uploaded_resume_name = None

if "report_evaluation_results" not in st.session_state:
    st.session_state.report_evaluation_results = None
if "report_parsed_resume" not in st.session_state:
    st.session_state.report_parsed_resume = None
if "report_cand_name" not in st.session_state:
    st.session_state.report_cand_name = None

# Initialize JD text input state
if "jd_text_input" not in st.session_state:
    st.session_state.jd_text_input = ""
if "jd_name_input" not in st.session_state:
    st.session_state.jd_name_input = ""
if "clear_jd_form" not in st.session_state:
    st.session_state.clear_jd_form = False

# NEW: Initialize JD change tracking variables
if "current_selected_jd" not in st.session_state:
    st.session_state.current_selected_jd = None
if "current_jd_text" not in st.session_state:
    st.session_state.current_jd_text = ""
if "current_jd_name" not in st.session_state:
    st.session_state.current_jd_name = ""

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

# JD Selection Section with Tabs
st.header("Job Description")

tab1, tab2 = st.tabs(["📋 Select Existing JD", "💾 Add New JD"])

jd_content = None
jd_source = None

with tab1:
    st.info("Select from previously saved Job Descriptions")

    # Fetch existing JDs from backend
    try:
        response = requests.get(f"{BACKEND_URL}/list_jds")
        if response.status_code == 200:
            existing_jds_response = response.json()
            existing_jds = existing_jds_response.get("jds", [])
            jd_options = ["Select a pre-existing JD"] + existing_jds
            selected_jd_display = st.selectbox("Choose a Job Description:", options=jd_options, index=0, key="jd_dropdown")

            if selected_jd_display != "Select a pre-existing JD":
                # NEW: Check if JD selection has changed
                if st.session_state.get("current_selected_jd") != selected_jd_display:
                    st.session_state.current_selected_jd = selected_jd_display
                    # Reset evaluation state when JD changes
                    st.session_state.parsed_data_combined = None
                    st.session_state.decision_made = None
                    st.session_state.report_evaluation_results = None
                    st.session_state.report_parsed_resume = None
                    st.session_state.report_cand_name = None

                # Load the selected JD file
                try:
                    jd_filename = f"{selected_jd_display}.json"
                    jd_path = os.path.join("jd_json", jd_filename)
                    # st.write(os.getcwd())
                    # st.write(jd_path)
                    if os.path.exists(jd_path):
                        with open(jd_path, "r") as f:
                            jd_content = json.load(f)
                        jd_source = f"Selected JD: {selected_jd_display}"
                    else:
                        st.warning(f"JD file not found locally: {jd_filename}")
                except Exception as e:
                    st.error(f"Error loading selected JD: {str(e)}")

                # Add the main evaluate button here inside tab1
                if selected_jd_display != "Select a pre-existing JD" and st.session_state.uploaded_resume_name:
                    st.markdown("---")
                    # Show re-evaluation message if already evaluated
                    if st.session_state.parsed_data_combined is not None:
                        st.info("🔄 Click to re-evaluate with the current JD selection")

                    if st.button("🚀 Evaluate", key="main_evaluate_btn"):
                        # Reset previous results before new evaluation
                        st.session_state.parsed_data_combined = None
                        st.session_state.decision_made = None
                        st.session_state.report_evaluation_results = None
                        st.session_state.report_parsed_resume = None
                        st.session_state.report_cand_name = None

                        with st.spinner("Processing resume and evaluating..."):
                            try:
                                # Read resume text
                                resume_pdf_reader = pymupdf.open(stream=uploaded_resume.getvalue(), filetype="pdf")
                                resume_text = ""
                                for i in range(resume_pdf_reader.page_count):
                                    page = resume_pdf_reader.load_page(i)
                                    resume_text += page.get_text()

                                # Upload resume file
                                files = {"resume_file": (uploaded_resume.name, uploaded_resume.getvalue(), uploaded_resume.type)}
                                upload_response = requests.post(f"{BACKEND_URL}/upload_resume_file", files=files)

                                if upload_response.status_code != 200:
                                    st.error(f"Failed to upload resume to backend: {upload_response.status_code} - {upload_response.text}")
                                    st.session_state.parsed_data_combined = None
                                    st.session_state.decision_made = None
                                else:
                                    if jd_content:
                                        combined_json = {"resume_data": resume_text, "jd_json": jd_content}
                                        response = requests.post(f"{BACKEND_URL}/parse_and_evaluate", json=combined_json)

                                        if response.status_code == 200:
                                            st.session_state.parsed_data_combined = response.json()
                                        else:
                                            st.error(f"Evaluation failed: {response.status_code} - {response.text}")
                                            st.session_state.parsed_data_combined = None
                                            st.session_state.decision_made = None
                                    else:
                                        st.error("Failed to process Job Description")
                            except Exception as e:
                                st.error(f"An error occurred during evaluation: {e}")
                                st.session_state.parsed_data_combined = None
                                st.session_state.decision_made = None
            else:
                # Reset when no JD is selected
                if st.session_state.get("current_selected_jd") is not None:
                    st.session_state.current_selected_jd = None
                    st.session_state.parsed_data_combined = None
                    st.session_state.decision_made = None
                    st.session_state.report_evaluation_results = None
                    st.session_state.report_parsed_resume = None
                    st.session_state.report_cand_name = None
        else:
            st.error("Failed to load existing JDs from backend")
            existing_jds = []
            selected_jd_display = "Select a pre-existing JD"
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        existing_jds = []
        selected_jd_display = "Select a pre-existing JD"

with tab2:
    st.info("Add a new Job Description")

    col1, col2 = st.columns([1, 2])
    with col1:
        jd_name_input = st.text_input("JD Name:", placeholder="e.g., Senior Python Developer", key="jd_name_input_field", value="" if st.session_state.clear_jd_form else st.session_state.jd_name_input)

    with col2:
        jd_text_input = st.text_area("JD Text:", height=150, placeholder="Paste the job description text here...", key="jd_text_input_field", value="" if st.session_state.clear_jd_form else st.session_state.jd_text_input)

    # NEW: Check if JD text input has changed
    if jd_text_input != st.session_state.current_jd_text or jd_name_input != st.session_state.current_jd_name:
        st.session_state.current_jd_text = jd_text_input
        st.session_state.current_jd_name = jd_name_input
        # Reset evaluation state when JD text changes
        if jd_text_input and jd_name_input:  # Only reset if both fields have content
            st.session_state.parsed_data_combined = None
            st.session_state.decision_made = None
            st.session_state.report_evaluation_results = None
            st.session_state.report_parsed_resume = None
            st.session_state.report_cand_name = None
            # Also reset selected JD to avoid conflicts
            st.session_state.current_selected_jd = None

    # Reset the clear trigger
    if st.session_state.clear_jd_form:
        st.session_state.clear_jd_form = False

    # Enhanced button layout with Save and Evaluate side by side
    col_save, col_evaluate = st.columns([2, 8])

    with col_save:
        if st.button("💾 Save JD", key="save_jd_btn"):
            if jd_name_input and jd_text_input:
                with st.spinner("💾 Saving JD..."):
                    try:
                        save_response = requests.post(f"{BACKEND_URL}/save_jd_raw_text/", json={"jd_name": jd_name_input, "jd_text": jd_text_input})

                        if save_response.status_code == 200:
                            response_data = save_response.json()
                            st.success(f"✅ JD '{jd_name_input}' saved successfully!")

                            # Clear fields after successful save
                            st.session_state.jd_name_input = ""
                            st.session_state.jd_text_input = ""
                            st.session_state.show_nav_message = True
                            st.session_state.nav_message_time = time.time()
                            st.session_state.clear_jd_form = True
                            st.rerun()

                        else:
                            error_detail = save_response.json().get("detail", save_response.text)
                            st.error(f"❌ Failed to save JD: {error_detail}")

                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Could not connect to the backend server. Please make sure it's running.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"🌐 Network error: {str(e)}")
                    except json.JSONDecodeError:
                        st.error("📄 Invalid response format from server.")
                    except Exception as e:
                        st.error(f"💥 Unexpected error: {str(e)}")
            else:
                st.warning("📝 Please provide both JD name and JD text")

    # Evaluate with temporary JD button
    with col_evaluate:
        # Enable evaluate button if we have JD text and uploaded resume
        temp_evaluate_disabled = not (jd_text_input.strip() and st.session_state.uploaded_resume_name)

        if st.button("🚀 Evaluate (Temp)", key="temp_evaluate_btn", disabled=temp_evaluate_disabled, help="Evaluate resume with current JD text without saving"):
            if jd_text_input.strip() and st.session_state.uploaded_resume_name:
                # Reset previous results before new evaluation
                st.session_state.parsed_data_combined = None
                st.session_state.decision_made = None
                st.session_state.report_evaluation_results = None
                st.session_state.report_parsed_resume = None
                st.session_state.report_cand_name = None

                with st.spinner("🔄 Processing resume with temporary JD..."):
                    try:
                        # Read resume text
                        resume_pdf_reader = pymupdf.open(stream=uploaded_resume.getvalue(), filetype="pdf")
                        resume_text = ""
                        for i in range(resume_pdf_reader.page_count):
                            page = resume_pdf_reader.load_page(i)
                            resume_text += page.get_text()

                        # Upload resume file
                        files = {"resume_file": (uploaded_resume.name, uploaded_resume.getvalue(), uploaded_resume.type)}
                        upload_response = requests.post(f"{BACKEND_URL}/upload_resume_file", files=files)

                        if upload_response.status_code != 200:
                            st.error(f"Failed to upload resume to backend: {upload_response.status_code} - {upload_response.text}")
                        else:
                            # Parse JD text temporarily WITHOUT saving to backend
                            temp_parse_response = requests.post(f"{BACKEND_URL}/parse_jd_temp/", json={"jd_text": jd_text_input})

                            if temp_parse_response.status_code == 200:
                                response_data = temp_parse_response.json()
                                temp_jd_content = response_data.get("parsed_data")

                                # Evaluate with temporary JD using the parsed content directly
                                combined_json = {"resume_data": resume_text, "jd_json": temp_jd_content}
                                response = requests.post(f"{BACKEND_URL}/parse_and_evaluate", json=combined_json)

                                if response.status_code == 200:
                                    st.session_state.parsed_data_combined = response.json()
                                    st.success("✅ Temporary evaluation complete! (JD not saved)")
                                    # Set source for display
                                    jd_source = f"Temporary JD: {jd_name_input or 'Unnamed JD'}"
                                else:
                                    st.error(f"Evaluation failed: {response.status_code} - {response.text}")
                            else:
                                st.error("Failed to parse JD text for temporary evaluation")

                    except Exception as e:
                        st.error(f"An error occurred during temporary evaluation: {e}")
            else:
                st.warning("📝 Please provide JD text and upload a resume first")
    # Show navigation message after successful save
    if st.session_state.get("show_nav_message", False) and st.session_state.get("nav_message_time"):
        import time

        elapsed_time = time.time() - st.session_state.nav_message_time
        if elapsed_time < 120:  # 2 minutes = 120 seconds
            st.info("📋 Now go to 'Select Existing JD' tab to choose your saved JD and then click the Evaluate button!")
        else:
            st.session_state.show_nav_message = False
            st.session_state.nav_message_time = None

# Show current JD being used for evaluation
if st.session_state.parsed_data_combined and jd_source:
    st.info(f"📋 Evaluation performed using: **{jd_source}**")

# Display Results - SCOREBOARD FIRST, then parsed resume details
if st.session_state.parsed_data_combined:
    parsed_resume_data = st.session_state.parsed_data_combined.get("Parsed_Resume")
    eval_results = st.session_state.parsed_data_combined.get("Evaluation")

    candidate_name = parsed_resume_data.get("Name", "Candidate")
    st.header(f"📊 Evaluation Report for: {candidate_name}")

    # SCOREBOARD SECTION - DISPLAYED FIRST
    st.markdown("---")
    st.subheader("🏆 Overall Performance")

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
    st.subheader("📈 Detailed Scores")

    # Check if projects were excluded from scoring
    projects_score = eval_results.get("Projects_Score", 0)
    projects_excluded = projects_score == 0.0

    if projects_excluded:
        st.info("ℹ️ Projects section was excluded from scoring due to insufficient project information. Weights redistributed to other sections.")

        col_ind_score1, col_ind_score2, col_ind_score3 = st.columns(3)
        with col_ind_score1:
            st.metric(label="Experience Score (40%)", value=exp_score)
        with col_ind_score2:
            st.metric(label="Skills Score (50%)", value=skill_score)
        with col_ind_score3:
            st.metric(label="Education Score (10%)", value=edu_score)
    else:
        col_ind_score1, col_ind_score2, col_ind_score3, col_ind_score4 = st.columns(4)
        with col_ind_score1:
            st.metric(label="Experience Score (30%)", value=exp_score)
        with col_ind_score2:
            st.metric(label="Skills Score (40%)", value=skill_score)
        with col_ind_score3:
            st.metric(label="Education Score (10%)", value=edu_score)
        with col_ind_score4:
            st.metric(label="Projects Score (20%)", value=projects_score)
    st.markdown("---")
    st.subheader("💪 Strengths and Areas for Improvement")

    pros = eval_results.get("Pros")
    cons = eval_results.get("Cons")

    col_pros, col_cons = st.columns(2)

    with col_pros:
        st.success("##### ✅ Strengths")
        if pros:
            for p in pros:
                st.markdown(f"- {p}")
        else:
            st.info("No specific strengths identified.")

    with col_cons:
        st.warning("##### ⚠️ Weaknesses")
        if cons:
            for c in cons:
                st.markdown(f"- {c}")
        else:
            st.info("No specific weaknesses identified.")

    # Skills Analysis
    skills_match = eval_results.get("Skills Match")
    if skills_match and len(skills_match) > 0:
        st.markdown("---")
        st.markdown("#### 🎯 Skills Matched with JD")
        for skill_item in skills_match:
            st.markdown(f"✓ {skill_item}")
    else:
        st.markdown("---")
        st.info("No specific skills match details provided.")

    # Missing Skills
    missing_skills_from_resume = eval_results.get("Required_Skills_Missing_from_Resume")
    if missing_skills_from_resume and len(missing_skills_from_resume) > 0:
        st.markdown("---")
        st.markdown("#### ❌ Required Skills Missing from Resume")
        st.warning(", ".join(missing_skills_from_resume))
    else:
        st.markdown("---")
        st.info("No required skills missing from resume identified.")

    # Extra Skills
    extra_skills = eval_results.get("Extra skills")
    if extra_skills and len(extra_skills) > 0:
        st.markdown("---")
        st.markdown("#### ⭐ Extra Skills (Beyond JD Requirements)")
        st.info(", ".join(extra_skills))
    else:
        st.markdown("---")
        st.info("No extra skills identified.")

    # Summary
    summary_eval = eval_results.get("Summary")
    if summary_eval:
        st.markdown("---")
        st.markdown("📝 **Summary**")
        st.markdown(f"- {summary_eval}")

    # PARSED RESUME DETAILS IN EXPANDABLE DROPDOWN
    st.markdown("---")
    st.subheader("📄 Parsed Resume Information")

    if parsed_resume_data:
        with st.expander("📋 View Full Parsed Resume Data", expanded=False):

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
            st.markdown("#### 🎓 Education")
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
            st.markdown("#### 💼 Professional Experience")
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
            st.markdown("#### 🚀 Projects")
            project_entries = parsed_resume_data.get("Projects", [])

            # Check if projects are meaningful or just NA placeholders
            has_valid_projects = False
            if project_entries:
                for proj in project_entries:
                    project_name = proj.get("Project_Name", proj.get("Title", "")).strip()
                    if project_name and project_name.upper() not in ["NA", "N/A", ""]:
                        has_valid_projects = True
                        break

            if has_valid_projects:
                for proj in project_entries:
                    project_name = proj.get("Project_Name", proj.get("Title", "N/A"))
                    if project_name.upper() not in ["NA", "N/A"]:
                        st.markdown(f"**Project Name:** {project_name}")
                        description = proj.get("Project_Description", proj.get("Description", "N/A"))
                        if description and description.strip().lower() not in ["na", "n/a"]:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Description:* {description}")
            else:
                st.info("No project details provided. (Projects section excluded from scoring)")

            st.markdown("---")
            st.markdown("#### 🏆 Certifications")
            certification_entries = parsed_resume_data.get("Certifications", [])
            if certification_entries and len(certification_entries) > 0:
                for cer in certification_entries:
                    st.markdown(f"- {cer}")
            else:
                st.info("No certifications provided.")

            st.markdown("---")
            st.markdown("#### 💻 Technical Skills")
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

    # DECISION ACTIONS
    st.markdown("---")
    st.subheader("🎯 Decision Actions")

    combine_eval_results = eval_results
    combine_eval_results["name"] = candidate_name

    if st.session_state.decision_made:
        if st.session_state.decision_made == "Accept":
            st.success(f"✅ **{candidate_name}** has been marked as **Accepted**!")
        else:
            st.warning(f"❌ **{candidate_name}** has been marked as **Rejected**!")

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
            if st.button("📥 Download PDF Report", key="generate_pdf_report_btn"):
                with st.spinner("🔄 Generating PDF report..."):
                    try:
                        # Determine JD source properly
                        if st.session_state.get("current_selected_jd"):
                            jd_source_name = f"Selected JD: {st.session_state.current_selected_jd}"
                        elif st.session_state.get("current_jd_name"):
                            jd_source_name = f"Temporary JD: {st.session_state.current_jd_name}"
                        else:
                            jd_source_name = "Unknown JD"

                        report_data = {"evaluation_results": eval_results, "parsed_resume": parsed_resume_data, "candidate_name": candidate_name, "jd_source": jd_source_name}

                        # Call backend to generate PDF
                        response = requests.post(f"{BACKEND_URL}/generate_pdf_report", json=report_data)

                        if response.status_code == 200:
                            result = response.json()
                            pdf_filename = os.path.basename(result["pdf_path"])
                            download_url = f"{BACKEND_URL}/download_report/{pdf_filename}"

                            st.success("✅ PDF Report generated successfully!")

                            # Inject JS to auto-download the PDF
                            download_html = f"""
                                <html>
                                    <body>
                                        <a id="download_pdf_link" href="{download_url}" download style="display:none;"></a>
                                        <script>
                                            document.getElementById('download_pdf_link').click();
                                        </script>
                                    </body>
                                </html>
                            """
                            st.components.v1.html(download_html, height=0)

                        else:
                            st.error(f"❌ Failed to generate PDF: {response.text}")

                    except Exception as e:
                        st.error(f"❌ Error generating PDF report: {str(e)}")
