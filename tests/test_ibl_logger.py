import json
from pathlib import Path

from src.ui.ibl_logger import IblSignalLogger


def test_structured_log_written(tmp_path: Path) -> None:
    logger = IblSignalLogger(log_dir=tmp_path)

    qml_message = "2025-01-01T00:00:00Z | WARN | IblProbeLoader | No primary source"
    logger.logIblEvent(qml_message)
    logger.log_python_event("INFO", "unit-test", "structured entry")

    json_log = tmp_path / "ibl_events.jsonl"
    assert json_log.exists(), "JSON log file should be created for structured logging"

    lines = [
        line
        for line in json_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) >= 2, "Both QML and Python events should be recorded"

    first_entry = json.loads(lines[0])
    assert first_entry["level"] == "WARN"
    assert first_entry["source"] == "IblProbeLoader"
    assert "No primary source" in first_entry["message"]

    second_entry = json.loads(lines[1])
    assert second_entry["level"] == "INFO"
    assert second_entry["source"] == "unit-test"
    assert second_entry["message"] == "structured entry"
