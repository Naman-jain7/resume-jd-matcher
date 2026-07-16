from typing import Dict, List, Any, Annotated, Optional
from pydantic import BaseModel, Field
from schemas.parse_resume import StructuralMetadata
from schemas.responses import RewriteSuggestion

class MatcherState(BaseModel):
    resume_text: str
    resume_skills: Dict[str, Any]
    jd_text: str
    jd_skills: Dict[str, Any]

    match_score: Annotated[int, Field(..., ge=0, le=100, description='Match score between 0 and 100')]
    summary: Annotated[str, Field(..., description='A concise narrative summary explaining the match score and overall fit')]

    matched_skills: Annotated[
        Optional[List[str]], Field(default_factory=list, description='Skills found in both resume and job description')
    ]
    missing_skills: Annotated[
        Optional[List[str]], Field(default_factory=list, description='Critical Skills required in job description but missing in resume')
    ]

    rewrite_suggestions: List[RewriteSuggestion]

    # ── Added for the pipeline workflow ──────────────────────────────────────
    # Raw PDF bytes carried into the graph so load_node can materialise the text.
    raw_file_bytes: Optional[bytes] = None
    # Structural metadata produced by parse_node; available to all downstream nodes.
    structural_metadata: Optional[StructuralMetadata] = None