"""CrewAI wiring: four agents, four sequential tasks, one policy-lookup tool.

CrewAI is imported lazily so the rest of the package (and the test suite) works
without it. Install the extra with ``pip install -e ".[live]"``.

Design note: the numeric findings are computed by ``rules.evaluate`` and handed
to the agents as facts. The agents add judgement, policy citations and writing,
not arithmetic.
"""

from __future__ import annotations

from typing import Any

from .models import Application
from .pipeline import intake
from .rag import PolicyIndex
from .rules import decide, evaluate


def build_crew(app: Application, index: PolicyIndex, model: str = "gpt-4o-mini") -> Any:
    """Assemble (but do not run) the crew for one application."""
    try:
        from crewai import LLM, Agent, Crew, Process, Task
        from crewai.tools import tool
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(
            'CrewAI is not installed. Run: pip install -e ".[live]"'
        ) from exc

    @tool("policy_lookup")
    def policy_lookup(query: str) -> str:
        """Search the lending policy library and return the most relevant passages."""
        hits = index.search(query, k=3)
        if not hits:
            return "No matching policy found."
        return "\n\n".join(f"[{h.ref}] {h.text}" for h in hits)

    llm = LLM(model=model, temperature=0)
    findings = evaluate(app)
    facts = "\n".join(f"- {f.check}: {f.status.upper()} ({f.detail})" for f in findings)

    intake_agent = Agent(
        role="Intake Analyst",
        goal="Turn the raw application into a short, accurate factual summary.",
        backstory="You check applications for completeness and never invent missing facts.",
        llm=llm,
        allow_delegation=False,
    )
    risk_agent = Agent(
        role="Credit Risk Analyst",
        goal="Explain what the verified policy findings mean for this applicant.",
        backstory="You reason about risk from verified numbers and never recalculate them.",
        llm=llm,
        allow_delegation=False,
    )
    compliance_agent = Agent(
        role="Compliance Reviewer",
        goal="Ground the recommendation in written policy and flag fair-lending obligations.",
        backstory="You cite the policy library for every claim and require human sign-off.",
        tools=[policy_lookup],
        llm=llm,
        allow_delegation=False,
    )
    writer_agent = Agent(
        role="Memo Writer",
        goal="Write a concise underwriting memo that a human reviewer can act on.",
        backstory="You write plain, structured memos and never contradict the verified findings.",
        llm=llm,
        allow_delegation=False,
    )

    t_intake = Task(
        description=f"Summarise this application in three sentences:\n{intake(app)}",
        expected_output="A three-sentence factual summary.",
        agent=intake_agent,
    )
    t_risk = Task(
        description=(
            "Using only these verified findings, assess the applicant's risk profile.\n"
            f"{facts}\nRule-based recommendation: {decide(findings)}"
        ),
        expected_output="A short risk assessment that agrees with the verified findings.",
        agent=risk_agent,
        context=[t_intake],
    )
    t_compliance = Task(
        description=(
            "Use the policy_lookup tool to find the policy behind each finding and the "
            "fair-lending rules for this outcome. List every policy reference you used."
        ),
        expected_output="Policy references and compliance obligations for this outcome.",
        agent=compliance_agent,
        context=[t_risk],
    )
    t_memo = Task(
        description="Write the final underwriting memo in Markdown, with the recommendation first.",
        expected_output="A Markdown memo: recommendation, key findings, policy references, next step.",
        agent=writer_agent,
        context=[t_intake, t_risk, t_compliance],
    )

    return Crew(
        agents=[intake_agent, risk_agent, compliance_agent, writer_agent],
        tasks=[t_intake, t_risk, t_compliance, t_memo],
        process=Process.sequential,
        verbose=False,
    )
