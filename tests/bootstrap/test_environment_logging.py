"""Tests for startup environment logging helpers."""

from src.app_runner import ApplicationRunner


def test_startup_environment_message_contains_required_keys() -> None:
    snapshot = {
        "platform": "linux",
        "QT_QPA_PLATFORM": "wayland",
        "QSG_RHI_BACKEND": "opengl",
        "QT_PLUGIN_PATH": "/tmp/plugins",
        "PySide6": "6.7.0",
    }

    message = ApplicationRunner._format_startup_environment_message(snapshot)

    for key in snapshot:
        assert f"{key}=" in message
