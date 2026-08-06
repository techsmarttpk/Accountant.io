"""Pure, deterministic Indian income-tax calculation.

Deliberately has zero I/O and zero framework dependencies — it takes plain
numbers in and returns a plain result object, which is what makes it
trivial to unit test exhaustively (see tests/unit/test_tax_calculator.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.db.models.calculation import TaxRegime
from app.services.tax_engine.rules import RuleSet, TaxSlab, get_rule_set


@dataclass(frozen=True)
class SlabBreakdownEntry:
    from_amount: float
    upto: float | None
    rate: float
    taxed_amount: float
    tax: float


@dataclass(frozen=True)
class TaxCalculationResult:
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
    slab_breakdown: list[SlabBreakdownEntry] = field(default_factory=list)


def _apply_slabs(taxable_income: float, slabs: list[TaxSlab]) -> tuple[float, list[SlabBreakdownEntry]]:
    total_tax = 0.0
    breakdown: list[SlabBreakdownEntry] = []
    for slab in slabs:
        if taxable_income <= slab.from_amount:
            break
        upper = slab.upto if slab.upto is not None else taxable_income
        taxed_amount = max(0.0, min(taxable_income, upper) - slab.from_amount)
        slab_tax = round(taxed_amount * slab.rate, 2)
        total_tax += slab_tax
        if taxed_amount > 0:
            breakdown.append(
                SlabBreakdownEntry(
                    from_amount=slab.from_amount,
                    upto=slab.upto,
                    rate=slab.rate,
                    taxed_amount=taxed_amount,
                    tax=slab_tax,
                )
            )
    return round(total_tax, 2), breakdown


class TaxCalculationService:
    """Computes tax liability against a specific, versioned rule set.

    Known simplification (tracked, not hidden): `total_expenses` is
    subtracted directly from gross income before deductions. Real Indian
    tax law does not work this way for most expense types (e.g. rent paid
    only reduces taxable income via the HRA exemption formula under
    Section 10(13A), not as a flat subtraction). This mirrors what the
    legacy prototype did so behavior stays explainable, but it is a known
    correctness gap — proper per-category treatment (HRA, capital gains,
    business expenses) is the right follow-up before this handles anything
    beyond simple salaried-employee estimates.
    """

    def calculate(
        self,
        *,
        total_income: float,
        total_expenses: float,
        total_deductions: float,
        financial_year: str,
        regime: TaxRegime,
    ) -> TaxCalculationResult:
        rule_set: RuleSet = get_rule_set(financial_year, regime)

        net_income = max(0.0, total_income - total_expenses)
        taxable_income = max(
            0.0, net_income - total_deductions - rule_set.standard_deduction
        )

        tax_before_rebate, breakdown = _apply_slabs(taxable_income, rule_set.slabs)
        rebate = rule_set.compute_rebate(taxable_income, tax_before_rebate)
        base_tax = round(tax_before_rebate - rebate, 2)
        cess = round(base_tax * rule_set.cess_rate, 2)
        total_payable = round(base_tax + cess, 2)

        return TaxCalculationResult(
            financial_year=financial_year,
            regime=regime,
            rule_set_version=rule_set.version,
            total_income=total_income,
            total_expenses=total_expenses,
            total_deductions=total_deductions,
            standard_deduction=rule_set.standard_deduction,
            taxable_income=taxable_income,
            tax_before_rebate=tax_before_rebate,
            rebate_applied=rebate,
            base_tax=base_tax,
            cess=cess,
            total_payable=total_payable,
            slab_breakdown=breakdown,
        )
