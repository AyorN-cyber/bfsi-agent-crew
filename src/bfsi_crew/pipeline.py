"""The offline pipeline.

It mirrors the four roles in the CrewAI crew (intake, risk, compliance,
summary) but uses deterministic code instead of a language model. That gives
the project a fast test suite, a baseline to compare live runs against, and a
demo that works without an API key.
"""

from __future__ import annotations

from typing import Dict, List

from .models import Application, Citation, Finding, ReviewReport
from .rag import PolicyIndex
from .rules import decide, evaluate

# What to search for when citing policy for each check.
POLICY_QUERIES: Dict[str, str] = {
    "credit score": "minimum credit score threshold",
    "debt-to-income": "debt to income ratio limit",
    "loan-to-value": "loan to value ratio limit down payment",
    "employment history": "employment history stability years",
}


def intake(app: Application) -> str:
    """Intake analyst: normalise the application into a short factual summary."""
    return (
        f"{app.applicant} ({app.id}) requests ${app.loan_amount:,.0f} for {app.purpose} "
        f"against a property valued at ${app.property_value:,.0f}. Annual income "
        f"${app.annual_income:,.0f}, monthly obligations ${app.monthly_debt:,.0f}, "
        f"credit score {app.credit_score}, {app.employment_years:g} years in current employment."
    )


def risk_analysis(app: Application) -> List[Finding]:
    """Risk analyst: apply the numeric policy limits."""
    return evaluate(app)


def compliance_review(findings: List[Finding], index: PolicyIndex) -> List[Citation]:
    """Compliance reviewer: attach the policy passage behind every finding."""
    citations: List[Citation] = []
    seen = set()
    queries = [POLICY_QUERIES[f.check] for f in findings if f.check in POLICY_QUERIES]
    queries.append("fair lending human review adverse action reasons")
    for query in queries:
        for hit in index.search(query, k=1):
            if hit.ref not in seen:
                seen.add(hit.ref)
                citations.append(hit)
    return citations


def write_memo(
    app: Application, findings: List[Finding], decision: str, citations: List[Citation]
) -> str:
    """Summary writer: produce a reviewer-ready memo in Markdown."""
    lines = [
        f"## {app.id}: {app.applicant}",
        "",
        f"**Recommendation: {decision}**",
        "",
        intake(app),
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    lines += [f"| {f.check} | {f.status.upper()} | {f.detail} |" for f in findings]
    lines += ["", "**Policy references**", ""]
    lines += [f"- {c.ref}" for c in citations]
    lines += ["", "**Compliance note**", ""]
    declines = [f for f in findings if f.status == "decline"]
    refers = [f for f in findings if f.status == "refer"]
    if declines:
        reasons = ", ".join(f.check for f in declines)
        lines.append(
            f"Adverse action: the applicant must receive a notice naming the specific reasons ({reasons}). "
            "A human underwriter confirms the decision before it is communicated."
        )
    elif refers:
        reasons = ", ".join(f.check for f in refers)
        lines.append(f"Route to a human underwriter. Items needing judgement: {reasons}.")
    else:
        lines.append("All checks passed. This is a recommendation only; a human makes the final decision.")
    return "\n".join(lines) + "\n"


def run_review(app: Application, index: PolicyIndex) -> ReviewReport:
    findings = risk_analysis(app)
    decision = decide(findings)
    citations = compliance_review(findings, index)
    memo = write_memo(app, findings, decision, citations)
    return ReviewReport(app, findings, citations, decision, memo)
