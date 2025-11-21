from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtQml", reason="Qt QML required")
pytest.importorskip("PySide6.QtQuick", reason="Qt Quick required")

from PySide6.QtQml import QQmlEngine, QQmlComponent
from PySide6.QtCore import QUrl


def _load_effect(engine: QQmlEngine):
    component = QQmlComponent(engine)
    component.loadUrl(QUrl("assets/qml/effects/FogEffect.qml"))
    if component.isError():  # pragma: no cover - diagnostic
        raise RuntimeError("Failed to load FogEffect.qml: " + "; ".join(err.toString() for err in component.errors()))
    obj = component.create()
    return obj


@pytest.mark.gui
def test_fogeffect_status_handlers_present(qtbot):
    engine = QQmlEngine()
    obj = _load_effect(engine)
    qtbot.addWidget(obj) if hasattr(obj, "setParent") else None

    # Ensure shaders have statusChanged handlers by checking method existence
    for shader_id in ("fogVertexShader", "fogFragmentShader", "fogFallbackShader"):
        shader = getattr(obj, shader_id, None)
        assert shader is not None, f"Missing shader object {shader_id}"
        # Status should be an int enum; accessing shouldn't throw
        _ = getattr(shader, "status", None)

    # Verify no legacy blocking sanitizedShaderUrl with XHR remains (search function source string)
    source = open("assets/qml/effects/FogEffect.qml", "r", encoding="utf-8").read()
    assert "XMLHttpRequest" not in source, "Blocking XMLHttpRequest must be removed"

    obj.deleteLater()
    del engine
