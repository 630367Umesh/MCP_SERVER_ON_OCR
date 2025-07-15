# ocr_tools/summarise.py

import os
import tempfile
from fastapi import UploadFile
from typing import Literal
from ocr_tools.extract import extract
from llm.groq_client import query_groq_llm
import logging

logger = logging.getLogger(__name__)


def summarise_file(uploaded_file: UploadFile, engine: Literal["tesseract", "nougat"] = "tesseract") -> str:
    """
    Extracts text from an uploaded PDF or image using OCR (Tesseract or Nougat),
    and summarizes the content using the Groq LLM.

    Args:
        uploaded_file (UploadFile): File uploaded by the user (PDF or image).
        engine (str): OCR engine ('tesseract' or 'nougat').

    Returns:
        str: Summarized text output.
    """
    suffix = os.path.splitext(uploaded_file.filename)[-1]

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.file.read())
            tmp_path = tmp.name

        logger.info(f"📄 File saved temporarily at: {tmp_path}")

        # Step 1: Extract Text using OCR
        extracted_text = extract(tmp_path, engine=engine)

    except Exception as e:
        logger.error(f"❌ Error during OCR extraction: {e}")
        return f"❌ OCR Extraction failed: {str(e)}"
    
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            logger.info("🧹 Temporary file removed")

    if not extracted_text.strip():
        return "⚠️ No readable text was found in the document."

    # Step 2: Summarize via Groq LLM (safely truncated for token limits)
    try:
        prompt = f"Summarize the following document content:\n\n{extracted_text[:4000]}"
        summary = query_groq_llm(prompt=prompt)
        return summary or "⚠️ No summary returned."
    except Exception as e:
        logger.error(f"❌ LLM Summarization error: {e}")
        return f"❌ Summarization failed: {str(e)}"
