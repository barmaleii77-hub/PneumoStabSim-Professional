"""Runtime guard tests for setup_environment.py."""

from setup_environment import _runtime_version_blocker


def test_runtime_blocker_allows_supported_python() -> None:
    """Python 3.13 is within the supported range."""
    assert _runtime_version_blocker((3, 13)) is None


def test_runtime_blocker_blocks_unsupported_minor() -> None:
    """Python 3.14 should be rejected with a helpful message."""
    message = _runtime_version_blocker((3, 14))
    assert message is not None
    assert "3.14" in message
    assert "PySide6" in message or "Qt" in message
