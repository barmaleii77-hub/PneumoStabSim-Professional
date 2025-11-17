from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ui.main_window_pkg._hdr_paths import normalise_hdr_path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class _LoggerStub:
    def __init__(self) -> None:
        self.records: list[str] = []

    def warning(self, msg: str, *args) -> None:  # type: ignore[override]
        formatted = msg % args if args else msg
        self.records.append(formatted)


def _events_file() -> Path | None:
    logs_root = PROJECT_ROOT / "logs" / "ibl"
    target = logs_root / "ibl_events.jsonl"
    if target.exists():
        return target
    # fallback старого формата (на случай параллельных запусков)
    legacy = sorted(logs_root.glob("ibl_events_*.jsonl"))
    return legacy[-1] if legacy else None


def _clear_events_file() -> None:
    path = _events_file()
    if path is not None and path.exists():
        try:
            path.unlink()
        except OSError:
            pass


@pytest.fixture(autouse=True)
def _reset_ibl_events_file() -> None:
    _clear_events_file()
    yield
    _clear_events_file()


def _read_events() -> list[dict]:
    path = _events_file()
    if path is None:
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    events: list[dict] = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    return events


def test_hdr_logging_emits_ok_event(tmp_path: Path) -> None:
    hdr_file = tmp_path / "probe.hdr"
    hdr_file.write_bytes(b"HDR")
    logger = _LoggerStub()
    result = normalise_hdr_path(
        str(hdr_file), qml_base_dir=None, project_root=PROJECT_ROOT, logger=logger
    )
    assert result.endswith("probe.hdr") and result.startswith("file://")
    events = _read_events()
    assert any(e.get("status") == "ok" for e in events), "Ожидался статус ok в событиях"


def test_hdr_logging_emits_missing_event(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist.hdr"
    logger = _LoggerStub()
    result = normalise_hdr_path(
        str(missing_path), qml_base_dir=None, project_root=PROJECT_ROOT, logger=logger
    )
    assert result == ""
    events = _read_events()
    assert any(e.get("status") == "missing" for e in events), (
        "Ожидался статус missing в событиях"
    )


def test_hdr_logging_emits_empty_event() -> None:
    logger = _LoggerStub()

    result = normalise_hdr_path(
        "   ", qml_base_dir=None, project_root=PROJECT_ROOT, logger=logger
    )

    assert result == ""
    assert logger.records == []

    events = _read_events()
    statuses = {entry.get("status") for entry in events}

    assert "empty" in statuses
