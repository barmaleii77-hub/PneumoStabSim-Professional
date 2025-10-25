from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from tools.quality import report_metrics


def _write_metrics(tmp_path: Path, name: str, payload: dict[str, object]) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _read_dashboard(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames or []
        rows = list(reader)
    return header, rows


def test_report_metrics_creates_csv(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    metrics = {
        "timestamp": "2025-10-30T12:30:45Z",
        "lint": {"duration_seconds": 12.5, "issues": 0},
        "pytest": {"duration_seconds": 91.0, "flaky": 1},
        "coverage": {"percent": 78.5},
    }
    metrics_path = _write_metrics(tmp_path, "metrics.json", metrics)
    output = tmp_path / "dashboard.csv"

    exit_code = report_metrics.main(
        ["--input", str(metrics_path), "--output", str(output)]
    )

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "Wrote 1 entry" in captured

    header, rows = _read_dashboard(output)
    assert header[0] == "timestamp"
    assert rows == [
        {
            "timestamp": "2025-10-30T12:30:45+00:00",
            "coverage_percent": "78.5",
            "lint_duration_seconds": "12.5",
            "lint_issues": "0",
            "pytest_duration_seconds": "91.0",
            "pytest_flaky": "1",
        }
    ]


def test_report_metrics_appends_new_rows_without_duplicates(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "dashboard.csv"

    first = {
        "timestamp": "2025-10-30T12:30:45Z",
        "lint": {"duration_seconds": 12.5, "issues": 0},
        "pytest": {"duration_seconds": 91.0, "flaky": 1},
        "coverage": {"percent": 78.5},
    }
    second = {
        "timestamp": "2025-10-31T08:00:00+02:00",
        "typecheck": {"duration_seconds": 30.0, "errors": 1},
        "pytest": {"duration_seconds": 92.0, "failures": 0},
    }
    duplicate = {
        "timestamp": "2025-10-30T12:30:45Z",
        "lint": {"duration_seconds": 11.0, "issues": 0},
    }

    for index, payload in enumerate((first, second, duplicate), start=1):
        metrics_path = _write_metrics(tmp_path, f"metrics_{index}.json", payload)
        exit_code = report_metrics.main(
            ["--input", str(metrics_path), "--output", str(output)]
        )
        assert exit_code == 0

    captured = capsys.readouterr().out
    lines = [line for line in captured.splitlines() if line.strip()]
    assert any("Wrote 1 entry" in line for line in lines)
    assert lines[-1].startswith("Wrote 0 entries")

    header, rows = _read_dashboard(output)
    assert header[0] == "timestamp"
    assert len(rows) == 2

    assert rows[0]["timestamp"] == "2025-10-30T12:30:45+00:00"
    assert rows[1]["timestamp"] == "2025-10-31T08:00:00+02:00"

    expected_columns = {
        "coverage_percent",
        "lint_duration_seconds",
        "lint_issues",
        "pytest_duration_seconds",
        "pytest_failures",
        "pytest_flaky",
        "typecheck_duration_seconds",
        "typecheck_errors",
    }
    assert set(header[1:]) == expected_columns

    assert rows[0]["pytest_failures"] == ""
    assert rows[1]["typecheck_errors"] == "1"
