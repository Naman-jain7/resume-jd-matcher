import streamlit as st


st.set_page_config(
    page_title="Resume JD Matcher",
    layout="wide",
)

st.title("Resume JD Matcher")
st.caption("Open the matcher page from the sidebar to upload a resume and paste a job description.")

st.page_link("pages/resume_matcher.py", label="Go to Resume Matcher")
