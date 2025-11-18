import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from src.services import FeedbackPayload, FeedbackService


def test_feedback_payload_normalization():
    payload = FeedbackPayload(
        title="  Title with spaces  ",
        description="  Description  ",
        category="  ",
        severity="",
        contact="  user@example.com  ",
        metadata={
            "": "skip-empty-key",
            "valid": {"nested": 1},
            "invalid": {1, 2, 3},
        },
    )

    result = payload.as_dict()

    assert result["title"] == "Title with spaces"
    assert result["description"] == "Description"
    assert result["category"] == "unspecified"
    assert result["severity"] == "unspecified"
    assert result["contact"] == "user@example.com"
    assert result["metadata"] == {"valid": {"nested": 1}}


@pytest.mark.parametrize("workers, submissions", [(4, 12), (8, 24)])
def test_thread_safe_submission(tmp_path: Path, workers: int, submissions: int):
    service = FeedbackService(storage_dir=tmp_path)
    payload = FeedbackPayload(
        title="Threaded",
        description="Payload",
        category="ui",
        severity="medium",
    )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        list(
            executor.map(lambda _: service.submit_feedback(payload), range(submissions))
        )

    inbox_path = tmp_path / service.INBOX_FILENAME
    summary_path = tmp_path / service.SUMMARY_JSON_FILENAME

    assert inbox_path.exists()
    lines = inbox_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == submissions

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["totals"]["reports"] == submissions
    assert summary["totals"]["categories"] == {"ui": submissions}
    assert summary["totals"]["severity"] == {"medium": submissions}


def test_summary_aggregation_and_last_submission(tmp_path: Path):
    service = FeedbackService(storage_dir=tmp_path)

    first = service.submit_feedback(
        FeedbackPayload(
            title="One",
            description="Desc",
            category="ui",
            severity="low",
        )
    )
    second = service.submit_feedback(
        FeedbackPayload(
            title="Two",
            description="Desc",
            category="controls",
            severity="high",
        )
    )

    summary_path = tmp_path / service.SUMMARY_JSON_FILENAME
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["totals"]["reports"] == 2
    assert summary["totals"]["categories"] == {"controls": 1, "ui": 1}
    assert summary["totals"]["severity"] == {"high": 1, "low": 1}

    newest = max(first.created_at, second.created_at)
    assert summary["last_submission_at"] == newest.isoformat()


def test_markdown_generation(tmp_path: Path):
    service = FeedbackService(storage_dir=tmp_path)
    service.submit_feedback(
        FeedbackPayload(
            title="Alpha",
            description="Desc",
            category="rendering",
            severity="critical",
        )
    )
    service.submit_feedback(
        FeedbackPayload(
            title="Beta",
            description="Desc",
            category="rendering",
            severity="medium",
        )
    )
    service.submit_feedback(
        FeedbackPayload(
            title="Gamma",
            description="Desc",
            category="ui",
            severity="medium",
        )
    )

    markdown_path = tmp_path / service.SUMMARY_MARKDOWN_FILENAME
    lines = markdown_path.read_text(encoding="utf-8").splitlines()

    assert lines[0] == "# Feedback summary"
    assert any(line.startswith("_Generated at_:") for line in lines)
    assert any(line.startswith("_Last submission_:") for line in lines)
    assert any("**Total reports:** 3" in line for line in lines)

    rendering_row = "| rendering | 2 |"
    ui_row = "| ui | 1 |"
    critical_row = "| critical | 1 |"
    medium_row = "| medium | 2 |"

    assert rendering_row in lines
    assert ui_row in lines
    assert critical_row in lines
    assert medium_row in lines

    rendering_index = lines.index(rendering_row)
    ui_index = lines.index(ui_row)
    assert rendering_index < ui_index

    medium_index = lines.index(medium_row)
    critical_index = lines.index(critical_row)
    assert medium_index < critical_index
