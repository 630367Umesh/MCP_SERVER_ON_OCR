# ocr_tools/extract.py

import os
import tempfile
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from ocr_tools.nougat_model import NougatOCR
from ocr_tools.mistral_ocr import mistral_ocr
import logging

logger = logging.getLogger(__name__)


def extract(file_path: str, engine: str = "tesseract") -> str:
    """
    Extract text from a PDF or image using Tesseract, Nougat, or Mistral.

    Args:
        file_path (str): Path to a PDF or image file.
        engine (str): OCR engine to use ('tesseract' or 'nougat').

    Returns:
        str: Extracted text from the file.
    """
    extracted_text = []

    try:
        ext = os.path.splitext(file_path)[1].lower()

        if engine == "mistral":
            if ext == ".pdf":
                doc = fitz.open(file_path)
                mistral_texts = []
                for i in range(doc.page_count):
                    page = doc.load_page(i)
                    try:
                        pix = page.get_pixmap(dpi=300)  # type: ignore
                    except AttributeError:
                        pix = page.getPixmap(dpi=300)  # type: ignore
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
                        tmp_img_path = tmp_img.name
                    pix.save(tmp_img_path)
                    try:
                        text = mistral_ocr(tmp_img_path)
                        mistral_texts.append(text)
                    finally:
                        if os.path.exists(tmp_img_path):
                            os.unlink(tmp_img_path)
                doc.close()
                return "\n\n".join(mistral_texts)
            else:
                return mistral_ocr(file_path)

        if ext == ".pdf":
            doc = fitz.open(file_path)
            for i in range(doc.page_count):
                page = doc.load_page(i)
                try:
                    pix = page.get_pixmap(dpi=300)  # type: ignore
                except AttributeError:
                    pix = page.getPixmap(dpi=300)  # type: ignore
                # Create and close the temp file before saving and OCR
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
                    tmp_img_path = tmp_img.name
                pix.save(tmp_img_path)
                try:
                    text = run_ocr(tmp_img_path, engine)
                    extracted_text.append(text)
                finally:
                    if os.path.exists(tmp_img_path):
                        os.unlink(tmp_img_path)
            doc.close()

        elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            text = run_ocr(file_path, engine)
            extracted_text.append(text)

        else:
            raise ValueError("❌ Unsupported file format. Only PDF and image files are allowed.")

        return "\n\n".join(extracted_text)

    except Exception as e:
        logger.error(f"Error in extract(): {e}")
        raise RuntimeError(f"❌ Failed to extract text: {str(e)}")


def run_ocr(image_path: str, engine: str) -> str:
    """
    Apply OCR engine to a single image.

    Args:
        image_path (str): Path to image file.
        engine (str): OCR engine.

    Returns:
        str: Recognized text.
    """
    try:
        if engine == "nougat":
            return NougatOCR().extract(image_path)
        else:
            with Image.open(image_path).convert("RGB") as img:
                return pytesseract.image_to_string(img)
    except Exception as e:
        logger.error(f"OCR failed with {engine}: {e}")
        return f"[OCR Error: {e}]"
