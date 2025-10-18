"""Graphics Panel Coordinator - Refactored Version v3.0

Координатор для GraphicsPanel с полностью рефакторенными табами.
Все табы теперь независимы и находятся в src/ui/panels/graphics/.

ИЗМЕНЕНИЯ v3.0 (КРИТИЧНО):
- ✅ Интегрирован SettingsManager (единый источник настроек)
- ❌ УДАЛЁН импорт defaults.py (дефолты теперь в JSON!)
- ✅ Добавлена кнопка "Сохранить как дефолт"
- ✅ Автосохранение через SettingsManager (не QSettings!)
- ✅ Сброс загружает defaults_snapshot из JSON

ИЗМЕНЕНИЯ v2.0:
- Удалена зависимость от state_manager (табы сами управляют состоянием)
- Импорты из корня graphics/ вместо tabs/
- Упрощённая инициализация табов (без state_manager)
- Прямая агрегация сигналов от табов

Russian UI / English code.
"""
from __future__ import annotations

import copy
import logging
from typing import Any, Dict

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# ✅ НОВЫЕ ИМПОРТЫ - рефакторенные табы из корня graphics/
from .effects_tab import EffectsTab
from .environment_tab import EnvironmentTab
from .quality_tab import QualityTab
from .camera_tab import CameraTab
from .materials_tab import MaterialsTab
from .lighting_tab import LightingTab

# ✅ КРИТИЧНО: SettingsManager вместо defaults.py
from src.common.settings_manager import get_settings_manager

# ✅ ИСПРАВЛЕН ИМПОРТ - graphics_logger находится в src/ui/panels/
from src.ui.panels.graphics_logger import get_graphics_logger
from src.common.event_logger import get_event_logger


class GraphicsPanel(QWidget):
    """Координатор графической панели с модульными табами.
    
    Responsibilities:
    1. Создание табов и координация
    2. Агрегация сигналов от табов
    3. Управление настройками через SettingsManager (НЕ QSettings!)
    4. Публичный API для MainWindow
    
    Design: Coordinator Pattern (минимальная логика)
    
    ВАЖНО: Все настройки хранятся в config/app_settings.json
    """
    
    # Агрегированные сигналы (пробрасываются от табов)
    lighting_changed = Signal(dict)
    environment_changed = Signal(dict)
    material_changed = Signal(dict)
    quality_changed = Signal(dict)
    camera_changed = Signal(dict)
    effects_changed = Signal(dict)
    preset_applied = Signal(str)
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # ✅ НОВОЕ: SettingsManager (единый источник истины)
        self.settings_manager = get_settings_manager()
        
        # Логгеры
        self.graphics_logger = get_graphics_logger()
        self.event_logger = get_event_logger()
        
        # ✅ НОВОЕ: Загружаем текущее состояние из JSON
        self.state: Dict[str, Any] = self.settings_manager.get_category("graphics")
        
        # Табы (создаются в _create_ui)
        self.lighting_tab: LightingTab | None = None
        self.environment_tab: EnvironmentTab | None = None
        self.quality_tab: QualityTab | None = None
        self.camera_tab: CameraTab | None = None
        self.materials_tab: MaterialsTab | None = None
        self.effects_tab: EffectsTab | None = None
        
        # Построение UI
        self._create_ui()
        
        # Загрузка сохранённых настроек из JSON
        self.load_settings()
        
        # Начальная синхронизация (асинхронно)
        QTimer.singleShot(0, self._emit_all_initial)
        
        self.logger.info("✅ GraphicsPanel coordinator initialized (v3.0 - SettingsManager)")
    
    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _create_ui(self) -> None:
        """Создать UI - только структуру"""
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
        """Создать все табы и подключить сигналы"""
        # ✅ Создаём табы БЕЗ state_manager (они независимы)
        self.lighting_tab = LightingTab(parent=self)
        self.environment_tab = EnvironmentTab(parent=self)
        self.quality_tab = QualityTab(parent=self)
        self.camera_tab = CameraTab(parent=self)
        self.materials_tab = MaterialsTab(parent=self)
        self.effects_tab = EffectsTab(parent=self)
        
        # Добавление в TabWidget (ПОРЯДОК КАК В МОНОЛИТЕ)
        tabs.addTab(self.lighting_tab, "Освещение")
        tabs.addTab(self.environment_tab, "Окружение")
        tabs.addTab(self.quality_tab, "Качество")
        tabs.addTab(self.camera_tab, "Камера")
        tabs.addTab(self.materials_tab, "Материалы")
        tabs.addTab(self.effects_tab, "Эффекты")
        
        # Подключение сигналов
        self._connect_tab_signals()
        
        self.logger.debug("All tabs created and connected")
    
    def _connect_tab_signals(self) -> None:
        """Подключить сигналы табов к агрегированным сигналам"""
        # Lighting
        self.lighting_tab.lighting_changed.connect(self._on_lighting_changed)
        if hasattr(self.lighting_tab, 'preset_applied'):
            self.lighting_tab.preset_applied.connect(self.preset_applied.emit)
        
        # Environment
        self.environment_tab.environment_changed.connect(self._on_environment_changed)
        
        # Quality
        self.quality_tab.quality_changed.connect(self._on_quality_changed)
        self.quality_tab.preset_applied.connect(self.preset_applied.emit)
        
        # Camera
        self.camera_tab.camera_changed.connect(self._on_camera_changed)
        
        # Materials
        self.materials_tab.material_changed.connect(self._on_material_changed)
        
        # Effects
        self.effects_tab.effects_changed.connect(self._on_effects_changed)
        
        self.logger.debug("Tab signals connected")
    
    # ------------------------------------------------------------------
    # Signal Handlers (обновляют state и пробрасывают дальше)
    # ------------------------------------------------------------------
    def _on_lighting_changed(self, data: Dict[str, Any]) -> None:
        """Обработчик изменения освещения"""
        # Пробрасыем сигнал
        self.lighting_changed.emit(data)
        
        # ✅ НОВОЕ: Автосохранение через SettingsManager
        try:
            self.save_settings()
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
    
    def _on_environment_changed(self, data: Dict[str, Any]) -> None:
        """Обработчик изменения окружения"""
        self.environment_changed.emit(data)
        try:
            self.save_settings()
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
    
    def _on_quality_changed(self, data: Dict[str, Any]) -> None:
        """Обработчик изменения качества"""
        self.quality_changed.emit(data)
        try:
            self.save_settings()
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
    
    def _on_camera_changed(self, data: Dict[str, Any]) -> None:
        """Обработчик изменения камеры"""
        self.camera_changed.emit(data)
        try:
            self.save_settings()
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
    
    def _on_material_changed(self, data: Dict[str, Any]) -> None:
        """Обработчик изменения материалов"""
        self.material_changed.emit(data)
        try:
            self.save_settings()
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
    
    def _on_effects_changed(self, data: Dict[str, Any]) -> None:
        """Обработчик изменения эффектов"""
        self.effects_changed.emit(data)
        try:
            self.save_settings()
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
    
    def _create_control_buttons(self) -> QHBoxLayout:
        """Создать кнопки управления"""
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)
        button_row.addStretch(1)
        
        # ✅ НОВОЕ: Кнопка "Сброс к дефолтам" (из JSON!)
        reset_btn = QPushButton("↩︎ Сброс к дефолтам", self)
        reset_btn.setToolTip("Сбросить к значениям из config/app_settings.json (defaults_snapshot)")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_row.addWidget(reset_btn)
        
        # ✅ НОВОЕ: Кнопка "Сохранить как дефолт"
        save_default_btn = QPushButton("💾 Сохранить как дефолт", self)
        save_default_btn.setToolTip("Сохранить текущие настройки в defaults_snapshot")
        save_default_btn.clicked.connect(self.save_current_as_defaults)
        button_row.addWidget(save_default_btn)
        
        # Export analysis button
        export_btn = QPushButton("📊 Экспорт анализа", self)
        export_btn.setToolTip("Экспортировать анализ синхронизации Python↔QML")
        export_btn.clicked.connect(self.export_sync_analysis)
        button_row.addWidget(export_btn)
        
        return button_row
    
    # ------------------------------------------------------------------
    # State Management (через SettingsManager!)
    # ------------------------------------------------------------------
    def _emit_all_initial(self) -> None:
        """Начальная синхронизация - эмитим все сигналы"""
        try:
            # Каждый таб эмитит своё текущее состояние
            self.lighting_changed.emit(self.lighting_tab.get_state())
            self.environment_changed.emit(self.environment_tab.get_state())
            self.quality_changed.emit(self.quality_tab.get_state())
            self.camera_changed.emit(self.camera_tab.get_state())
            
            # Materials - нужно эмитить для каждого материала
            materials_state = self.materials_tab.get_state()
            self.material_changed.emit(materials_state)
            
            self.effects_changed.emit(self.effects_tab.get_state())
            
            self.logger.info("✅ Initial state emitted to QML")
        except Exception as e:
            self.logger.error(f"❌ Failed to emit initial state: {e}")
    
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @Slot()
    def save_settings(self) -> None:
        """
        Сохранить текущее состояние всех табов в JSON через SettingsManager
        
        ВАЖНО: Автосохранение при каждом изменении!
        """
        try:
            # Собираем состояние от каждого таба
            state = {
                "lighting": self.lighting_tab.get_state(),
                "environment": self.environment_tab.get_state(),
                "quality": self.quality_tab.get_state(),
                "camera": self.camera_tab.get_state(),
                "materials": self.materials_tab.get_state(),
                "effects": self.effects_tab.get_state(),
            }
            
            # ✅ НОВОЕ: Сохраняем через SettingsManager (в JSON!)
            self.settings_manager.set_category("graphics", state, auto_save=True)
            
            # Обновляем локальный state
            self.state = state
            
            self.logger.debug("✅ Settings saved to app_settings.json")
        except Exception as e:
            self.logger.error(f"❌ Failed to save settings: {e}")
    
    @Slot()
    def load_settings(self) -> None:
        """
        Загрузить состояние из JSON через SettingsManager и применить к табам
        """
        try:
            # ✅ НОВОЕ: Загружаем из SettingsManager (из JSON!)
            self.state = self.settings_manager.get_category("graphics")
            
            # Применяем к каждому табу
            if "lighting" in self.state:
                self.lighting_tab.set_state(self.state["lighting"])
            
            if "environment" in self.state:
                self.environment_tab.set_state(self.state["environment"])
            
            if "quality" in self.state:
                self.quality_tab.set_state(self.state["quality"])
            
            if "camera" in self.state:
                self.camera_tab.set_state(self.state["camera"])
            
            if "materials" in self.state:
                self.materials_tab.set_state(self.state["materials"])
            
            if "effects" in self.state:
                self.effects_tab.set_state(self.state["effects"])
            
            self.logger.info("✅ Settings loaded from app_settings.json")
        except Exception as e:
            self.logger.error(f"❌ Failed to load settings: {e}")
    
    @Slot()
    def reset_to_defaults(self) -> None:
        """
        Сбросить все настройки к дефолтам (из defaults_snapshot в JSON!)
        
        ВАЖНО: Дефолты НЕ в коде, а в config/app_settings.json
        """
        self.logger.info("🔄 Resetting graphics to defaults (from JSON defaults_snapshot)")
        
        try:
            # ✅ НОВОЕ: Сброс через SettingsManager (загружает defaults_snapshot)
            self.settings_manager.reset_to_defaults(category="graphics")
            
            # Перезагружаем state
            self.state = self.settings_manager.get_category("graphics")
            
            # Применяем к табам
            if "lighting" in self.state:
                self.lighting_tab.set_state(self.state["lighting"])
            
            if "environment" in self.state:
                self.environment_tab.set_state(self.state["environment"])
            
            if "quality" in self.state:
                self.quality_tab.set_state(self.state["quality"])
            
            if "camera" in self.state:
                self.camera_tab.set_state(self.state["camera"])
            
            if "materials" in self.state:
                # Materials требует особой обработки
                for material_key, material_state in self.state["materials"].items():
                    if hasattr(self.materials_tab, 'set_material_state'):
                        self.materials_tab.set_material_state(material_key, material_state)
            
            if "effects" in self.state:
                self.effects_tab.set_state(self.state["effects"])
            
            # Эмитим все сигналы
            self._emit_all_initial()
            
            self.preset_applied.emit("Сброс к дефолтам из config/app_settings.json")
            self.logger.info("✅ Reset to defaults completed")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to reset to defaults: {e}")
    
    @Slot()
    def save_current_as_defaults(self) -> None:
        """
        Сохранить текущие настройки как новые дефолты
        (кнопка "Сохранить как дефолт" в UI)
        
        ВАЖНО: Обновляет defaults_snapshot в config/app_settings.json
        """
        try:
            # Сохраняем текущие настройки как дефолты
            self.settings_manager.save_current_as_defaults(category="graphics")
            
            self.logger.info("✅ Current graphics settings saved as new defaults")
            self.preset_applied.emit("Текущие настройки сохранены как новые дефолты")
            
        except Exception as e:
            self.logger.error(f"❌ Save as defaults failed: {e}")
    
    def export_sync_analysis(self) -> None:
        """Экспортировать анализ синхронизации Python↔QML"""
        try:
            report_path = self.graphics_logger.export_analysis_report()
            self.logger.info(f"📄 Sync analysis exported: {report_path}")
            
            # Получаем анализ
            analysis = self.graphics_logger.analyze_qml_sync()
            
            # Выводим статистику
            print("\n" + "="*60)
            print("📊 GRAPHICS SYNC ANALYSIS")
            print("="*60)
            print(f"Total changes: {analysis.get('total_events', 0)}")
            print(f"Successful QML updates: {analysis.get('successful_updates', 0)}")
            print(f"Failed QML updates: {analysis.get('failed_updates', 0)}")
            print(f"Sync rate: {analysis.get('sync_rate', 0):.1f}%")
            print("\nBy category:")
            for cat, stats in analysis.get('by_category', {}).items():
                print(f"  {cat}: {stats['total']} changes, {stats['successful']} synced")
            
            if analysis.get('errors_by_parameter'):
                print("\n⚠️ Parameters with errors:")
                for param, errors in analysis['errors_by_parameter'].items():
                    print(f"  {param}: {len(errors)} error(s)")
            
            print("="*60)
            print(f"Full report: {report_path}")
            print("="*60 + "\n")
            
        except Exception as e:
            self.logger.error(f"Failed to export sync analysis: {e}")
    
    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        """Обработка закрытия панели"""
        self.logger.info("🛑 GraphicsPanel closing...")
        
        try:
            self.save_settings()
            self.logger.info("   ✅ Settings saved to JSON")
        except Exception as e:
            self.logger.error(f"   ❌ Failed to save settings: {e}")
        
        try:
            report_path = self.graphics_logger.export_analysis_report()
            self.logger.info(f"   ✅ Analysis report saved: {report_path}")
        except Exception as e:
            self.logger.error(f"   ❌ Failed to export analysis: {e}")
        
        super().closeEvent(event)
