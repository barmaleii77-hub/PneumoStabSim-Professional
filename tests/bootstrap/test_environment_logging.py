import logging
from pathlib import Path

import pytest

from src.app_runner import ApplicationRunner


@pytest.fixture(autouse=True)
def clear_logging_handlers():
    logger = logging.getLogger("pss-test-startup")
    old_handlers = logger.handlers[:]
    try:
        logger.handlers = []
        logger.propagate = False
        yield
    finally:
        logger.handlers = old_handlers
        logger.propagate = True


def _extract_message(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("STARTUP_ENVIRONMENT"):
            return line
    raise AssertionError("STARTUP_ENVIRONMENT message not found in output")


@pytest.mark.parametrize(
    "qt_qpa, qsg_backend, plugin_path",
    [
        ("offscreen", "opengl", "/tmp/plugins"),
        ("xcb", "vulkan", ""),
    ],
)
def test_startup_environment_message_contains_required_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, qt_qpa, qsg_backend, plugin_path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QT_QPA_PLATFORM", qt_qpa)
    monkeypatch.setenv("QSG_RHI_BACKEND", qsg_backend)
    monkeypatch.setenv("QT_PLUGIN_PATH", plugin_path)

    runner = ApplicationRunner(object, object, object, object)
    runner.app_logger = logging.getLogger("pss-test-startup")

    runner._log_startup_environment()

    captured = capsys.readouterr()
    message = _extract_message(captured.out)

    log_path = tmp_path / "logs" / "startup.log"
    assert log_path.exists(), "startup.log should be created in the logs directory"
    log_message = _extract_message(log_path.read_text(encoding="utf-8"))

    expected_keys = [
        "platform",
        "QT_QPA_PLATFORM",
        "QSG_RHI_BACKEND",
        "QT_PLUGIN_PATH",
        "PySide6",
    ]

    for key in expected_keys:
        assert any(
            part.startswith(f"{key}=") for part in message.split(" | ")
        ), f"stdout message missing key {key}"
        assert any(
            part.startswith(f"{key}=") for part in log_message.split(" | ")
        ), f"log message missing key {key}"
