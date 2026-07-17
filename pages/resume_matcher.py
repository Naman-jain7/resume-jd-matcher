import streamlit as st
from requests import RequestException

from api_client import match_resume_api


st.set_page_config(
    page_title="Resume JD Matcher",
    layout="wide",
)


st.header("Resume JD Matcher")

with st.container():
    st.title("AI Career Compass")
    st.caption("Upload your resume and paste a job description to prepare a match analysis.")

st.divider()

st.subheader("Inputs")

left_column, right_column = st.columns(2, gap="large")

with left_column:
    resume_file = st.file_uploader(
        "Resume",
        type=["pdf", "docx"],
        help="Upload a PDF or DOCX resume.",
    )

with right_column:
    job_description = st.text_area(
        "Job Description",
        placeholder="Paste the raw job description text here...",
        height=250,
    )

analyze_clicked = st.button("Analyze Match", type="primary")

if analyze_clicked:
    if resume_file is None:
        st.error("Please upload a resume before analyzing the match.")
    elif not job_description.strip():
        st.error("Please paste a job description before analyzing the match.")
    else:
        with st.spinner("Analyzing resume match..."):
            try:
                st.session_state["match_response"] = match_resume_api(
                    resume_file,
                    resume_file.name,
                    job_description,
                )
            except RequestException as exc:
                st.session_state.pop("match_response", None)
                st.error(f"Analysis failed: {exc}")

response = st.session_state.get("match_response")

if response:
    st.divider()
    st.subheader("Analysis & Results")

    score = response.get("match_score", 0)
    summary = response.get("summary", "")
    matched_skills = response.get("matched_skills") or []
    missing_skills = response.get("missing_skills") or []
    rewrite_suggestions = response.get("rewrite_suggestions") or []

    st.metric("Match Score", f"{score}%")
    st.progress(max(0, min(int(score), 100)) / 100)

    st.subheader("Summary")
    st.write(summary or "No summary was returned.")

    skills_left, skills_right = st.columns(2, gap="large")

    with skills_left:
        st.subheader("Matched Skills")
        if matched_skills:
            for skill in matched_skills:
                st.success(skill)
        else:
            st.info("No matched skills were returned.")

    with skills_right:
        st.subheader("Missing Skills")
        if missing_skills:
            for skill in missing_skills:
                st.warning(skill)
        else:
            st.success("No missing skills were returned.")

    st.subheader("Rewrite Suggestions")
    if rewrite_suggestions:
        for index, suggestion in enumerate(rewrite_suggestions, start=1):
            if isinstance(suggestion, dict):
                section = suggestion.get("section", f"Suggestion {index}")
                with st.expander(section, expanded=index == 1):
                    st.markdown("**Original text**")
                    st.write(suggestion.get("original_text", "Not provided."))
                    st.markdown("**Suggested text**")
                    st.write(suggestion.get("suggested_text", "Not provided."))
                    st.markdown("**Rationale**")
                    st.write(suggestion.get("rationale", "Not provided."))
            else:
                st.write(f"{index}. {suggestion}")
    else:
        st.info("No rewrite suggestions were returned.")
