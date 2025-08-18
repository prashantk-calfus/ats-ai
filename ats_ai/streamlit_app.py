import json
import os
import time
from pathlib import Path

import mammoth
import pymupdf
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(layout="wide", page_title="ATS AI")
st.title("ATS AI : Intelligent Resume Screening")


def extract_text_from_uploaded_file(uploaded_file):
    file_extension = Path(uploaded_file.name).suffix.lower()

    if file_extension == ".pdf":
        resume_pdf_reader = pymupdf.open(stream=uploaded_file.getvalue(), filetype="pdf")
        resume_text = ""
        for i in range(resume_pdf_reader.page_count):
            page = resume_pdf_reader.load_page(i)
            resume_text += page.get_text()
        return resume_text

    elif file_extension in [".doc", ".docx"]:
        try:
            result = mammoth.extract_raw_text(uploaded_file)
            return result.value
        except Exception as e:
            st.error(f"Error reading {file_extension} file: {str(e)}")
            return None

    else:
        st.error(f"Unsupported file format: {file_extension}")
        return None


def validate_weightage_sum(exp, skills, edu, projects):
    """Validate that weightages sum to 100"""
    total = exp + skills + edu + projects
    return total, abs(total - 100) <= 1  # Allow 1% tolerance


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
if "weightage_config" not in st.session_state:
    st.session_state.weightage_config = {"experience_weight": 30, "skills_weight": 40, "education_weight": 10, "projects_weight": 20}  # Store as percentages for UI
if "show_weightage_config" not in st.session_state:
    st.session_state.show_weightage_config = False

uploaded_resume = st.file_uploader("Upload resume file (PDF, DOC, DOCX)", type=["pdf", "doc", "docx"], help="Supported formats: PDF, DOC, DOCX")

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

# ---- WEIGHTAGE CONFIGURATION SECTION ----
st.markdown("---")
st.header("Evaluation Weightage Configuration")

# Toggle button for weightage configuration
col_toggle, col_reset = st.columns([3, 1])
with col_toggle:
    if st.button("🔧 Configure Custom Weightage" if not st.session_state.show_weightage_config else "📊 Use Default Weightage"):
        st.session_state.show_weightage_config = not st.session_state.show_weightage_config

with col_reset:
    if st.button("🔄 Reset to Default"):
        st.session_state.weightage_config = {"experience_weight": 30, "skills_weight": 40, "education_weight": 10, "projects_weight": 20}
        if st.session_state.show_weightage_config:
            st.rerun()

if st.session_state.show_weightage_config:
    st.info("Customize the weightage for each evaluation criterion. Total must equal 100%.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        experience_weight = st.slider("Experience Weight (%)", min_value=0, max_value=100, value=st.session_state.weightage_config["experience_weight"], step=5, key="exp_weight_slider")

    with col2:
        skills_weight = st.slider("Skills Weight (%)", min_value=0, max_value=100, value=st.session_state.weightage_config["skills_weight"], step=5, key="skills_weight_slider")

    with col3:
        projects_weight = st.slider("Projects Weight (%)", min_value=0, max_value=100, value=st.session_state.weightage_config["projects_weight"], step=5, key="projects_weight_slider")

    with col4:
        education_weight = st.slider("Education Weight (%)", min_value=0, max_value=100, value=st.session_state.weightage_config["education_weight"], step=5, key="edu_weight_slider")

    # Update session state
    st.session_state.weightage_config = {"experience_weight": experience_weight, "skills_weight": skills_weight, "education_weight": education_weight, "projects_weight": projects_weight}

    # Validate sum
    total_weight, is_valid = validate_weightage_sum(experience_weight, skills_weight, education_weight, projects_weight)

    # Display validation status
    col_status, col_current = st.columns([1, 2])
    with col_status:
        if is_valid:
            st.success(f"✅ Valid Configuration (Total: {total_weight}%)")
        else:
            st.error(f"❌ Invalid Configuration (Total: {total_weight}%)")

    with col_current:
        st.write(f"**Current:** Exp: {experience_weight}%, Skills: {skills_weight}%, Projects: {projects_weight}%, Education: {education_weight}%")

else:
    # Show current default weightage
    st.info("Using Default Weightage: Experience: 30%, Skills: 40%, Projects: 20%, Education: 10%")

st.markdown("---")

# JD Selection Section with Tabs
st.header("Job Description")

tab1, tab2 = st.tabs(["📋 Select Existing JD", "💾 Add New JD"])

jd_content = None
jd_source = None

with tab1:
    st.info("Select from previously saved Job Descriptions")

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
                    if os.path.exists(jd_path):
                        with open(jd_path, "r") as f:
                            jd_content = json.load(f)
                        jd_source = f"Selected JD: {selected_jd_display}"
                    else:
                        st.warning(f"JD file not found locally: {jd_filename}")
                except Exception as e:
                    st.error(f"Error loading selected JD: {str(e)}")

                # Add the main evaluate button here inside tab1
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
                    jd_content = None  # Initialize jd_content
                    try:
                        jd_filename = f"{selected_jd_display}.json"
                        jd_path = os.path.join("jd_json", jd_filename)
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
                                    resume_text = extract_text_from_uploaded_file(uploaded_resume)
                                    if resume_text is None:
                                        st.error("Failed to extract text from the uploaded file")
                                        st.stop()

                                    # Upload resume file
                                    files = {"resume_file": (uploaded_resume.name, uploaded_resume.getvalue(), uploaded_resume.type)}
                                    upload_response = requests.post(f"{BACKEND_URL}/upload_resume_file", files=files)

                                    if upload_response.status_code != 200:
                                        st.error(f"Failed to upload resume to backend: {upload_response.status_code} - {upload_response.text}")
                                        st.session_state.parsed_data_combined = None
                                        st.session_state.decision_made = None
                                    else:
                                        if jd_content:
                                            # Prepare weightage config for API
                                            weightage_api = {
                                                "experience_weight": st.session_state.weightage_config["experience_weight"] / 100,
                                                "skills_weight": st.session_state.weightage_config["skills_weight"] / 100,
                                                "education_weight": st.session_state.weightage_config["education_weight"] / 100,
                                                "projects_weight": st.session_state.weightage_config["projects_weight"] / 100,
                                            }

                                            combined_json = {"resume_data": resume_text, "jd_json": jd_content, "weightage_config": weightage_api}
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
                        resume_text = extract_text_from_uploaded_file(uploaded_resume)
                        if resume_text is None:
                            st.error("Failed to extract text from the uploaded file")
                            st.stop()

                        # Upload resume file
                        files = {"resume_file": (uploaded_resume.name, uploaded_resume.getvalue(), uploaded_resume.type)}
                        upload_response = requests.post(f"{BACKEND_URL}/upload_resume_file", files=files)

                        if upload_response.status_code != 200:
                            st.error(f"Failed to upload resume to backend: {upload_response.status_code} - {upload_response.text}")
                        else:
                            # Parse JD text temporarily WITHOUT saving to backend
                            # Parse JD text temporarily WITHOUT saving to backend
                            temp_parse_response = requests.post(f"{BACKEND_URL}/parse_jd_temp/", json={"jd_text": jd_text_input})

                            if temp_parse_response.status_code == 200:
                                response_data = temp_parse_response.json()
                                temp_jd_content = response_data.get("parsed_data")

                                # Prepare weightage config for API
                                weightage_api = {
                                    "experience_weight": st.session_state.weightage_config["experience_weight"] / 100,
                                    "skills_weight": st.session_state.weightage_config["skills_weight"] / 100,
                                    "education_weight": st.session_state.weightage_config["education_weight"] / 100,
                                    "projects_weight": st.session_state.weightage_config["projects_weight"] / 100,
                                }

                                # Evaluate with temporary JD using the parsed content directly
                                combined_json = {"resume_data": resume_text, "jd_json": temp_jd_content, "weightage_config": weightage_api}
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


if st.session_state.parsed_data_combined and jd_source:
    st.info(f"📋 Evaluation performed using: **{jd_source}**")

    # Show weightage used for evaluation
    weightage_display = (
        f"Experience: {st.session_state.weightage_config['experience_weight']}%, "
        f"Skills: {st.session_state.weightage_config['skills_weight']}%, "
        f"Projects: {st.session_state.weightage_config['projects_weight']}%, "
        f"Education: {st.session_state.weightage_config['education_weight']}%"
    )
    st.info(f"⚖️ Weightage used: {weightage_display}")

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
        status = eval_results.get("Qualification Status", "Unknown")
        experience_gap = eval_results.get("Experience_Gap", 0)

        if experience_gap > 0:
            st.error(f"❌ Status: {status}")
            candidate_exp = eval_results.get("Total_Experience_Years", 0)
            required_exp = eval_results.get("JD_Required_Experience_Years", 0)
            st.caption(f"Missing {experience_gap:.1f} years of required experience")
        elif status in ["Qualified", "Suitable", "Highly Suitable"]:
            st.success(f"✅ Status: {status}")
            if eval_results.get("Total_Experience_Years") >= eval_results.get("JD_Required_Experience_Years", 0):
                st.caption("✓ Experience requirement met")
        else:
            st.error(f"❌ Status: {status}")

    if eval_results.get("Total_Experience_Years") is not None and eval_results.get("JD_Required_Experience_Years") is not None:
        st.markdown("---")
        st.subheader(" Experience Analysis")

        candidate_exp = eval_results["Total_Experience_Years"]
        required_exp = eval_results["JD_Required_Experience_Years"]

        col_exp1, col_exp2, col_exp3 = st.columns(3)

        with col_exp1:
            st.metric(label="Candidate Experience", value=f"{candidate_exp} years")

        with col_exp2:
            st.metric(label="Required Experience", value=f"{required_exp}+ years" if required_exp > 0 else "No minimum specified")

        with col_exp3:
            if required_exp > 0:
                if candidate_exp >= required_exp:
                    gap = candidate_exp - required_exp
                    st.success(f"✅ Meets requirement (+{gap:.1f} years)")
                else:
                    gap = required_exp - candidate_exp
                    st.error(f"❌ Experience Gap (-{gap:.1f} years)")
            else:
                st.info("ℹ️ No minimum experience required")

        # Experience Gap Warning
        if required_exp > 0 and candidate_exp < required_exp:
            gap = required_exp - candidate_exp
            st.warning(f" **Experience Disqualification**: Candidate has {gap:.1f} years less than the minimum required experience.")
    # rough

    st.markdown("---")
    st.subheader("📈 Detailed Scores")

    # Check if projects were excluded from scoring
    projects_score = eval_results.get("Projects_Score", 0)
    projects_excluded = projects_score == 0.0

    exp_pct = st.session_state.weightage_config["experience_weight"]
    skills_pct = st.session_state.weightage_config["skills_weight"]
    edu_pct = st.session_state.weightage_config["education_weight"]
    projects_pct = st.session_state.weightage_config["projects_weight"]

    # Create list of sections with non-zero weights
    active_sections = []
    if exp_pct > 0:
        active_sections.append(("Experience", exp_score, exp_pct))
    if skills_pct > 0:
        active_sections.append(("Skills", skill_score, skills_pct))
    if edu_pct > 0:
        active_sections.append(("Education", edu_score, edu_pct))
    if projects_pct > 0 and not projects_excluded:
        active_sections.append(("Projects", projects_score, projects_pct))

    # Handle projects redistribution display
    if projects_excluded and projects_pct > 0:
        # Calculate redistributed weights for display
        total_other = exp_pct + skills_pct + edu_pct
        if total_other > 0:
            exp_adj = exp_pct + (projects_pct * (exp_pct / total_other)) if exp_pct > 0 else 0
            skills_adj = skills_pct + (projects_pct * (skills_pct / total_other)) if skills_pct > 0 else 0
            edu_adj = edu_pct + (projects_pct * (edu_pct / total_other)) if edu_pct > 0 else 0

            st.warning(f"ℹ️ Projects excluded from scoring. {projects_pct}% weight redistributed proportionally.")

            # Update active sections with adjusted weights
            active_sections = []
            if exp_pct > 0:
                active_sections.append(("Experience", exp_score, exp_adj))
            if skills_pct > 0:
                active_sections.append(("Skills", skill_score, skills_adj))
            if edu_pct > 0:
                active_sections.append(("Education", edu_score, edu_adj))

    # Display scores based on number of active sections
    num_active = len(active_sections)

    if num_active == 0:
        st.error("⚠️ No sections have weight assigned. Please configure weightage.")
    elif num_active == 1:
        col1 = st.columns(1)[0]
        with col1:
            name, score, weight = active_sections[0]
            st.metric(label=f"{name} Score ({weight:.1f}%)", value=score)
    elif num_active == 2:
        col1, col2 = st.columns(2)
        with col1:
            name, score, weight = active_sections[0]
            st.metric(label=f"{name} Score ({weight:.1f}%)", value=score)
        with col2:
            name, score, weight = active_sections[1]
            st.metric(label=f"{name} Score ({weight:.1f}%)", value=score)
    elif num_active == 3:
        col1, col2, col3 = st.columns(3)
        with col1:
            name, score, weight = active_sections[0]
            st.metric(label=f"{name} Score ({weight:.1f}%)", value=score)
        with col2:
            name, score, weight = active_sections[1]
            st.metric(label=f"{name} Score ({weight:.1f}%)", value=score)
        with col3:
            name, score, weight = active_sections[2]
            st.metric(label=f"{name} Score ({weight:.1f}%)", value=score)
    elif num_active == 4:
        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]
        for i, (name, score, weight) in enumerate(active_sections):
            with cols[i]:
                st.metric(label=f"{name} Score ({weight:.1f}%)", value=score)

    # Show sections with 0% weight as informational
    zero_weight_sections = []
    if exp_pct == 0:
        # Only show if we actually have a meaningful score
        if exp_score and exp_score > 0:
            zero_weight_sections.append(("Experience", exp_score))
        else:
            zero_weight_sections.append(("Experience", "Not Evaluated"))

    if skills_pct == 0:
        # Only show if we actually have a meaningful score
        if skill_score and skill_score > 0:
            zero_weight_sections.append(("Skills", skill_score))
        else:
            zero_weight_sections.append(("Skills", "Not Evaluated"))

    if edu_pct == 0:
        # Only show if we actually have a meaningful score
        if edu_score and edu_score > 0:
            zero_weight_sections.append(("Education", edu_score))
        else:
            zero_weight_sections.append(("Education", "Not Evaluated"))

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
            # Separate experience-related cons from others
            experience_cons = []
            other_cons = []

            for c in cons:
                if any(keyword in c.lower() for keyword in ["experience", "years", "senior", "junior"]):
                    experience_cons.append(c)
                else:
                    other_cons.append(c)

            # Display experience cons first and prominently
            if experience_cons:
                st.error("**Experience Issues:**")
                for exp_con in experience_cons:
                    st.markdown(f"- 🚫 {exp_con}")

            # Then display other cons
            if other_cons:
                if experience_cons:  # Only add header if we had experience cons
                    st.warning("**Other Areas for Improvement:**")
                for other_con in other_cons:
                    st.markdown(f"- {other_con}")
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
                    # Check if edu is a dictionary or string
                    if isinstance(edu, dict):
                        # Handle dictionary format
                        degree = edu.get("Degree", "N/A")
                        institution = edu.get("Institution", "N/A")
                        score = edu.get("Score", "N/A")
                        duration = edu.get("Duration", "N/A")
                        st.markdown(f"**{degree}** at {institution}")
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Score:* {score}, *Duration:* {duration}")
                    elif isinstance(edu, str):
                        # Handle string format
                        st.markdown(f"- {edu}")
                    else:
                        # Fallback for any other format
                        st.markdown(f"- {str(edu)}")
            else:
                st.info("No education details provided.")

            st.markdown("---")
            st.markdown("#### 💼 Professional Experience")
            experience_entries = parsed_resume_data.get("Professional_Experience", [])
            if experience_entries:
                for exp in experience_entries:
                    # Check if exp is a dictionary or string
                    if isinstance(exp, dict):
                        # Handle dictionary format
                        role = exp.get("Role", "N/A")
                        company = exp.get("Company", "N/A")
                        duration = exp.get("Duration", "N/A")
                        description = exp.get("Description", "N/A")

                        st.markdown(f"**{role}** at **{company}**")
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Duration:* {duration}")
                        if description and description.strip().lower() not in ["na", "n/a"]:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Description:* {description}")
                    elif isinstance(exp, str):
                        # Handle string format
                        st.markdown(f"- {exp}")
                    else:
                        # Fallback for any other format
                        st.markdown(f"- {str(exp)}")
            else:
                st.info("No professional experience details provided.")

            # st.markdown("---")
            # st.markdown("#### 🚀 Projects")
            # project_entries = parsed_resume_data.get("Projects", [])
            #
            # # Check if projects are meaningful or just NA placeholders
            # has_valid_projects = False
            # if project_entries:
            #     for proj in project_entries:
            #         if isinstance(proj, dict):
            #             project_name = proj.get("Project_Name", proj.get("Title", "")).strip()
            #             if project_name and project_name.upper() not in ["NA", "N/A", ""]:
            #                 has_valid_projects = True
            #                 break
            #         elif isinstance(proj, str):
            #             if proj.strip() and proj.strip().upper() not in ["NA", "N/A", ""]:
            #                 has_valid_projects = True
            #                 break
            #
            # if has_valid_projects:
            #     for proj in project_entries:
            #         if isinstance(proj, dict):
            #             project_name = proj.get("Project_Name", proj.get("Title", "N/A"))
            #             if project_name.upper() not in ["NA", "N/A"]:
            #                 st.markdown(f"**Project Name:** {project_name}")
            #                 description = proj.get("Project_Description", proj.get("Description", "N/A"))
            #                 technologies = proj.get("Technologies", [])
            #                 if description and description.strip().lower() not in ["na", "n/a"]:
            #                     st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Description:* {description}")
            #                 if technologies and isinstance(technologies, list) and len(technologies) > 0:
            #                     tech_str = ", ".join(technologies)
            #                     st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Technologies:* {tech_str}")
            #         elif isinstance(proj, str):
            #             if proj.strip().upper() not in ["NA", "N/A"]:
            #                 st.markdown(f"**Project:** {proj}")
            # else:
            #     st.info("No project details provided. (Projects section excluded from scoring)")
            # Replace the project validation section in streamlit_app.py (around line 385-420)

            st.markdown("---")
            st.markdown("#### 🚀 Projects")
            project_entries = parsed_resume_data.get("Projects", [])

            # FIXED: Better project validation logic
            has_valid_projects = False
            if project_entries:
                for proj in project_entries:
                    if isinstance(proj, dict):
                        # Check both possible field names that your parser might use
                        project_name = proj.get("Title", proj.get("Project_Name", "")).strip()
                        project_desc = proj.get("Description", proj.get("Project_Description", "")).strip()

                        # A project is valid if it has a meaningful title AND description
                        if project_name and project_name.upper() not in ["NA", "N/A", "", "NOT PROVIDED"] and project_desc and project_desc.upper() not in ["NA", "N/A", "", "NOT PROVIDED"] and len(project_desc) > 10:  # Description should be substantial
                            has_valid_projects = True
                            break
                    elif isinstance(proj, str):
                        if proj.strip() and proj.strip().upper() not in ["NA", "N/A", "", "NOT PROVIDED"] and len(proj.strip()) > 10:
                            has_valid_projects = True
                            break

            if has_valid_projects:
                for proj in project_entries:
                    if isinstance(proj, dict):
                        # Use the correct field names from your parser
                        project_name = proj.get("Title", proj.get("Project_Name", "N/A"))
                        if project_name and project_name.upper() not in ["NA", "N/A", "", "NOT PROVIDED"]:
                            st.markdown(f"**Project Name:** {project_name}")

                            description = proj.get("Description", proj.get("Project_Description", "N/A"))
                            technologies = proj.get("Technologies", [])

                            if description and description.strip().upper() not in ["NA", "N/A", "", "NOT PROVIDED"]:
                                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Description:* {description}")

                            if technologies and isinstance(technologies, list) and len(technologies) > 0:
                                # Filter out NA values from technologies list
                                valid_technologies = [tech for tech in technologies if tech.strip().upper() not in ["NA", "N/A", ""]]
                                if valid_technologies:
                                    tech_str = ", ".join(valid_technologies)
                                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Technologies:* {tech_str}")
                    elif isinstance(proj, str):
                        if proj.strip().upper() not in ["NA", "N/A", "", "NOT PROVIDED"]:
                            st.markdown(f"**Project:** {proj}")
            else:
                st.info("No project details provided. (Projects section excluded from scoring)")
            st.markdown("---")
            st.markdown("#### 🏆 Certifications")
            certification_entries = parsed_resume_data.get("Certifications", [])
            if certification_entries and len(certification_entries) > 0:
                for cert in certification_entries:
                    # Check if cert is a dictionary or string
                    if isinstance(cert, dict):
                        # Handle dictionary format
                        cert_authority = cert.get("Certification_Authority", "N/A")
                        cert_details = cert.get("Certification_Details", "N/A")
                        if cert_authority != "N/A" and cert_details != "N/A":
                            st.markdown(f"- **{cert_details}** from {cert_authority}")
                        elif cert_details != "N/A":
                            st.markdown(f"- {cert_details}")
                        else:
                            st.markdown(f"- {str(cert)}")
                    elif isinstance(cert, str):
                        # Handle string format
                        if cert.strip() and cert.strip().upper() not in ["NA", "N/A"]:
                            st.markdown(f"- {cert}")
                    else:
                        # Fallback for any other format
                        st.markdown(f"- {str(cert)}")
            else:
                st.info("No certifications provided.")

            st.markdown("---")
            st.markdown("#### 💻 Technical Skills")
            programming_languages = parsed_resume_data.get("Programming_Language", [])
            frameworks = parsed_resume_data.get("Frameworks", [])
            technologies = parsed_resume_data.get("Technologies", [])

            all_skills = []
            if programming_languages and len(programming_languages) > 0:
                # Handle both list of strings and single string
                if isinstance(programming_languages, list):
                    all_skills.append("##### Programming Languages")
                    all_skills.extend([f"⦿ {s}" for s in programming_languages if s.strip()])
                else:
                    all_skills.append("##### Programming Languages")
                    all_skills.append(f"⦿ {programming_languages}")

            if frameworks and len(frameworks) > 0:
                # Handle both list of strings and single string
                if isinstance(frameworks, list):
                    all_skills.append("##### Frameworks")
                    all_skills.extend([f"⦿ {s}" for s in frameworks if s.strip()])
                else:
                    all_skills.append("##### Frameworks")
                    all_skills.append(f"⦿ {frameworks}")

            if technologies and len(technologies) > 0:
                # Handle both list of strings and single string
                if isinstance(technologies, list):
                    all_skills.append("##### Technologies")
                    all_skills.extend([f"⦿ {s}" for s in technologies if s.strip()])
                else:
                    all_skills.append("##### Technologies")
                    all_skills.append(f"⦿ {technologies}")

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

                        # ADD WEIGHTAGE CONFIG TO REPORT DATA
                        report_data = {"evaluation_results": eval_results, "parsed_resume": parsed_resume_data, "candidate_name": candidate_name, "jd_source": jd_source_name, "weightage_config": st.session_state.weightage_config}  # ADD THIS LINE

                        # Call backend to generate PDF
                        response = requests.post(f"{BACKEND_URL}/generate_pdf_report", json=report_data)

                        if response.status_code == 200:
                            result = response.json()
                            pdf_filename = os.path.basename(result["pdf_path"])
                            download_url = f"http://localhost:8000/download_report/{pdf_filename}"
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
        # with col3:
        #     if st.button("📥 Download PDF Report", key="generate_pdf_report_btn"):
        #         with st.spinner("🔄 Generating PDF report..."):
        #             try:
        #                 # Determine JD source properly
        #                 if st.session_state.get("current_selected_jd"):
        #                     jd_source_name = f"Selected JD: {st.session_state.current_selected_jd}"
        #                 elif st.session_state.get("current_jd_name"):
        #                     jd_source_name = f"Temporary JD: {st.session_state.current_jd_name}"
        #                 else:
        #                     jd_source_name = "Unknown JD"
        #
        #                 report_data = {
        #                     "evaluation_results": eval_results,
        #                     "parsed_resume": parsed_resume_data,
        #                     "candidate_name": candidate_name,
        #                     "jd_source": jd_source_name,
        #                     "weightage_config": st.session_state.weightage_config
        #                 }
        #
        #                 # Generate PDF
        #                 response = requests.post(f"{BACKEND_URL}/generate_pdf_report", json=report_data)
        #
        #                 if response.status_code == 200:
        #                     result = response.json()
        #                     pdf_filename = os.path.basename(result["pdf_path"])
        #
        #                     # Download the PDF file
        #                     download_response = requests.get(f"{BACKEND_URL}/download_report/{pdf_filename}")
        #
        #                     if download_response.status_code == 200:
        #                         st.success("✅ PDF Report generated successfully!")
        #
        #                         # Use Streamlit's download button
        #                         st.download_button(
        #                             label="📥 Download PDF Report",
        #                             data=download_response.content,
        #                             file_name=pdf_filename,
        #                             mime="application/pdf"
        #                         )
        #                     else:
        #                         st.error("❌ Failed to download PDF")
        #                 else:
        #                     st.error(f"❌ Failed to generate PDF: {response.text}")
        #
        #             except Exception as e:
        #                 st.error(f"❌ Error generating PDF report: {str(e)}")
