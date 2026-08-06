"""Import every model module so `Base.metadata` is fully populated for
Alembic autogeneration and `create_all` in tests."""

from app.db.models.audit_log import AuditLog
from app.db.models.calculation import Calculation, TaxRegime
from app.db.models.chat import ChatMessage
from app.db.models.document import Document, DocumentSource, ExtractionStatus
from app.db.models.user import User

__all__ = [
    "AuditLog",
    "Calculation",
    "TaxRegime",
    "ChatMessage",
    "Document",
    "DocumentSource",
    "ExtractionStatus",
    "User",
]
