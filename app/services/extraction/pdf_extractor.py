"""PDF text extraction with automatic OCR fallback per page."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from app.core.exceptions import DocumentExtractionError
from app.core.logging import get_logger
from app.services.extraction.ocr_extractor import MIN_EMBEDDED_CHARS_PER_PAGE, OcrExtractor

logger = get_logger(__name__)


@dataclass
class PdfExtractionResult:
    text: str
    page_count: int
    ocr_pages_used: int


class PdfExtractor:
    def __init__(self, ocr_extractor: OcrExtractor | None = None) -> None:
        self._ocr = ocr_extractor or OcrExtractor()

    def extract(self, pdf_path: Path | str) -> PdfExtractionResult:
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as exc:  # PyMuPDF raises its own error types
            raise DocumentExtractionError(f"Could not open PDF: {exc}") from exc

        pages_text: list[str] = []
        ocr_pages_used = 0

        try:
            for page in doc:
                embedded = page.get_text()
                if len(embedded.strip()) >= MIN_EMBEDDED_CHARS_PER_PAGE:
                    pages_text.append(embedded)
                    continue

                logger.info("pdf_page_fallback_to_ocr", page=page.number)
                ocr_text = self._ocr.extract_page_text(page)
                ocr_pages_used += 1
                pages_text.append(ocr_text)
        finally:
            page_count = doc.page_count
            doc.close()

        text = "\n".join(pages_text)
        if not text.strip():
            raise DocumentExtractionError(
                "No text could be extracted from this document, even with OCR."
            )

        return PdfExtractionResult(text=text, page_count=page_count, ocr_pages_used=ocr_pages_used)
