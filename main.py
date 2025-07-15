# main.py

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal
import base64
import tempfile
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from ocr_tools.extract import extract
from ocr_tools.summarise import summarise_file
from ocr_tools.translate import translate_file

app = FastAPI(title="OCR MCP Server")

# CORS for Streamlit or web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Convert base64 to temporary image
def save_temp_image_from_base64(base64_str: str) -> str:
    decoded = base64.b64decode(base64_str)
    img = Image.open(io.BytesIO(decoded)).convert("RGB")
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)
    return temp_path

@app.post("/tools/extract")
async def extract_tool(
    image_base64: str = Form(...),
    engine: str = Form("tesseract")
):
    try:
        image_path = save_temp_image_from_base64(image_base64)
        result = extract(image_path, engine=engine)
        return {"result": result}
    except Exception as e:
        return {"error": f"❌ Failed to extract text: {str(e)}"}

@app.post("/tools/summarise")
async def summarise_tool(
    uploaded_file: UploadFile = File(...),
    engine: str = Form("tesseract")
):
    try:
        result = summarise_file(uploaded_file, engine=engine)  # type: ignore
        return {"result": result}
    except Exception as e:
        return {"error": f"❌ Failed to summarise: {str(e)}"}

@app.post("/tools/translate")
async def translate_tool(
    uploaded_file: UploadFile = File(...),
    target_language: str = Form(...),
    engine: str = Form("tesseract")
):
    try:
        result = translate_file(uploaded_file, target_language, engine=engine)  # type: ignore
        return {"result": result}
    except Exception as e:
        return {"error": f"❌ Translation failed: {str(e)}"}
