import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.document import DocumentSource, ExtractionStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    source: DocumentSource
    extraction_status: ExtractionStatus
    page_count: int | None
    extraction_error: str | None
    created_at: datetime


class DocumentTextPreview(DocumentRead):
    extracted_text_preview: str | None
