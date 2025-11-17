from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from src.services.feedback_service import FeedbackPayload, FeedbackService


@pytest.fixture()
def feedback_service(tmp_path: Path) -> FeedbackService:
    return FeedbackService(storage_dir=tmp_path)


def test_payload_normalisation() -> None:
    payload = FeedbackPayload(
        title="  Title  ",
        description=" Description with space  ",
        category="  ",
        severity="",
        contact="  tester@example.com  ",
        metadata={"": "ignored", "valid": {"key": "value"}, "bad": set()},
    )

    normalised = payload.as_dict()

    assert normalised == {
        "title": "Title",
        "description": "Description with space",
        "category": "unspecified",
        "severity": "unspecified",
        "contact": "tester@example.com",
        "metadata": {"valid": {"key": "value"}},
    }


def test_thread_safe_submission(feedback_service: FeedbackService) -> None:
    payloads = [
        FeedbackPayload(
            title=f"Report {idx}",
            description="Description",
            category="ui",
            severity="low",
        )
        for idx in range(5)
    ]

    threads: list[threading.Thread] = []
    for payload in payloads:
        thread = threading.Thread(target=feedback_service.submit_feedback, args=(payload,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    inbox_path = feedback_service.storage_dir / FeedbackService.INBOX_FILENAME
    with inbox_path.open("r", encoding="utf-8") as handle:
        lines = [line.strip() for line in handle if line.strip()]

    assert len(lines) == len(payloads)

    summary_path = feedback_service.storage_dir / FeedbackService.SUMMARY_JSON_FILENAME
    with summary_path.open("r", encoding="utf-8") as handle:
        summary = json.load(handle)

    assert summary["totals"]["reports"] == len(payloads)
    assert summary["totals"]["categories"] == {"ui": len(payloads)}
    assert summary["totals"]["severity"] == {"low": len(payloads)}
    assert summary["last_submission_at"] is not None


def test_summary_generation_and_markdown(feedback_service: FeedbackService) -> None:
    feedback_service.submit_feedback(
        FeedbackPayload(
            title="Crash",
            description="App crashes",
            category="stability",
            severity="critical",
        )
    )
    feedback_service.submit_feedback(
        FeedbackPayload(
            title="Glitch",
            description="Minor glitch",
            category="ui",
            severity="low",
        )
    )

    feedback_service.refresh_summary()

    summary_path = feedback_service.storage_dir / FeedbackService.SUMMARY_JSON_FILENAME
    markdown_path = feedback_service.storage_dir / FeedbackService.SUMMARY_MARKDOWN_FILENAME

    with summary_path.open("r", encoding="utf-8") as handle:
        summary = json.load(handle)

    assert summary["totals"] == {
        "reports": 2,
        "categories": {"stability": 1, "ui": 1},
        "severity": {"critical": 1, "low": 1},
    }
    assert summary["last_submission_at"] is not None

    with markdown_path.open("r", encoding="utf-8") as handle:
        markdown = handle.read()

    assert "# Feedback summary" in markdown
    assert "**Total reports:** 2" in markdown
    assert "Категории" in markdown
    assert "| stability | 1 |" in markdown
    assert "| critical | 1 |" in markdown
