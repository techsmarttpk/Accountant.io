"""OCR fallback for scanned/photographed documents.

The legacy extractor only pulled embedded text via PyMuPDF, which returns
an empty string for scanned/photographed pages — the majority of
real-world tax paperwork (photographed Form 16s, scanned rent receipts).
This module renders such pages to images and runs Tesseract OCR over them.
"""

from __future__ import annotations

import io

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from app.core.logging import get_logger

logger = get_logger(__name__)

# Below this many characters of embedded text per page, we assume the page
# is a scan/image and route it through OCR instead of trusting the (empty
# or near-empty) embedded text layer.
MIN_EMBEDDED_CHARS_PER_PAGE = 20


class OcrExtractor:
    def extract_page_text(self, page: fitz.Page, *, dpi: int = 300) -> str:
        pix = page.get_pixmap(dpi=dpi)
        image = Image.open(io.BytesIO(pix.tobytes("png")))
        try:
            return pytesseract.image_to_string(image)
        except pytesseract.TesseractNotFoundError:
            logger.warning("tesseract_not_available", page=page.number)
            return ""

    def extract_image_bytes(self, image_bytes: bytes) -> str:
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
