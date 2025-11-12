from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

import pytest

from tests.helpers import require_qt_modules

require_qt_modules(
    "PySide6.QtQuick3D",
    "PySide6.QtQml",
)

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from tests.helpers import SignalListener


REPO_ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = REPO_ROOT / "assets" / "qml"

os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")
os.environ.setdefault("QSG_RHI_BACKEND", "opengl")


def _load_component(engine: QQmlEngine, path: Path) -> QQmlComponent:
    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(str(path)))
    if component.status() != QQmlComponent.Ready:
        raise RuntimeError(
            f"Failed to load component {path}: {component.errorString()}"
        )
    return component


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_post_effects_bypass_triggers_view_effects_reset(qapp) -> None:  # type: ignore[missing-type-doc]
    engine = QQmlEngine()
    engine.addImportPath(str(QML_ROOT))

    post_effects_component = _load_component(
        engine, QML_ROOT / "effects" / "PostEffects.qml"
    )
    simulation_component = _load_component(
        engine, QML_ROOT / "PneumoStabSim" / "SimulationRoot.qml"
    )

    view_stub_component = QQmlComponent(engine)
    view_stub_component.setData(
        b"import QtQml 6.10; QtObject { property var effects: [] }",
        QUrl(),
    )

    post_effects = post_effects_component.create()
    simulation_root = simulation_component.create()
    scene_view = view_stub_component.create()

    assert post_effects is not None, "Expected PostEffects to instantiate"
    assert simulation_root is not None, "Expected SimulationRoot to instantiate"
    assert scene_view is not None, "Expected stub View3D replacement to instantiate"

    status_spy = SignalListener(simulation_root.shaderStatusDumpRequested)

    try:
        simulation_root.setProperty("sceneView", scene_view)
        simulation_root.setProperty("postEffects", post_effects)
        qapp.processEvents()

        baseline_bypass = bool(post_effects.property("effectsBypass"))
        failure_payload = post_effects.property("persistentEffectFailures")
        if isinstance(failure_payload, Mapping):
            failure_keys = [
                key
                for key, value in failure_payload.items()
                if value not in (None, "", False)
            ]
        else:
            failure_keys = []

        if baseline_bypass and not failure_keys:
            pytest.fail(
                (
                    "PostEffects started in fallback mode without persistent failures; "
                    "headless rendering lacks depth/normal/velocity buffers. "
                    "Re-run `python -m tools.cross_platform_test_prep --use-uv --run-tests` "
                    "to provision the required GPU resources."
                ),
                pytrace=False,
            )

        initial_effects = scene_view.property("effects")
        assert isinstance(initial_effects, list)
        assert len(initial_effects) == len(post_effects.property("effectList"))

        post_effects.setEffectPersistentFailure("bloom", True, "forced failure")
        qapp.processEvents()

        assert post_effects.property("effectsBypass") is True
        assert simulation_root.property("postProcessingBypassed") is True
        assert scene_view.property("effects") == []
        assert (
            simulation_root.property("postProcessingBypassReason")
            == "bloom: forced failure"
        )
        assert post_effects.property("effectsBypassReason") == "bloom: forced failure"
        assert len(status_spy) >= 1
        latest_snapshot = status_spy[-1][0]
        assert isinstance(latest_snapshot, dict)
        assert latest_snapshot["effectsBypass"] is True
        assert latest_snapshot["effectsBypassReason"] == "bloom: forced failure"

        post_effects.setEffectPersistentFailure("bloom", False, "")
        qapp.processEvents()

        assert post_effects.property("effectsBypass") is False
        assert simulation_root.property("postProcessingBypassed") is False
        restored_effects = scene_view.property("effects")
        assert isinstance(restored_effects, list)
        assert len(restored_effects) == len(post_effects.property("effectList"))
        for restored, original in zip(restored_effects, initial_effects):
            assert restored is original
    finally:
        scene_view.deleteLater()
        simulation_root.deleteLater()
        post_effects.deleteLater()
        view_stub_component.deleteLater()
        simulation_component.deleteLater()
        post_effects_component.deleteLater()
        engine.deleteLater()
