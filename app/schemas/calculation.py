import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.models.calculation import TaxRegime
from app.services.tax_engine.rules import DEFAULT_FINANCIAL_YEAR


class CalculationRequest(BaseModel):
    # Either `text` is supplied directly, or `document_id` points at a
    # previously uploaded document and the server reads its full stored
    # extracted text — the client never needs to round-trip large document
    # text through the API a second time.
    text: str | None = Field(default=None, max_length=50_000)
    financial_year: str = DEFAULT_FINANCIAL_YEAR
    regime: TaxRegime = TaxRegime.NEW
    document_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _require_text_or_document(self) -> "CalculationRequest":
        if not self.text and not self.document_id:
            raise ValueError("Either 'text' or 'document_id' must be provided.")
        return self


class SlabBreakdownEntryRead(BaseModel):
    from_amount: float
    upto: float | None
    rate: float
    taxed_amount: float
    tax: float


class CalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    financial_year: str
    regime: TaxRegime
    rule_set_version: str
    total_income: float
    total_expenses: float
    total_deductions: float
    standard_deduction: float
    taxable_income: float
    tax_before_rebate: float
    rebate_applied: float
    base_tax: float
    cess: float
    total_payable: float
    extracted_fields: dict[str, float]
    slab_breakdown: list[SlabBreakdownEntryRead]
    created_at: datetime
