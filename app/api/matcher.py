# http routes, validate request inputs, handle api level errors
import uuid
from typing import Any, Dict, List, Optional

from langsmith import traceable

from fastapi import APIRouter, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.graphs.matcher_graph import run_matcher_graph
from app.models.schemas import MatchResponse
from app.services.ingestion import extract_text_from_file

matcher_router = APIRouter(prefix='/api', tags=['matcher'])

SUPPORTED_FILE_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

@traceable(name='match_resume')
@matcher_router.post('/match')
async def match_resume(resume_file: UploadFile = File(...), job_description: str = Form(...)):
    """ Match resume to job description using AI. Business logic layer will be delegated to langgraph later"""
    if resume_file.content_type not in SUPPORTED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="JD can't be empty")

    request_id = str(uuid.uuid4())

    # extract text from resume file
    resume_text = await extract_text_from_file(resume_file)

    graph_res = await run_matcher_graph(resume_text=resume_text, job_description_text=job_description)

    return MatchResponse(
        request_id=request_id,
        match_score=graph_res["match_score"],
        matched_skills=graph_res["matched_skills"],
        missing_skills=graph_res["missing_skills"],
        rewrite_suggestions=graph_res["rewrite_suggestions"],
        status="completed",
    )
