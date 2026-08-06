"""Append-only audit trail writer.

Every service that touches user financial data calls this. It never
raises on its own logging failure into the caller's success path — an
audit-log write failure is itself logged, not allowed to break the user
request, but in production this should also fire an alert (see
core/logging.py) since a silently-failing audit trail is a compliance gap.
"""

from __future__ import annotations

import uuid

from app.core.logging import get_logger
from app.db.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository

logger = get_logger(__name__)


class AuditService:
    def __init__(self, audit_log_repository: AuditLogRepository) -> None:
        self._repo = audit_log_repository

    async def record(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        context: dict | None = None,
        success: bool = True,
    ) -> None:
        try:
            await self._repo.add(
                AuditLog(
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    user_id=user_id,
                    context=context or {},
                    success=success,
                )
            )
        except Exception:
            logger.error("audit_log_write_failed", action=action, entity_type=entity_type, exc_info=True)
