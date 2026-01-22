from fastapi import UploadFile
import asyncio
import fitz
import io

async def extract_text_from_file(file: UploadFile) -> str:
    """
    Extract text from PDF using PyMuPDF.
    DOCX/TXT fallback included.
    """

    content = await file.read()
    content_type = file.content_type

    # ------------PDF---------------------
    if content_type == "application/pdf":
        text = []
        with fitz.open(stream=content, filetype="pdf") as doc:
            for page in doc:
                text.append(page.get_text())
        return "\n".join(text)

    # -------- TXT --------
    if content_type == "text/plain":
        return content.decode("utf-8", errors="ignore")

    # -------- DOCX (fallback – basic) --------
    if content_type in {
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }:
        # Minimal fallback: treat as binary text
        # (Replace later with python-docx if needed)
        return content.decode("utf-8", errors="ignore")

    return ""
