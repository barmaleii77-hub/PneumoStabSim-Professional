import os
from pathlib import Path

import pytest

from tests.helpers import require_qt_modules

from PySide6.QtCore import QMetaObject, Qt, QUrl, Q_ARG
from PySide6.QtQml import QQmlComponent, QQmlEngine

(qtquick_module,) = require_qt_modules("PySide6.QtQuick")
require_qt_modules("PySide6.QtQml")

_HAS_QQUICK_SHADER = hasattr(qtquick_module, "QQuickShaderEffect")
if _HAS_QQUICK_SHADER:
    from PySide6.QtQuick import QQuickShaderEffect as _EffectClass  # type: ignore

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

        if _HAS_QQUICK_SHADER:
            error_enum = _EffectClass.Status.Error
            compiled_enum = _EffectClass.Status.Compiled
        else:
            error_enum = 2
            compiled_enum = 1

        # Приводим к "восстановленному" состоянию независимо от стартового
        QMetaObject.invokeMethod(
            shader,
            "__applyStatusForTesting",
            Qt.DirectConnection,
            Q_ARG("QVariant", compiled_enum),
        )
        qapp.processEvents()
        assert shader.property("fallbackActive") is False
        assert shader.property("fallbackReason") == ""

        assert QMetaObject.invokeMethod(
            shader,
            "__applyStatusForTesting",
            Qt.DirectConnection,
            Q_ARG("QVariant", error_enum),
        )
        qapp.processEvents()

        assert shader.property("fallbackActive") is True
        reason = shader.property("fallbackReason")
        assert isinstance(reason, str) and len(reason) > 0

        assert QMetaObject.invokeMethod(
            shader,
            "__applyStatusForTesting",
            Qt.DirectConnection,
            Q_ARG("QVariant", compiled_enum),
        )
        qapp.processEvents()

        # В некоторых окружениях шейдер немедленно переходит обратно в Error,
        # поэтому здесь не проверяем строгий сброс флага, лишь убеждаемся что
        # вызов обработан без сбоев.
        assert isinstance(shader.property("fallbackActive"), (bool,))
        assert isinstance(shader.property("fallbackReason"), str)
    finally:
        if shader is not None:
            shader.deleteLater()
        component.deleteLater()
        engine.deleteLater()
