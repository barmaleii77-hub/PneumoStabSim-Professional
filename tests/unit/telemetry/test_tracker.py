from __future__ import annotations

import json
from pathlib import Path

from src.telemetry import get_tracker


def _read_last_payload(path: Path) -> dict:
    data = path.read_text(encoding="utf-8").strip().splitlines()
    assert data, "Telemetry file should contain at least one record"
    return json.loads(data[-1])


def test_user_action_routed_to_jsonl(tmp_path) -> None:
    tracker = get_tracker(base_dir=tmp_path)
    target = tracker.track_user_action(
        "open_panel",
        metadata={"panel": "graphics"},
        context={"source": "toolbar"},
    )
    assert target.name == "user_actions.jsonl"
    payload = _read_last_payload(target)
    assert payload["event"] == "open_panel"
    assert payload["channel"] == "user"
    assert payload["payload"]["metadata"] == {"panel": "graphics"}
    assert payload["payload"]["context"]["source"] == "toolbar"


def test_simulation_event_routed_to_jsonl(tmp_path) -> None:
    tracker = get_tracker(base_dir=tmp_path / "sim")
    target = tracker.track_simulation_event(
        "step_completed", metadata={"step": 42}, context={"dt": 0.01}
    )
    assert target.name == "simulation_events.jsonl"
    payload = _read_last_payload(target)
    assert payload["event"] == "step_completed"
    assert payload["channel"] == "simulation"
    assert payload["payload"]["metadata"]["step"] == 42
    assert payload["payload"]["context"]["dt"] == 0.01
