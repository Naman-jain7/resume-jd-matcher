from pydantic import Field, BaseModel
from typing import Annotated, Optional, List

class RewriteSuggestion(BaseModel):
    section: Annotated[str, Field(..., description="The section of the resume to update (e.g., 'Summary', 'Experience', 'Projects')")]
    
    original_text: Annotated[str, Field(..., description="The original text from the resume that needs improvement")]
    suggested_text: Annotated[str, Field(..., description="The tailored, optimized text incorporating the missing JD keywords")]
    
    rationale: Annotated[str, Field(..., description="Why this change helps close the gap with the job description")]

class MatchResponse(BaseModel):
    """
    Response schema for resume matching API.
    request_id, match_score, matched_skills, missing_skills, rewrite_suggestions, status
    """
    
    match_score: Annotated[int, Field(..., ge=0, le=100, description='Match score between 0 and 10')]
    summary: Annotated[str, Field(..., description='A concise narrative summary explaining the match score and overall fit')]

    matched_skills: Annotated[
        Optional[List[str]], Field(default_factory=list, description='Skills found in both resume and job description')
    ]
    missing_skills: Annotated[
        Optional[List[str]], Field(default_factory=list, description='Critical Skills required in job description but missing in resume')
    ]
    
    rewrite_suggestions: Annotated[
        List[RewriteSuggestion], 
        Field(default_factory=list, description="Structured rewrite suggestions mapping directly back to resume sections")
    ]
    