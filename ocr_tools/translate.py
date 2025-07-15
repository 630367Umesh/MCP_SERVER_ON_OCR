import os
import tempfile
from fastapi import UploadFile
from typing import Literal
from ocr_tools.extract import extract
from ocr_tools.summarise import summarise_file
from llm.groq_client import query_groq_llm
import logging

logger = logging.getLogger(__name__)

def translate_file(uploaded_file: UploadFile, target_language: str, engine: Literal["tesseract", "nougat", "mistral"] = "tesseract") -> str:
    """
    Extracts text from an uploaded PDF or image using OCR, summarizes it, then translates the summary to the target language using the Groq LLM.

    Args:
        uploaded_file (UploadFile): File uploaded by the user (PDF or image).
        target_language (str): The language to translate the summary into (e.g., 'French', 'es', 'zh').
        engine (str): OCR engine ('tesseract', 'nougat', or 'mistral').a

    Returns:
        str: Translated summary output.
    """
    # Ensure filename is a string
    filename = uploaded_file.filename or 'file'
    suffix = os.path.splitext(filename)[-1]

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

    # Step 2: Summarize the extracted text
    try:
        # Use the same summarization logic as summarise_file
        prompt = f"Summarize the following document content:\n\n{extracted_text[:4000]}"
        summary = query_groq_llm(prompt=prompt)
        summary = summary or "⚠️ No summary returned."
    except Exception as e:
        logger.error(f"❌ LLM Summarization error: {e}")
        return f"❌ Summarization failed: {str(e)}"

    # Step 3: Translate the summary
    try:
        prompt = f"Translate the following summary to {target_language}:\n\n{summary}"
        translation = query_groq_llm(prompt=prompt)
        return translation or "⚠️ No translation returned."
    except Exception as e:
        logger.error(f"❌ LLM Translation error: {e}")
        return f"❌ Translation failed: {str(e)}" 