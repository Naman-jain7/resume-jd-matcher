from pydantic import BaseModel, Field
from typing import List, Annotated, Optional, Dict

class MatchResponse(BaseModel):
    """
    Response schema for resume matching API.
    request_id, match_score, matched_skills, missing_skills, rewrite_suggestions, status
    """
    request_id: Annotated[str, Field(..., description='Request ID for match request')]
    match_score: Annotated[int, Field(..., ge=0, le=100, description='Match score between 0 and 100')]
    matched_skills: Annotated[Optional[List[str]], Field(default_factory=list, description='Skills found in both resume and job description')]
    missing_skills: Annotated[Optional[List[str]], Field(default_factory=list, description='Skills required in job description but missing in resume')]
    rewrite_suggestions: Annotated[List[Dict[str, str]], Field(default_factory=list, description="Resume rewrite suggestions aligned to JD")]
    status: Annotated[str, Field(..., description='Processing status of the request')]