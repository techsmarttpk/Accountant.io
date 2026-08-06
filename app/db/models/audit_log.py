from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin, utcnow


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Append-only audit trail. Deliberately has no `updated_at` and no
    ORM-level update path — audit rows are written once and never mutated.
    Every action that touches user financial data must write one of these.
    """

    __tablename__ = "audit_logs"

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    success: Mapped[bool] = mapped_column(default=True)
