from __future__ import annotations

import json

from scripts.check_coverage_thresholds import main


def _report(tmp_path, *, total_lines=96.0, total_branches=91.0, critical_lines=100.0, critical_branches=100.0):
    path = tmp_path / "coverage.json"
    path.write_text(
        json.dumps(
            {
                "totals": {
                    "percent_statements_covered": total_lines,
                    "percent_branches_covered": total_branches,
                },
                "files": {
                    "backend\\security.py": {
                        "summary": {
                            "percent_statements_covered": critical_lines,
                            "percent_branches_covered": critical_branches,
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_coverage_gate_accepts_overall_and_critical_thresholds(tmp_path) -> None:
    report = _report(tmp_path)
    assert main([str(report), "--lines", "95", "--branches", "90", "--critical", "backend/security.py"]) == 0


def test_coverage_gate_rejects_overall_regression(tmp_path) -> None:
    report = _report(tmp_path, total_branches=89.99)
    assert main([str(report), "--lines", "95", "--branches", "90"]) == 1


def test_coverage_gate_rejects_critical_regression_or_missing_target(tmp_path) -> None:
    report = _report(tmp_path, critical_branches=99.99)
    assert main([str(report), "--critical", "backend/security.py"]) == 1
    assert main([str(report), "--critical", "backend/jobs.py"]) == 1
