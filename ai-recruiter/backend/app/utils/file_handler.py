import os
import re
import uuid
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
import fitz  # PyMuPDF
import docx
from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def clean_extracted_text(text: str) -> str:
    """Normalize extracted text by stripping control characters and excessive whitespace."""
    if not text:
        return ""
    # Replace non-breaking spaces and exotic line breaks
    text = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple consecutive newlines and horizontal spaces
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using PyMuPDF (fitz) across all pages."""
    text_parts = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text:
                text_parts.append(page_text)
        doc.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse PDF content: {str(e)}"
        )
    return clean_extracted_text("\n\n".join(text_parts))


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from Word document (.docx) including tables and paragraphs."""
    import io
    text_parts = []
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_parts.append(" | ".join(row_text))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse DOCX document: {str(e)}"
        )
    return clean_extracted_text("\n".join(text_parts))


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from TXT with multiple encoding fallbacks."""
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            return clean_extracted_text(file_bytes.decode(enc))
        except UnicodeDecodeError:
            continue
    return clean_extracted_text(file_bytes.decode("utf-8", errors="replace"))


async def process_and_store_resume(file: UploadFile) -> Tuple[str, str, str]:
    """
    Validate, save resume file to storage, and extract cleaned raw text.
    Returns: (original_filename, stored_file_path, extracted_text)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file lacks a valid filename")

    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: PDF, DOCX, TXT."
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum allowed limit of 10 MB."
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Generate collision-free filename
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Extract text based on extension
    if ext == ".pdf":
        extracted_text = extract_text_from_pdf(content)
    elif ext == ".docx":
        extracted_text = extract_text_from_docx(content)
    else:  # .txt
        extracted_text = extract_text_from_txt(content)

    return file.filename, file_path, extracted_text
