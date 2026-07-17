"""
src/pipeline/workflow.py
────────────────────────
LangGraph resume-matching pipeline.

Topology:
    START → load → parse → score (OllamaProvider)          ─┐
                         → extract_skills (OllamaLocal)    ─┴→ rewrite (OpenRouter) → END

• load          : PDF bytes → structured text   (pdfplumber, sync)
• parse         : text → StructuralMetadata     (OllamaLocalProvider, sync)
• score         : text+JD → match score/skills  (OllamaProvider,      async / parallel)
• extract_skills: text+JD → skill dicts         (OllamaLocalProvider, async / parallel)
• rewrite       : state   → rewrite suggestions (OpenRouterProvider,  async / fan-in)
"""

from __future__ import annotations

import io
from typing import Any, Dict, List

from langsmith import traceable
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from schemas.parse_resume import StructuralMetadata  # noqa: F401 (re-exported)
from schemas.responses import MatchResponse, RewriteSuggestion
from src.ingestion.loader import load_pdf_streamlit
from src.ingestion.parser import parse_resume
from src.llm.prompts import (
    MATCH_SCORE_PROMPT,
    REWRITE_SUGGESTIONS_PROMPT,
    SKILL_EXTRACTION_PROMPT,
)
from src.llm.providers import OllamaLocalProvider, OllamaProvider, OpenRouterProvider
from src.pipeline.state import MatcherState


# ─────────────────────────────────────────────────────────────────────────────
# Internal structured-output schemas (LLM response targets, not exposed to API)
# ─────────────────────────────────────────────────────────────────────────────


class _MatchScoreOutput(BaseModel):
    """Structured output for the score_node LLM call."""

    match_score: int = Field(ge=0, le=100, description="ATS match score 0-100.")
    summary: str = Field(description="Concise narrative explaining the match score.")
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)


class _SkillsOutput(BaseModel):
    """Structured output for the extract_skills_node LLM call."""

    resume_skills: Dict[str, Any] = Field(default_factory=dict)
    jd_skills: Dict[str, Any] = Field(default_factory=dict)


class _RewriteOutput(BaseModel):
    """Structured output for the rewrite_node LLM call."""

    rewrite_suggestions: List[RewriteSuggestion] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Node 1: load
# ─────────────────────────────────────────────────────────────────────────────


@traceable(name="load_node")
def load_node(state: MatcherState) -> Dict[str, Any]:
    """
    Read PDF bytes from state → extract spatially-aware text via pdfplumber.
    Produces: resume_text
    """
    if not state.raw_file_bytes:
        raise ValueError("load_node: 'raw_file_bytes' is empty — cannot load PDF.")

    file_obj = io.BytesIO(state.raw_file_bytes)
    resume_text = load_pdf_streamlit(file_obj)
    return {"resume_text": resume_text}


# ─────────────────────────────────────────────────────────────────────────────
# Node 2: parse
# ─────────────────────────────────────────────────────────────────────────────


@traceable(name="parse_node")
def parse_node(state: MatcherState) -> Dict[str, Any]:
    """
    Structural parsing via OllamaLocalProvider (llama3.2:3b).
    Produces: resume_text (normalised), structural_metadata
    """
    result = parse_resume(state.resume_text)
    return {
        "resume_text": result["normalized_content"],
        "structural_metadata": result["structural_metadata"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 3a: score  (parallel branch — OllamaProvider)
# ─────────────────────────────────────────────────────────────────────────────


@traceable(name="score_node")
async def score_node(state: MatcherState) -> Dict[str, Any]:
    """
    ATS match scoring via OllamaProvider (cloud Ollama).
    Uses raw resume_text + jd_text so it can run in parallel with extract_skills.
    Produces: match_score, summary, matched_skills, missing_skills
    """
    provider = OllamaLocalProvider()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an ATS evaluation expert. "
                "Return ONLY a structured JSON object — no extra text."
            ),
        },
        {
            "role": "user",
            "content": MATCH_SCORE_PROMPT.format(
                resume_data=state.resume_text,
                job_description_data=state.jd_text,
            ),
        },
    ]

    result: _MatchScoreOutput = await provider.agenerate(  # type: ignore[assignment]
        messages=messages,
        response_format=_MatchScoreOutput,
    )

    return {
        "match_score": result.match_score,
        "summary": result.summary,
        "matched_skills": result.matched_skills,
        "missing_skills": result.missing_skills,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 3b: extract_skills  (parallel branch — OllamaLocalProvider)
# ─────────────────────────────────────────────────────────────────────────────


@traceable(name="extract_skills_node")
async def extract_skills_node(state: MatcherState) -> Dict[str, Any]:
    """
    Skill extraction via OllamaLocalProvider (llama3.2:3b).
    Uses raw resume_text + jd_text so it can run in parallel with score.
    Produces: resume_skills, jd_skills
    """
    provider = OllamaLocalProvider()

    messages = [
        {
            "role": "system",
            "content": (
                "You are a skill extraction expert. "
                "Return ONLY a structured JSON object — no extra text."
            ),
        },
        {
            "role": "user",
            "content": SKILL_EXTRACTION_PROMPT.format(
                resume_text=state.resume_text,
                job_description_text=state.jd_text,
            ),
        },
    ]

    result: _SkillsOutput = await provider.agenerate(  # type: ignore[assignment]
        messages=messages,
        response_format=_SkillsOutput,
    )

    return {
        "resume_skills": result.resume_skills,
        "jd_skills": result.jd_skills,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 4: rewrite  (fan-in — OpenRouterProvider)
# ─────────────────────────────────────────────────────────────────────────────


@traceable(name="rewrite_node")
async def rewrite_node(state: MatcherState) -> Dict[str, Any]:
    """
    Rewrite suggestions via OpenRouterProvider.
    Runs only after BOTH score_node AND extract_skills_node complete (fan-in).
    Uses the merged state (skills + score data) for rich, targeted suggestions.
    Produces: rewrite_suggestions
    """
    provider = OllamaLocalProvider()

    # Flatten jd_skills into a keyword string for the prompt
    if state.jd_skills:
        jd_keywords = "; ".join(
            f"{k}: {', '.join(str(x) for x in v) if isinstance(v, list) else v}"
            for k, v in state.jd_skills.items()
        )
    else:
        # Fallback to raw JD text if skill extraction produced nothing
        jd_keywords = state.jd_text[:2000]

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert Resume Optimization Agent. "
                "Return ONLY a structured JSON object — no explanations."
            ),
        },
        {
            "role": "user",
            "content": REWRITE_SUGGESTIONS_PROMPT.format(
                resume_bullets=state.resume_text,
                job_keywords=jd_keywords,
            ),
        },
    ]

    result: _RewriteOutput = await provider.agenerate(  # type: ignore[assignment]
        messages=messages,
        response_format=_RewriteOutput,
    )

    return {"rewrite_suggestions": result.rewrite_suggestions}


# ─────────────────────────────────────────────────────────────────────────────
# Graph assembly
# ─────────────────────────────────────────────────────────────────────────────


def build_matcher_graph() -> Any:
    """
    Compile the LangGraph pipeline.

    Fan-out:  parse  → [score, extract_skills]  (executed concurrently)
    Fan-in:   [score, extract_skills] → rewrite  (waits for both)
    """
    graph: StateGraph = StateGraph(MatcherState)

    graph.add_node("load", load_node)
    graph.add_node("parse", parse_node)
    graph.add_node("score", score_node)
    graph.add_node("extract_skills", extract_skills_node)
    graph.add_node("rewrite", rewrite_node)

    # Sequential spine
    graph.add_edge(START, "load")
    graph.add_edge("load", "parse")

    # Fan-out: parse → both parallel nodes
    graph.add_edge("parse", "score")
    graph.add_edge("parse", "extract_skills")

    # Fan-in: rewrite runs only after BOTH parallel nodes complete
    graph.add_edge("score", "rewrite")
    graph.add_edge("extract_skills", "rewrite")

    graph.add_edge("rewrite", END)

    return graph.compile()


matcher_graph = build_matcher_graph()


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────


@traceable(name="run_matcher_graph")
async def run_matcher_graph(
    file_obj,
    jd_text: str,
) -> MatchResponse:
    """
    Execute the full resume-matching pipeline end-to-end.

    Args:
        file_obj : Streamlit UploadedFile or any BytesIO-compatible object.
        jd_text  : Raw job-description text.

    Returns:
        MatchResponse — fully populated API response schema.
    """
    # Materialise bytes so the Pydantic state can carry them
    raw_bytes: bytes = file_obj.read() if hasattr(file_obj, "read") else bytes(file_obj)

    initial_state = MatcherState(
        raw_file_bytes=raw_bytes,
        # Placeholder values — filled by graph nodes
        resume_text="",
        jd_text=jd_text,
        resume_skills={},
        jd_skills={},
        match_score=0,
        summary="",
        matched_skills=[],
        missing_skills=[],
        rewrite_suggestions=[],
        structural_metadata=None,
    )

    final: Dict[str, Any] = await matcher_graph.ainvoke(initial_state)

    return MatchResponse(
        match_score=final["match_score"],
        summary=final["summary"],
        matched_skills=final.get("matched_skills", []),
        missing_skills=final.get("missing_skills", []),
        rewrite_suggestions=final.get("rewrite_suggestions", []),
    )
