# http routes, validate request inputs, handle api level errors
import uuid
from typing import Any, Dict, List, Optional

from langsmith import traceable

from fastapi import APIRouter, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.pipeline.workflow import run_matcher_graph
from schemas.responses import MatchResponse
from src.utils.logger import APP_LOGGER

matcher_router = APIRouter(prefix='/api', tags=['matcher'])

SUPPORTED_FILE_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

@matcher_router.post('/match', response_model=MatchResponse)
@traceable(name='match_resume')
async def match_resume(resume_file: UploadFile = File(...), job_description: str = Form(...)):
    """ Match resume to job description using AI. Business logic layer is delegated to langgraph"""
    if resume_file.content_type not in SUPPORTED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="JD can't be empty")

    try:
        # Run the LangGraph workflow directly passing the file-like object
        response = await run_matcher_graph(file_obj=resume_file.file, jd_text=job_description)
        return response
    except HTTPException:
        raise
    except Exception as e:
        APP_LOGGER.exception("Unhandled error in /api/match: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
