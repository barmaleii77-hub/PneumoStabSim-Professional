"""Test-only helpers for exercising :mod:`src.ui.qml_bridge`."""

from __future__ import annotations

from typing import Any


class BridgeWindowStub:
    """Minimal stand-in for :class:`src.ui.main_window_pkg.main_window.MainWindow`.

    ``QMLBridge.queue_update`` expects the window to expose a handful of private
    attributes used to store pending payloads and bookkeeping metadata. Real
    ``MainWindow`` instances provide these slots, but unit tests often just need
    an object that can accept attribute assignment. ``BridgeWindowStub`` fulfils
    those expectations so tests can exercise the real queueing logic without
    pulling in the heavy Qt stack.
    """

    __slots__ = (
        "_qml_update_queue",
        "_last_dispatched_payloads",
        "_qml_root_object",
        "_qml_flush_timer",
    )

    def __init__(self) -> None:
        self._qml_update_queue: dict[str, dict[str, Any]] = {}
        self._last_dispatched_payloads: dict[str, dict[str, Any]] = {}
        self._qml_root_object: object | None = None
        self._qml_flush_timer: Any | None = None
