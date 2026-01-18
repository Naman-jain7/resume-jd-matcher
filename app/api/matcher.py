from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import uuid

matcher_router = APIRouter(prefix='/api', tags=['matcher'])

@matcher_router.post('/match')
async def match_resume(resume: UploadFile = File(...), jd: str = Form(...)):
    """ Match resume to job description using AI """