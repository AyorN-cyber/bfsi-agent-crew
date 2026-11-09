import json
from pathlib import Path

from bfsi_crew import Application, PolicyIndex, run_review
from bfsi_crew.cli import main

ROOT = Path(__file__).resolve().parents[1]


def _load():
    index = PolicyIndex.from_directory(ROOT / "data" / "policies")
    apps = [Application.from_dict(a) for a in json.loads((ROOT / "data" / "sample_applications.json").read_text())]
    return index, {a.id: a for a in apps}


def test_sample_decisions():
    index, apps = _load()
    expected = {
        "APP-001": "APPROVE",
        "APP-002": "REFER TO HUMAN UNDERWRITER",
        "APP-003": "DECLINE",
        "APP-004": "REFER TO HUMAN UNDERWRITER",
    }
    for app_id, decision in expected.items():
        assert run_review(apps[app_id], index).decision == decision


def test_memo_cites_policy_and_names_decline_reasons():
    index, apps = _load()
    report = run_review(apps["APP-003"], index)
    assert "credit-score.md" in report.memo
    assert "fair-lending.md" in report.memo
    assert "Adverse action" in report.memo
    assert "credit score" in report.memo


def test_cli_offline_run(capsys):
    code = main(
        [
            "review",
            "--applications", str(ROOT / "data" / "sample_applications.json"),
            "--policies", str(ROOT / "data" / "policies"),
            "--id", "APP-001",
        ]
    )
    assert code == 0
    assert "Recommendation: APPROVE" in capsys.readouterr().out


def test_cli_unknown_id_fails(capsys):
    code = main(
        [
            "review",
            "--applications", str(ROOT / "data" / "sample_applications.json"),
            "--policies", str(ROOT / "data" / "policies"),
            "--id", "NOPE",
        ]
    )
    assert code == 1
