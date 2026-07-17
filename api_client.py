import os
import requests
from typing import Any, Dict

API_URL = os.getenv("MATCHER_API_URL", "http://localhost:8000/api/match")

CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

def match_resume_api(file_obj, filename: str, job_description: str) -> Dict[str, Any]:
    """
    Call the FastAPI matcher endpoint.
    
    Args:
        file_obj: BytesIO object from Streamlit file_uploader
        filename: Name of the uploaded file
        job_description: The job description text
        
    Returns:
        A dictionary containing the parsed MatchResponse fields (match_score, summary, etc.)
    """
    # Rewind file pointer just in case it was read earlier
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)

    file_extension = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""
    content_type = CONTENT_TYPES.get(file_extension, "application/octet-stream")

    files = {"resume_file": (filename, file_obj, content_type)}
    data = {"job_description": job_description}
    
    response = requests.post(API_URL, files=files, data=data)
    
    # Raise an exception if the request failed
    response.raise_for_status()
    
    return response.json()
