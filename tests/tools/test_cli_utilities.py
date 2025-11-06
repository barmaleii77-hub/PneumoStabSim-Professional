"""Tests covering the new CLI utilities that produce reports."""

from __future__ import annotations

from pathlib import Path

from tools import collect_qml_errors, run_test_case, check_shader_logs


def test_run_test_case_generates_report(
    physics_case_loader, reports_tests_dir, tmp_path
):
    case = physics_case_loader("standard-suspension-balance")
    summary = run_test_case.run(case.identifier, output_dir=tmp_path)
    report_path = Path(summary["report_path"])
    assert report_path.exists()
    assert summary["passed"] is True


def test_collect_qml_errors(tmp_path):
    log_path = tmp_path / "qml.log"
    log_path.write_text(
        """
        [INFO] Application starting
        qrc:/Main.qml:45: TypeError: cannot assign to property
        QFontDatabase: Cannot find font directory
        file:///something.qml:12:5: QML Warning: binding loop detected
        """,
        encoding="utf-8",
    )

    report = collect_qml_errors.analyse_log(log_path)
    assert report["total_entries"] == 2
    assert any("TypeError" in entry["message"] for entry in report["entries"])


def test_check_shader_logs(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    good = log_dir / "material.log"
    good.write_text("Compilation successful\n", encoding="utf-8")
    bad = log_dir / "skybox.log"
    bad.write_text("ERROR: uniform missing\nWARNING: fallback used\n", encoding="utf-8")

    summary = check_shader_logs.scan_directory(log_dir)
    error_entry = next(item for item in summary if "skybox" in item["source"])
    assert error_entry["error_count"] == 1
    assert error_entry["warning_count"] == 1
