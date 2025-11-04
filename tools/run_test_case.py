"""CLI utility that evaluates structured physics test cases."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.tools.reporting import evaluate_physics_case, summarise_assertions
from tests.physics.cases import build_case_loader, load_test_case


def _resolve_case(identifier: str) -> Any:
    path = Path(identifier)
    if path.exists():
        return load_test_case(path)
    loader = build_case_loader()
    return loader(identifier)


def _default_reports_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports" / "tests"
    reports.mkdir(parents=True, exist_ok=True)
    return reports


def run(case_identifier: str, output_dir: Path | None = None) -> dict[str, Any]:
    case = _resolve_case(case_identifier)
    evaluation = evaluate_physics_case(case)
    assertion_results = summarise_assertions(case, evaluation)

    summary = {
        "id": case.identifier,
        "name": case.name,
        "description": case.description,
        "tags": list(case.tags),
        "generated_at": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "assertions": [
            {
                "kind": result.kind,
                "target": result.target,
                "expected": result.expected,
                "actual": result.actual,
                "tolerance": result.tolerance,
                "passed": result.passed,
            }
            for result in assertion_results
        ],
        "moments": evaluation["moments"],
        "vertical_forces": evaluation["vertical_forces"],
        "passed": all(result.passed for result in assertion_results),
    }

    target_dir = output_dir or _default_reports_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    report_path = target_dir / f"{case.identifier}_report.json"
    report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    summary["report_path"] = str(report_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", help="Case identifier or path to .test.json descriptor")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where the JSON report should be stored",
    )
    args = parser.parse_args()

    summary = run(args.case, output_dir=args.output_dir)
    status = "PASSED" if summary["passed"] else "FAILED"
    print(f"Case {summary['id']} – {status}")
    print(f"Report saved to {summary['report_path']}")

    if not summary["passed"]:
        exit(1)


if __name__ == "__main__":
    main()
