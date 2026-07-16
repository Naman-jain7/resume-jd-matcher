from typing import Literal
from pydantic import BaseModel, Field
from typing_extensions import Annotated

class StructuralMetadata(BaseModel):
    layout_type: Annotated[
        Literal["single-column", "two-column", "grid"], 
        Field(..., description="The physical visual layout architecture of the resume document.")
    ]
    has_tables: Annotated[
        bool, 
        Field(..., description="Indicates whether the document contains embedded tables for layout or data.")
    ]
    has_bullet_points: Annotated[
        bool, 
        Field(..., description="Indicates whether the document heavily relies on bulleted or ordered lists.")
    ]
    section_density: Annotated[
        Literal["low", "medium", "high/dense"], 
        Field(..., description="Visual density of information within sections.")
    ]
    parsing_confidence: Annotated[
        Literal["low", "medium", "high"], 
        Field(..., description="The parser's confidence score regarding the layout extraction integrity.")
    ]

class ResumeParsedData(BaseModel):
    """
    Schema for holding layout-aware parsed resume content along with 
    its structural metadata profile.
    """
    normalized_content: Annotated[
        str, 
        Field(..., description="The raw or markdown-formatted text stream extracted from the PDF, preserving spatial layout.")
    ]
    structural_metadata: Annotated[
        StructuralMetadata, 
        Field(..., description="Structural and structural profiling metrics used to assist downstream LLM context mapping.")
    ]