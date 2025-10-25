from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from tools.audit.redundant_files import (
    AuditCandidate,
    build_markdown_report,
    scan_redundant_files,
)


@pytest.fixture()
def sample_structure(tmp_path: Path) -> Path:
    root = tmp_path
    # Корневые документы с похожими названиями
    (root / "LEGACY_REPORT_v1.md").write_text("draft", encoding="utf-8")
    (root / "LEGACY_REPORT_v2.md").write_text("final", encoding="utf-8")
    # Документ с ключевым словом
    (root / "STATUS_SUMMARY.md").write_text("status", encoding="utf-8")
    # Временный сценарий фикса
    (root / "fix_orientation.py").write_text("print('fix')", encoding="utf-8")
    # Файлы в подпапках не должны учитываться эвристикой по корню
    docs_dir = root / "docs"
    docs_dir.mkdir()
    (docs_dir / "important_report.md").write_text("keep", encoding="utf-8")
    return root


def test_scan_redundant_files_detects_keywords(sample_structure: Path) -> None:
    candidates = scan_redundant_files(sample_structure)
    rel_paths = {
        candidate.path.relative_to(sample_structure) for candidate in candidates
    }

    assert Path("STATUS_SUMMARY.md") in rel_paths
    status_candidate = next(
        candidate
        for candidate in candidates
        if candidate.path.name == "STATUS_SUMMARY.md"
    )
    assert any("ключевое слово" in reason for reason in status_candidate.reasons)


def test_scan_redundant_files_detects_duplicates(sample_structure: Path) -> None:
    candidates = scan_redundant_files(sample_structure)

    duplicate_candidates = [
        candidate
        for candidate in candidates
        if candidate.path.name.startswith("LEGACY_REPORT")
    ]
    assert len(duplicate_candidates) == 2
    for candidate in duplicate_candidates:
        assert any("несколько документов" in reason for reason in candidate.reasons)


def test_scan_redundant_files_marks_fix_scripts(sample_structure: Path) -> None:
    candidates = scan_redundant_files(sample_structure)
    script_candidate = next(
        candidate
        for candidate in candidates
        if candidate.path.name == "fix_orientation.py"
    )
    assert any("временный фикс" in reason for reason in script_candidate.reasons)


def test_build_markdown_report_handles_empty_list(tmp_path: Path) -> None:
    report = build_markdown_report([], tmp_path)
    assert "Подходящих кандидатов не найдено" in report


def test_build_markdown_report_includes_metadata(sample_structure: Path) -> None:
    candidate = AuditCandidate(
        path=sample_structure / "STATUS_SUMMARY.md",
        reasons=["Пример"],
        size_bytes=7,
        modified_at=dt.datetime(2024, 12, 31, tzinfo=dt.timezone.utc),
    )

    report = build_markdown_report([candidate], sample_structure)
    assert "STATUS_SUMMARY.md" in report
    assert "Размер: 7" in report
    assert "Причины" in report
