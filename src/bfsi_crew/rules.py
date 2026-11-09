"""Deterministic policy checks.

The numbers are computed in plain Python on purpose. Language models are good
at reading policy and explaining a decision, but they should not be trusted to
do arithmetic. The crew receives these findings as facts and reasons over them.
"""

from __future__ import annotations

from typing import List

from .models import Application, Finding

# Limits mirror data/policies/*.md. Change both together.
MIN_CREDIT_REFER = 620
MIN_CREDIT_DECLINE = 580
MAX_DTI_REFER = 0.43
MAX_DTI_DECLINE = 0.50
MAX_LTV_REFER = 0.80
MAX_LTV_DECLINE = 0.95
MIN_EMPLOYMENT_YEARS = 2.0


def check_credit(app: Application) -> Finding:
    score = app.credit_score
    if score < MIN_CREDIT_DECLINE:
        return Finding("credit score", "decline", f"Score {score} is below the {MIN_CREDIT_DECLINE} floor.")
    if score < MIN_CREDIT_REFER:
        return Finding("credit score", "refer", f"Score {score} is below {MIN_CREDIT_REFER} and needs manual review.")
    return Finding("credit score", "pass", f"Score {score} meets the {MIN_CREDIT_REFER} minimum.")


def check_dti(app: Application) -> Finding:
    dti = app.dti
    pct = f"{dti:.1%}"
    if dti > MAX_DTI_DECLINE:
        return Finding("debt-to-income", "decline", f"DTI {pct} exceeds the {MAX_DTI_DECLINE:.0%} ceiling.")
    if dti > MAX_DTI_REFER:
        return Finding("debt-to-income", "refer", f"DTI {pct} exceeds {MAX_DTI_REFER:.0%} and needs manual review.")
    return Finding("debt-to-income", "pass", f"DTI {pct} is within the {MAX_DTI_REFER:.0%} limit.")


def check_ltv(app: Application) -> Finding:
    ltv = app.ltv
    pct = f"{ltv:.1%}"
    if ltv > MAX_LTV_DECLINE:
        return Finding("loan-to-value", "decline", f"LTV {pct} exceeds the {MAX_LTV_DECLINE:.0%} ceiling.")
    if ltv > MAX_LTV_REFER:
        return Finding("loan-to-value", "refer", f"LTV {pct} exceeds {MAX_LTV_REFER:.0%} and needs manual review.")
    return Finding("loan-to-value", "pass", f"LTV {pct} is within the {MAX_LTV_REFER:.0%} limit.")


def check_employment(app: Application) -> Finding:
    years = app.employment_years
    if years < MIN_EMPLOYMENT_YEARS:
        return Finding(
            "employment history",
            "refer",
            f"{years:g} years of history is under the {MIN_EMPLOYMENT_YEARS:g} year guideline.",
        )
    return Finding("employment history", "pass", f"{years:g} years of history meets the guideline.")


def evaluate(app: Application) -> List[Finding]:
    """Run every check and return the findings in a stable order."""
    return [check_credit(app), check_dti(app), check_ltv(app), check_employment(app)]


def decide(findings: List[Finding]) -> str:
    """Combine findings into a recommendation. A human always makes the final call."""
    statuses = {f.status for f in findings}
    if "decline" in statuses:
        return "DECLINE"
    if "refer" in statuses:
        return "REFER TO HUMAN UNDERWRITER"
    return "APPROVE"
