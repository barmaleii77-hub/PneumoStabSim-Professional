"""Regression tests for RealismEnvironment fallback handling."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytestqt")
pytest.importorskip("PySide6.QtQml")
pytest.importorskip("PySide6.QtQuick")
pytest.importorskip("PySide6.QtQuick3D")

from PySide6.QtCore import QObject, QUrl, QtMsgType, Slot, qInstallMessageHandler
from PySide6.QtQml import QQmlComponent, QQmlEngine


REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_QML = REPO_ROOT / "tests" / "qml" / "RealismEnvironmentHarness.qml"


class DiagnosticsRecorder(QObject):
    """Captures diagnostics entries emitted by the QML overlay."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[tuple[str, dict[str, Any], str, str]] = []

    @Slot(str, "QVariant", str, str)
    def recordObservation(
        self, name: str, entry: dict[str, Any], source: str, origin: str
    ) -> None:
        self.records.append((name, entry, source, origin))


@pytest.fixture
def qml_engine(qapp):  # type: ignore[no-untyped-def]
    engine = QQmlEngine()
    engine.addImportPath(str((REPO_ROOT / "assets" / "qml").resolve()))
    try:
        yield engine
    finally:
        engine.deleteLater()


def _create_harness(engine: QQmlEngine) -> QObject:
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(HARNESS_QML.resolve())))
    if component.isError():
        messages = "; ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load RealismEnvironmentHarness: {messages}")
    harness = component.create()
    assert harness is not None, "Expected harness instance"
    component.deleteLater()
    return harness


@pytest.mark.gui
def test_warn_records_undefined_fallback(qml_engine):
    harness = _create_harness(qml_engine)
    recorder = DiagnosticsRecorder()

    try:
        harness.setSceneBridge({"signalTrace": recorder})
        harness.callWarnWithoutFallback("environment", "exposure", "missing")

        assert recorder.records, "Expected diagnostics entry to be recorded"
        _, entry, source, origin = recorder.records[-1]
        assert source == "qml"
        assert origin == "RealismEnvironment"
        assert entry["fallback"] == "<undefined>"
        assert entry["reason"] == "missing"
    finally:
        harness.deleteLater()
        qml_engine.collectGarbage()


@pytest.mark.gui
def test_number_missing_value_uses_fallback(qml_engine):
    harness = _create_harness(qml_engine)
    recorder = DiagnosticsRecorder()

    try:
        harness.setSceneBridge({"signalTrace": recorder, "environment": {}})
        result = harness.callNumber("environment", "ibl_intensity", 1.5)

        assert math.isclose(result, 1.5)
        assert recorder.records, "Expected diagnostics entry for missing value"
        _, entry, _, _ = recorder.records[-1]
        assert entry["fallback"] == "1.5"
        assert entry["reason"] == "missing"
    finally:
        harness.deleteLater()
        qml_engine.collectGarbage()


@pytest.mark.gui
def test_number_invalid_fallback_logs_error_and_uses_safe_value(qml_engine):
    harness = _create_harness(qml_engine)
    recorder = DiagnosticsRecorder()

    messages: list[tuple[QtMsgType, str]] = []

    def _message_handler(mode: QtMsgType, _context, message: str) -> None:
        messages.append((mode, message))

    previous_handler = qInstallMessageHandler(_message_handler)

    try:
        harness.setSceneBridge({"signalTrace": recorder, "environment": {}})
        result = harness.callNumber("environment", "ibl_intensity", float("inf"))
    finally:
        qInstallMessageHandler(previous_handler)
        harness.deleteLater()
        qml_engine.collectGarbage()

    assert result == 0
    assert recorder.records, "Expected diagnostics entry for invalid fallback"
    _, entry, _, _ = recorder.records[-1]
    assert entry["fallback"] == "0"
    assert entry["reason"] == "missing"
    assert any("Invalid numeric fallback" in message for _mode, message in messages), (
        "Expected console error about invalid numeric fallback"
    )
