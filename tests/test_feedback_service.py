import json
import threading
from datetime import datetime

import pytest

from src.services.feedback_service import (
    FeedbackPayload,
    FeedbackService,
)


@pytest.fixture()
def feedback_service(tmp_path):
    return FeedbackService(storage_dir=tmp_path)


def test_payload_normalization_and_filtering_metadata():
    payload = FeedbackPayload(
        title="  Title with spaces  ",
        description="  Description  ",
        category="   ",
        severity="",
        contact="  tester@example.com  ",
        metadata={
            "valid": "value",
            "": "should be ignored",
            "serialisable": {"nested": 1},
            "non_serialisable": object(),
        },
    )

    normalised = payload.as_dict()

    assert normalised["title"] == "Title with spaces"
    assert normalised["description"] == "Description"
    assert normalised["category"] == "unspecified"
    assert normalised["severity"] == "unspecified"
    assert normalised["contact"] == "tester@example.com"
    assert "" not in normalised.get("metadata", {})
    assert "non_serialisable" not in normalised.get("metadata", {})
    assert normalised["metadata"]["valid"] == "value"
    assert normalised["metadata"]["serialisable"] == {"nested": 1}


def test_submission_persists_and_updates_summary(feedback_service, tmp_path):
    payloads = [
        FeedbackPayload("Title A", "Desc A", "cat1", "high"),
        FeedbackPayload("Title B", "Desc B", "cat2", "low"),
    ]

    results = [feedback_service.submit_feedback(payload) for payload in payloads]

    inbox_path = tmp_path / feedback_service.INBOX_FILENAME
    summary_path = tmp_path / feedback_service.SUMMARY_JSON_FILENAME

    assert inbox_path.exists()
    with inbox_path.open() as handle:
        lines = [line.strip() for line in handle if line.strip()]
    assert len(lines) == len(payloads)

    summary = json.loads(summary_path.read_text())
    assert summary["totals"]["reports"] == 2
    assert summary["totals"]["categories"] == {"cat1": 1, "cat2": 1}
    assert summary["totals"]["severity"] == {"high": 1, "low": 1}

    latest_timestamp = max(result.created_at for result in results)
    assert summary["last_submission_at"] == latest_timestamp.isoformat()


def test_thread_safe_writes(feedback_service, tmp_path):
    results: list[str] = []

    def _submit(idx: int) -> None:
        result = feedback_service.submit_feedback(
            FeedbackPayload(
                title=f"Title {idx}",
                description="Concurrent write",
                category="load",
                severity="medium",
            )
        )
        results.append(result.submission_id)

    threads = [threading.Thread(target=_submit, args=(idx,)) for idx in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 10
    assert len(set(results)) == 10

    inbox_path = tmp_path / feedback_service.INBOX_FILENAME
    with inbox_path.open() as handle:
        lines = [line.strip() for line in handle if line.strip()]
    assert len(lines) == 10

    summary = json.loads(
        (tmp_path / feedback_service.SUMMARY_JSON_FILENAME).read_text()
    )
    assert summary["totals"]["reports"] == 10
    assert summary["totals"]["categories"] == {"load": 10}
    assert summary["totals"]["severity"] == {"medium": 10}


@pytest.mark.usefixtures("feedback_service")
def test_markdown_summary_generation(tmp_path):
    service = FeedbackService(storage_dir=tmp_path)
    service.submit_feedback(FeedbackPayload("Title 1", "Desc", "catA", "high"))
    service.submit_feedback(FeedbackPayload("Title 2", "Desc", "catA", "low"))
    service.submit_feedback(FeedbackPayload("Title 3", "Desc", "catB", "low"))

    summary = json.loads((tmp_path / service.SUMMARY_JSON_FILENAME).read_text())
    markdown = (tmp_path / service.SUMMARY_MARKDOWN_FILENAME).read_text()

    assert "# Feedback summary" in markdown
    assert f"**Total reports:** {summary['totals']['reports']}" in markdown
    assert "## Категории" in markdown
    assert "## Критичность" in markdown

    category_table = "| catA | 2 |" in markdown and "| catB | 1 |" in markdown
    severity_table = "| low | 2 |" in markdown and "| high | 1 |" in markdown
    assert category_table
    assert severity_table

    assert summary["totals"]["reports"] == 3
    assert summary["totals"]["categories"] == {"catA": 2, "catB": 1}
    assert summary["totals"]["severity"] == {"high": 1, "low": 2}

    last_submission = datetime.fromisoformat(summary["last_submission_at"])
    generated_at = datetime.fromisoformat(summary["generated_at"])
    assert generated_at >= last_submission
