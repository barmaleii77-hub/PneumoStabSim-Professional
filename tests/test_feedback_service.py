import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.services.feedback_service import FeedbackPayload, FeedbackService


@pytest.fixture()
def feedback_service(tmp_path: Path) -> FeedbackService:
    return FeedbackService(storage_dir=tmp_path)


def test_payload_normalization_trims_filters_and_casts_metadata(
    feedback_service: FeedbackService,
) -> None:
    payload = FeedbackPayload(
        title="  Title with spaces  ",
        description="  Description  ",
        category="   ",
        severity="",
        contact="  tester@example.com  ",
        metadata={
            "valid": "value",
            "": "should be ignored",
            123: "numeric key",
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

    metadata = normalised["metadata"]
    assert metadata["valid"] == "value"
    assert metadata["serialisable"] == {"nested": 1}
    assert metadata["123"] == "numeric key"
    assert "" not in metadata
    assert "non_serialisable" not in metadata


def test_refresh_summary_aggregates_only_valid_entries(
    tmp_path: Path, feedback_service: FeedbackService
) -> None:
    inbox_path = tmp_path / feedback_service.INBOX_FILENAME
    inbox_path.write_text(
        "\n".join(
            [
                "not json",
                "",
                json.dumps(
                    {
                        "submission_id": "abc",
                        "created_at": datetime(2024, 5, 1, tzinfo=timezone.utc).isoformat(),
                        "category": "",
                        "severity": "",
                    }
                ),
                json.dumps(
                    {
                        "submission_id": "def",
                        "created_at": "bad timestamp",
                        "category": "ux",
                        "severity": "low",
                    }
                ),
                json.dumps(
                    {
                        "submission_id": "ghi",
                        "created_at": datetime(2024, 6, 1, tzinfo=timezone.utc).isoformat(),
                        "category": "ux",
                        "severity": "low",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    feedback_service.refresh_summary()

    summary = json.loads((tmp_path / feedback_service.SUMMARY_JSON_FILENAME).read_text())

    assert summary["totals"]["reports"] == 3
    assert summary["totals"]["categories"] == {"unspecified": 1, "ux": 2}
    assert summary["totals"]["severity"] == {"unspecified": 1, "low": 2}
    assert summary["last_submission_at"] == datetime(2024, 6, 1, tzinfo=timezone.utc).isoformat()


def test_submit_feedback_is_thread_safe(
    feedback_service: FeedbackService, tmp_path: Path
) -> None:
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
    with inbox_path.open(encoding="utf-8") as handle:
        lines = [line.strip() for line in handle if line.strip()]
    assert len(lines) == 10

    summary = json.loads((tmp_path / feedback_service.SUMMARY_JSON_FILENAME).read_text())
    assert summary["totals"]["reports"] == 10
    assert summary["totals"]["categories"] == {"load": 10}
    assert summary["totals"]["severity"] == {"medium": 10}

    last_submission = datetime.fromisoformat(summary["last_submission_at"])
    generated_at = datetime.fromisoformat(summary["generated_at"])
    assert generated_at >= last_submission


def test_markdown_summary_for_empty_dataset(tmp_path: Path) -> None:
    service = FeedbackService(storage_dir=tmp_path)
    service.refresh_summary()

    summary = json.loads((tmp_path / service.SUMMARY_JSON_FILENAME).read_text())
    markdown = (tmp_path / service.SUMMARY_MARKDOWN_FILENAME).read_text()

    assert summary["totals"] == {
        "reports": 0,
        "categories": {},
        "severity": {},
    }
    assert summary["last_submission_at"] is None
    assert "**Total reports:** 0" in markdown
    assert "## Категории" in markdown
    assert "## Критичность" in markdown
    assert "Нет данных" in markdown


def test_markdown_summary_generation(tmp_path: Path) -> None:
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

    assert "| catA | 2 |" in markdown
    assert "| catB | 1 |" in markdown
    assert "| low | 2 |" in markdown
    assert "| high | 1 |" in markdown

    assert summary["totals"]["reports"] == 3
    assert summary["totals"]["categories"] == {"catA": 2, "catB": 1}
    assert summary["totals"]["severity"] == {"high": 1, "low": 2}

    last_submission = datetime.fromisoformat(summary["last_submission_at"])
    generated_at = datetime.fromisoformat(summary["generated_at"])
    assert generated_at >= last_submission
