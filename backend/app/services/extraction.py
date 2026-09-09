from __future__ import annotations

import io
from dataclasses import dataclass

import fitz  # PyMuPDF
from PIL import Image

from app.services import ocr

# If a natively-extracted PDF page has fewer characters than this, we assume it
# is a scanned/image page and fall back to OCR for that page only.
_OCR_CHAR_THRESHOLD = 40
# Render scanned pages at 2x for better OCR accuracy.
_OCR_RENDER_ZOOM = 2.0


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    used_ocr: bool


@dataclass
class ExtractionResult:
    pages: list[ExtractedPage]

    @property
    def method(self) -> str:
        used = {p.used_ocr for p in self.pages}
        if used == {True}:
            return "ocr"
        if used == {False}:
            return "native"
        return "mixed"


def extract_pdf(content: bytes) -> ExtractionResult:
    """Extract text from a PDF, using OCR only for pages without a usable text layer."""
    pages: list[ExtractedPage] = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for index, page in enumerate(doc):
            native_text = page.get_text("text").strip()
            if len(native_text) >= _OCR_CHAR_THRESHOLD:
                pages.append(ExtractedPage(index + 1, native_text, used_ocr=False))
                continue

            # Render the page to an image and OCR it.
            matrix = fitz.Matrix(_OCR_RENDER_ZOOM, _OCR_RENDER_ZOOM)
            pixmap = page.get_pixmap(matrix=matrix)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            ocr_text = ocr.pil_image_to_text(image)
            # Prefer whichever produced more content.
            if len(ocr_text) >= len(native_text):
                pages.append(ExtractedPage(index + 1, ocr_text, used_ocr=True))
            else:
                pages.append(ExtractedPage(index + 1, native_text, used_ocr=False))
    return ExtractionResult(pages=pages)


def extract_image(content: bytes) -> ExtractionResult:
    """OCR a single-image notice."""
    text = ocr.image_bytes_to_text(content)
    return ExtractionResult(pages=[ExtractedPage(1, text, used_ocr=True)])


def extract(content: bytes, content_type: str) -> ExtractionResult:
    if content_type == "application/pdf":
        return extract_pdf(content)
    return extract_image(content)
