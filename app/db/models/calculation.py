from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TaxRegime(str, enum.Enum):
    OLD = "old"
    NEW = "new"


class Calculation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single tax computation, fully traceable back to the inputs that
    produced it — this is the auditability the legacy script had none of.
    """

    __tablename__ = "calculations"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True, index=True
    )

    financial_year: Mapped[str] = mapped_column(String(9))  # e.g. "2024-25"
    regime: Mapped[TaxRegime] = mapped_column(Enum(TaxRegime))

    total_income: Mapped[float] = mapped_column(Numeric(14, 2))
    total_expenses: Mapped[float] = mapped_column(Numeric(14, 2))
    total_deductions: Mapped[float] = mapped_column(Numeric(14, 2))
    standard_deduction: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    taxable_income: Mapped[float] = mapped_column(Numeric(14, 2))
    tax_before_rebate: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    rebate_applied: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    base_tax: Mapped[float] = mapped_column(Numeric(14, 2))
    cess: Mapped[float] = mapped_column(Numeric(14, 2))
    total_payable: Mapped[float] = mapped_column(Numeric(14, 2))

    # Raw field-level extraction results, kept for auditability/debugging —
    # lets us answer "why did the engine think income was X" after the fact.
    extracted_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    rule_set_version: Mapped[str] = mapped_column(String(64))

    user: Mapped["User"] = relationship(back_populates="calculations")
    document: Mapped["Document" ] = relationship(back_populates="calculations")
