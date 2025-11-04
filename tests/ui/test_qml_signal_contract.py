"""Contract tests ensuring Python↔QML signal wiring stays in sync."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List

import pytest
import yaml

from src.ui.qml_bridge import QMLSignalSpec, register_qml_signals


@pytest.fixture(scope="module")
def qml_bridge_metadata() -> Dict[str, object]:
    """Return the parsed contents of ``config/qml_bridge.yaml`` for reuse."""

    metadata_path = Path("config/qml_bridge.yaml")
    raw = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
    return raw


@pytest.fixture(scope="module")
def main_qml_text() -> str:
    """Load the main QML document once for string-based assertions."""

    return Path("assets/qml/main.qml").read_text(encoding="utf-8")


def _parse_proxy_methods(qml_source: str) -> List[str]:
    """Extract the ``_proxyMethodNames`` list from ``main.qml``."""

    match = re.search(r"_proxyMethodNames:\s*\[(?P<body>.*?)\]", qml_source, re.S)
    if not match:
        raise AssertionError("main.qml is missing the _proxyMethodNames list")

    body = "[" + match.group("body") + "]"
    try:
        methods = ast.literal_eval(body)
    except Exception as exc:  # pragma: no cover - defensive guardrail
        raise AssertionError("Failed to parse _proxyMethodNames from main.qml") from exc

    if not isinstance(methods, list):
        raise AssertionError("_proxyMethodNames is expected to be a list")

    return [str(name) for name in methods]


def test_update_methods_have_matching_qml_proxies(
    qml_bridge_metadata: Dict[str, object], main_qml_text: str
) -> None:
    """Every Python-declared update method must have a QML proxy."""

    update_methods = qml_bridge_metadata.get("update_methods", {})
    flat_methods = {
        str(method)
        for methods in update_methods.values()
        for method in (methods or [])
    }

    proxy_methods = set(_parse_proxy_methods(main_qml_text))
    missing = sorted(flat_methods - proxy_methods)
    assert not missing, f"Missing QML proxy methods: {missing}"


def test_qml_signals_declared_in_main_qml(
    qml_bridge_metadata: Dict[str, object], main_qml_text: str
) -> None:
    """Signals in the metadata must be declared by ``main.qml``."""

    signals = {
        str(entry.get("signal"))
        for entry in qml_bridge_metadata.get("qml_signals", []) or []
    }

    declared = set(re.findall(r"signal\s+([A-Za-z_][A-Za-z0-9_]*)", main_qml_text))
    missing = sorted(signals - declared)
    assert not missing, f"Signals missing in main.qml: {missing}"


def test_batch_ack_emission_present_in_simulation_root() -> None:
    """``SimulationRoot`` must emit ``batchUpdatesApplied`` when batching."""

    root_text = Path("assets/qml/PneumoStabSim/SimulationRoot.qml").read_text(
        encoding="utf-8"
    )

    assert "function applyBatchedUpdates" in root_text, (
        "SimulationRoot is expected to expose applyBatchedUpdates"
    )
    assert "batchUpdatesApplied(summary)" in root_text, (
        "applyBatchedUpdates must emit batchUpdatesApplied(summary)"
    )


def test_qml_signal_handlers_exist_in_main_window() -> None:
    """Ensure every handler declared in YAML exists in ``MainWindow`` code."""

    metadata = Path("config/qml_bridge.yaml").read_text(encoding="utf-8")
    raw = yaml.safe_load(metadata) or {}
    handlers = {
        str(entry.get("handler"))
        for entry in raw.get("qml_signals", []) or []
    }

    source = Path("src/ui/main_window_pkg/main_window_refactored.py").read_text(
        encoding="utf-8"
    )

    missing = sorted({handler for handler in handlers if f"def {handler}" not in source})
    assert not missing, f"Handlers missing in MainWindow: {missing}"


def test_register_qml_signals_links_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    """``register_qml_signals`` must wire QML signals to Python handlers."""

    connected: list[tuple[str, object]] = []

    class _DummySignal:
        def connect(self, handler, connection_type=None):  # noqa: D401 - Qt mimic
            connected.append((handler.__name__, connection_type))

    class _DummyRoot:
        batchUpdatesApplied = _DummySignal()
        animationToggled = _DummySignal()

    class _DummyWindow:
        def _on_qml_batch_ack(self, summary):  # pragma: no cover - runtime hook
            return SimpleNamespace(summary=summary)

        def _on_animation_toggled(self, running):  # pragma: no cover - runtime hook
            return bool(running)

    window = _DummyWindow()
    root = _DummyRoot()

    specs: list[QMLSignalSpec] = register_qml_signals(window, root)
    names = {spec.name for spec in specs}
    assert names == {"batchUpdatesApplied", "animationToggled"}

    wired_handlers = {name for name, _ in connected}
    assert wired_handlers == {"_on_qml_batch_ack", "_on_animation_toggled"}
