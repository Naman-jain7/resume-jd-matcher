"""
src/ingestion/parser.py
-----------------------
Structural parser for resume text extracted by the pdfplumber loader.

Flow:
  1. Heuristically scan the extracted text to build a lightweight pre-analysis
     dict (layout_type, has_tables, has_bullet_points).
  2. Render STRUCTURAL_PROMPT_INSTRUCTION with those heuristics so the LLM
     has grounding context.
  3. Call OllamaLocalProvider (llama3.2:3b) with `response_format=StructuralMetadata`
     to obtain a validated, structured metadata object.
  4. Return the canonical dict:
        {
            "normalized_content":  <extracted_text str>,
            "structural_metadata": <StructuralMetadata pydantic object>
        }
"""

from __future__ import annotations

import re
from typing import Any, Dict

from schemas.parse_resume import StructuralMetadata
from src.llm.providers import OllamaLocalProvider
from src.llm.prompts import STRUCTURAL_PROMPT_INSTRUCTION


# ---------------------------------------------------------------------------
# Heuristic pre-analysis helpers
# ---------------------------------------------------------------------------

def _detect_layout_type(text: str) -> str:
    """
    Coarse heuristic: infer the visual layout architecture from text markers.

    - "two-column"  → pdfplumber tends to place two independent column streams
                      side-by-side; we detect short lines interleaved with
                      longer ones, or explicit '|' separators from table render.
    - "grid"        → multiple markdown table blocks detected.
    - "single-column" → default fallback.
    """

    lines = [l for l in text.splitlines() if l.strip()]

    if not lines:
        return "single-column"

    # Grid: several markdown table rows
    table_lines = [l for l in lines if l.startswith("|") and "|" in l[1:]]
    if len(table_lines) >= 6:
        return "grid"

    # Two-column heuristic: high proportion of very short lines (< 40 chars)
    #   suggests two streams were extracted alternately.
    short = sum(1 for l in lines if len(l.strip()) < 40)
    if short / len(lines) > 0.55 and len(lines) > 20:
        return "two-column"

    return "single-column"

def _has_tables(text: str) -> bool:
    """True if the text contains at least one markdown table (from the loader)."""
    table_rows = [l for l in text.splitlines() if l.startswith("|") and "|" in l[1:]]
    return len(table_rows) >= 3  # header + divider + at least one data row


def _has_bullet_points(text: str) -> bool:
    """True if the text contains common bullet-point markers."""
    bullet_pattern = re.compile(r"^\s*[-•*▪▸◦–]\s+\S", re.MULTILINE)
    return bool(bullet_pattern.search(text))


def _pre_analyse(text: str) -> Dict[str, Any]:
    """Return a lightweight metadata dict used to ground the LLM prompt."""
    return {
        "layout_type":      _detect_layout_type(text),
        "has_tables":       _has_tables(text),
        "has_bullet_points": _has_bullet_points(text),
    }


# ---------------------------------------------------------------------------
# Public parser entry point
# ---------------------------------------------------------------------------

def parse_resume(extracted_text: str) -> Dict[str, Any]:
    """
    Structurally parse a resume's extracted text using a local LLM.

    Args:
        extracted_text: The raw/markdown-like string produced by
                        `load_pdf_streamlit()` in loader.py.

    Returns:
        {
            "normalized_content":  str              – the original extracted text,
            "structural_metadata": StructuralMetadata – validated pydantic object.
        }

    Raises:
        ExternalServiceError: propagated from OllamaLocalProvider if the
                              local Ollama service is unreachable or the
                              model call fails.
    """
    # 1. Heuristic pre-analysis ------------------------------------------------
    metadata = _pre_analyse(extracted_text)

    # 2. Render the system prompt with heuristic context ----------------------
    #    STRUCTURAL_PROMPT_INSTRUCTION uses Python dict-access syntax inside
    #    an f-string style template, so we substitute with str.replace to
    #    avoid KeyError from .format().
    system_content = (
        STRUCTURAL_PROMPT_INSTRUCTION
        .replace("{metadata['layout_type']}",      str(metadata["layout_type"]))
        .replace("{metadata['has_tables']}",       str(metadata["has_tables"]))
        .replace("{metadata['has_bullet_points']}", str(metadata["has_bullet_points"]))
    )

    # 3. Build the message list -----------------------------------------------
    #    System message: task + heuristic context
    #    Human message:  the actual resume text (truncated to avoid OOM on 3b)
    MAX_TEXT_CHARS = 6000  # llama3.2:3b context is limited; keep it lean
    truncated_text = extracted_text[:MAX_TEXT_CHARS]
    if len(extracted_text) > MAX_TEXT_CHARS:
        truncated_text += "\n\n[... content truncated for context window ...]"

    messages = [
        {
            "role": "system",
            "content": (
                system_content.strip()
                + "\n\n"
                "Analyse the resume text below and return ONLY a structured JSON "
                "object matching the requested schema. Do NOT add any explanation."
            ),
        },
        {
            "role": "user",
            "content": (
                "Resume text to analyse:\n\n"
                + truncated_text
            ),
        },
    ]

    # 4. Call the LLM with structured output ----------------------------------
    provider = OllamaLocalProvider(
        temperature=0.0,   # deterministic – layout classification needs no creativity
    )

    structural_metadata: StructuralMetadata = provider.generate(  # type: ignore[assignment]
        messages=messages,
        response_format=StructuralMetadata,
    )

    # 5. Return canonical output dict -----------------------------------------
    return {
        "normalized_content":  extracted_text,
        "structural_metadata": structural_metadata,
    }
