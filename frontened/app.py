
import streamlit as st
import requests
import base64
import os

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000"

# --- Page Config ---
st.set_page_config(
    page_title="AI Resume Matcher",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Enhanced CSS Styling ---
st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        /* Global Styles */
        .stApp {
            background: #ffffff;
            font-family: 'Poppins', sans-serif;
            color: #2c3e50;
        }

        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Custom Header */
        .main-header {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 50%, #dee2e6 100%);
            padding: 1rem 0;
            text-align: center;
            margin-bottom: 1rem;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            border: 1px solid #e9ecef;
        }

        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #2c3e50;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }

        .subtitle {
            font-size: 1rem;
            color: #6c757d;
            margin-top: 0.3rem;
            font-weight: 300;
        }

        /* Sidebar Styling - Fixed for dark theme */
        .css-1d391kg {
            background: #2c3e50 !important;
            border-right: 1px solid #34495e !important;
        }

        .css-1d391kg .css-1v0mbdj {
            color: #ffffff !important;
        }

        /* Sidebar content styling */
        .css-1d391kg .stMarkdown,
        .css-1d391kg .stMarkdown p,
        .css-1d391kg .stMarkdown h1,
        .css-1d391kg .stMarkdown h2,
        .css-1d391kg .stMarkdown h3,
        .css-1d391kg .stMarkdown h4,
        .css-1d391kg .stMarkdown h5,
        .css-1d391kg .stMarkdown h6,
        .css-1d391kg .stMarkdown li,
        .css-1d391kg .stMarkdown ol,
        .css-1d391kg .stMarkdown ul {
            color: #ffffff !important;
        }

        /* Sidebar code elements */
        .css-1d391kg .stMarkdown code {
            background: #34495e !important;
            color: #e74c3c !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
            font-size: 0.85em !important;
        }

        .sidebar-content {
           background: rgba(255, 255, 255, 0.8) !important;
            border-radius: 12px;
            padding: 1rem;
            margin: 0.8rem 0;
            border: 1px solid #34495e;
        }

        .sidebar-title {
            color: #080707 !important;
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.8rem;
        }

        /* Main Content Cards */
        .content-card {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 1.2rem;
            margin: 1rem 0;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .content-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.12);
        }

        .card-header {
            font-size: 1.3rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .card-icon {
            font-size: 1.4rem;
            color: #6c757d;
        }

        /* Custom Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #495057 0%, #6c757d 100%);
            color: white;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            box-shadow: 0 6px 15px rgba(73, 80, 87, 0.3);
            text-transform: uppercase;
            letter-spacing: 0.3px;
            height: 40px;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(73, 80, 87, 0.4);
            background: linear-gradient(135deg, #343a40 0%, #495057 100%);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Primary Action Button */
        .primary-btn {
            background: linear-gradient(135deg, #212529 0%, #343a40 100%) !important;
            box-shadow: 0 6px 15px rgba(33, 37, 41, 0.4) !important;
        }

        .primary-btn:hover {
            box-shadow: 0 8px 20px rgba(33, 37, 41, 0.5) !important;
        }

        /* Success and Reject Buttons */
        .success-btn {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
            box-shadow: 0 6px 15px rgba(40, 167, 69, 0.4) !important;
        }

        .reject-btn {
            background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%) !important;
            box-shadow: 0 6px 15px rgba(220, 53, 69, 0.4) !important;
        }

        /* File Uploader */
        .uploadedFile {
            background: rgba(108, 117, 125, 0.1);
            border-radius: 8px;
            padding: 0.8rem;
            border: 2px dashed #6c757d;
        }

        .stFileUploader > div {
            padding: 0.5rem 0;
        }

        .stFileUploader label {
            font-size: 0.9rem;
            font-weight: 500;
            color: #2c3e50;
        }

        /* Selectbox */
        .stSelectbox > div > div {
            background: #ffffff;
            border-radius: 8px;
            border: 2px solid #e9ecef;
            min-height: 40px;
        }

        .stSelectbox label {
            font-size: 0.9rem;
            font-weight: 500;
            color: #2c3e50;
        }
           /* 🔧 Metric Box Styling: White Background + Black Text */
        [data-testid="metric-container"] {
            background-color: #ffffff !important;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            color: black !important;
        }
        
        /* Force label to black */
        [data-testid="metric-container"] label {
            color: black !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }
        
        /* Force metric value to black */
        [data-testid="metric-container"] .stMetricValue {
            color: black !important;
            font-weight: 700 !important;
            font-size: 1.6rem !important;
        }
        
        /* Catch any span or div overriding inside metric */
        [data-testid="metric-container"] * {
            color: black !important;
        }




        /* Candidate Name Display */
        .candidate-name-display {
            background: linear-gradient(135deg, #495057 0%, #6c757d 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            font-size: 2rem;
            font-weight: 700;
            margin: 1.5rem 0;
            box-shadow: 0 12px 30px rgba(73, 80, 87, 0.3);
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        /* Results Section */
        .results-section {
            background: #f8f9fa;
            border-radius: 20px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 15px 30px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }

        /* Skills Section */
        .skills-card {
            background: #ffffff;
            color: black;
            border-radius: 12px;
            padding: 1.2rem;
            margin: 0.8rem 0;
            border-left: 4px solid #6c757d;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }

        .skills-header {
            font-size: 1.1rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 0.8rem;
        }

        .skill-item {
            background: rgba(108, 117, 125, 0.1);
            color: #2c3e50;
            padding: 0.4rem 0.8rem;
            border-radius: 15px;
            margin: 0.2rem 0;
            border-left: 3px solid #6c757d;
            font-size: 0.9rem;
            border: 1px solid #e9ecef;
        }

        /* Status Messages - Fixed for better visibility */
        .stSuccess {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.8rem !important;
            border: none !important;
            font-size: 0.9rem !important;
        }

        .stError {
            background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%) !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.8rem !important;
            border: none !important;
            font-size: 0.9rem !important;
        }

        .stWarning {
            background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%) !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.8rem !important;
            border: none !important;
            font-size: 0.9rem !important;
        }

        .stInfo {
            background: linear-gradient(135deg, #17a2b8 0%, #20c997 100%) !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.8rem !important;
            border: none !important;
            font-size: 0.9rem !important;
        }

        /* Fix for info messages text visibility */
        .stInfo > div {
            color: white !important;
        }

        .stInfo p {
            color: white !important;
        }

        /* Loading Spinner */
        .stSpinner {
            color: #6c757d;
        }

        /* Links */
        .profile-link {
            background: linear-gradient(135deg, #495057 0%, #6c757d 100%);
            color: white;
            text-decoration: none;
            padding: 0.4rem 0.8rem;
            border-radius: 15px;
            display: inline-block;
            margin: 0.3rem;
            transition: transform 0.3s ease;
            font-size: 0.9rem;
        }

        .profile-link:hover {
            transform: translateY(-2px);
            color: white;
            text-decoration: none;
            background: linear-gradient(135deg, #343a40 0%, #495057 100%);
        }

        /* Compact spacing */
        .element-container {
            margin-bottom: 0.5rem;
        }

        /* Text colors */
        .stMarkdown {
            color: #2c3e50;
        }

        /* Input fields */
        .stTextInput > div > div > input {
            background: #ffffff;
            color: #2c3e50;
            border: 1px solid #e9ecef;
        }

        .stTextArea > div > div > textarea {
            background: #ffffff;
            color: #2c3e50;
            border: 1px solid #e9ecef;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .main-title {
                font-size: 2rem;
            }

            .content-card {
                padding: 1rem;
            }

            .card-header {
                font-size: 1.2rem;
            }

            .stButton > button {
                padding: 0.4rem 1rem;
                font-size: 0.8rem;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- Custom Header ---
st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🚀 AI Resume Matcher</h1>
        <p class="subtitle">Intelligent Resume Screening with Advanced AI Analytics</p>
    </div>
""", unsafe_allow_html=True)
#
# --- Sidebar About Section ---
st.sidebar.markdown("""
    <div class="sidebar-content">
        <h3 class="sidebar-title">📊 About</h3>
        <p>This application uses an AI-powered backend to score resumes against job descriptions, providing insights into skill and experience matches.</p>
    </div>
""", unsafe_allow_html=True)

# # --- Sidebar About Section ---
# st.sidebar.image("app/assets/img.png", use_column_width=True)
#
# st.sidebar.markdown("""
#     <div class="sidebar-content">
#         <h3 class="sidebar-title">📊 About</h3>
#         <p>This application uses an AI-powered backend to score resumes against job descriptions, providing insights into skill and experience matches.</p>
#     </div>
# """, unsafe_allow_html=True)

# --- Session State ---
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


# --- Backend API Calls ---
@st.cache_data(ttl=300)
def fetch_jd_list():
    try:
        res = requests.get(f"{BACKEND_URL}/list-jds/")
        res.raise_for_status()
        return res.json().get("jd_list", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching JD list: {e}. Is the backend running at {BACKEND_URL}?")
        return []


# --- Main Content Layout ---
col1, col2 = st.columns([1, 1])

with col1:
    # --- Upload Resume ---
    st.markdown("""
        <div class="content-card">
            <h2 class="card-header">
                <span class="card-icon">📄</span>
                Upload Resume
            </h2>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose PDF file", type=["pdf"], key="resume_uploader")

    if uploaded_file:
        if st.session_state.uploaded_resume_name != uploaded_file.name or not st.session_state.resume_uploaded_successfully:
            st.session_state.uploaded_resume_name = uploaded_file.name
            st.session_state.resume_uploaded_successfully = False
            st.session_state.match_result = None
            st.session_state.action_status = ""

            file_bytes = uploaded_file.read()
            encoded_file_data = base64.b64encode(file_bytes).decode("utf-8")
            upload_payload = {
                "filename": uploaded_file.name,
                "file_data": encoded_file_data
            }

            try:
                with st.spinner(f"🔄 Uploading '{uploaded_file.name}'..."):
                    res = requests.post(f"{BACKEND_URL}/upload-resume/", json=upload_payload)
                    res.raise_for_status()
                    st.session_state.resume_uploaded_successfully = True
                    st.success(f"✅ Resume uploaded successfully!")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Upload failed: {e}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
            st.rerun()
    else:
        if st.session_state.uploaded_resume_name:
            st.session_state.uploaded_resume_name = None
            st.session_state.resume_uploaded_successfully = False
            st.session_state.match_result = None
            st.session_state.action_status = ""
            st.rerun()

with col2:
    # --- Select JD ---
    st.markdown("""
        <div class="content-card">
            <h2 class="card-header">
                <span class="card-icon">🎯</span>
                Job Description
            </h2>
        </div>
    """, unsafe_allow_html=True)

    jd_list = fetch_jd_list()

    if not jd_list:
        st.warning("⚠️ No job descriptions found. Please add .json files to backend.")
        selected_jd = "-- No JDs Available --"
    else:
        current_jd_index = 0
        if st.session_state.selected_jd_name and st.session_state.selected_jd_name in jd_list:
            current_jd_index = jd_list.index(st.session_state.selected_jd_name)

        selected_jd = st.selectbox(
            "Choose JD",
            jd_list,
            key="jd_selector",
            index=current_jd_index
        )

if selected_jd != st.session_state.selected_jd_name:
    st.session_state.selected_jd_name = selected_jd
    st.session_state.match_result = None
    st.session_state.action_status = ""
    st.rerun()

# --- Run Matching ---
st.markdown("""
    <div class="content-card">
        <h2 class="card-header">
            <span class="card-icon">🔍</span>
            Generate Score
        </h2>
    </div>
""", unsafe_allow_html=True)

run_matching_disabled = (
        not st.session_state.resume_uploaded_successfully or
        not st.session_state.uploaded_resume_name or
        not selected_jd or
        selected_jd == "-- No JDs Available --"
)

if st.button("🚀 Run ATS Matching", disabled=run_matching_disabled, key="run_matching"):
    try:
        with st.spinner("🔄 Running ATS Matching..."):
            response = requests.post(f"{BACKEND_URL}/match/", json={
                "jd_filename": selected_jd,
                "resume_filename": st.session_state.uploaded_resume_name
            })
            response.raise_for_status()
            st.session_state.match_result = response.json()
            st.success("✅ Matching complete!")
            st.session_state.action_status = ""
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Matching error: {e}")
    except Exception as e:
        st.error(f"❌ Failed to match: {e}")

if run_matching_disabled:
    if not st.session_state.resume_uploaded_successfully:
        st.info("ℹ️ Upload a resume first to enable matching.")
    elif selected_jd == "-- No JDs Available --":
        st.info("ℹ️ No Job Descriptions available. Please add some to the backend.")

# --- Show Results ---
if st.session_state.match_result:
    result = st.session_state.match_result
    name = result.get("name", "Candidate Name Not Found")

    # 🔽 Collapsible Section for ATS Results
    with st.expander("📊 View ATS Results", expanded=False):
        # Display Candidate Name
        st.markdown(f'<div class="candidate-name-display">👤 {name}</div>', unsafe_allow_html=True)

        st.markdown('<div class="results-section">', unsafe_allow_html=True)

        # Resume and JD Info
        st.markdown(f"**📄 Resume:** `{st.session_state.uploaded_resume_name}`")
        st.markdown(f"**🎯 Job:** `{st.session_state.selected_jd_name}`")

        # ✅ Custom Metric Cards with black text
        skill = result.get("skill_score", "N/A")
        exp = result.get("experience_score", "N/A")
        match = result.get("match_score", "0%")
        cgpa = result.get("cgpa", "Not given")

        st.markdown(f"""
            <div style="display: flex; gap: 1rem; justify-content: space-between; margin: 1.5rem 0;">
                <div style="flex: 1; background: white; color: black; text-align: center; padding: 1rem; border-radius: 10px;">
                    <div style="font-weight: 600; font-size: 1.1rem;">🎯 Skill Score</div>
                    <div style="font-weight: 700; font-size: 2rem;">{skill}</div>
                </div>
                <div style="flex: 1; background: white; color: black; text-align: center; padding: 1rem; border-radius: 10px;">
                    <div style="font-weight: 600; font-size: 1.1rem;">💼 Experience</div>
                    <div style="font-weight: 700; font-size: 2rem;">{exp}</div>
                </div>
                <div style="flex: 1; background: white; color: black; text-align: center; padding: 1rem; border-radius: 10px;">
                    <div style="font-weight: 600; font-size: 1.1rem;">📈 Match</div>
                    <div style="font-weight: 700; font-size: 2rem;">{match}</div>
                </div>
                <div style="flex: 1; background: white; color: black; text-align: center; padding: 1rem; border-radius: 10px;">
                    <div style="font-weight: 600; font-size: 1.1rem;">🎓 CGPA</div>
                    <div style="font-weight: 700; font-size: 2rem;">{cgpa}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Links
        linkedin = result.get("linkedin", "")
        github = result.get("github", "")

        col1, col2 = st.columns(2)
        with col1:
            if linkedin:
                st.markdown(f'<a href="{linkedin}" class="profile-link">🔗 LinkedIn</a>', unsafe_allow_html=True)
        with col2:
            if github:
                st.markdown(f'<a href="{github}" class="profile-link">🐙 GitHub</a>', unsafe_allow_html=True)

        st.markdown("---")

        # Skills Section
        st.markdown("### 🛠️ Skills Analysis")
        col_m1, col_m2, col_m3 = st.columns(3)

        with col_m1:
            st.markdown('<div class="skills-card"><h4 class="skills-header">✅ Matched</h4>', unsafe_allow_html=True)
            for s in result.get("matched_skills", []):
                st.markdown(f'<div class="skill-item">{s}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_m2:
            st.markdown('<div class="skills-card"><h4 class="skills-header">❌ Missing</h4>', unsafe_allow_html=True)
            for s in result.get("missing_skills", []):
                st.markdown(f'<div class="skill-item">{s}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_m3:
            st.markdown('<div class="skills-card"><h4 class="skills-header">💡 Extra</h4>', unsafe_allow_html=True)
            for s in result.get("extra_skills", []):
                st.markdown(f'<div class="skill-item">{s}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # AI Feedback
        st.markdown("### 🤖 AI Feedback")
        col_pos, col_neg = st.columns(2)

        with col_pos:
            st.markdown('<div class="skills-card"><h4 class="skills-header">👍 Strengths</h4>', unsafe_allow_html=True)
            for s in result.get("positive", []):
                st.markdown(f'<div class="skill-item">{s}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_neg:
            st.markdown('<div class="skills-card"><h4 class="skills-header">👎 Improvements</h4>',
                        unsafe_allow_html=True)
            for s in result.get("negative", []):
                st.markdown(f'<div class="skill-item">{s}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Action Buttons
    st.markdown("""
        <div class="content-card">
            <h2 class="card-header">
                <span class="card-icon">⚡</span>
                Action
            </h2>
        </div>
    """, unsafe_allow_html=True)

    col_select, col_reject = st.columns(2)

    with col_select:
        if st.button("✔️ Select", use_container_width=True, key="select_btn"):
            try:
                r = requests.post(f"{BACKEND_URL}/store-selection/", json={
                    "resume_file": st.session_state.uploaded_resume_name,
                    "jd_file": selected_jd,
                    "status": "select",
                    "match_score": result.get("match_score", "0%"),
                    "linkedin": linkedin,
                    "github": github,
                    "name": name
                })
                r.raise_for_status()
                st.session_state.action_status = f"Candidate {name} **selected**."
                st.success(f"✅ {st.session_state.action_status}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Selection failed: {e}")

    with col_reject:
        if st.button("❌ Reject", use_container_width=True, key="reject_btn"):
            try:
                r = requests.post(f"{BACKEND_URL}/store-selection/", json={
                    "resume_file": st.session_state.uploaded_resume_name,
                    "jd_file": selected_jd,
                    "status": "reject",
                    "match_score": result.get("match_score", "0%"),
                    "name": name
                })
                r.raise_for_status()
                st.session_state.action_status = f"Candidate {name} **rejected**."
                st.warning(f"⚠️ {st.session_state.action_status}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Rejection failed: {e}")

    if st.session_state.action_status:
        st.markdown(f"""
            <div style="text-align: center; margin-top: 1.5rem; padding: 0.8rem; background: rgba(108, 117, 125, 0.1); border-radius: 8px; border: 1px solid #e9ecef;">
                <h4 style="color: #2c3e50;">📋 Status: {st.session_state.action_status}</h4>
            </div>
        """, unsafe_allow_html=True)