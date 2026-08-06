"""Structured exception hierarchy.

Every domain-level failure raises one of these instead of a bare Exception.
Each carries a stable `error_code` (safe to show a user / log for support)
and an `http_status` so the API layer can translate it without a giant
if/elif chain in every route handler.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application (non-programming-bug) errors."""

    error_code: str = "internal_error"
    http_status: int = 500

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    error_code = "not_found"
    http_status = 404


class ValidationFailedError(AppError):
    error_code = "validation_failed"
    http_status = 422


class UnauthorizedError(AppError):
    error_code = "unauthorized"
    http_status = 401


class UnsupportedFileTypeError(AppError):
    error_code = "unsupported_file_type"
    http_status = 415


class FileTooLargeError(AppError):
    error_code = "file_too_large"
    http_status = 413


class DocumentExtractionError(AppError):
    """Raised when text cannot be extracted from an uploaded document at all."""

    error_code = "document_extraction_failed"
    http_status = 422


class InsufficientFinancialDataError(AppError):
    """Raised when extraction succeeded but no usable financial fields were found.

    This is the structured replacement for the legacy behavior of silently
    computing a tax of ₹0 when nothing matched — that failure mode is banned
    in this codebase. Absence of data must be surfaced, never guessed away.
    """

    error_code = "insufficient_financial_data"
    http_status = 422


class TranscriptionError(AppError):
    error_code = "transcription_failed"
    http_status = 422


class RagServiceError(AppError):
    error_code = "rag_service_error"
    http_status = 502
