"""Tests for :mod:`src.services.feedback_service`."""

from __future__ import annotations

import json
import threading
from datetime import datetime

import pytest

from src.services.feedback_service import FeedbackPayload, FeedbackService


def test_feedback_payload_normalization() -> None:
    payload = FeedbackPayload(
        title="  Critical bug  ",
        description="  Crashes on start  ",
        category=" ",
        severity="  high  ",
        contact="  user@example.com  ",
        metadata={"": "skip", "valid": {"nested": 1}, "invalid": {1, 2}},
    )

    normalised = payload.as_dict()

    assert normalised["title"] == "Critical bug"
    assert normalised["description"] == "Crashes on start"
    assert normalised["category"] == "unspecified"
    assert normalised["severity"] == "high"
    assert normalised["contact"] == "user@example.com"
    assert normalised["metadata"] == {"valid": {"nested": 1}}


def test_submit_feedback_is_thread_safe(tmp_path: pytest.PathLike[str]) -> None:
    service = FeedbackService(storage_dir=tmp_path)

    submissions = 12
    categories = ["ui", "backend", "backend"] * 4
    severities = ["low", "medium", "medium"] * 4
    results: list[str] = []

    def _worker(index: int) -> None:
        payload = FeedbackPayload(
            title=f"Issue {index}",
            description=f"Details {index}",
            category=categories[index],
            severity=severities[index],
        )
        result = service.submit_feedback(payload)
        results.append(result.submission_id)

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(submissions)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    inbox_path = tmp_path / FeedbackService.INBOX_FILENAME
    with inbox_path.open(encoding="utf-8") as handle:
        lines = [line for line in handle if line.strip()]

    summary_path = tmp_path / FeedbackService.SUMMARY_JSON_FILENAME
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert len(results) == submissions
    assert len(lines) == submissions
    assert summary["totals"]["reports"] == submissions
    assert summary["totals"]["categories"] == {"backend": 8, "ui": 4}
    assert summary["totals"]["severity"] == {"low": 4, "medium": 8}


def test_summary_and_markdown_generation(tmp_path: pytest.PathLike[str]) -> None:
    service = FeedbackService(storage_dir=tmp_path)

    payloads = [
        FeedbackPayload(
            title="UI glitch",
            description="Button misaligned",
            category="ui",
            severity="low",
        ),
        FeedbackPayload(
            title="",
            description="Missing logs",
            category="backend",
            severity="",
        ),
        FeedbackPayload(
            title="No category",
            description="Unspecified",
            category="",
            severity="critical",
        ),
    ]

    for payload in payloads:
        service.submit_feedback(payload)

    service.refresh_summary()

    summary_path = tmp_path / FeedbackService.SUMMARY_JSON_FILENAME
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["totals"]["reports"] == 3
    assert summary["totals"]["categories"] == {"backend": 1, "ui": 1, "unspecified": 1}
    assert summary["totals"]["severity"] == {"critical": 1, "low": 1, "unspecified": 1}

    entries = service._iter_entries()
    newest_entry = max(
        (datetime.fromisoformat(entry["created_at"]) for entry in entries),
        key=lambda item: item,
    )
    assert datetime.fromisoformat(summary["last_submission_at"]) == newest_entry

    markdown_path = tmp_path / FeedbackService.SUMMARY_MARKDOWN_FILENAME
    markdown_content = markdown_path.read_text(encoding="utf-8").splitlines()

    assert markdown_content[0] == "# Feedback summary"
    assert any("Total reports" in line for line in markdown_content)
    assert "| ui | 1 |" in markdown_content
    assert "| backend | 1 |" in markdown_content
    assert "| unspecified | 1 |" in markdown_content
