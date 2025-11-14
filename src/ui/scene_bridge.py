"""Qt bridge exposing :class:`VisualizationService` state to QML."""

from __future__ import annotations

from typing import Any
from collections.abc import Iterable
import json
import os

from PySide6.QtCore import QObject, Property, Signal
try:  # попытка импортировать QJSValue (может отсутствовать в минимальных окружениях)
    from PySide6.QtQml import QJSValue  # type: ignore
except Exception:  # pragma: no cover - мягкий фолбек
    QJSValue = None  # type: ignore

from src.common.settings_manager import SettingsManager
from src.common.signal_trace import SignalTraceService, get_signal_trace_service
from src.ui.services.visualization_service import VisualizationService


class SceneBridge(QObject):
    """Expose simulation and graphics state updates to QML listeners."""

    updatesDispatched = Signal("QVariantMap")
    geometryChanged = Signal("QVariantMap")
    cameraChanged = Signal("QVariantMap")
    lightingChanged = Signal("QVariantMap")
    environmentChanged = Signal("QVariantMap")
    sceneChanged = Signal("QVariantMap")
    qualityChanged = Signal("QVariantMap")
    materialsChanged = Signal("QVariantMap")
    effectsChanged = Signal("QVariantMap")
    animationChanged = Signal("QVariantMap")
    threeDChanged = Signal("QVariantMap")
    renderChanged = Signal("QVariantMap")
    simulationChanged = Signal("QVariantMap")

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        visualization_service: VisualizationService | None = None,
        settings_manager: SettingsManager | None = None,
        signal_trace_service: SignalTraceService | None = None,
    ) -> None:
        super().__init__(parent)
        if visualization_service is not None:
            self._service = visualization_service
        else:
            self._service = VisualizationService(settings_manager=settings_manager)
        if signal_trace_service is not None:
            self._signal_trace = signal_trace_service
        else:
            try:
                self._signal_trace = get_signal_trace_service()
            except Exception:  # pragma: no cover - optional diagnostics dependency
                self._signal_trace = None
        self._signal_map = {
            "geometry": self.geometryChanged,
            "camera": self.cameraChanged,
            "lighting": self.lightingChanged,
            "environment": self.environmentChanged,
            "scene": self.sceneChanged,
            "quality": self.qualityChanged,
            "materials": self.materialsChanged,
            "effects": self.effectsChanged,
            "animation": self.animationChanged,
            "threeD": self.threeDChanged,
            "render": self.renderChanged,
            "simulation": self.simulationChanged,
        }

        # Parse optional startup batch from environment so QML can pull it on load
        self._initial_graphics_updates: dict[str, Any] = {}
        try:
            raw = os.environ.get("PSS_GRAPHICS_UPDATES_JSON")
            if raw:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    # Expect mapping of categories → payloads
                    self._initial_graphics_updates = parsed
        except Exception:
            # Ignore malformed input silently; diagnostics/logging not required here
            self._initial_graphics_updates = {}

        initial = self._service.populate_initial_state()
        if initial:
            self._emit_updates(initial)

    # ------------------------------------------------------------------
    # Qt Properties
    # ------------------------------------------------------------------
    @Property("QVariantMap", notify=geometryChanged)
    def geometry(self) -> dict[str, Any]:
        return dict(self._service.state_for("geometry"))

    @Property("QVariantMap", notify=cameraChanged)
    def camera(self) -> dict[str, Any]:
        return dict(self._service.state_for("camera"))

    @Property("QVariantMap", notify=lightingChanged)
    def lighting(self) -> dict[str, Any]:
        return dict(self._service.state_for("lighting"))

    @Property("QVariantMap", notify=environmentChanged)
    def environment(self) -> dict[str, Any]:
        return dict(self._service.state_for("environment"))

    @Property("QVariantMap", notify=sceneChanged)
    def scene(self) -> dict[str, Any]:
        return dict(self._service.state_for("scene"))

    @Property("QVariantMap", notify=qualityChanged)
    def quality(self) -> dict[str, Any]:
        return dict(self._service.state_for("quality"))

    @Property("QVariantMap", notify=materialsChanged)
    def materials(self) -> dict[str, Any]:
        return dict(self._service.state_for("materials"))

    @Property("QVariantMap", notify=effectsChanged)
    def effects(self) -> dict[str, Any]:
        return dict(self._service.state_for("effects"))

    @Property("QVariantMap", notify=animationChanged)
    def animation(self) -> dict[str, Any]:
        return dict(self._service.state_for("animation"))

    @Property("QVariantMap", notify=threeDChanged)
    def threeD(self) -> dict[str, Any]:
        return dict(self._service.state_for("threeD"))

    @Property("QVariantMap", notify=renderChanged)
    def render(self) -> dict[str, Any]:
        return dict(self._service.state_for("render"))

    @Property("QVariantMap", notify=simulationChanged)
    def simulation(self) -> dict[str, Any]:
        return dict(self._service.state_for("simulation"))

    @Property("QVariantMap")
    def initialGraphicsUpdates(self) -> dict[str, Any]:
        """Expose optional startup batch parsed from PSS_GRAPHICS_UPDATES_JSON.

        QML can read this property during Component.onCompleted and forward the
        payload to its ``pendingPythonUpdates`` contract. The value is provided
        once per process and remains immutable afterwards.
        """
        return dict(self._initial_graphics_updates)

    @Property("QVariantMap", notify=updatesDispatched)
    def latestUpdates(self) -> dict[str, Any]:
        """Последний пакет обновлений категорий от Python.

        Используется тестами и диагностикой для проверки того, что бридж
        действительно отправил обновления и какие категории были затронуты.
        """
        raw = self._service.latest_updates()
        return {k: self._coerce_jsvalue(v) for k, v in raw.items()}

    # ------------------------------------------------------------------
    # Public API used by Python-side controllers
    # ------------------------------------------------------------------
    def dispatch_updates(self, updates: dict[str, dict[str, Any]]) -> None:
        self._service.dispatch_updates(updates)
        self._emit_updates(updates)

    def refresh_orbit_presets(self) -> dict[str, Any]:
        """Перечитать пресеты орбитальной камеры и уведомить QML.

        Возвращает манифест пресетов, а также эмитит ``cameraChanged`` и
        ``updatesDispatched`` для совместимости с тестами и логикой UI.
        """
        manifest = self._service.refresh_orbit_presets()
        camera_payload = self._service.state_for("camera")
        if camera_payload:
            self._emit_updates({"camera": dict(camera_payload)})
        return dict(manifest)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _coerce_jsvalue(self, value: Any) -> Any:
        """Рекурсивно привести QJSValue / QObject к сериализуемой структуре.

        * QJSValue → toVariant() (если доступно)
        * QObject → dict(property_name → value)
        * Списки / dict обрабатываются глубоко
        """
        # QJSValue
        if QJSValue is not None and isinstance(value, QJSValue):  # type: ignore[arg-type]
            try:
                variant = value.toVariant()  # type: ignore[attr-defined]
            except Exception:
                return None
            return self._coerce_jsvalue(variant)
        # QObject → перечисляем свойства
        if isinstance(value, QObject):
            result: dict[str, Any] = {}
            meta = value.metaObject()
            for i in range(meta.propertyCount()):
                prop = meta.property(i)
                name = prop.name()
                try:
                    result[name] = self._coerce_jsvalue(value.property(name))
                except Exception:
                    pass
            return result
        # dict
        if isinstance(value, dict):
            return {k: self._coerce_jsvalue(v) for k, v in value.items()}
        # list / tuple
        if isinstance(value, (list, tuple)):
            return [self._coerce_jsvalue(v) for v in value]
        return value

    def _emit_updates(self, updates: dict[str, dict[str, Any]]) -> None:
        # Emit category-specific signals, затем батч
        for category, payload in updates.items():
            signal = self._signal_map.get(category)
            if signal is not None:
                coerced = self._coerce_jsvalue(payload)
                try:
                    signal.emit(dict(coerced))  # type: ignore[arg-type]
                except Exception:
                    signal.emit({})  # type: ignore[arg-type]
        try:
            batch_payload = {k: self._coerce_jsvalue(v) for k, v in updates.items()}
            self.updatesDispatched.emit(dict(batch_payload))  # type: ignore[arg-type]
        except Exception:
            self.updatesDispatched.emit({})  # type: ignore[arg-type]


__all__ = ["SceneBridge"]
