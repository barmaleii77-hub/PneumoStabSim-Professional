"""Graphics Panel Coordinator - Refactored Version v3.1

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
from typing import Any, Dict

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

from src.common.settings_manager import get_settings_manager
from src.ui.panels.graphics_logger import get_graphics_logger
from src.common.event_logger import get_event_logger


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
    effects_changed = Signal(dict)
    preset_applied = Signal(dict)  # ✅ передаем полный state

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.logger = logging.getLogger(__name__)
        self.settings_manager = get_settings_manager()
        self.graphics_logger = get_graphics_logger()
        self.event_logger = get_event_logger()

        # Загружаем текущее состояние из JSON (не дефолты)
        self.state: Dict[str, Any] = (
            self.settings_manager.get_category("graphics") or {}
        )

        # Таб-виджеты
        self.lighting_tab: LightingTab | None = None
        self.environment_tab: EnvironmentTab | None = None
        self.quality_tab: QualityTab | None = None
        self.camera_tab: CameraTab | None = None
        self.materials_tab: MaterialsTab | None = None
        self.effects_tab: EffectsTab | None = None

        # Построение UI и загрузка состояния
        self._create_ui()
        self.load_settings()

        # Начальная синхронизация
        QTimer.singleShot(0, self._emit_all_initial)
        self.logger.info(
            "✅ GraphicsPanel coordinator initialized (v3.1, centralized save-on-exit)"
        )

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
        self.camera_tab = CameraTab(parent=self)
        self.materials_tab = MaterialsTab(parent=self)
        self.effects_tab = EffectsTab(parent=self)

        tabs.addTab(self.lighting_tab, "Освещение")
        tabs.addTab(self.environment_tab, "Окружение")
        tabs.addTab(self.quality_tab, "Качество")
        tabs.addTab(self.camera_tab, "Камера")
        tabs.addTab(self.materials_tab, "Материалы")
        tabs.addTab(self.effects_tab, "Эффекты")

        self._connect_tab_signals()

    def _connect_tab_signals(self) -> None:
        # Без автосохранения — только проброс сигналов к MainWindow
        self.lighting_tab.lighting_changed.connect(self._on_lighting_changed)
        if hasattr(self.lighting_tab, "preset_applied"):
            self.lighting_tab.preset_applied.connect(
                lambda _: self.preset_applied.emit(self.collect_state())
            )

        self.environment_tab.environment_changed.connect(self._on_environment_changed)
        self.quality_tab.quality_changed.connect(self._on_quality_changed)
        self.quality_tab.preset_applied.connect(
            lambda _: self.preset_applied.emit(self.collect_state())
        )
        self.camera_tab.camera_changed.connect(self._on_camera_changed)
        self.materials_tab.material_changed.connect(self._on_material_changed)
        self.effects_tab.effects_changed.connect(self._on_effects_changed)

    # ------------------------------------------------------------------
    # Handlers — только эмитим, без записи в файл
    # ------------------------------------------------------------------
    def _on_lighting_changed(self, data: Dict[str, Any]) -> None:
        self.lighting_changed.emit(data)

    def _on_environment_changed(self, data: Dict[str, Any]) -> None:
        self.environment_changed.emit(data)

    def _on_quality_changed(self, data: Dict[str, Any]) -> None:
        self.quality_changed.emit(data)

    def _on_camera_changed(self, data: Dict[str, Any]) -> None:
        self.camera_changed.emit(data)

    def _on_material_changed(self, data: Dict[str, Any]) -> None:
        self.material_changed.emit(data)

    def _on_effects_changed(self, data: Dict[str, Any]) -> None:
        self.effects_changed.emit(data)

    def _create_control_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addStretch(1)

        reset_btn = QPushButton("↩︎ Сброс к дефолтам", self)
        reset_btn.setToolTip(
            "Сбросить к значениям из config/app_settings.json (defaults_snapshot)"
        )
        reset_btn.clicked.connect(self.reset_to_defaults)
        row.addWidget(reset_btn)

        save_default_btn = QPushButton("💾 Сохранить как дефолт", self)
        save_default_btn.setToolTip("Сохранить текущие настройки в defaults_snapshot")
        save_default_btn.clicked.connect(self.save_current_as_defaults)
        row.addWidget(save_default_btn)

        export_btn = QPushButton("📊 Экспорт анализа", self)
        export_btn.setToolTip(
            "Экспортировать анализ синхронизации Python↔QML (не настройки)"
        )
        export_btn.clicked.connect(self.export_sync_analysis)
        row.addWidget(export_btn)

        return row

    # ------------------------------------------------------------------
    # Загрузка/применение состояния (без записи)
    # ------------------------------------------------------------------
    @Slot()
    def load_settings(self) -> None:
        try:
            # Диагностика: где именно лежит файл настроек
            try:
                self.logger.info(
                    f"Settings file path: {self.settings_manager.settings_file}"
                )
            except Exception:
                pass
            self.state = self.settings_manager.get_category("graphics") or {}
            if "lighting" in self.state:
                self.lighting_tab.set_state(self.state["lighting"])
            if "environment" in self.state:
                self.environment_tab.set_state(self.state["environment"])
            if "quality" in self.state:
                self.quality_tab.set_state(self.state["quality"])
            if "camera" in self.state:
                self.camera_tab.set_state(self.state["camera"])
            # Материалы: строгая валидация (никаких скрытых автодополнений)
            materials_state = (
                self.state.get("materials") if isinstance(self.state, dict) else None
            )
            expected_keys = {
                "frame",
                "lever",
                "tail",
                "cylinder",
                "piston_body",
                "piston_rod",
                "joint_tail",
                "joint_arm",
                "joint_rod",
            }
            if not isinstance(materials_state, dict):
                cfg_path = getattr(self.settings_manager, "settings_file", "<unknown>")
                msg = (
                    f"Некорректный формат graphics.materials (ожидался dict)\n"
                    f"Путь: {cfg_path}\nТип: {type(materials_state).__name__}"
                )
                self.logger.critical(msg)
                raise RuntimeError(msg)
            found_keys = set(
                k
                for k in materials_state.keys()
                if isinstance(materials_state.get(k), dict)
            )
            missing = sorted(list(expected_keys - found_keys))
            if missing:
                cfg_path = getattr(self.settings_manager, "settings_file", "<unknown>")
                msg = (
                    f"Отсутствуют обязательные материалы в graphics.materials: {', '.join(missing)}\n"
                    f"Путь: {cfg_path}\nНайдено: {sorted(list(found_keys))}"
                )
                self.logger.critical(msg)
                raise RuntimeError(msg)
            # Передаём БЕЗ обёртки current_material — таб сам разберёт ключи
            self.materials_tab.set_state(materials_state)
            if "effects" in self.state:
                self.effects_tab.set_state(self.state["effects"])
            self.logger.info("✅ Graphics settings loaded from app_settings.json")
        except Exception as e:
            # Эскалируем исключение — заглушки запрещены
            self.logger.error(f"❌ Failed to load graphics settings: {e}")
            raise

    def _emit_all_initial(self) -> None:
        try:
            self.lighting_changed.emit(self.lighting_tab.get_state())
            self.environment_changed.emit(self.environment_tab.get_state())
            self.quality_changed.emit(self.quality_tab.get_state())
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
            self.settings_manager.reset_to_defaults(category="graphics")
            self.load_settings()
            self._emit_all_initial()
            # передаём полный state для MainWindow
            self.preset_applied.emit(self.collect_state())
            self.logger.info("✅ Graphics reset to defaults completed")
        except Exception as e:
            self.logger.error(f"❌ Failed to reset graphics defaults: {e}")

    @Slot()
    def save_current_as_defaults(self) -> None:
        try:
            state = self.collect_state()
            self.settings_manager.set_category("graphics", state, auto_save=False)
            self.settings_manager.save_current_as_defaults(category="graphics")
            self.preset_applied.emit(state)
            self.logger.info("✅ Graphics defaults snapshot updated")
        except Exception as e:
            self.logger.error(f"❌ Save graphics as defaults failed: {e}")

    # ------------------------------------------------------------------
    # Централизованный сбор состояния — для MainWindow.closeEvent()
    # ------------------------------------------------------------------
    def collect_state(self) -> Dict[str, Any]:
        try:
            state = {
                "lighting": self.lighting_tab.get_state(),
                "environment": self.environment_tab.get_state(),
                "quality": self.quality_tab.get_state(),
                "camera": self.camera_tab.get_state(),
                # Для сохранения берём ВСЕ материалы из кэша таба
                "materials": self.materials_tab.get_all_state(),
                "effects": self.effects_tab.get_state(),
            }
            return state
        except Exception as e:
            self.logger.error(f"❌ Failed to collect graphics state: {e}")
            return self.state or {}

    # ------------------------------------------------------------------
    # Анализ (не настройки)
    # ------------------------------------------------------------------
    def export_sync_analysis(self) -> None:
        try:
            report_path = self.graphics_logger.export_analysis_report()
            analysis = self.graphics_logger.analyze_qml_sync()
            print("\n" + "=" * 60)
            print("📊 GRAPHICS SYNC ANALYSIS")
            print("=" * 60)
            print(f"Total changes: {analysis.get('total_events', 0)}")
            print(f"Successful QML updates: {analysis.get('successful_updates', 0)}")
            print(f"Failed QML updates: {analysis.get('failed_updates', 0)}")
            print("=" * 60)
            print(f"Full report: {report_path}")
            print("=" * 60 + "\n")
        except Exception as e:
            self.logger.error(f"Failed to export sync analysis: {e}")

    # Не сохраняем здесь — централизованно в MainWindow.closeEvent()
    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.logger.info(
            "GraphicsPanel closed (no direct save, centralized by MainWindow)"
        )
        super().closeEvent(event)
