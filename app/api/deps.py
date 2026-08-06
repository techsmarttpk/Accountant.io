"""Central place for FastAPI dependency wiring.

Every route depends on abstractions constructed here rather than
instantiating repositories/services itself — this is the dependency
injection seam that makes services swappable and the API layer thin.
"""

from __future__ import annotations

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.db.models.user import User
from app.db.session import get_db
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.calculation_repository import CalculationRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from app.services.audio_ingestion_service import AudioIngestionService
from app.services.audit_service import AuditService
from app.services.calculation_service import CalculationService
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.extraction.audio_transcriber import get_transcription_provider
from app.services.extraction.financial_field_extractor import FinancialFieldExtractor
from app.services.extraction.ocr_extractor import OcrExtractor
from app.services.extraction.pdf_extractor import PdfExtractor
from app.services.rag.rag_service import RAGService
from app.services.storage import FileStorage, LocalFileStorage
from app.services.tax_engine.calculator import TaxCalculationService

# --- Repositories -----------------------------------------------------------


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


def get_document_repository(session: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(session)


def get_calculation_repository(session: AsyncSession = Depends(get_db)) -> CalculationRepository:
    return CalculationRepository(session)


def get_audit_log_repository(session: AsyncSession = Depends(get_db)) -> AuditLogRepository:
    return AuditLogRepository(session)


def get_chat_repository(session: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(session)


# --- Cross-cutting services -----------------------------------------------------------


def get_audit_service(repo: AuditLogRepository = Depends(get_audit_log_repository)) -> AuditService:
    return AuditService(repo)


def get_file_storage(settings: Settings = Depends(get_settings)) -> FileStorage:
    return LocalFileStorage(settings.storage_dir / "documents")


def get_audio_storage(settings: Settings = Depends(get_settings)) -> FileStorage:
    return LocalFileStorage(settings.storage_dir / "audio")


# --- Domain services -----------------------------------------------------------


def get_document_service(
    document_repo: DocumentRepository = Depends(get_document_repository),
    storage: FileStorage = Depends(get_file_storage),
    audit_service: AuditService = Depends(get_audit_service),
) -> DocumentService:
    return DocumentService(document_repo, storage, PdfExtractor(OcrExtractor()), audit_service)


def get_calculation_service(
    calculation_repo: CalculationRepository = Depends(get_calculation_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> CalculationService:
    return CalculationService(
        calculation_repo,
        document_repo,
        FinancialFieldExtractor(),
        TaxCalculationService(),
        audit_service,
    )


def get_audio_ingestion_service(
    storage: FileStorage = Depends(get_audio_storage),
    calculation_service: CalculationService = Depends(get_calculation_service),
    audit_service: AuditService = Depends(get_audit_service),
    settings: Settings = Depends(get_settings),
) -> AudioIngestionService:
    transcriber = get_transcription_provider(settings.stt_provider)
    return AudioIngestionService(storage, transcriber, calculation_service, audit_service)


def get_rag_service(request: Request) -> RAGService:
    """The RAG retriever embeds the whole knowledge base on construction,
    so it's built once at app startup (see app.main) and reused across
    requests via `app.state`, rather than rebuilt per-request."""
    return request.app.state.rag_service


def get_chat_service(
    chat_repo: ChatRepository = Depends(get_chat_repository),
    rag_service: RAGService = Depends(get_rag_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> ChatService:
    return ChatService(chat_repo, rag_service, audit_service)


# --- Auth / identity -----------------------------------------------------------


async def get_current_user(
    x_telegram_user_id: int | None = Header(default=None),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    if x_telegram_user_id is None:
        raise UnauthorizedError("X-Telegram-User-Id header is required.")
    return await user_repo.get_or_create_by_telegram_id(x_telegram_user_id)
