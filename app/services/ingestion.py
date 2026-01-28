from fastapi import UploadFile
import asyncio
import fitz
import io

async def extract_text_from_file(file: UploadFile) -> str:
    """
    Extract text from PDF using PyMuPDF.
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

    return ""
