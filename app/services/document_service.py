"""Document ingestion orchestration: store the file, extract its text,
persist the result, write an audit record — every time, in that order."""

from __future__ import annotations

import uuid
from pathlib import Path

from app.core.logging import get_logger
from app.db.models.document import Document, DocumentSource, ExtractionStatus
from app.repositories.document_repository import DocumentRepository
from app.services.audit_service import AuditService
from app.services.extraction.pdf_extractor import PdfExtractor
from app.services.storage import FileStorage

logger = get_logger(__name__)


class DocumentService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        storage: FileStorage,
        pdf_extractor: PdfExtractor,
        audit_service: AuditService,
    ) -> None:
        self._repo = document_repository
        self._storage = storage
        self._pdf_extractor = pdf_extractor
        self._audit = audit_service

    async def ingest_pdf(
        self,
        *,
        user_id: uuid.UUID,
        filename: str,
        content: bytes,
        source: DocumentSource,
        mime_type: str | None = "application/pdf",
    ) -> Document:
        storage_path = self._storage.save(user_id=user_id, filename=filename, content=content)

        document = Document(
            user_id=user_id,
            original_filename=filename,
            storage_path=storage_path,
            mime_type=mime_type,
            source=source,
            extraction_status=ExtractionStatus.PENDING,
        )

        try:
            result = self._pdf_extractor.extract(storage_path)
            document.extracted_text = result.text
            document.page_count = result.page_count
            document.extraction_status = ExtractionStatus.SUCCESS
        except Exception as exc:
            document.extraction_status = ExtractionStatus.FAILED
            document.extraction_error = str(exc)
            logger.warning("document_extraction_failed", filename=filename, error=str(exc))

        document = await self._repo.add(document)

        await self._audit.record(
            action="document.ingested",
            entity_type="document",
            entity_id=document.id,
            user_id=user_id,
            context={
                "filename": filename,
                "status": document.extraction_status.value,
                "page_count": document.page_count,
            },
            success=document.extraction_status == ExtractionStatus.SUCCESS,
        )

        return document
