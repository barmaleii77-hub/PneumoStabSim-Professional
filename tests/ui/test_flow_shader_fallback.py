import os
from pathlib import Path

import pytest

from tests.helpers import require_qt_modules

from PySide6.QtCore import QMetaObject, Qt, QUrl, Q_ARG
from PySide6.QtQml import QQmlComponent, QQmlEngine

(qtquick_module,) = require_qt_modules("PySide6.QtQuick")
require_qt_modules("PySide6.QtQml")

if not hasattr(qtquick_module, "QQuickShaderEffect"):
    pytest.fail(
        (
            "QQuickShaderEffect is not available in this PySide6 build. "
            "Run `python -m tools.cross_platform_test_prep --use-uv --run-tests` "
            "to install the required Qt shader components."
        ),
        pytrace=False,
    )

from PySide6.QtQuick import QQuickShaderEffect


REPO_ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = REPO_ROOT / "qml"

os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")


def _create_flow_shader(engine: QQmlEngine) -> QQmlComponent:
    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(str(QML_ROOT / "Shaders" / "FlowShader.qml")))
    return component


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_flow_shader_requests_fallback_on_error(qapp) -> None:  # type: ignore[missing-type-doc]
    engine = QQmlEngine()
    engine.addImportPath(str(QML_ROOT))

    component = _create_flow_shader(engine)
    if component.status() != QQmlComponent.Ready:
        pytest.fail(
            (
                "FlowShader.qml failed to load: "
                f"{component.errorString()}\n"
                "Ensure shader assets are built by running `python -m tools.cross_platform_test_prep --use-uv --run-tests`."
            ),
            pytrace=False,
        )

    shader = component.create()
    try:
        assert shader is not None, "FlowShader should instantiate"
        assert shader.property("fallbackActive") is False
        assert shader.property("fallbackReason") == ""

        error_enum = QQuickShaderEffect.Status.Error
        compiled_enum = QQuickShaderEffect.Status.Compiled

        assert QMetaObject.invokeMethod(
            shader,
            "__applyStatusForTesting",
            Qt.DirectConnection,
            Q_ARG(int, error_enum),
        )
        qapp.processEvents()

        assert shader.property("fallbackActive") is True
        reason = shader.property("fallbackReason")
        assert isinstance(reason, str) and len(reason) > 0

        assert QMetaObject.invokeMethod(
            shader,
            "__applyStatusForTesting",
            Qt.DirectConnection,
            Q_ARG(int, compiled_enum),
        )
        qapp.processEvents()

        assert shader.property("fallbackActive") is False
        assert shader.property("fallbackReason") == ""
    finally:
        if shader is not None:
            shader.deleteLater()
        component.deleteLater()
        engine.deleteLater()
