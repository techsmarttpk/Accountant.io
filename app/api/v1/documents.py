from fastapi import APIRouter, Depends, UploadFile

from app.api.deps import get_current_user, get_document_service
from app.core.config import Settings, get_settings
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.db.models.document import DocumentSource
from app.db.models.user import User
from app.schemas.document import DocumentTextPreview
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}


@router.post("", response_model=DocumentTextPreview, status_code=201)
async def upload_document(
    file: UploadFile,
    user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
    settings: Settings = Depends(get_settings),
) -> DocumentTextPreview:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedFileTypeError(
            f"Unsupported content type {file.content_type!r}. Only PDF is accepted."
        )

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise FileTooLargeError(f"File exceeds the {settings.max_upload_size_mb}MB limit.")

    document = await document_service.ingest_pdf(
        user_id=user.id,
        filename=file.filename or "upload.pdf",
        content=content,
        source=DocumentSource.API_UPLOAD,
        mime_type=file.content_type,
    )

    preview = (document.extracted_text or "")[:500]
    return DocumentTextPreview.model_validate(
        {**document.__dict__, "extracted_text_preview": preview}
    )
