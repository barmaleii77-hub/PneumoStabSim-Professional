from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtQml", reason="Qt QML required")
pytest.importorskip("PySide6.QtQuick", reason="Qt Quick required")

from PySide6.QtQml import QQmlEngine, QQmlComponent
from PySide6.QtCore import QUrl


def _create(engine):
    c = QQmlComponent(engine)
    c.loadUrl(QUrl("assets/qml/effects/FogEffect.qml"))
    if c.isError():
        raise RuntimeError("FogEffect load error: " + "; ".join(e.toString() for e in c.errors()))
    return c.create()


@pytest.mark.gui
def test_fogeffect_fallback_switch_and_rebind(qtbot):
    engine = QQmlEngine()
    obj = _create(engine)
    qtbot.addWidget(obj) if hasattr(obj, "setParent") else None

    # Force depth texture unavailable
    obj.forceDepthTextureUnavailable = True
    qtbot.wait(50)
    assert obj.fallbackActive or obj.fallbackDueToDepth, "Fallback not activated on depth unavailable"

    # Simulate profile switch
    prevShader = obj.fogFragmentShader.shader
    obj.requestDesktopShaderProfile("test switch")
    qtbot.wait(50)
    # After rebind, shader url should update or remain valid
    assert obj.fogFragmentShader.shader is not None
    assert isinstance(obj.fogFragmentShader.shader, str)

    # Ensure passes updated
    shaders = obj.activePassShaders
    assert len(shaders) == 2, "Pass configuration must have two shaders"

    obj.deleteLater()
    del engine
