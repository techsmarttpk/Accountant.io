from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentSource(str, enum.Enum):
    TELEGRAM_UPLOAD = "telegram_upload"
    TELEGRAM_VOICE = "telegram_voice"
    API_UPLOAD = "api_upload"


class ExtractionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)

    original_filename: Mapped[str] = mapped_column(String(512))
    storage_path: Mapped[str] = mapped_column(String(1024))
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[DocumentSource] = mapped_column(Enum(DocumentSource))

    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus), default=ExtractionStatus.PENDING
    )
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="documents")
    calculations: Mapped[list["Calculation"]] = relationship(back_populates="document")
