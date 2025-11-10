"""Helper utilities for registering Qt/QML types used by the UI."""

from __future__ import annotations

from collections.abc import Iterable
from importlib import import_module
from typing import Any, Callable, cast

QmlByteLike = bytes | bytearray | memoryview

RegisterModule = Callable[[QmlByteLike | str, int, int], None]
RegisterType = Callable[[type[Any], QmlByteLike | str, int, int, QmlByteLike | str], int]

_runtime_register_module: Any = None
_runtime_register_type: Any = None

try:
    from PySide6.QtQml import qmlRegisterModule as _runtime_register_module
    from PySide6.QtQml import qmlRegisterType as _runtime_register_type
except Exception:  # pragma: no cover - headless environments
    pass

qml_register_module: RegisterModule | None = cast(
    RegisterModule | None, _runtime_register_module
)
qml_register_type: RegisterType | None = cast(
    RegisterType | None, _runtime_register_type
)

_QML_ELEMENT_MODULES: Iterable[str] = (
    "src.ui.example_geometry",
    "src.ui.simple_geometry",
    "src.ui.triangle_geometry",
    "src.ui.custom_geometry",
    "src.ui.direct_geometry",
    "src.ui.correct_geometry",
    "src.ui.stable_geometry",
)


def _call_qml_register_module(register: RegisterModule, uri: str) -> None:
    """Вызвать qmlRegisterModule, совместимо со старыми/новыми сигнатурами."""

    try:
        register(b"PneumoStabSim", 1, 0)  # type: ignore[arg-type]
        return
    except Exception:
        pass
    # Fallback на строковый URI
    register(uri, 1, 0)


def _call_qml_register_type(
    register: RegisterType, t: type[Any], uri: str, qml_name: str
) -> None:
    """Вызвать qmlRegisterType, совместимо со старыми/новыми сигнатурами."""

    try:
        register(t, b"PneumoStabSim", 1, 0, qml_name.encode("ascii"))  # type: ignore[arg-type]
        return
    except Exception:
        pass
    register(t, uri, 1, 0, qml_name)


def register_qml_types() -> None:
    """Register QML modules and load Python QML elements."""

    if qml_register_module is None or qml_register_type is None:
        return

    _call_qml_register_module(qml_register_module, "PneumoStabSim")

    from src.ui.scene_bridge import SceneBridge

    _call_qml_register_type(qml_register_type, SceneBridge, "PneumoStabSim", "SceneBridge")

    for module_name in _QML_ELEMENT_MODULES:
        import_module(module_name)

    from src.ui.main_window_pkg import qml_bridge as _qml_bridge

    if not getattr(_qml_bridge.QMLBridge, "_scene_bridge_patched", False):
        original_push: Callable[..., Any] = _qml_bridge.QMLBridge._push_batched_updates
        original_set_state: Callable[..., Any] = (
            _qml_bridge.QMLBridge.set_simulation_state
        )

        def _push_with_scene_bridge(
            window: Any,
            updates: dict[str, Any],
            *,
            detailed: bool = False,
            raise_on_error: bool = False,
        ) -> Any:
            if not updates:
                return _qml_bridge.QMLBridge._make_update_result(True, detailed)

            scene_bridge = getattr(window, "_scene_bridge", None)
            if scene_bridge is not None:
                try:
                    sanitized = _qml_bridge.QMLBridge._prepare_for_qml(updates)
                    scene_bridge.dispatch_updates(sanitized)
                    return _qml_bridge.QMLBridge._make_update_result(True, detailed)
                except Exception as exc:
                    _qml_bridge.QMLBridge.logger.error(
                        "SceneBridge dispatch failed: %s",
                        exc,
                        exc_info=True,
                    )

            return original_push(
                window,
                updates,
                detailed=detailed,
                raise_on_error=raise_on_error,
            )

        def _set_state_with_scene_bridge(window: Any, snapshot: Any) -> bool:
            scene_bridge = getattr(window, "_scene_bridge", None)
            if scene_bridge is not None and snapshot is not None:
                try:
                    payload = _qml_bridge.QMLBridge._snapshot_to_payload(snapshot)
                    animation_section = payload.setdefault("animation", {})
                    animation_section["isRunning"] = bool(
                        getattr(window, "is_simulation_running", False)
                    )
                    sanitized = _qml_bridge.QMLBridge._prepare_for_qml(payload)
                    scene_bridge.dispatch_updates(sanitized)
                    return True
                except Exception as exc:
                    _qml_bridge.QMLBridge.logger.error(
                        "SceneBridge simulation dispatch failed: %s",
                        exc,
                        exc_info=True,
                    )

            result = original_set_state(window, snapshot)
            return bool(result)

        setattr(
            _qml_bridge.QMLBridge,
            "_push_batched_updates",
            staticmethod(_push_with_scene_bridge),
        )
        setattr(
            _qml_bridge.QMLBridge,
            "set_simulation_state",
            staticmethod(_set_state_with_scene_bridge),
        )
        setattr(_qml_bridge.QMLBridge, "_scene_bridge_patched", True)


__all__ = ["register_qml_types"]
