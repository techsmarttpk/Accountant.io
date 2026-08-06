"""Versioned Indian income-tax rule tables.

The legacy script hardcoded a single, undated 4-bracket table with no
regime distinction, no cess, and no rebate — wrong for most real filers and
impossible to update without editing code. Every rule set here is tagged by
financial year and regime, so adding/adjusting a year is a data change, not
a code change, and every `Calculation` row can record exactly which rule
set version produced it.

Sources: Union Budget slab announcements for the respective financial
years. Verify against the current year's Finance Act before relying on
this for real filings — tax law changes annually and this table must be
kept current by whoever owns the product.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.db.models.calculation import TaxRegime


@dataclass(frozen=True)
class TaxSlab:
    """A single income bracket. `upto` of None means "and above"."""

    from_amount: float
    upto: float | None
    rate: float  # fraction, e.g. 0.05 for 5%


@dataclass(frozen=True)
class RuleSet:
    version: str  # e.g. "IN-2024-25-NEW"
    financial_year: str
    regime: TaxRegime
    slabs: list[TaxSlab]
    standard_deduction: float
    cess_rate: float
    rebate_87a_income_threshold: float
    rebate_87a_max_amount: float

    def compute_rebate(self, taxable_income: float, tax_before_rebate: float) -> float:
        if taxable_income <= self.rebate_87a_income_threshold:
            return min(tax_before_rebate, self.rebate_87a_max_amount)
        return 0.0


# Old regime slabs are unchanged across recent financial years.
_OLD_REGIME_SLABS = [
    TaxSlab(0, 250_000, 0.0),
    TaxSlab(250_000, 500_000, 0.05),
    TaxSlab(500_000, 1_000_000, 0.20),
    TaxSlab(1_000_000, None, 0.30),
]

_NEW_REGIME_SLABS_2023_24 = [
    TaxSlab(0, 300_000, 0.0),
    TaxSlab(300_000, 600_000, 0.05),
    TaxSlab(600_000, 900_000, 0.10),
    TaxSlab(900_000, 1_200_000, 0.15),
    TaxSlab(1_200_000, 1_500_000, 0.20),
    TaxSlab(1_500_000, None, 0.30),
]

_NEW_REGIME_SLABS_2024_25 = [
    TaxSlab(0, 300_000, 0.0),
    TaxSlab(300_000, 700_000, 0.05),
    TaxSlab(700_000, 1_000_000, 0.10),
    TaxSlab(1_000_000, 1_200_000, 0.15),
    TaxSlab(1_200_000, 1_500_000, 0.20),
    TaxSlab(1_500_000, None, 0.30),
]

RULE_REGISTRY: dict[tuple[str, TaxRegime], RuleSet] = {
    ("2023-24", TaxRegime.OLD): RuleSet(
        version="IN-2023-24-OLD",
        financial_year="2023-24",
        regime=TaxRegime.OLD,
        slabs=_OLD_REGIME_SLABS,
        standard_deduction=50_000,
        cess_rate=0.04,
        rebate_87a_income_threshold=500_000,
        rebate_87a_max_amount=12_500,
    ),
    ("2023-24", TaxRegime.NEW): RuleSet(
        version="IN-2023-24-NEW",
        financial_year="2023-24",
        regime=TaxRegime.NEW,
        slabs=_NEW_REGIME_SLABS_2023_24,
        standard_deduction=50_000,
        cess_rate=0.04,
        rebate_87a_income_threshold=700_000,
        rebate_87a_max_amount=25_000,
    ),
    ("2024-25", TaxRegime.OLD): RuleSet(
        version="IN-2024-25-OLD",
        financial_year="2024-25",
        regime=TaxRegime.OLD,
        slabs=_OLD_REGIME_SLABS,
        standard_deduction=50_000,
        cess_rate=0.04,
        rebate_87a_income_threshold=500_000,
        rebate_87a_max_amount=12_500,
    ),
    ("2024-25", TaxRegime.NEW): RuleSet(
        version="IN-2024-25-NEW",
        financial_year="2024-25",
        regime=TaxRegime.NEW,
        slabs=_NEW_REGIME_SLABS_2024_25,
        standard_deduction=75_000,
        cess_rate=0.04,
        rebate_87a_income_threshold=700_000,
        rebate_87a_max_amount=25_000,
    ),
}

DEFAULT_FINANCIAL_YEAR = "2024-25"
LATEST_FINANCIAL_YEAR = "2024-25"


def get_rule_set(financial_year: str, regime: TaxRegime) -> RuleSet:
    key = (financial_year, regime)
    if key not in RULE_REGISTRY:
        available = sorted({fy for fy, _ in RULE_REGISTRY})
        raise KeyError(
            f"No tax rule set for financial year {financial_year!r} / regime "
            f"{regime.value!r}. Available financial years: {available}."
        )
    return RULE_REGISTRY[key]
