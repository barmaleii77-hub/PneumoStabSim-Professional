from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

from src.core.resource_cache import ResourceCache
from src.core.settings_service import SettingsService
from src.infrastructure.event_bus import EventBus


os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")

BASELINE_RESULTS = json.loads(Path("optimization_test_results.json").read_text(encoding="utf-8"))


def _copy_settings(tmp_path: Path) -> Path:
    source = Path("config/app_settings.json")
    target = tmp_path / "app_settings.json"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_lazy_load_works(qapp) -> None:
    engine = QQmlEngine()
    engine.addImportPath(str(Path("qml").resolve()))

    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(str(Path("qml/SimulationRoot.qml").resolve())))
    if component.isError():
        messages = "; ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load SimulationRoot.qml: {messages}")

    root = component.create()
    assert isinstance(root, QObject)

    loader = root.findChild(QObject, "simulationLoader")
    assert loader is not None

    initial_clean = not bool(loader.property("active"))

    payload = {
        "maxLineIntensity": 0.4,
        "masterIsolationOpen": True,
        "lines": {
            "a1": {
                "direction": "intake",
                "netFlow": 0.2,
                "flowIntensity": 0.25,
                "animationSpeed": 0.65,
                "valves": {"atmosphereOpen": True, "tankOpen": False},
            },
            "b1": {
                "direction": "exhaust",
                "netFlow": -0.1,
                "flowIntensity": 0.15,
                "valves": {"atmosphereOpen": False, "tankOpen": True},
            },
        },
        "receiver": {
            "pressures": {"a1": 110_000.0, "b1": 90_000.0},
            "tankPressure": 105_000.0,
            "minPressure": 85_000.0,
            "maxPressure": 125_000.0,
        },
        "linePressures": {"a1": 110_000.0, "b1": 90_000.0},
    }

    root.setProperty("flowTelemetry", payload)
    qapp.processEvents()

    for _ in range(20):
        if root.property("panelReady"):
            break
        qapp.processEvents()
        QTest.qWait(15)

    panel = root.property("simulationPanel")
    assert panel is not None

    flow_model = panel.property("flowArrowsModel")
    assert flow_model is not None
    if hasattr(flow_model, "rowCount"):
        count = flow_model.rowCount()
    else:
        count = flow_model.property("count")
    assert count == 2

    lazy_load_works = bool(loader.property("active")) and bool(root.property("panelReady"))
    expected_lazy = BASELINE_RESULTS["lazy_loading"]["result"]["lazy_load_works"]
    expected_clean = BASELINE_RESULTS["lazy_loading"]["result"]["initial_clean"]

    assert initial_clean == expected_clean
    assert lazy_load_works == expected_lazy

    root.deleteLater()
    component.deleteLater()
    engine.deleteLater()


@pytest.mark.usefixtures("tmp_path")
def test_cache_works(tmp_path: Path) -> None:
    settings_path = _copy_settings(tmp_path)
    service = SettingsService(settings_path, validate_schema=False)
    bus = EventBus()
    cache = ResourceCache(settings_service=service, event_bus=bus)

    first = cache.snapshot()
    second = cache.snapshot()

    assert first.revision == second.revision
    assert first.geometry.current == second.geometry.current

    bus.publish("settings.updated", {"section": "graphics"})
    updated = cache.snapshot()
    cache_works = (
        updated.revision > first.revision
        and first.revision == second.revision
        and first.geometry.current == second.geometry.current
    )

    expected = BASELINE_RESULTS["caching"]["result"]["cache_works"]
    assert cache_works == expected


@pytest.mark.usefixtures("tmp_path")
def test_data_consistent(tmp_path: Path) -> None:
    settings_path = _copy_settings(tmp_path)
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    payload["defaults_snapshot"]["graphics"]["materials"]["frame"]["id"] = (
        "frame_mismatch"
    )
    settings_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    service = SettingsService(settings_path, validate_schema=False)
    cache = ResourceCache(settings_service=service, event_bus=EventBus())

    with pytest.raises(ValueError):
        cache.snapshot()

    expected = BASELINE_RESULTS["caching"]["result"]["data_consistent"]
    assert expected is True
