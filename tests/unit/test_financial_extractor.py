from app.services.extraction.financial_field_extractor import FinancialFieldExtractor

extractor = FinancialFieldExtractor()


def test_extracts_salary_deduction_and_expense():
    data = extractor.extract("Salary: ₹9,00,000\n80C: 100000\nRent Paid: 180000")
    assert data.fields_found["salary"] == 900_000
    assert data.fields_found["section_80c"] == 100_000
    assert data.fields_found["rent_paid"] == 180_000
    assert data.total_income == 900_000
    assert data.total_deductions == 100_000
    assert data.total_expenses == 180_000


def test_case_insensitive_and_synonyms():
    data = extractor.extract("gross salary: 500000, Section 80D: 25000")
    assert data.fields_found["salary"] == 500_000
    assert data.fields_found["section_80d"] == 25_000


def test_no_recognizable_fields_is_empty():
    data = extractor.extract("Hello, I have a question about tax filing deadlines.")
    assert data.is_empty
    assert data.total_income == 0


def test_multiple_income_style_fields_do_not_double_count_same_field():
    # "Total Income" and "Salary" are synonyms for the same `salary` field;
    # only the first matching pattern should be used, not both summed.
    data = extractor.extract("Salary: 100000\nTotal Income: 999999")
    assert data.fields_found["salary"] == 100_000


def test_home_loan_interest_section_24b():
    data = extractor.extract("Home Loan Interest: 180000")
    assert data.fields_found["home_loan_interest_24b"] == 180_000
    assert data.total_deductions == 180_000
