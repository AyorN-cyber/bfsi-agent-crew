"""Plain data models shared by the offline pipeline and the CrewAI crew."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Application:
    """A single loan application.

    ``monthly_debt`` is the applicant's total monthly obligations including the
    proposed loan payment, which is the figure policy uses for debt-to-income.
    """

    id: str
    applicant: str
    annual_income: float
    monthly_debt: float
    credit_score: int
    loan_amount: float
    property_value: float
    employment_years: float
    purpose: str = "home purchase"

    @property
    def monthly_income(self) -> float:
        return self.annual_income / 12

    @property
    def dti(self) -> float:
        """Debt-to-income ratio as a fraction (0.36 means 36%)."""
        if not self.monthly_income:
            return float("inf")
        return self.monthly_debt / self.monthly_income

    @property
    def ltv(self) -> float:
        """Loan-to-value ratio as a fraction."""
        if not self.property_value:
            return float("inf")
        return self.loan_amount / self.property_value

    @classmethod
    def from_dict(cls, data: dict) -> "Application":
        return cls(**data)


@dataclass(frozen=True)
class Finding:
    """The result of one policy check."""

    check: str
    status: str  # "pass", "refer" or "decline"
    detail: str


@dataclass(frozen=True)
class Citation:
    """A policy passage retrieved to support a finding."""

    source: str
    heading: str
    text: str
    score: float

    @property
    def ref(self) -> str:
        return f"{self.source} > {self.heading}"


@dataclass
class ReviewReport:
    """Everything the pipeline produces for one application."""

    application: Application
    findings: List[Finding] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    decision: str = ""
    memo: str = ""
