from __future__ import annotations

import io

import pytesseract
from PIL import Image

from app.core.config import settings


def image_bytes_to_text(image_bytes: bytes) -> str:
    """Run Tesseract OCR over raw image bytes."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        return pytesseract.image_to_string(img, lang=settings.ocr_language).strip()


def pil_image_to_text(img: "Image.Image") -> str:
    """Run Tesseract OCR over a PIL image (used for rendered PDF pages)."""
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return pytesseract.image_to_string(img, lang=settings.ocr_language).strip()
