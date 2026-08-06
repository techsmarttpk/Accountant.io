"""Voice-note ingestion: store the audio, transcribe it, then hand the
transcript to CalculationService exactly like a text message would be.

Kept as its own thin orchestrator rather than folded into
CalculationService so that service stays focused on "text in, tax
calculation out" — transcription and audio storage are a distinct
concern with their own failure modes (audio unreadable, STT provider
down) that deserve their own error handling and audit events.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from app.core.exceptions import TranscriptionError
from app.db.models.calculation import Calculation, TaxRegime
from app.services.audit_service import AuditService
from app.services.calculation_service import CalculationService
from app.services.extraction.audio_transcriber import TranscriptionProvider
from app.services.storage import FileStorage
from app.services.tax_engine.calculator import TaxCalculationResult
from app.services.tax_engine.rules import DEFAULT_FINANCIAL_YEAR


class AudioIngestionService:
    def __init__(
        self,
        storage: FileStorage,
        transcriber: TranscriptionProvider,
        calculation_service: CalculationService,
        audit_service: AuditService,
    ) -> None:
        self._storage = storage
        self._transcriber = transcriber
        self._calculation_service = calculation_service
        self._audit = audit_service

    async def calculate_from_audio(
        self,
        *,
        user_id: uuid.UUID,
        filename: str,
        content: bytes,
        financial_year: str = DEFAULT_FINANCIAL_YEAR,
        regime: TaxRegime = TaxRegime.NEW,
    ) -> tuple[Calculation, TaxCalculationResult, str]:
        storage_path = self._storage.save(user_id=user_id, filename=filename, content=content)

        try:
            transcript = self._transcriber.transcribe(Path(storage_path))
        except TranscriptionError:
            await self._audit.record(
                action="audio.transcription_failed",
                entity_type="audio",
                user_id=user_id,
                context={"filename": filename},
                success=False,
            )
            raise

        await self._audit.record(
            action="audio.transcribed",
            entity_type="audio",
            user_id=user_id,
            context={"filename": filename, "transcript_length": len(transcript)},
        )

        calculation, result = await self._calculation_service.calculate_from_text(
            user_id=user_id,
            text=transcript,
            financial_year=financial_year,
            regime=regime,
        )
        return calculation, result, transcript
