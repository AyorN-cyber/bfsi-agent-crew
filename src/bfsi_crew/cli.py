"""Command line entry point: ``bfsi-crew review``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .models import Application
from .pipeline import run_review
from .rag import PolicyIndex


def _load_applications(path: Path) -> List[Application]:
    return [Application.from_dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="bfsi-crew", description="Multi-agent loan application review.")
    sub = parser.add_subparsers(dest="command", required=True)

    review = sub.add_parser("review", help="Review applications and print underwriting memos.")
    review.add_argument("--applications", type=Path, default=Path("data/sample_applications.json"))
    review.add_argument("--policies", type=Path, default=Path("data/policies"))
    review.add_argument("--id", help="Only review the application with this id.")
    review.add_argument("--live", action="store_true", help="Run the CrewAI crew instead of the offline pipeline.")
    review.add_argument("--model", default="gpt-4o-mini", help="LLM model name for --live.")

    args = parser.parse_args(argv)

    index = PolicyIndex.from_directory(args.policies)
    applications = _load_applications(args.applications)
    if args.id:
        applications = [a for a in applications if a.id == args.id]
        if not applications:
            print(f"No application with id {args.id}", file=sys.stderr)
            return 1

    for app in applications:
        if args.live:
            from .crew import build_crew

            print(build_crew(app, index, model=args.model).kickoff())
        else:
            print(run_review(app, index).memo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
