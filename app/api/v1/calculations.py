from fastapi import APIRouter, Depends, Form, UploadFile

from app.api.deps import (
    get_audio_ingestion_service,
    get_calculation_repository,
    get_calculation_service,
    get_current_user,
)
from app.db.models.calculation import TaxRegime
from app.db.models.user import User
from app.repositories.calculation_repository import CalculationRepository
from app.schemas.calculation import CalculationRequest, CalculationResponse, SlabBreakdownEntryRead
from app.services.audio_ingestion_service import AudioIngestionService
from app.services.calculation_service import CalculationService
from app.services.tax_engine.rules import DEFAULT_FINANCIAL_YEAR

router = APIRouter(prefix="/calculations", tags=["calculations"])


def _to_response(calculation, result) -> CalculationResponse:
    return CalculationResponse(
        id=calculation.id,
        financial_year=result.financial_year,
        regime=result.regime,
        rule_set_version=result.rule_set_version,
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
        extracted_fields=calculation.extracted_fields,
        slab_breakdown=[SlabBreakdownEntryRead(**vars(s)) for s in result.slab_breakdown],
        created_at=calculation.created_at,
    )


@router.post("", response_model=CalculationResponse, status_code=201)
async def create_calculation(
    payload: CalculationRequest,
    user: User = Depends(get_current_user),
    calculation_service: CalculationService = Depends(get_calculation_service),
) -> CalculationResponse:
    calculation, result = await calculation_service.calculate_from_text(
        user_id=user.id,
        text=payload.text,
        document_id=payload.document_id,
        financial_year=payload.financial_year,
        regime=payload.regime,
    )
    return _to_response(calculation, result)


@router.post("/from-audio", response_model=CalculationResponse, status_code=201)
async def create_calculation_from_audio(
    file: UploadFile,
    financial_year: str = Form(default=DEFAULT_FINANCIAL_YEAR),
    regime: TaxRegime = Form(default=TaxRegime.NEW),
    user: User = Depends(get_current_user),
    audio_service: AudioIngestionService = Depends(get_audio_ingestion_service),
) -> CalculationResponse:
    content = await file.read()
    calculation, result, _transcript = await audio_service.calculate_from_audio(
        user_id=user.id,
        filename=file.filename or "voice.ogg",
        content=content,
        financial_year=financial_year,
        regime=regime,
    )
    return _to_response(calculation, result)


@router.get("", response_model=list[CalculationResponse])
async def list_calculations(
    user: User = Depends(get_current_user),
    calculation_repo: CalculationRepository = Depends(get_calculation_repository),
) -> list[CalculationResponse]:
    calculations = await calculation_repo.list_for_user(user.id)
    return [
        CalculationResponse(
            id=c.id,
            financial_year=c.financial_year,
            regime=c.regime,
            rule_set_version=c.rule_set_version,
            total_income=float(c.total_income),
            total_expenses=float(c.total_expenses),
            total_deductions=float(c.total_deductions),
            standard_deduction=float(c.standard_deduction),
            taxable_income=float(c.taxable_income),
            tax_before_rebate=float(c.tax_before_rebate),
            rebate_applied=float(c.rebate_applied),
            base_tax=float(c.base_tax),
            cess=float(c.cess),
            total_payable=float(c.total_payable),
            extracted_fields=c.extracted_fields,
            slab_breakdown=[],
            created_at=c.created_at,
        )
        for c in calculations
    ]
