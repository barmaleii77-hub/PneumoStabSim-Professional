import json

import pytest

from analyze_logs import LogAnalyzer


@pytest.mark.usefixtures("tmp_path")
def test_log_analyzer_creates_missing_structure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    analyzer = LogAnalyzer()
    analyzer.run()

    logs_dir = tmp_path / "logs"
    assert logs_dir.is_dir()
    for subdir in LogAnalyzer.DEFAULT_SUBDIRS:
        assert (logs_dir / subdir).is_dir()
    assert (logs_dir / "run.log").exists()


def test_log_analyzer_respects_env_override(tmp_path, monkeypatch):
    target_dir = tmp_path / "custom-logs"
    monkeypatch.setenv("PNEUMOSTABSIM_LOGS_DIR", str(target_dir))
    monkeypatch.chdir(tmp_path)

    analyzer = LogAnalyzer()
    analyzer.run()

    assert target_dir.is_dir()
    for subdir in LogAnalyzer.DEFAULT_SUBDIRS:
        assert (target_dir / subdir).is_dir()
    assert (target_dir / "run.log").exists()


def test_log_analyzer_exports_unsynced_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    graphics_dir = tmp_path / "logs" / "graphics"
    graphics_dir.mkdir(parents=True)

    session_path = graphics_dir / "session_test.jsonl"
    events = [
        {
            "timestamp": "2025-10-31T23:15:52Z",
            "category": "lighting",
            "parameter_name": "exposure",
            "applied_to_qml": True,
            "old_value": 0.5,
            "new_value": 0.9,
        },
        {
            "timestamp": "2025-10-31T23:15:54Z",
            "category": "lighting",
            "parameter_name": "bloom_strength",
            "applied_to_qml": False,
            "qml_state": {"applied": False, "error": "shader busy"},
            "new_value": 1.2,
        },
        {
            "timestamp": "2025-10-31T23:15:55Z",
            "category": "geometry",
            "parameter_name": "mesh_quality",
            "applied_to_qml": False,
            "new_value": "high",
        },
    ]

    with open(session_path, "w", encoding="utf-8") as handle:
        for event in events:
            json.dump(event, handle, ensure_ascii=False)
            handle.write("\n")

    analyzer = LogAnalyzer()
    analyzer.run()

    report_path = tmp_path / "reports" / "graphics" / "unsynced_events.json"
    assert report_path.exists()

    payload = json.loads(report_path.read_text("utf-8"))
    assert payload["unsynced_total"] == 2

    summary = {
        f"{item['category']}.{item['parameter']}": item["total"]
        for item in payload["unsynced_by_parameter"]
    }
    assert summary["lighting.bloom_strength"] == 1
    assert summary["geometry.mesh_quality"] == 1

    statuses = {sample["status"] for sample in payload["samples"]}
    assert "failed" in statuses
    assert "pending" in statuses
