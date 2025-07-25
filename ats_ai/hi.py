# Frontend:
# import json
# import os
# from typing import Any, Dict
#
# import requests
# import streamlit as st
# from frontend_calls import (
#     evaluate_resume_with_backend,
#     parse_resume_from_backend,
#     upload_resume_file_to_backend,
# )
#
# BACKEND_URL = os.getenv("BACKEND_URL", default="http://localhost:8000")
#
#
# def display_parsed_resume_in_markdown(parsed_resume_data: Dict[str, Any]):
#     """
#     Displays the parsed resume information in a user-friendly Markdown format.
#     """
#     st.markdown("#### Personal Information")
#     st.write(f"**Name:** {parsed_resume_data.get('Name', 'N/A')}")
#
#     contact_details = parsed_resume_data.get("Contact_Details", {})
#     if contact_details:
#         st.write(f"**Mobile No:** {contact_details.get('Mobile_No', 'N/A')}")
#         st.write(f"**Email:** {contact_details.get('Email', 'N/A')}")
#     else:
#         st.write("**Contact Details:** Not provided")
#
#     st.write(f"**GitHub:** {parsed_resume_data.get('Github_Repo', 'N/A')}")
#     st.write(f"**LinkedIn:** {parsed_resume_data.get('LinkedIn', 'N/A')}")
#
#     st.markdown("---")
#     st.markdown("#### Education")
#     education_entries = parsed_resume_data.get("Education", [])
#     if education_entries:
#         for edu in education_entries:
#             st.markdown(f"**{edu.get('Degree', 'N/A')}** at {edu.get('Institution', 'N/A')}")
#             st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Score:* {edu.get('Score', 'N/A')}, *Duration:* {edu.get('Duration', 'N/A')}")
#     else:
#         st.info("No education details provided.")
#
#     st.markdown("---")
#     st.markdown("#### Professional Experience")
#     experience_entries = parsed_resume_data.get("Professional_Experience", [])
#     if experience_entries:
#         for exp in experience_entries:
#             st.markdown(f"**{exp.get('Role', 'N/A')}** at **{exp.get('Company', 'N/A')}**")
#             st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Duration:* {exp.get('Duration', 'N/A')}")
#             if exp.get("Description", "N/A") != "N/A":
#                 st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Description:* {exp.get('Description', 'N/A')}")
#     else:
#         st.info("No professional experience details provided.")
#
#     st.markdown("---")
#     st.markdown("#### Projects")
#     project_entries = parsed_resume_data.get("Projects", [])
#     if project_entries and project_entries[0].get("Project_Name", "NA").upper() != "NA":
#         for proj in project_entries:
#             st.markdown(f"**Project Name:** {proj.get('Project_Name', 'N/A')}")
#             st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Description:* {proj.get('Project_Description', 'N/A')}")
#     else:
#         st.info("No project details provided.")
#
#     st.markdown("---")
#     st.markdown("#### Certifications")
#     certification_entries = parsed_resume_data.get("Certifications", [])
#     if certification_entries and certification_entries[0].get("Certification_Authority", "NA").upper() != "NA":
#         for cert in certification_entries:
#             st.markdown(f"**Certification:** {cert.get('Certification_Details', 'N/A')}")
#             st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Authority:* {cert.get('Certification_Authority', 'N/A')}")
#     else:
#         st.info("No certification details provided.")
#
#     st.markdown("---")
#     st.markdown("#### Technical Skills")
#     prog_lang = parsed_resume_data.get("Programming_Language", [])
#     if prog_lang:
#         st.write(f"**Programming Languages:** {', '.join(prog_lang)}")
#     else:
#         st.write("**Programming Languages:** N/A")
#
#     frameworks = parsed_resume_data.get("Frameworks", [])
#     if frameworks:
#         st.write(f"**Frameworks:** {', '.join(frameworks)}")
#     else:
#         st.write("**Frameworks:** N/A")
#
#     technologies = parsed_resume_data.get("Technologies", [])
#     if technologies:
#         st.write(f"**Technologies:** {', '.join(technologies)}")
#     else:
#         st.write("**Technologies:** N/A")
#
#
# def display_final_evaluation_results(evaluation_results: Dict[str, Any]):
#     """Display the final evaluation results summary"""
#     st.subheader("Final Resume Evaluation Results Summary")
#
#     # === Overall Scores ===
#     eval_summary = evaluation_results.get("Evaluation_Summary", {})
#     match_with_jd = eval_summary.get("Match_Percentage", "N/A").strip()
#     qualification_status = eval_summary.get("Qualification_Status", "N/A")
#     exp_score = eval_summary.get("Experience_Score", "N/A")
#     skills_score = eval_summary.get("Skills_Score", "N/A")
#     edu_score = eval_summary.get("Education_Score", "N/A")
#     projects_score = eval_summary.get("Projects_Score", "N/A")
#     overall_score = eval_summary.get("Overall_Weighted_Score", "N/A")
#
#     col_score1, col_score2, col_score3 = st.columns(3)
#     with col_score1:
#         st.metric(label=" Overall Score (0-10)", value=overall_score)
#     with col_score2:
#         st.metric(label=" Match with JD", value=match_with_jd)
#     with col_score3:
#         if qualification_status == "Qualified":
#             st.success(f" Status: {qualification_status}")
#         else:
#             st.error(f" Status: {qualification_status}")
#
#     # === Individual Scores ===
#     st.markdown("---")
#     st.markdown("#### Detailed Scores")
#
#     col_ind_score1, col_ind_score2, col_ind_score3, col_ind_score4 = st.columns(4)  # Added a column for projects score
#     with col_ind_score1:
#         st.metric(label="Experience Score (0-10)", value=exp_score)
#     with col_ind_score2:
#         st.metric(label="Skills Score (0-10)", value=skills_score)
#     with col_ind_score3:
#         st.metric(label="Education Score (0-10)", value=edu_score)
#     with col_ind_score4:
#         st.metric(label="Projects Score (0-10)", value=projects_score)
#
#     # === Pros and Cons ===
#     st.markdown("---")
#     st.markdown("#### Strengths and Areas for Improvement")
#
#     pros_and_cons = evaluation_results.get("Strengths_and_Weaknesses", {})
#     pros = pros_and_cons.get("Pros", [])
#     cons = pros_and_cons.get("Cons", [])
#
#     col_pros, col_cons = st.columns(2)
#     with col_pros:
#         st.success("##### Strengths")
#         if pros:
#             for p in pros:
#                 st.write(f"- {p}")
#         else:
#             st.info("No specific strengths identified.")
#
#     with col_cons:
#         st.warning("##### Weaknesses")
#         if cons:
#             for c in cons:
#                 st.write(f"- {c}")
#         else:
#             st.info("No specific weaknesses identified.")
#
#     # === Skills Match ===
#     st.markdown("---")
#     st.markdown("#### Skills Match Analysis")
#
#     skill_analysis = evaluation_results.get("Skill_Analysis", {})
#     skills_match = skill_analysis.get("Skills Match", [])
#     skills_not_matching = skill_analysis.get("Required_Skills_Missing_from_Resume", [])
#     extra_skills = skill_analysis.get("Extra skills", [])  # This alias is expected from the LLM JSON, so keep it.
#
#     if skills_match:
#         st.markdown("**Matching Skills:**")
#         st.info(",\n ".join(skills_match))
#     else:
#         st.warning("No direct skill matches found.")
#
#     if skills_not_matching:
#         st.markdown("**Missing Skills (from JD):**")
#         st.warning(",\n ".join(skills_not_matching))
#
#     if extra_skills:
#         st.markdown("** Extra Skills (beyond JD):**")
#         st.info(",\n ".join(extra_skills))
#     else:
#         st.info("No additional skills beyond JD requirements identified.")
#
#     # === Key Considerations ===
#     st.markdown("---")
#     st.markdown("####  Key Considerations")
#
#     key_considerations = evaluation_results.get("Key_Considerations", {})
#     kpis = key_considerations.get("Quantifiable_Achievements_Identified", [])
#     red_flags = key_considerations.get("Red_Flags_Noted", [])
#     overall_recommendation = key_considerations.get("Overall_Recommendation", "N/A")
#
#     if kpis:
#         st.markdown("** Quantifiable Achievements:**")
#         for kpi in kpis:
#             st.markdown(f"- {kpi}")
#     else:
#         st.info("No quantifiable achievements noted.")
#
#     if red_flags:
#         st.markdown("** Red Flags:**")
#         for flag in red_flags:
#             st.warning(f"- {flag}")
#     else:
#         st.success("No red flags identified.")
#
#     if overall_recommendation and overall_recommendation != "N/A":
#         st.markdown("** Final Recommendation:**")
#         st.markdown(f"- {overall_recommendation}")
#
#
# # --- Streamlit Frontend (main app structure) ---
# st.set_page_config(layout="wide", page_title="Resume Analyzer")
#
# st.title("Resume Analyzer and Evaluator")
#
# # Initialize session state variables
# if "uploaded_resume_filename" not in st.session_state:
#     st.session_state.uploaded_resume_filename = None
# if "parsed_resume" not in st.session_state:
#     st.session_state.parsed_resume = None
# if "personal_details" not in st.session_state:
#     st.session_state.personal_details = None
# if "evaluation_results" not in st.session_state:
#     st.session_state.evaluation_results = None
# if "show_jd_sections" not in st.session_state:
#     st.session_state.show_jd_sections = False
# if "decision_made" not in st.session_state:
#     st.session_state.decision_made = None
# if "temp_jd_path" not in st.session_state:
#     st.session_state.temp_jd_path = None
#
#
# # --- Section 1: Upload and Parse Resume ---
# st.header("1. Upload and Parse Resume")
# uploaded_file = st.file_uploader("Choose a resume file (PDF)", type=["pdf"])
#
# # Placeholder for messages during upload/parsing
# parsing_status_messages = st.empty()
#
# if uploaded_file is not None:
#     if st.button("Process Resume", key="process_resume_btn"):
#         # Clear states of previous sessions when a new resume is processed
#         st.session_state.uploaded_resume_filename = None
#         st.session_state.parsed_resume = None
#         st.session_state.evaluation_results = None
#         st.session_state.show_jd_sections = False
#         st.session_state.decision_made = None
#         st.session_state.temp_jd_path = None
#
#         with st.spinner("Uploading resume..."):
#             uploaded_filename = upload_resume_file_to_backend(uploaded_file, parsing_status_messages)
#             st.session_state.uploaded_resume_filename = uploaded_filename
#
#         if st.session_state.uploaded_resume_filename:
#             with st.spinner("Parsing resume with LLM..."):
#                 parsed_data = parse_resume_from_backend(st.session_state.uploaded_resume_filename, parsing_status_messages)
#                 st.session_state.parsed_resume = parsed_data
#
#                 if st.session_state.parsed_resume:
#                     st.session_state.show_jd_sections = True
#                     parsing_status_messages.success("Resume processed and parsed successfully!")
#                 else:
#                     st.session_state.show_jd_sections = False
#                     parsing_status_messages.error("Failed to parse resume after upload.")
#         else:
#             parsing_status_messages.error("Resume upload failed. Cannot proceed with parsing.")
#
#
# # --- Collapsible Parsed Resume Section ---
# if st.session_state.parsed_resume:
#     with st.expander("View Parsed Resume Information (Click to Expand)"):
#         display_parsed_resume_in_markdown(st.session_state.parsed_resume)
#     st.markdown("---")
#
#     # --- Section 2: Provide Job Description ---
#     st.header("2. Provide Job Description")
#
#     # Add tabs for different JD input methods
#     tab1, tab2 = st.tabs([ "📋 Select Existing JD", "💾 Save New JD"])
#
#
#
#     with tab1:
#         st.info("Select from previously saved Job Descriptions")
#
#         # Fetch existing JDs from backend
#         try:
#             response = requests.get(f"{BACKEND_URL}/list_jds")
#             if response.status_code == 200:
#                 existing_jds = response.json()
#                 jd_options = ["Select a pre-existing JD"] + list(existing_jds.keys())
#                 selected_jd_display = st.selectbox(
#                     "Choose a Job Description:",
#                     options=jd_options,
#                     index=0,
#                     key="jd_dropdown"
#                 )
#             else:
#                 st.error("Failed to load existing JDs")
#                 existing_jds = {}
#                 selected_jd_display = "Select a pre-existing JD"
#         except Exception as e:
#             st.error(f"Error loading JDs: {str(e)}")
#             existing_jds = {}
#             selected_jd_display = "Select a pre-existing JD"
#
#     with tab2:
#         st.info("Save a new Job Description for future use")
#
#         # Initialize a form clear trigger
#         if "clear_jd_form" not in st.session_state:
#             st.session_state.clear_jd_form = False
#
#         col1, col2 = st.columns([1, 2])
#         with col1:
#             jd_name_input = st.text_input(
#                 "JD Name:",
#                 placeholder="e.g., Senior Python Developer",
#                 key="jd_name_input",
#                 value="" if st.session_state.clear_jd_form else st.session_state.get("jd_name_input", "")
#             )
#
#         with col2:
#             jd_text_input = st.text_area(
#                 "JD Text:",
#                 height=150,
#                 placeholder="Paste the job description text here...",
#                 key="jd_text_input",
#                 value="" if st.session_state.clear_jd_form else st.session_state.get("jd_text_input", "")
#             )
#
#         # Reset the clear trigger
#         if st.session_state.clear_jd_form:
#             st.session_state.clear_jd_form = False
#
#         if st.button("💾 Save JD", key="save_jd_btn"):
#             if jd_name_input and jd_text_input:
#                 try:
#                     save_response = requests.post(
#                         f"{BACKEND_URL}/upload_jd_text/",
#                         json={
#                             "jd_name": jd_name_input,
#                             "jd_text": jd_text_input
#                         }
#                     )
#                     if save_response.status_code == 200:
#                         st.success(f"✅ JD '{jd_name_input}' saved successfully!")
#                         st.session_state.clear_jd_form = True
#                         st.rerun()
#                     else:
#                         st.error(f"Failed to save JD: {save_response.text}")
#                 except Exception as e:
#                     st.error(f"Error saving JD: {str(e)}")
#
#     # Determine the JD content to use for evaluation
#     jd_content = None
#     jd_source = None
#
#
#     if selected_jd_display != "Select a pre-existing JD" and existing_jds:
#         # Load the selected JD file
#         try:
#             jd_filename = existing_jds[selected_jd_display]
#             # Try to read from the jd_json folder (matching backend)
#             jd_path = f"jd_json/{jd_filename}"
#             if os.path.exists(jd_path):
#                 with open(jd_path, 'r') as f:
#                     jd_content = json.load(f)
#                 jd_source = f"Selected JD: {selected_jd_display}"
#                 st.success(f"✅ Using selected JD: **{selected_jd_display}**")
#             else:
#                 # If local file doesn't exist, try to fetch from backend
#                 st.info(f"Loading JD: {selected_jd_display}")
#                 jd_content = {"job_description": f"Using JD: {selected_jd_display}"}
#                 jd_source = f"Backend JD: {selected_jd_display}"
#         except Exception as e:
#             st.error(f"Error loading selected JD: {str(e)}")
#             jd_content = None
#
#     # Placeholder for messages during evaluation
#     evaluation_status_messages = st.empty()
#
#     # --- Section 3: Evaluate Resume against JD ---
#     if st.session_state.parsed_resume is not None and jd_content:
#         if st.button("Evaluate Resume", key="evaluate_resume_btn"):
#             # Clear previous decision when re-evaluating
#
#             st.header("3. Evaluate Resume against JD")
#
#             st.session_state.decision_made = None
#
#             with st.spinner("Evaluating..."):
#                 # Store personal details separately for the report page.
#                 personal_details_keys = ["Name", "Contact_Details", "Github_Repo", "LinkedIn"]
#                 st.session_state.personal_details = {key: st.session_state.parsed_resume.get(key) for key in
#                                                      personal_details_keys}
#
#                 st.session_state.evaluation_results = evaluate_resume_with_backend(
#                     st.session_state.parsed_resume,
#                     jd_content,
#                     evaluation_status_messages,
#                 )
#
#                 if st.session_state.evaluation_results:
#                     evaluation_status_messages.success("Resume evaluation complete!")
#                 else:
#                     evaluation_status_messages.error("Resume evaluation failed. Check backend logs for details.")
#
#     elif st.session_state.parsed_resume is None:
#         evaluation_status_messages.warning("Please upload and parse a resume first to proceed with evaluation.")
#
#
# # --- Display Final Evaluation Results (Outside of button logic) ---
# if st.session_state.evaluation_results:
#     display_final_evaluation_results(st.session_state.evaluation_results)
#
#     # Accept/Reject buttons
#     candidate_name = (st.session_state.personal_details.get("Name") if st.session_state.personal_details else None) or st.session_state.parsed_resume.get("Name", "Unknown")
#
#     # Display decision status if already made
#     if st.session_state.decision_made:
#         if st.session_state.decision_made == "Accept":
#             st.success(f" **{candidate_name}** has been marked as **Accepted**!")
#         else:
#             st.warning(f" **{candidate_name}** has been marked as **Rejected**!")
#     else:
#         # Shown when no decision made yet
#         col1, col2, col3 = st.columns([1, 1, 2])
#
#         with col1:
#             if st.button("✅ Accept", key="accept_btn"):
#                 response = requests.post(f"{BACKEND_URL}/store_decision", params={"name": candidate_name, "decision": "Accept"})
#                 if response.status_code == 200:
#                     st.session_state.decision_made = "Accept"
#                     st.rerun()
#                 else:
#                     st.error(f"Failed to store decision: {response.text}")
#
#         with col2:
#             if st.button("❌ Reject", key="reject_btn"):
#                 response = requests.post(f"{BACKEND_URL}/store_decision", params={"name": candidate_name, "decision": "Reject"})
#                 if response.status_code == 200:
#                     st.session_state.decision_made = "Reject"
#                     st.rerun()
#                 else:
#                     st.error(f"Failed to store decision: {response.text}")
#
#         with col3:
#             # Generate Report Button
#             if st.button("Generate Report", key="generate_report_btn"):
#                 # Store data in session state for the report page
#                 st.session_state.report_evaluation_results = st.session_state.evaluation_results
#                 st.session_state.report_parsed_resume = st.session_state.parsed_resume
#                 # Ensure personal_details is set before navigating
#                 personal_details_keys = ["Name", "Contact_Details", "Github_Repo", "LinkedIn"]
#                 st.session_state.report_personal_details = {key: st.session_state.parsed_resume.get(key) for key in personal_details_keys}
#                 # Navigate to the report page - ensure 'pages/report_page.py'
#                 st.switch_page("pages/report_page.py")
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# server: import os
# import re
# import shutil
# from typing import Any, Dict
# import json
# import uvicorn
# from fastapi import FastAPI, File, HTTPException, UploadFile
# from langchain_community.document_loaders import PyMuPDFLoader
# from starlette import status
# from starlette.responses import RedirectResponse, JSONResponse
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# import logging
# from ats_ai.agent.jd_parser import extract_jd_info
#
#
# from ats_ai.agent.llm_agent import (
#     combined_parse_evaluate,
#     evaluate_resume_against_jd,
#     extract_resume_info,
# )
#
# RESUME_UPLOAD_FOLDER = "data/"
# JD_UPLOAD_FOLDER = "jd_json/"
# RESUME_FILE_UPLOAD = File(...)
#
#
# class ResumeEvaluationRequest(BaseModel):
#     resume_json: Dict[str, Any]
#     jd_json: Dict[str, Any]
#
#     model_config = {
#         "json_schema_extra": {
#             "examples": [
#                 {
#                     "resume_json": {
#                         "name": "John Doe",
#                         "email": "john.doe@example.com",
#                         "experience": [{"title": "Software Engineer", "company": "Tech Corp", "years": "2020-Present"}],
#                         "skills": ["Python", "FastAPI", "Docker"],
#                     },
#                     # "jd_json": "{Job Description}",
#                 }
#             ]
#         }
#     }
#
#
# app = FastAPI(title="Resume Parsing & Evaluation")
#
# """
#     Create a fastapi server for LLM validation of resumes.
# """
#
#
# def load_pdf_text(file_path: str) -> str:
#     loader = PyMuPDFLoader(file_path)
#     pages = loader.load()
#
#     return " ".join(page.page_content for page in pages)
#
#
# # UPDATED FOR STREAMING RESPONSE CAPABILITY
# @app.post("/upload_resume_file", status_code=status.HTTP_200_OK)
# async def upload_resume_file(resume_file: UploadFile = RESUME_FILE_UPLOAD):
#     if not resume_file.filename:
#         raise HTTPException(status_code=400, detail="No file found")
#     if not resume_file.filename.endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Only PDF format supported")
#
#     if os.path.exists(RESUME_UPLOAD_FOLDER):
#         file_path = os.path.join(RESUME_UPLOAD_FOLDER, resume_file.filename)
#     else:
#         os.makedirs(RESUME_UPLOAD_FOLDER, exist_ok=True)
#         file_path = os.path.join(RESUME_UPLOAD_FOLDER, resume_file.filename)
#
#     with open(file_path, "wb") as f:
#         shutil.copyfileobj(resume_file.file, f)
#
#     return {"message": "Resume uploaded successfully"}
#
#
# @app.get("/resume_parser")
# async def resume_parser(resume_path: str):
#     """
#     Endpoint to stream LLM responses.
#     Calls the LLM service to get the asynchronous generator.
#     """
#     raw_resume_text = load_pdf_text(RESUME_UPLOAD_FOLDER + resume_path)
#
#     try:
#         response = await extract_resume_info(raw_resume_text)
#
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to start LLM parsing stream: {e}")
#
#
# @app.post("/evaluate_resume", status_code=status.HTTP_200_OK)
# async def evaluate_resume(payload: ResumeEvaluationRequest):
#     """
#     EValuate resume by LLM 2
#     Expect response in JSON.
#     """
#
#     resume_json = payload.resume_json
#     jd_json = payload.jd_json
#
#     # Calls Evaluation LLM in llm_chain_agent.py
#     try:
#         response = await evaluate_resume_against_jd(jd_json, resume_json)
#
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to start LLM evaluation stream: {e}")
#
#
# @app.post("/parse_and_evaluate", status_code=status.HTTP_200_OK)
# async def parse_and_evaluate(combined_json: Dict[str, Any]):
#     resume_data = combined_json.get("resume_data")
#     jd_json = combined_json.get("jd_json")
#
#     print(resume_data, "\n\n", jd_json)
#
#     return await combined_parse_evaluate(resume_data, jd_json)
#
#
#
# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# class JDTextRequest(BaseModel):
#     jd_text: str
#     jd_name: str
#
#
# def clean_jd_response(jd_response) -> dict:
#     """Clean the JD response by handling both string and dict responses"""
#     try:
#         # If it's already a dictionary, return it directly
#         if isinstance(jd_response, dict):
#             return jd_response
#
#         # If it's a string, clean and parse it
#         if isinstance(jd_response, str):
#             cleaned = jd_response.strip()
#             if cleaned.startswith('`') and cleaned.endswith('`'):
#                 cleaned = cleaned[1:-1].strip()
#             return json.loads(cleaned)
#
#         # If it's neither string nor dict, try to convert to string first
#         str_response = str(jd_response).strip()
#         if str_response.startswith('`') and str_response.endswith('`'):
#             str_response = str_response[1:-1].strip()
#         return json.loads(str_response)
#
#     except json.JSONDecodeError as e:
#         logger.error(f"Failed to parse JD JSON: {e}")
#         logger.error(f"Raw content type: {type(jd_response)}")
#         logger.error(f"Raw content: {jd_response}")
#         raise ValueError(f"Failed to decode JSON: {e}\nRaw content: `{jd_response}`")
#     except Exception as e:
#         logger.error(f"Unexpected error in clean_jd_response: {e}")
#         logger.error(f"Response type: {type(jd_response)}")
#         logger.error(f"Response content: {jd_response}")
#         raise ValueError(f"Failed to process JD response: {e}")
#
#
# @app.post("/upload_jd_text/")
# async def upload_jd_text(request: JDTextRequest):
#     jd_text = request.jd_text.strip()  # Strip whitespace
#     jd_name = request.jd_name.strip()  # Strip whitespace
#
#     if not jd_text or not jd_name:
#         raise HTTPException(status_code=400, detail="Missing JD text or JD name.")
#
#     try:
#         # Clean the JD text - remove excessive newlines and normalize
#         cleaned_jd_text = re.sub(r'\n+', ' ', jd_text)  # Replace multiple newlines with space
#         cleaned_jd_text = re.sub(r'\s+', ' ', cleaned_jd_text)  # Replace multiple spaces with single space
#
#         # Extract JD info from cleaned text
#         jd_structured = extract_jd_info(cleaned_jd_text)
#         if not jd_structured:
#             raise HTTPException(status_code=400, detail="Failed to parse JD text")
#
#         # Use consistent folder name
#         os.makedirs("jd_json", exist_ok=True)
#
#         # Create safe filename
#         safe_filename = re.sub(r'[^\w\s-]', '', jd_name)  # Remove special characters
#         safe_filename = re.sub(r'[-\s]+', '_', safe_filename)  # Replace spaces and hyphens with underscore
#         output_path = os.path.join("jd_json", f"{safe_filename}.json")
#
#         # Save with proper JSON formatting
#         with open(output_path, "w", encoding='utf-8') as f:
#             json.dump(jd_structured, f, indent=2, ensure_ascii=False)
#
#         return {
#             "status": "success",
#             "message": f"JD saved as {safe_filename}.json",
#             "file": f"{safe_filename}.json"
#         }
#     except json.JSONDecodeError as e:
#         raise HTTPException(status_code=400, detail=f"JSON decode error: {str(e)}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error saving JD: {str(e)}")
#
#
# # Update the list endpoint to match the folder:
# @app.get("/list_jds")
# def list_jds():
#     jd_folder = "jd_json"  # Match the folder used in upload
#     if not os.path.exists(jd_folder):
#         return {}
#
#     files = os.listdir(jd_folder)
#     return {
#         f.replace(".json", "").replace("_", " "): f
#         for f in files if f.endswith(".json")
#     }
#
# @app.post("/save_jd")
# async def save_jd(request: Request):
#     """Alternative endpoint for saving JD from raw text"""
#     try:
#         # Get raw body content
#         body = await request.body()
#         jd_text = body.decode("utf-8").strip()
#
#         if not jd_text:
#             return JSONResponse(
#                 status_code=400,
#                 content={"detail": "Empty JD text"}
#             )
#
#         # Parse the JD using your function
#         jd_response = extract_jd_info(jd_text)
#         if not jd_response:
#             return JSONResponse(
#                 status_code=400,
#                 content={"detail": "Failed to parse JD text"}
#             )
#
#         # Log the response for debugging
#         logger.info(f"save_jd - JD response type: {type(jd_response)}")
#         logger.info(f"save_jd - JD response content: {jd_response}")
#
#         # Clean and parse the response (handles both dict and string responses)
#         jd_structured = clean_jd_response(jd_response)
#
#         # Generate a filename based on job title or timestamp
#         job_title = jd_structured.get("Job_Title", "Untitled_Job")
#         safe_filename = job_title.replace(" ", "_").replace("/", "_").replace("\\", "_")
#         safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._-")
#
#         # Create directory and save
#         os.makedirs("jd_json", exist_ok=True)
#         output_path = os.path.join("jd_json", f"{safe_filename}.json")
#
#         with open(output_path, "w", encoding='utf-8') as f:
#             json.dump(jd_structured, f, indent=2, ensure_ascii=False)
#
#         return JSONResponse(content={
#             "message": "JD saved successfully",
#             "filename": f"{safe_filename}.json",
#             "parsed_data": jd_structured
#         })
#
#     except ValueError as ve:
#         return JSONResponse(
#             status_code=400,
#             content={"detail": str(ve)}
#         )
#     except Exception as e:
#         logger.error(f"Error in save_jd: {str(e)}")
#         logger.error(f"Error type: {type(e)}")
#         return JSONResponse(
#             status_code=500,
#             content={"detail": f"Failed to save JD: {str(e)}"}
#         )
#
#
# @app.get("/")
# async def docs():
#     return RedirectResponse("/docs")
#
#
# # For local debug purpose
# if __name__ == "__main__":
#     uvicorn.run(app)
#
#
