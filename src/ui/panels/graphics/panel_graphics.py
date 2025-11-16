"""Graphics Panel Coordinator - Modular Version v3.1

Координатор для GraphicsPanel с полностью рефакторенными табами.
Все табы теперь независимы и находятся в src/ui/panels/graphics/.

ИЗМЕНЕНИЯ v3.1 (СОГЛАСНО ТРЕБОВАНИЯМ):
- ❌ УДАЛЕНО автосохранение при каждом изменении (теперь сохраняем только при выходе)
- ✅ Добавлен метод collect_state() для централизованного сохранения из MainWindow
- ✅ Кнопки "Сброс к дефолтам" и "Сохранить как дефолт" остаются (обновляют defaults_snapshot)
- ❌ НЕТ импорта/экспорта настроек (кнопка экспорта — только анализ синхронизации, не параметры)

Russian UI / English code.
"""

from __future__ import annotations

import logging
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
from collections.abc import Mapping

from PySide6.QtCore import QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Рефакторенные табы
from .effects_tab import EffectsTab
from .environment_tab import EnvironmentTab
from .quality_tab import QualityTab
from .camera_tab import CameraTab
from .materials_tab import MaterialsTab
from .lighting_tab import LightingTab
from .scene_tab import SceneTab
from .animation_tab import AnimationTab
from .panel_graphics_settings_manager import (
    GraphicsSettingsError,
    GraphicsSettingsService,
)

from src.ui.panels.graphics_logger import get_graphics_logger
from src.common.event_logger import get_event_logger
from src.common.logging_widgets import LoggingCheckBox
from src.core.history import HistoryStack
from src.core.settings_sync_controller import SettingsSyncController
from src.ui.panels.preset_manager import PanelPresetManager


class GraphicsPanel(QWidget):
    """Координатор графической панели с модульными табами.

    ТРЕБОВАНИЯ:
    - Настройки читаются при запуске (из SettingsManager)
    - Настройки пишутся только при выходе приложения (через MainWindow)
    - Дефолты обновляются ТОЛЬКО по кнопке "Сохранить как дефолт"
    - Никаких дефолтов в коде
    """

    # Агрегированные сигналы
    lighting_changed = Signal(dict)
    environment_changed = Signal(dict)
    material_changed = Signal(dict)
    quality_changed = Signal(dict)
    camera_changed = Signal(dict)
    scene_changed = Signal(dict)
    effects_changed = Signal(dict)
    animation_changed = Signal(dict)
    preset_applied = Signal(dict)  # ✅ передаем полный state

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.logger = logging.getLogger(__name__)
        self.settings_service = GraphicsSettingsService()
        self.settings_manager = self.settings_service.settings_manager
        self.graphics_logger = get_graphics_logger()
        self.event_logger = get_event_logger()

        # Загружаем текущее состояние из JSON (не дефолты)
        self.state: dict[str, Any] = {}

        self._history = HistoryStack()
        self._sync_controller = SettingsSyncController(history=self._history)
        self._sync_controller.register_listener(self._on_state_synced)
        self.preset_manager = PanelPresetManager("graphics", self._sync_controller)
        self._sync_guard = 0

        self._color_adjustments_toggle: LoggingCheckBox | None = None
        self._syncing_color_toggle = False

        # Таб-виджеты
        self.lighting_tab: LightingTab | None = None
        self.environment_tab: EnvironmentTab | None = None
        self.quality_tab: QualityTab | None = None
        self.scene_tab: SceneTab | None = None
        self.animation_tab: AnimationTab | None = None
        self.camera_tab: CameraTab | None = None
        self.materials_tab: MaterialsTab | None = None
        self.effects_tab: EffectsTab | None = None

        # Построение UI и загрузка состояния
        self._create_ui()
        self.load_settings()

        # Начальная синхронизация
        try:
            self._apply_state_to_tabs(self._sync_controller.snapshot())
        except Exception:  # pragma: no cover - защита от сбоев UI при старте
            pass
        QTimer.singleShot(0, self._emit_all_initial)
        self.logger.info(
            "✅ GraphicsPanel coordinator initialized (v3.1, centralized save-on-exit)"
        )

    # ------------------------------------------------------------------
    # PUBLIC API (используется тестами и MainWindow)
    # ------------------------------------------------------------------
    def apply_registered_preset(self, preset_id: str) -> bool:
        """Применить зарегистрированный пресет панели по идентификатору.

        - Использует `PanelPresetManager` для применения патча в контроллер синхронизации
        - Обновляет вкладки из текущего снапшота
        - Эмитит `preset_applied` с полным состоянием панели
        - Возвращает True при успехе
        """
        try:
            definition = self.preset_manager.apply_registered_preset(preset_id)
        except Exception as exc:  # pragma: no cover - предохранитель
            self.logger.warning("Не удалось применить пресет %s: %s", preset_id, exc)
            return False
        if definition is None:
            return False
        # Применённый патч уже занесён в контроллер; синхронизируем UI
        snapshot = self._sync_controller.snapshot()
        try:
            self._apply_state_to_tabs(snapshot)
        except Exception:
            # Продолжаем, даже если какая-то вкладка не готова
            pass
        full_state = self.collect_state()
        self.preset_applied.emit(full_state)
        return True

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _create_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Scroll area для табов
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll, 1)

        container = QWidget()
        scroll.setWidget(container)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        # Tab widget
        tabs = QTabWidget(container)
        container_layout.addWidget(tabs)

        # Создание табов
        self._create_tabs(tabs)

        # Кнопки управления
        button_row = self._create_control_buttons()
        main_layout.addLayout(button_row)

    def _create_tabs(self, tabs: QTabWidget) -> None:
        self.lighting_tab = LightingTab(parent=self)
        self.environment_tab = EnvironmentTab(parent=self)
        self.quality_tab = QualityTab(parent=self)
        self.scene_tab = SceneTab(parent=self)
        self.animation_tab = AnimationTab(parent=self)
        self.camera_tab = CameraTab(parent=self)
        self.materials_tab = MaterialsTab(parent=self)
        self.effects_tab = EffectsTab(parent=self)

        tabs.addTab(self.lighting_tab, "Освещение")
        tabs.addTab(self.environment_tab, "Окружение")
        tabs.addTab(self.quality_tab, "Качество")
        tabs.addTab(self.scene_tab, "Сцена")
        tabs.addTab(self.animation_tab, "Анимация")
        tabs.addTab(self.camera_tab, "Камера")
        tabs.addTab(self.materials_tab, "Материалы")
        tabs.addTab(self.effects_tab, "Эффекты")

        self._connect_tab_signals()

    def _connect_tab_signals(self) -> None:
        # Без автосохранения — только проброс сигналов к MainWindow
        self.lighting_tab.lighting_changed.connect(self._on_lighting_changed)
        if hasattr(self.lighting_tab, "preset_applied"):
            self.lighting_tab.preset_applied.connect(
                lambda label: self._on_tab_preset(
                    "lighting", label, self.lighting_tab.get_state()
                )
            )

        self.environment_tab.environment_changed.connect(self._on_environment_changed)
        self.quality_tab.quality_changed.connect(self._on_quality_changed)
        self.quality_tab.preset_applied.connect(
            lambda label: self._on_tab_preset(
                "quality", label, self.quality_tab.get_state()
            )
        )
        self.scene_tab.scene_changed.connect(self._on_scene_changed)
        self.camera_tab.camera_changed.connect(self._on_camera_changed)
        self.materials_tab.material_changed.connect(self._on_material_changed)
        self.effects_tab.effects_changed.connect(self._on_effects_changed)
        if self.animation_tab is not None:
            self.animation_tab.animation_changed.connect(self._on_animation_changed)

    # ------------------------------------------------------------------
    # Handlers — только эмитим, без записи в файл
    # ------------------------------------------------------------------
    def _log_state_changes(self, category: str, previous: Mapping[str, Any], new_payload: Mapping[str, Any]) -> None:
        """Логирование изменения состояния категории с предыдущим и новым payload.

        Args:
            category: имя категории (lighting, environment и т.д.)
            previous: предыдущее состояние категории из snapshot
            new_payload: новый payload, который будет применён
        """
        try:
            # Логируем дифф построчно для аналитики; сохраняем только новые значения
            diff: dict[str, Any] = {}
            for key, value in new_payload.items():
                try:
                    old = previous.get(key) if isinstance(previous, Mapping) else None
                except Exception:
                    old = None
                if old != value:
                    diff[key] = {"old": old, "new": value}
            self.event_logger.log_state_change(category, "update", previous, new_payload)  # type: ignore[arg-type]
        except Exception:
            pass

    def _emit_with_logging(self, signal_name: str, payload: dict[str, Any], category: str) -> None:
        if self._sync_guard:
            return
        previous_state = self._sync_controller.snapshot().get(category, {})
        self._log_state_changes(category, previous_state, payload)
        self._sync_controller.apply_patch(
            {category: deepcopy(payload)},
            description=f"Update graphics.{category}",
            source=signal_name,
            origin="local",
            metadata={"category": category},
        )
        getattr(self, signal_name).emit(deepcopy(payload))

    def _apply_state_to_tabs(self, state: Mapping[str, Any]) -> None:
        try:
            if self.lighting_tab is not None:
                self.lighting_tab.set_state(deepcopy(state.get("lighting", {})))
            if self.environment_tab is not None:
                self.environment_tab.set_state(deepcopy(state.get("environment", {})))
            if self.quality_tab is not None:
                self.quality_tab.set_state(deepcopy(state.get("quality", {})))
            if self.scene_tab is not None:
                self.scene_tab.set_state(deepcopy(state.get("scene", {})))
            if self.animation_tab is not None:
                self.animation_tab.set_state(deepcopy(state.get("animation", {})))
            if self.camera_tab is not None:
                self.camera_tab.set_state(deepcopy(state.get("camera", {})))
            if self.materials_tab is not None:
                self.materials_tab.set_state(deepcopy(state.get("materials", {})))
            if self.effects_tab is not None:
                self.effects_tab.set_state(deepcopy(state.get("effects", {})))
                self._update_color_adjustments_toggle(state.get("effects"))
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error("Failed to apply graphics state to tabs: %s", exc)

    def _on_state_synced(
        self, state: Mapping[str, Any], context: Mapping[str, Any]
    ) -> None:
        self.state = dict(state)
        origin = str(context.get("origin", ""))
        if origin == "local" and not context.get("force_refresh"):
            return

        self._sync_guard += 1
        try:
            self._apply_state_to_tabs(state)
        finally:
            self._sync_guard -= 1

    def _on_tab_preset(
        self, category: str, label: str | None, payload: Mapping[str, Any]
    ) -> None:
        metadata = self.preset_manager.record_application(category, label)
        description = metadata.get(
            "description", f"Apply {category} preset '{label or 'custom'}'"
        )
        source = metadata.get("preset_id") or (label or category)
        self._sync_controller.apply_patch(
            {category: deepcopy(payload)},
            description=description,
            source=str(source),
            origin="preset",
            metadata={**metadata, "force_refresh": True},
        )
        state = self.collect_state()
        self.preset_applied.emit(state)
        self.event_logger.log_signal_emit("preset_applied", state)

    def _on_lighting_changed(self, payload: dict[str, Any]) -> None:
        """Обработчик сигнала вкладки освещения – обновляем агрегированное состояние и эмитим наружу."""
        try:
            current = self.state.get("lighting") or {}
            merged = dict(current)
            # Глубокое объединение ключевых секций (key, fill, rim, point, spot)
            for section, section_payload in payload.items():
                if isinstance(section_payload, Mapping):
                    base = merged.get(section)
                    if isinstance(base, Mapping):
                        new_section = dict(base)
                        new_section.update(section_payload)
                        merged[section] = new_section
                    else:
                        merged[section] = dict(section_payload)
                else:
                    merged[section] = section_payload
            self.state["lighting"] = merged
            self._emit_with_logging("lighting_changed", merged, "lighting")
        except Exception:
            # Fallback: emit raw payload
            self._emit_with_logging("lighting_changed", payload, "lighting")

    def _on_environment_changed(self, data: dict[str, Any]) -> None:
        self._emit_with_logging("environment_changed", data, "environment")

    def _on_quality_changed(self, data: dict[str, Any]) -> None:
        self._emit_with_logging("quality_changed", data, "quality")

    def _on_scene_changed(self, data: dict[str, Any]) -> None:
        self._emit_with_logging("scene_changed", data, "scene")

    def _on_camera_changed(self, data: dict[str, Any]) -> None:
        self._emit_with_logging("camera_changed", data, "camera")

    def _on_material_changed(self, data: dict[str, Any]) -> None:
        self._emit_with_logging("material_changed", data, "materials")

    def _on_effects_changed(self, data: dict[str, Any]) -> None:
        self._update_color_adjustments_toggle(data)
        self._emit_with_logging("effects_changed", data, "effects")

    def _on_animation_changed(self, data: dict[str, Any]) -> None:
        self._emit_with_logging("animation_changed", data, "animation")

    def _create_control_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        toggle = LoggingCheckBox(
            "Цветокоррекция",
            "graphics.color_adjustments_toggle",
            self,
        )
        toggle.setToolTip(
            self.preset_manager.get_tooltip(
                "color_correction_toggle",
                "Включить или выключить цветокоррекцию (яркость, контраст, насыщенность)",
            )
        )
        toggle.blockSignals(True)
        # Убираем скрытый дефолт: состояние будет синхронизировано из настроек после загрузки
        toggle.setChecked(toggle.isChecked())
        toggle.blockSignals(False)
        toggle.toggled.connect(self._on_color_adjustments_toggled)
        self._color_adjustments_toggle = toggle
        row.addWidget(toggle)

        row.addStretch(1)

        reset_btn = QPushButton("↩︎ Сброс к дефолтам", self)
        reset_btn.setToolTip(
            self.preset_manager.get_tooltip(
                "reset_button",
                "Сбросить к значениям из config/app_settings.json (defaults_snapshot)",
            )
        )
        reset_btn.clicked.connect(self.reset_to_defaults)
        row.addWidget(reset_btn)

        save_default_btn = QPushButton("💾 Сохранить как дефолт", self)
        save_default_btn.setToolTip(
            self.preset_manager.get_tooltip(
                "save_defaults_button",
                "Сохранить текущие настройки в defaults_snapshot",
            )
        )
        save_default_btn.clicked.connect(self.save_current_as_defaults)
        row.addWidget(save_default_btn)

        export_btn = QPushButton("📦 Экспорт пресета", self)
        export_btn.setToolTip(
            self.preset_manager.get_tooltip(
                "export_button",
                "Сохранить текущие графические настройки и отчёт синхронизации",
            )
        )
        export_btn.clicked.connect(self.export_sync_analysis)
        row.addWidget(export_btn)

        return row

    def _on_color_adjustments_toggled(self, checked: bool) -> None:
        if self._syncing_color_toggle:
            return
        if self.effects_tab is None:
            return

        control = self.effects_tab._controls.get("color.enabled")
        if isinstance(control, LoggingCheckBox):
            if control.isChecked() != checked:
                control.setChecked(checked)
            return

        payload = dict(self.effects_tab.get_state())
        payload["color_adjustments_enabled"] = checked
        payload["color_adjustments_active"] = checked
        self._emit_with_logging("effects_changed", payload, "effects")

    def _update_color_adjustments_toggle(
        self, payload: Mapping[str, Any] | None
    ) -> None:
        toggle = self._color_adjustments_toggle
        if toggle is None or not isinstance(payload, Mapping):
            return

        enabled: Any | None = payload.get("color_adjustments_active")
        if enabled is None:
            enabled = payload.get("color_adjustments_enabled")
        if enabled is None:
            nested = payload.get("color_adjustments")
            if isinstance(nested, Mapping):
                enabled = (
                    nested.get("active")
                    if "active" in nested
                    else nested.get("enabled")
                )

        if enabled is None:
            return

        checked = bool(enabled)
        if toggle.isChecked() == checked:
            return

        self._syncing_color_toggle = True
        try:
            toggle.blockSignals(True)
            toggle.setChecked(checked)
        finally:
            toggle.blockSignals(False)
            self._syncing_color_toggle = False

    # ------------------------------------------------------------------
    # Загрузка/применение состояния (без записи)
    # ------------------------------------------------------------------
    @Slot()
    def load_settings(self) -> None:
        try:
            settings_path = self.settings_service.settings_file
            if settings_path is not None:
                self.logger.info(f"Settings file path: {settings_path}")

            state = self.settings_service.load_current()
            self._sync_controller.bootstrap(state)
            # Немедленно применяем загруженное состояние к табам,
            # чтобы их UI отражал значения из конфигурации
            self._apply_state_to_tabs(state)

            self.logger.info("✅ Graphics settings loaded from app_settings.json")
        except GraphicsSettingsError as exc:
            self.logger.critical(f"❌ Invalid graphics settings: {exc}")
            raise
        except Exception as exc:  # pragma: no cover - unexpected failures
            self.logger.error(f"❌ Failed to load graphics settings: {exc}")
            raise

    def _emit_all_initial(self) -> None:
        try:
            self.lighting_changed.emit(self.lighting_tab.get_state())
            self.environment_changed.emit(self.environment_tab.get_state())
            self.quality_changed.emit(self.quality_tab.get_state())
            self.scene_changed.emit(self.scene_tab.get_state())
            if self.animation_tab is not None:
                self.animation_changed.emit(self.animation_tab.get_state())
            self.camera_changed.emit(self.camera_tab.get_state())
            # Материалы: при инициализации отправляем ПОЛНЫЙ набор, чтобы QML применил все
            self.material_changed.emit(self.materials_tab.get_all_state())
            self.effects_changed.emit(self.effects_tab.get_state())
        except Exception as e:
            self.logger.error(f"❌ Failed to emit initial graphics state: {e}")

    # ------------------------------------------------------------------
    # Кнопки дефолтов
    # ------------------------------------------------------------------
    @Slot()
    def reset_to_defaults(self) -> None:
        try:
            state = self.settings_service.reset_to_defaults()
            self._sync_controller.apply_state(
                state,
                description="Reset graphics defaults",
                source="reset_button",
                origin="preset",
                metadata={"preset_id": "defaults", "force_refresh": True},
            )
            self.logger.info("✅ Graphics reset to defaults completed")
            payload = self.collect_state()
            self._emit_all_initial()
            self.preset_applied.emit(payload)
            self.event_logger.log_signal_emit("preset_applied", payload)
        except GraphicsSettingsError as exc:
            self.logger.error(f"❌ Failed to reset graphics defaults: {exc}")
        except Exception as exc:  # pragma: no cover - unexpected failures
            self.logger.error(f"❌ Failed to reset graphics defaults: {exc}")

    @Slot()
    def save_current_as_defaults(self) -> None:
        try:
            state = self.collect_state()
            self.settings_service.save_current_as_defaults(state)
            self.preset_applied.emit(state)
            self.event_logger.log_signal_emit("preset_applied", state)
            self.logger.info("✅ Graphics defaults snapshot updated")
        except GraphicsSettingsError as exc:
            self.logger.error(f"❌ Save graphics as defaults failed: {exc}")
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"❌ Save graphics as defaults failed: {exc}")

    # ------------------------------------------------------------------
    # Централизованный сбор состояния — для MainWindow.closeEvent()
    # ------------------------------------------------------------------
    def collect_state(self) -> dict[str, Any]:
        """Собрать текущее состояние напрямую из табов и синхронизировать снапшот.

        Требование тестов: возвращаемое состояние должно совпадать с тем, что
        отражено в UI-табах после всех нормализаций/квантования значений.
        Поэтому сбор выполняем ИЗ ТАБОВ, а не из внутреннего снапшота.
        """
        try:
            aggregated: dict[str, Any] = {}
            if self.lighting_tab is not None:
                aggregated["lighting"] = deepcopy(self.lighting_tab.get_state())
            if self.environment_tab is not None:
                aggregated["environment"] = deepcopy(self.environment_tab.get_state())
            if self.quality_tab is not None:
                aggregated["quality"] = deepcopy(self.quality_tab.get_state())
            if self.scene_tab is not None:
                aggregated["scene"] = deepcopy(self.scene_tab.get_state())
            if self.animation_tab is not None:
                aggregated["animation"] = deepcopy(self.animation_tab.get_state())
            if self.camera_tab is not None:
                aggregated["camera"] = deepcopy(self.camera_tab.get_state())
            if self.materials_tab is not None:
                # Материалы: экспортируем полный набор для QML синхронизации
                aggregated["materials"] = deepcopy(self.materials_tab.get_all_state())
            if self.effects_tab is not None:
                aggregated["effects"] = deepcopy(self.effects_tab.get_state())

            # Валидация структуры/типов на уровне сервиса (без форс-правок значений табов)
            try:
                validated = self.settings_service.ensure_valid_state(aggregated)
            except Exception:
                validated = aggregated

            # Синхронизируем внутренний снапшот, но не инициируем повторное применение к табам
            self._sync_controller.apply_state(
                validated,
                description="Collect graphics state",
                source="collect_state",
                origin="collection",
                record=False,
                metadata={"force_refresh": False},
            )
            self.state = deepcopy(validated)
            return validated
        except GraphicsSettingsError as exc:
            self.logger.error(f"❌ Failed to collect graphics state: {exc}")
            return self.state or {}
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error(f"❌ Failed to collect graphics state: {exc}")
            return self.state or {}

    def get_parameters(self) -> dict[str, Any]:
        """Возвращает полный снимок параметров панели для тестов.

        Собирает состояние из внутреннего `self.state` и актуального snapshot
        контроллера синхронизации, предпочитая локальные изменения.
        """
        snapshot = self._sync_controller.snapshot()
        combined: dict[str, Any] = {}
        # Приоритет локального состояния
        for category, value in snapshot.items():
            if isinstance(value, Mapping):
                combined[category] = deepcopy(value)
            else:
                combined[category] = value
        for category, value in self.state.items():
            if isinstance(value, Mapping):
                combined[category] = deepcopy(value)
            else:
                combined[category] = value
        return combined

    # ------------------------------------------------------------------
    # Анализ (не настройки)
    # ------------------------------------------------------------------
    def export_sync_analysis(self) -> None:
        try:
            state = self.collect_state()
            self.settings_service.save_current(state)

            export_dir = Path("reports") / "graphics"
            export_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            preset_path = export_dir / f"graphics-preset-{timestamp}.json"
            preset_path.write_text(
                json.dumps(state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            report_path = self.graphics_logger.export_analysis_report()
            analysis = self.graphics_logger.analyze_qml_sync()

            print("\n" + "=" * 60)
            print("📦 GRAPHICS PRESET EXPORT")
            print("=" * 60)
            print(f"Preset file: {preset_path}")
            print("-")
            print("📊 GRAPHICS SYNC ANALYSIS")
            print("=" * 60)
            print(f"Total changes: {analysis.get('total_events', 0)}")
            print(f"Successful QML updates: {analysis.get('successful_updates', 0)}")
            print(f"Failed QML updates: {analysis.get('failed_updates', 0)}")
            print("=" * 60)
            print(f"Analysis report: {report_path}")
            print("=" * 60 + "\n")

            self.logger.info("✅ Graphics preset exported to %s", preset_path)
        except Exception as e:
            self.logger.error(f"❌ Failed to export graphics preset: {e}")

    def undo_last_change(self) -> bool:
        return self._sync_controller.undo() is not None

    def redo_last_change(self) -> bool:
        return self._sync_controller.redo() is not None

    # Не сохраняем здесь — централизованно в MainWindow.closeEvent()
    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.logger.info(
            "GraphicsPanel closed (no direct save, centralized by MainWindow)"
        )
        super().closeEvent(event)
