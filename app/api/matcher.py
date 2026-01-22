# http routes, validate request inputs, handle api level errors
from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from app.models.schemas import MatchResponse
from app.graphs.matcher_graph import run_matcher_graph
from app.services.ingestion import extract_text_from_file
import uuid

matcher_router = APIRouter(prefix='/api', tags=['matcher'])

SUPPORTED_FILE_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

@matcher_router.post('/match')
async def match_resume(resume_file: UploadFile = File(...), job_description: str = Form(...))->MatchResponse:
    """ Match resume to job description using AI. Business logic layer will be delegated to langgraph later"""
    if resume_file.content_type not in SUPPORTED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="JD can't be empty")

    request_id = str(uuid.uuid4())

    resume_text = await extract_text_from_file(resume_file)

    graph_res = run_matcher_graph(resume_text=resume_text, job_description_text = job_description)

    return MatchResponse(
        request_id=request_id,
        match_score=graph_result["match_score"],
        matched_skills=graph_result["matched_skills"],
        missing_skills=graph_result["missing_skills"],
        rewrite_suggestions=graph_result["rewrite_suggestions"],
        status="completed",
    )