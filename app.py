"""Streamlit interface for the LangGraph Resume Analyzer."""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from document_loader import ResumeReadError, extract_resume_text
from resume_graph import analyze_resume


PROJECT_DIR = Path(__file__).resolve().parent
# Load the API key from this project. The parent lookup also supports the
# shared classroom workspace used during local development.
load_dotenv(PROJECT_DIR / ".env")
load_dotenv(PROJECT_DIR.parent / ".env")

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
)

st.title("📄 AI Resume Analyzer")
st.write(
    "Upload one resume to receive a structured, evidence-based review from a "
    "LangGraph agent powered by Groq."
)

with st.sidebar:
    st.header("How it works")
    st.markdown(
        "1. Upload one PDF, DOCX, or TXT resume.\n"
        "2. The app extracts its text.\n"
        "3. A LangGraph workflow analyzes it.\n"
        "4. Review the pros, cons, and improvements."
    )
    st.info(
        "The analysis is based only on the uploaded resume. It does not verify "
        "claims or make a hiring decision."
    )

# Stop early and show a clear message if the Groq key is missing.
if not os.getenv("GROQ_API_KEY"):
    st.error(
        "GROQ_API_KEY is not configured. Add it to a local .env file or the "
        "deployment platform's secret settings."
    )
    st.stop()

# Streamlit returns an UploadedFile after the student selects a file.
uploaded_resume = st.file_uploader(
    "Upload a resume",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=False,
    help="Supported formats: PDF, DOCX, and TXT. Maximum recommended size: 10 MB.",
)

if uploaded_resume is None:
    st.caption("No resume has been uploaded yet.")
    st.stop()

if uploaded_resume.size > 10 * 1024 * 1024:
    st.error("The uploaded file is larger than 10 MB. Please upload a smaller file.")
    st.stop()

# Convert the uploaded PDF, DOCX, or TXT file into plain text.
try:
    resume_text = extract_resume_text(
        filename=uploaded_resume.name,
        content=uploaded_resume.getvalue(),
    )
except ResumeReadError as error:
    st.error(str(error))
    st.stop()

with st.expander("Extracted resume text"):
    st.text(resume_text)

# The Groq API is called only after the user clicks this button.
if st.button("Analyze resume", type="primary", use_container_width=True):
    try:
        with st.spinner("The LangGraph agent is reviewing the resume..."):
            analysis = analyze_resume(resume_text)
        # Keep the result visible when Streamlit reruns the page.
        st.session_state["resume_analysis"] = analysis
        st.session_state["analyzed_file"] = uploaded_resume.name
    except Exception as error:
        st.error(f"The resume could not be analyzed: {error}")

# Read the saved structured result and display each section below.
analysis = st.session_state.get("resume_analysis")
if analysis is None or st.session_state.get("analyzed_file") != uploaded_resume.name:
    st.stop()

st.success("Resume analysis completed.")
st.subheader("Overall assessment")
st.write(analysis.executive_summary)

score_col, level_col, role_col = st.columns(3)
score_col.metric("Resume score", f"{analysis.resume_score}/100")
level_col.metric("Estimated level", analysis.candidate_snapshot.experience_level)
role_col.metric("Likely target role", analysis.candidate_snapshot.likely_target_role)

pros_tab, cons_tab, improve_tab, profile_tab = st.tabs(
    ["✅ Pros", "⚠️ Cons", "🛠 Improvements", "👤 Candidate snapshot"]
)

with pros_tab:
    for item in analysis.pros:
        st.markdown(f"- {item}")

with cons_tab:
    for item in analysis.cons:
        st.markdown(f"- {item}")

with improve_tab:
    for index, item in enumerate(analysis.improvement_plan, start=1):
        st.markdown(f"{index}. {item}")

with profile_tab:
    snapshot = analysis.candidate_snapshot
    st.markdown(f"**Profile summary:** {snapshot.profile_summary}")
    st.markdown("**Core skills:** " + ", ".join(snapshot.core_skills))
    st.markdown("**Strongest evidence:**")
    for item in snapshot.strongest_evidence:
        st.markdown(f"- {item}")

st.caption(
    "AI-generated feedback can be incomplete or incorrect. Review it before "
    "making changes to a resume or using it in a hiring process."
)
