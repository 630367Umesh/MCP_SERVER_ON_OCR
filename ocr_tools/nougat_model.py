# ocr_tools/nougat_model.py

from transformers import AutoProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
from typing import Optional


class NougatOCR:
    """
    Wrapper class for Facebook's Nougat OCR model.
    Supports extracting text from images using the VisionEncoderDecoder pipeline.
    """

    def __init__(self, model_name: str = "facebook/nougat-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_name).to(self.device)

    def extract(self, image_path: str) -> str:
        # Dummy implementation for testing pipeline
        return "TEST NOUGAT OUTPUT"
