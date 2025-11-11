from __future__ import annotations

import json as json_module
from typing import TYPE_CHECKING

import pytest

from tools.feedback import feedback

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def fixed_clock(monkeypatch: pytest.MonkeyPatch) -> "Iterator[None]":
    timestamps = iter([100.0, 160.0, 500.0, 502.5])

    def fake_time() -> float:
        return next(timestamps)

    monkeypatch.setattr(feedback.time, "time", fake_time)
    monkeypatch.setattr(
        feedback.time,
        "strftime",
        lambda fmt: "2025-10-06 10:00:00",
    )

    yield


def read_plan(tmp_path) -> dict:
    plan_path = tmp_path / "reports" / "feedback" / "CONTROL_PLAN.json"
    return json_module.loads(plan_path.read_text(encoding="utf-8"))


def test_span_records_details_and_updates_plan(tmp_path, fixed_clock) -> None:
    system = feedback.FeedbackSystem(base_dir=str(tmp_path))

    with system.span("ui/test_step") as span:
        span["record_details"](summary="done", files_changed=["foo.py"])

    plan = read_plan(tmp_path)
    assert plan["status"] == "ready_for_acceptance"
    assert plan["current_time"] == "2025-10-06 10:00:00"
    assert len(plan["microsteps"]) == 1

    microstep = plan["microsteps"][0]
    assert microstep["summary"] == "done"
    assert microstep["files_changed"] == ["foo.py"]
    assert microstep["status"] == "completed"
    assert microstep["duration_sec"] == 60.0


def test_failed_span_marks_attention(tmp_path, fixed_clock) -> None:
    system = feedback.FeedbackSystem(base_dir=str(tmp_path))

    with system.span("core/initial_step") as span:
        span["record_details"](summary="ok")

    with pytest.raises(RuntimeError):
        with system.span("core/failing_step") as span:
            span["record_details"](summary="fail")
            raise RuntimeError("boom")

    plan = read_plan(tmp_path)
    assert plan["status"] == "attention_required"
    assert plan["current_time"] == "2025-10-06 10:00:00"
    assert len(plan["microsteps"]) == 2

    last_step = plan["microsteps"][-1]
    assert last_step["summary"] == "fail"
    assert last_step["status"] == "failed"
    assert last_step["duration_sec"] == 2.5
