import pytest

from app.db.models.calculation import TaxRegime
from app.services.tax_engine.calculator import TaxCalculationService

calc = TaxCalculationService()


def test_zero_income_has_zero_tax():
    result = calc.calculate(
        total_income=0, total_expenses=0, total_deductions=0,
        financial_year="2024-25", regime=TaxRegime.NEW,
    )
    assert result.taxable_income == 0
    assert result.total_payable == 0


def test_new_regime_below_rebate_threshold_is_fully_rebated():
    # FY2024-25 new regime: standard deduction 75,000, rebate up to taxable
    # income of 700,000. Gross 700,000 -> taxable 625,000 -> tax before
    # rebate is small enough that the ₹25,000 rebate cap fully cancels it.
    result = calc.calculate(
        total_income=700_000, total_expenses=0, total_deductions=0,
        financial_year="2024-25", regime=TaxRegime.NEW,
    )
    assert result.taxable_income == 625_000
    assert result.total_payable == 0
    assert result.rebate_applied == result.tax_before_rebate


def test_new_regime_above_rebate_threshold_pays_full_slab_tax():
    result = calc.calculate(
        total_income=2_000_000, total_expenses=0, total_deductions=0,
        financial_year="2024-25", regime=TaxRegime.NEW,
    )
    # taxable = 2,000,000 - 75,000 standard deduction = 1,925,000
    # slabs: 0-3L:0, 3-7L@5%=20000, 7-10L@10%=30000, 10-12L@15%=30000,
    # 12-15L@20%=60000, 15L-19.25L (425,000)@30%=127,500 => 267,500
    assert result.taxable_income == 1_925_000
    assert result.rebate_applied == 0
    assert result.base_tax == pytest.approx(267_500)
    assert result.cess == pytest.approx(267_500 * 0.04)
    assert result.total_payable == pytest.approx(267_500 * 1.04)


def test_old_regime_applies_80c_and_hra_style_deduction():
    result = calc.calculate(
        total_income=1_000_000, total_expenses=200_000, total_deductions=150_000,
        financial_year="2024-25", regime=TaxRegime.OLD,
    )
    # net = 800,000; taxable = 800,000 - 150,000 - 50,000 std ded = 600,000
    assert result.taxable_income == 600_000
    # slabs: 0-2.5L:0, 2.5-5L@5%=12500, 5-6L@20%=20000 => 32500
    assert result.base_tax == pytest.approx(32_500)


def test_expenses_never_push_income_negative():
    result = calc.calculate(
        total_income=100_000, total_expenses=500_000, total_deductions=0,
        financial_year="2024-25", regime=TaxRegime.NEW,
    )
    assert result.taxable_income == 0
    assert result.total_payable == 0


def test_unknown_financial_year_raises():
    with pytest.raises(KeyError):
        calc.calculate(
            total_income=500_000, total_expenses=0, total_deductions=0,
            financial_year="1999-00", regime=TaxRegime.NEW,
        )


def test_slab_breakdown_sums_to_tax_before_rebate():
    result = calc.calculate(
        total_income=1_500_000, total_expenses=0, total_deductions=0,
        financial_year="2024-25", regime=TaxRegime.NEW,
    )
    assert sum(entry.tax for entry in result.slab_breakdown) == pytest.approx(result.tax_before_rebate)
