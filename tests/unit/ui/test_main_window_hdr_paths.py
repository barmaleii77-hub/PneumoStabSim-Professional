from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.ui.main_window_pkg._hdr_paths as hdr_paths
from src.ui.main_window_pkg._hdr_paths import normalise_hdr_path


class _CapturingLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, str]] = []

    def warning(self, message: str, *args) -> None:
        formatted = message % args if args else message
        self.records.append(("warning", formatted))

    def debug(self, message: str, *args, **kwargs) -> None:
        formatted = message % args if args else message
        self.records.append(("debug", formatted))


@pytest.fixture()
def logger_stub() -> _CapturingLogger:
    return _CapturingLogger()


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _invoke_normalize(
    raw_value: str,
    logger: _CapturingLogger,
    base_dir: Path | None = None,
    project_root: Path | None = None,
) -> str:
    return normalise_hdr_path(
        raw_value,
        qml_base_dir=base_dir,
        project_root=project_root or PROJECT_ROOT,
        logger=logger,
    )


def _read_events(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.fixture(autouse=True)
def reset_ibl_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hdr_paths, "_ibl_session_path_cache", {})


def test_normalize_hdr_path_returns_empty_string_when_file_missing(
    logger_stub: _CapturingLogger,
) -> None:
    missing_relative = "assets/hdr/does_not_exist.hdr"

    result = _invoke_normalize(missing_relative, logger_stub)

    assert result == ""
    warning_messages = [msg for level, msg in logger_stub.records if level == "warning"]
    assert warning_messages, "Expected a warning when HDR asset is missing"
    assert "does_not_exist.hdr" in warning_messages[0]


def test_normalize_hdr_path_prefers_existing_file(
    tmp_path: Path, logger_stub: _CapturingLogger
) -> None:
    hdr_file = tmp_path / "placeholder.hdr"
    hdr_file.write_bytes(b"HDR")

    result = _invoke_normalize(str(hdr_file), logger_stub)

    assert result == hdr_file.resolve().as_uri()
    assert not any(level == "warning" for level, _ in logger_stub.records)


def test_normalize_hdr_path_resolves_relative_to_qml_base_dir(
    tmp_path: Path, logger_stub: _CapturingLogger
) -> None:
    hdr_file = tmp_path / "textures" / "probe.hdr"
    hdr_file.parent.mkdir()
    hdr_file.write_bytes(b"HDR")

    relative_value = "textures/probe.hdr"

    result = _invoke_normalize(relative_value, logger_stub, base_dir=tmp_path)

    expected_url = hdr_file.resolve().as_uri()
    assert result == expected_url
    assert not any(level == "warning" for level, _ in logger_stub.records)


def test_normalize_hdr_path_logs_empty_and_missing_inputs(
    tmp_path: Path, logger_stub: _CapturingLogger
) -> None:
    log_path = tmp_path / "logs" / "ibl" / "ibl_events.jsonl"

    empty_result = _invoke_normalize("", logger_stub, project_root=tmp_path)
    missing_result = _invoke_normalize(
        "textures/offline_probe.hdr",
        logger_stub,
        base_dir=tmp_path,
        project_root=tmp_path,
    )

    assert empty_result == ""
    assert missing_result == ""

    events = _read_events(log_path)
    statuses = {event.get("status") for event in events}
    assert {"empty", "missing"} <= statuses


def test_normalize_hdr_path_logs_successful_resolution(
    tmp_path: Path, logger_stub: _CapturingLogger
) -> None:
    hdr_file = tmp_path / "assets" / "hdr" / "sky.hdr"
    hdr_file.parent.mkdir(parents=True)
    hdr_file.write_bytes(b"HDR")

    log_path = tmp_path / "logs" / "ibl" / "ibl_events.jsonl"

    resolved = _invoke_normalize(str(hdr_file), logger_stub, project_root=tmp_path)

    assert resolved == hdr_file.resolve().as_uri()

    events = _read_events(log_path)
    assert events
    last_event = events[-1]
    assert last_event["status"] == "ok"
    assert last_event["resolved"] == resolved
