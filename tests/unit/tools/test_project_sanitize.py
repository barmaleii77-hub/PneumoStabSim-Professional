"""Tests for the project sanitisation CLI helpers."""

from __future__ import annotations

from tools import project_sanitize


def test_normalise_argv_supports_compact_report_history_flag() -> None:
    result = project_sanitize._normalise_argv(["--report-history5", "--dry-run"])

    assert result == ["--report-history", "5", "--dry-run"]


def test_main_parses_compact_report_history_flag(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_sanitize_repository(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)

    monkeypatch.setattr(project_sanitize, "sanitize_repository", fake_sanitize_repository)

    project_sanitize.main(["--report-history5"])

    assert captured == {"dry_run": False, "verbose": False, "report_history": 5}
