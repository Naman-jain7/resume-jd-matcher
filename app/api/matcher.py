# http routes, validate request inputs, handle api level errors
from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from app.models.schemas import MatchResponse
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

    # ------------STUB RESPONSE---------------------
    return MatchResponse(
        request_id=request_id,
        match_score=0,
        matched_skills=[],
        missing_skills=[],
        rewrite_suggestions=[],
        status="stub_response",
    )
    # ------------STUB RESPONSE---------------------