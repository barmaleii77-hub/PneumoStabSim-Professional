from __future__ import annotations

from pathlib import Path

import pytest

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
    raw_value: str, logger: _CapturingLogger, base_dir: Path | None = None
) -> str:
    return normalise_hdr_path(
        raw_value,
        qml_base_dir=base_dir,
        project_root=PROJECT_ROOT,
        logger=logger,
    )


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
