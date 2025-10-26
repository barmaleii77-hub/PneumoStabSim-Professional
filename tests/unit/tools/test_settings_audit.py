from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.tools import settings_audit


@pytest.fixture()
def sample_payloads() -> tuple[dict[str, object], dict[str, object]]:
    baseline = {
        "metadata": {"version": "1.0"},
        "current": {
            "graphics": {"exposure": 0.5, "profiles": ["studio", "sunset"]},
            "simulation": {"dt": 0.01},
        },
    }
    target = {
        "metadata": {"version": "1.1"},
        "current": {
            "graphics": {"exposure": 0.75, "profiles": ["studio", "noon", "sunset"]},
            "simulation": {"dt": 0.01},
            "pneumatic": {"receiver_volume": 0.02},
        },
    }
    return baseline, target


def test_diff_settings_reports_structural_changes(
    sample_payloads: tuple[dict[str, object], dict[str, object]],
) -> None:
    baseline, target = sample_payloads

    entries = settings_audit.diff_settings(baseline, target)

    paths = {entry.path: entry.change for entry in entries}
    assert paths["metadata.version"] == "changed"
    assert paths["current.graphics.exposure"] == "changed"
    assert paths["current.graphics.profiles[2]"] == "added"
    assert paths["current.pneumatic"] == "added"


def test_render_report_text_format(
    sample_payloads: tuple[dict[str, object], dict[str, object]],
) -> None:
    baseline, target = sample_payloads
    entries = settings_audit.diff_settings(baseline, target)

    report = settings_audit.render_report(entries, format="text")

    assert "Settings audit report" in report
    assert "current.graphics.exposure" in report
    assert "Added" not in report  # textual output uses symbols
    assert "~ current.graphics.exposure" in report


def test_generate_report_to_file(
    tmp_path: Path, sample_payloads: tuple[dict[str, object], dict[str, object]]
) -> None:
    baseline, target = sample_payloads
    baseline_path = tmp_path / "baseline.json"
    target_path = tmp_path / "target.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    target_path.write_text(json.dumps(target), encoding="utf-8")

    entries, report = settings_audit.generate_report(
        baseline_path,
        target_path,
        output_format="markdown",
    )

    assert entries
    assert report.startswith("# Settings audit")


def test_cli_fail_on_diff(
    tmp_path: Path, sample_payloads: tuple[dict[str, object], dict[str, object]]
) -> None:
    baseline, target = sample_payloads
    baseline_path = tmp_path / "baseline.json"
    target_path = tmp_path / "target.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    target_path.write_text(json.dumps(target), encoding="utf-8")

    exit_code = settings_audit.main(
        [
            "--baseline",
            str(baseline_path),
            "--target",
            str(target_path),
            "--fail-on-diff",
        ]
    )

    assert exit_code == 1
