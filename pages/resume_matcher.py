import streamlit as st


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
        height=360,
    )

analyze_clicked = st.button("Analyze Match", type="primary")

if analyze_clicked:
    st.divider()
    st.subheader("Analysis & Results")
    st.info("Results will be added here in the next step.")
