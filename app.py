"""Three-feature Streamlit interface for the LangGraph Resume Analyzer."""

import hashlib
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from document_loader import ResumeReadError, extract_resume_text
from resume_export import build_comparison_html, create_resume_docx
from resume_graph import analyze_resume, match_resume_to_job, tailor_resume_to_job


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")
load_dotenv(PROJECT_DIR.parent / ".env")

st.set_page_config(page_title="AI Resume Studio", page_icon="📄", layout="wide")


def read_uploaded_resume(uploaded_file):
    """Validate one Streamlit upload and return its extracted text."""

    if uploaded_file is None:
        return None
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("The resume is larger than 10 MB. Please upload a smaller file.")
        return None
    try:
        return extract_resume_text(uploaded_file.name, uploaded_file.getvalue())
    except ResumeReadError as error:
        st.error(str(error))
        return None


def input_fingerprint(uploaded_file, job_description: str = "") -> str:
    """Identify the exact inputs so an old result is never shown for a new file."""

    digest = hashlib.sha256(uploaded_file.getvalue())
    digest.update(job_description.strip().encode("utf-8"))
    return digest.hexdigest()


def render_items(items: list[str], empty_message: str = "None identified."):
    """Render a simple list without failing when a model returns an empty list."""

    if not items:
        st.caption(empty_message)
    for item in items:
        st.markdown(f"- {item}")


def friendly_error(error: Exception) -> str:
    """Hide provider internals and give the user a useful retry message."""

    message = str(error)
    if "json_validate_failed" in message or "valid format" in message:
        return "The AI response format was invalid. Please click the button again."
    return message


st.title("📄 AI Resume Studio")
st.write(
    "Review a resume, compare it with a job description, or create a truthful "
    "job-targeted version using LangGraph and Groq."
)

with st.sidebar:
    st.header("Workflow")
    st.markdown(
        "1. Choose a feature tab.\n"
        "2. Upload one resume.\n"
        "3. Add a job description when required.\n"
        "4. Run the relevant LangGraph workflow."
    )
    st.warning(
        "The system must not invent candidate information. Always review AI output "
        "before applying for a job or making a hiring decision."
    )

if not os.getenv("GROQ_API_KEY"):
    st.error("GROQ_API_KEY is missing. Add it to `.env` and restart the app.")
    st.stop()

review_tab, match_tab, tailor_tab = st.tabs(
    ["1️⃣ Resume analysis", "2️⃣ Job match", "3️⃣ Update resume"]
)

with review_tab:
    st.header("Resume strengths and weaknesses")
    review_file = st.file_uploader(
        "Upload a resume",
        type=["pdf", "docx", "txt"],
        key="review_file",
    )
    review_text = read_uploaded_resume(review_file)

    if review_text:
        with st.expander("Extracted resume text"):
            st.text(review_text)

        review_key = input_fingerprint(review_file)
        if st.button("Analyze resume", type="primary", key="review_button"):
            try:
                with st.spinner("Reviewing the resume..."):
                    st.session_state.review_result = analyze_resume(review_text)
                    st.session_state.review_key = review_key
            except Exception as error:
                st.error(f"The resume could not be analyzed: {friendly_error(error)}")

        analysis = st.session_state.get("review_result")
        if analysis and st.session_state.get("review_key") == review_key:
            st.success("Resume analysis completed.")
            st.subheader("Overall assessment")
            st.write(analysis.executive_summary)

            score_col, level_col, role_col = st.columns(3)
            score_col.metric("Resume score", f"{analysis.resume_score}/100")
            level_col.metric("Estimated level", analysis.candidate_snapshot.experience_level)
            role_col.metric("Likely role", analysis.candidate_snapshot.likely_target_role)

            pros_col, cons_col = st.columns(2)
            with pros_col:
                st.subheader("Pros")
                render_items(analysis.pros)
            with cons_col:
                st.subheader("Cons")
                render_items(analysis.cons)

            st.subheader("Improvement plan")
            for number, item in enumerate(analysis.improvement_plan, start=1):
                st.markdown(f"{number}. {item}")

with match_tab:
    st.header("Resume and job-description match")
    match_file = st.file_uploader(
        "Upload a resume",
        type=["pdf", "docx", "txt"],
        key="match_file",
    )
    match_job = st.text_area(
        "Paste the job description",
        height=240,
        key="match_job",
        placeholder="Paste the complete role description here...",
    )
    match_text = read_uploaded_resume(match_file)

    if match_text and match_job.strip():
        match_key = input_fingerprint(match_file, match_job)
        if st.button("Calculate match score", type="primary", key="match_button"):
            if len(match_job.strip()) < 100:
                st.error("Please provide a more complete job description (at least 100 characters).")
            else:
                try:
                    with st.spinner("Comparing the resume with the job description..."):
                        st.session_state.match_result = match_resume_to_job(
                            match_text, match_job.strip()
                        )
                        st.session_state.match_key = match_key
                except Exception as error:
                    st.error(
                        f"The job match could not be calculated: {friendly_error(error)}"
                    )

        match_result = st.session_state.get("match_result")
        if match_result and st.session_state.get("match_key") == match_key:
            st.success("Job-match analysis completed.")
            st.metric("Matching score", f"{match_result.match_score}/100")
            st.write(match_result.summary)

            matched_col, missing_col = st.columns(2)
            with matched_col:
                st.subheader("Matched requirements")
                render_items(match_result.matched_requirements)
                st.subheader("Transferable strengths")
                render_items(match_result.transferable_strengths)
            with missing_col:
                st.subheader("Missing or unsupported requirements")
                render_items(match_result.missing_requirements)
                st.subheader("Keyword gaps")
                render_items(match_result.keyword_gaps)

            st.subheader("Recommendations")
            render_items(match_result.recommendations)

with tailor_tab:
    st.header("Create a job-targeted resume")
    st.caption(
        "Python code safely reorders existing skills and bullet points according to "
        "job relevance. It does not generate or rewrite candidate claims."
    )
    tailor_file = st.file_uploader(
        "Upload a resume",
        type=["pdf", "docx", "txt"],
        key="tailor_file",
    )
    tailor_job = st.text_area(
        "Paste the target job description",
        height=240,
        key="tailor_job",
        placeholder="Paste the complete role description here...",
    )
    tailor_text = read_uploaded_resume(tailor_file)

    if tailor_text and tailor_job.strip():
        tailor_key = input_fingerprint(tailor_file, tailor_job)
        if st.button("Update resume", type="primary", key="tailor_button"):
            if len(tailor_job.strip()) < 100:
                st.error("Please provide a more complete job description (at least 100 characters).")
            else:
                try:
                    with st.spinner("Reassembling the resume using existing content..."):
                        st.session_state.tailor_result = tailor_resume_to_job(
                            tailor_text, tailor_job.strip()
                        )
                        st.session_state.tailor_key = tailor_key
                except Exception as error:
                    st.error(f"The resume could not be updated: {friendly_error(error)}")

        tailored = st.session_state.get("tailor_result")
        if tailored and st.session_state.get("tailor_key") == tailor_key:
            st.success("Updated resume created. Review every change before using it.")
            st.subheader("Highlighted comparison")
            st.caption("Red indicates removed or replaced text; green indicates new wording.")
            st.markdown(
                build_comparison_html(tailor_text, tailored.updated_resume),
                unsafe_allow_html=True,
            )

            st.subheader("What changed")
            render_items(tailored.change_summary)
            st.info(tailored.preserved_facts_confirmation)

            download_col, text_col = st.columns(2)
            with download_col:
                st.download_button(
                    "Download clean updated resume (DOCX)",
                    data=create_resume_docx(tailored.updated_resume),
                    file_name="updated_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            with text_col:
                st.download_button(
                    "Download clean updated resume (TXT)",
                    data=tailored.updated_resume,
                    file_name="updated_resume.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

st.divider()
st.caption(
    "AI-generated feedback can be incomplete or incorrect. Matching scores measure "
    "document alignment only and must not be treated as hiring decisions."
)
