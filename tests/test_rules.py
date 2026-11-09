from bfsi_crew.models import Application
from bfsi_crew.rules import check_credit, check_dti, check_ltv, decide, evaluate


def make(**overrides) -> Application:
    base = dict(
        id="T-1",
        applicant="Test",
        annual_income=120000,
        monthly_debt=3000,
        credit_score=720,
        loan_amount=300000,
        property_value=450000,
        employment_years=5,
    )
    base.update(overrides)
    return Application(**base)


def test_clean_application_is_approved():
    assert decide(evaluate(make())) == "APPROVE"


def test_credit_boundaries():
    assert check_credit(make(credit_score=620)).status == "pass"
    assert check_credit(make(credit_score=619)).status == "refer"
    assert check_credit(make(credit_score=580)).status == "refer"
    assert check_credit(make(credit_score=579)).status == "decline"


def test_dti_boundaries():
    # monthly income is 10,000, so debt maps directly to DTI.
    assert check_dti(make(monthly_debt=4300)).status == "pass"
    assert check_dti(make(monthly_debt=4301)).status == "refer"
    assert check_dti(make(monthly_debt=5001)).status == "decline"


def test_ltv_boundaries():
    assert check_ltv(make(loan_amount=360000, property_value=450000)).status == "pass"
    assert check_ltv(make(loan_amount=361000, property_value=450000)).status == "refer"
    assert check_ltv(make(loan_amount=430000, property_value=450000)).status == "decline"


def test_decline_outranks_refer():
    findings = evaluate(make(credit_score=500, employment_years=0.5))
    assert decide(findings) == "DECLINE"


def test_zero_income_does_not_crash():
    findings = evaluate(make(annual_income=0))
    assert decide(findings) == "DECLINE"
