from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single grounded question/answer exchange from the RAG assistant."""

    __tablename__ = "chat_messages"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    # List of {"source": str, "score": float, "excerpt": str} — lets us show
    # citations to the user and lets an auditor verify the answer was grounded.
    retrieved_sources: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(default=0.0)
