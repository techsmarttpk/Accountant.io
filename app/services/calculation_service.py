"""Tax calculation orchestration.

Ties together field extraction, the pure tax engine, persistence, and
audit logging. This is also where the legacy "silently return ₹0 when
nothing was extracted" failure mode is closed off for good: if extraction
finds nothing usable, this raises `InsufficientFinancialDataError` instead
of computing a confident-looking wrong answer.
"""

from __future__ import annotations

import uuid

from app.core.exceptions import DocumentExtractionError, InsufficientFinancialDataError, NotFoundError
from app.db.models.calculation import Calculation, TaxRegime
from app.db.models.document import ExtractionStatus
from app.repositories.calculation_repository import CalculationRepository
from app.repositories.document_repository import DocumentRepository
from app.services.audit_service import AuditService
from app.services.extraction.financial_field_extractor import FinancialFieldExtractor
from app.services.tax_engine.calculator import TaxCalculationResult, TaxCalculationService
from app.services.tax_engine.rules import DEFAULT_FINANCIAL_YEAR


class CalculationService:
    def __init__(
        self,
        calculation_repository: CalculationRepository,
        document_repository: DocumentRepository,
        field_extractor: FinancialFieldExtractor,
        tax_calculator: TaxCalculationService,
        audit_service: AuditService,
    ) -> None:
        self._repo = calculation_repository
        self._document_repo = document_repository
        self._field_extractor = field_extractor
        self._tax_calculator = tax_calculator
        self._audit = audit_service

    async def calculate_from_text(
        self,
        *,
        user_id: uuid.UUID,
        text: str | None = None,
        document_id: uuid.UUID | None = None,
        financial_year: str = DEFAULT_FINANCIAL_YEAR,
        regime: TaxRegime = TaxRegime.NEW,
    ) -> tuple[Calculation, TaxCalculationResult]:
        resolved_text = text or ""

        if document_id is not None:
            document = await self._document_repo.get(document_id)
            if document is None or document.user_id != user_id:
                raise NotFoundError(f"Document {document_id} not found.")
            if document.extraction_status != ExtractionStatus.SUCCESS or not document.extracted_text:
                raise DocumentExtractionError(
                    "This document has no successfully extracted text to calculate from."
                )
            resolved_text = document.extracted_text

        extracted = self._field_extractor.extract(resolved_text)

        if extracted.is_empty:
            await self._audit.record(
                action="calculation.rejected_insufficient_data",
                entity_type="calculation",
                user_id=user_id,
                context={"document_id": str(document_id) if document_id else None},
                success=False,
            )
            raise InsufficientFinancialDataError(
                "No recognizable financial fields (salary, deductions, etc.) were "
                "found in the provided text or document. No tax figure has been "
                "computed — please provide clearer financial details rather than "
                "receive a guessed number."
            )

        result = self._tax_calculator.calculate(
            total_income=extracted.total_income,
            total_expenses=extracted.total_expenses,
            total_deductions=extracted.total_deductions,
            financial_year=financial_year,
            regime=regime,
        )

        calculation = await self._repo.add(
            Calculation(
                user_id=user_id,
                document_id=document_id,
                financial_year=result.financial_year,
                regime=result.regime,
                total_income=result.total_income,
                total_expenses=result.total_expenses,
                total_deductions=result.total_deductions,
                standard_deduction=result.standard_deduction,
                taxable_income=result.taxable_income,
                tax_before_rebate=result.tax_before_rebate,
                rebate_applied=result.rebate_applied,
                base_tax=result.base_tax,
                cess=result.cess,
                total_payable=result.total_payable,
                extracted_fields=extracted.fields_found,
                rule_set_version=result.rule_set_version,
            )
        )

        await self._audit.record(
            action="calculation.completed",
            entity_type="calculation",
            entity_id=calculation.id,
            user_id=user_id,
            context={
                "financial_year": financial_year,
                "regime": regime.value,
                "total_payable": result.total_payable,
                "fields_found": list(extracted.fields_found.keys()),
            },
        )

        return calculation, result
