"""Tests for ``MainWindow._push_batched_updates`` fallback behaviour."""

from types import SimpleNamespace
from typing import Any, Dict
from unittest.mock import Mock

from src.ui.main_window_legacy import MainWindow


class _DummyRoot:
    """Minimal stub emulating QML root object."""

    def __init__(self, *, result: bool) -> None:
        self._result = result
        self.calls: list[tuple[str, Dict[str, Any]]] = []

    def setProperty(self, name: str, value: Dict[str, Any]) -> bool:  # noqa: N802
        self.calls.append((name, value))
        return self._result


def _make_window(result: bool):
    root = _DummyRoot(result=result)
    logger = Mock()
    window = SimpleNamespace(_qml_root_object=root, logger=logger)
    return window, root, logger


def test_push_batched_updates_returns_true_on_success() -> None:
    window, root, _ = _make_window(True)

    payload = {"lighting": {"intensity": 0.5}}
    assert MainWindow._push_batched_updates(window, payload) is True
    assert root.calls == [("pendingPythonUpdates", payload)]


def test_push_batched_updates_returns_false_on_failure_and_logs_warning() -> None:
    window, root, logger = _make_window(False)

    payload = {"quality": {"samples": 4}}
    assert MainWindow._push_batched_updates(window, payload) is False
    assert root.calls == [("pendingPythonUpdates", payload)]
    assert logger.warning.call_count == 1
