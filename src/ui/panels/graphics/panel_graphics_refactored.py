"""Graphics Panel Coordinator - Refactored Version

Тонкий координатор для GraphicsPanel, делегирующий всю работу специализированным вкладкам.
Этот файл заменит старый монолитный panel_graphics.py после тестирования.

Russian UI / English code.
"""
from __future__ import annotations

import copy
import logging
from typing import Any, Dict

from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Import все вкладки из модульной структуры
from .tabs.lighting_tab import LightingTab
from .tabs.environment_tab import EnvironmentTab
from .tabs.quality_tab import QualityTab
from .tabs.camera_tab import CameraTab
from .tabs.materials_tab import MaterialsTab
from .tabs.effects_tab import EffectsTab

# Import менеджер состояния
from .state_manager import GraphicsStateManager

# Import логгеры
from .graphics_logger import get_graphics_logger
from src.common.event_logger import get_event_logger


class GraphicsPanel(QWidget):
    """Координатор графической панели с делегированием вкладкам.
    
    Responsibilities (МИНИМАЛЬНЫЕ):
    1. Создание вкладок (делегирование)
    2. Агрегация сигналов от вкладок
    3. Координация state_manager
    4. Публичный API для MainWindow
    
    Design Pattern: Coordinator + Delegation
    """
    
    # Агрегированные сигналы (проброшены от вкладок)
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
        self.settings = QSettings("PneumoStabSim", "GraphicsPanel")
        
        # Логгеры
        self.graphics_logger = get_graphics_logger()
        self.event_logger = get_event_logger()
        
        # State manager (централизованное управление состоянием)
        self.state_manager = GraphicsStateManager(self.settings)
        
        # Вкладки (создаются один раз)
        self.lighting_tab: LightingTab | None = None
        self.environment_tab: EnvironmentTab | None = None
        self.quality_tab: QualityTab | None = None
        self.camera_tab: CameraTab | None = None
        self.materials_tab: MaterialsTab | None = None
        self.effects_tab: EffectsTab | None = None
        
        # Построение UI
        self._create_ui()
        
        # Загрузка состояния
        self._load_and_apply_state()
        
        # Начальная синхронизация (асинхронно)
        QTimer.singleShot(0, self._emit_all_initial)
        
        self.logger.info("GraphicsPanel coordinator initialized (refactored version)")
    
    # ------------------------------------------------------------------
    # UI Construction (МИНИМАЛЬНАЯ)
    # ------------------------------------------------------------------
    def _create_ui(self) -> None:
        """Создать UI - только структуру, без логики"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Scroll area для вкладок
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
        
        # Создание вкладок (делегирование)
        self._create_tabs(tabs)
        
        # Кнопки управления
        button_row = self._create_control_buttons()
        main_layout.addLayout(button_row)
    
    def _create_tabs(self, tabs: QTabWidget) -> None:
        """Создать все вкладки и подключить сигналы"""
        # Создаём вкладки с передачей state_manager
        self.lighting_tab = LightingTab(
            state_manager=self.state_manager,
            parent=self
        )
        self.environment_tab = EnvironmentTab(
            state_manager=self.state_manager,
            parent=self
        )
        self.quality_tab = QualityTab(
            state_manager=self.state_manager,
            parent=self
        )
        self.camera_tab = CameraTab(
            state_manager=self.state_manager,
            parent=self
        )
        self.materials_tab = MaterialsTab(
            state_manager=self.state_manager,
            parent=self
        )
        self.effects_tab = EffectsTab(
            state_manager=self.state_manager,
            parent=self
        )
        
        # Добавление в TabWidget
        tabs.addTab(self.lighting_tab, "Освещение")
        tabs.addTab(self.environment_tab, "Окружение")
        tabs.addTab(self.quality_tab, "Качество")
        tabs.addTab(self.camera_tab, "Камера")
        tabs.addTab(self.materials_tab, "Материалы")
        tabs.addTab(self.effects_tab, "Эффекты")
        
        # Подключение сигналов (агрегация)
        self._connect_tab_signals()
    
    def _connect_tab_signals(self) -> None:
        """Подключить сигналы вкладок к агрегированным сигналам координатора"""
        # Lighting
        self.lighting_tab.lighting_changed.connect(self.lighting_changed.emit)
        self.lighting_tab.preset_applied.connect(self.preset_applied.emit)
        
        # Environment
        self.environment_tab.environment_changed.connect(self.environment_changed.emit)
        
        # Quality
        self.quality_tab.quality_changed.connect(self.quality_changed.emit)
        self.quality_tab.preset_applied.connect(self.preset_applied.emit)
        
        # Camera
        self.camera_tab.camera_changed.connect(self.camera_changed.emit)
        
        # Materials
        self.materials_tab.material_changed.connect(self.material_changed.emit)
        
        # Effects
        self.effects_tab.effects_changed.connect(self.effects_changed.emit)
        
        self.logger.debug("Tab signals connected to coordinator")
    
    def _create_control_buttons(self) -> QHBoxLayout:
        """Создать кнопки управления (Reset, Export)"""
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)
        button_row.addStretch(1)
        
        # Reset button
        reset_btn = QPushButton("↩︎ Сброс", self)
        reset_btn.setToolTip("Сбросить все настройки к значениям по умолчанию")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_row.addWidget(reset_btn)
        
        # Export analysis button (для отладки)
        export_btn = QPushButton("📊 Экспорт анализа", self)
        export_btn.setToolTip("Экспортировать анализ синхронизации Python↔QML")
        export_btn.clicked.connect(self.export_sync_analysis)
        button_row.addWidget(export_btn)
        
        return button_row
    
    # ------------------------------------------------------------------
    # State Management (ДЕЛЕГИРОВАНИЕ)
    # ------------------------------------------------------------------
    def _load_and_apply_state(self) -> None:
        """Загрузить состояние и применить к вкладкам"""
        try:
            self.state_manager.load_settings()
            self.logger.info("Settings loaded from QSettings")
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
        
        # Применить состояние к каждой вкладке
        self._apply_state_to_tabs()
    
    def _apply_state_to_tabs(self) -> None:
        """Применить текущее состояние ко всем вкладкам"""
        try:
            self.lighting_tab.apply_state()
            self.environment_tab.apply_state()
            self.quality_tab.apply_state()
            self.camera_tab.apply_state()
            self.materials_tab.apply_state()
            self.effects_tab.apply_state()
            self.logger.debug("State applied to all tabs")
        except Exception as e:
            self.logger.error(f"Failed to apply state to tabs: {e}")
    
    def _emit_all_initial(self) -> None:
        """Начальная синхронизация - эмитим все сигналы"""
        try:
            self.lighting_tab.emit_current_state()
            self.environment_tab.emit_current_state()
            self.quality_tab.emit_current_state()
            self.camera_tab.emit_current_state()
            self.materials_tab.emit_current_state()
            self.effects_tab.emit_current_state()
            self.logger.info("Initial state emitted to QML")
        except Exception as e:
            self.logger.error(f"Failed to emit initial state: {e}")
    
    # ------------------------------------------------------------------
    # Public API (Обратная совместимость с MainWindow)
    # ------------------------------------------------------------------
    @Slot()
    def save_settings(self) -> None:
        """Сохранить текущее состояние (вызывается из MainWindow)"""
        try:
            self.state_manager.save_settings()
            self.logger.info("Settings saved to QSettings")
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
    
    @Slot()
    def load_settings(self) -> None:
        """Загрузить состояние (вызывается из MainWindow)"""
        try:
            self.state_manager.load_settings()
            self._apply_state_to_tabs()
            self.logger.info("Settings loaded and applied")
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
    
    @Slot()
    def reset_to_defaults(self) -> None:
        """Сбросить все настройки к дефолтам"""
        self.logger.info("🔄 Resetting all graphics settings to defaults")
        
        # Логируем полный сброс
        old_state = copy.deepcopy(self.state_manager.state)
        
        # Сброс через state_manager
        self.state_manager.reset_to_defaults()
        
        # Применяем к вкладкам
        self._apply_state_to_tabs()
        
        # Эмитим все сигналы
        self._emit_all_initial()
        
        # Сохраняем
        try:
            self.state_manager.save_settings()
        except Exception:
            pass
        
        # Логируем
        self.graphics_logger.log_change(
            parameter_name="RESET_ALL",
            old_value=old_state,
            new_value=copy.deepcopy(self.state_manager.state),
            category="system",
            panel_state=self.state_manager.state,
        )
        
        self.preset_applied.emit("Сброс к значениям по умолчанию")
        self.logger.info("✅ Reset to defaults completed")
    
    def export_sync_analysis(self) -> None:
        """Экспортировать анализ синхронизации Python↔QML"""
        try:
            report_path = self.graphics_logger.export_analysis_report()
            self.logger.info(f"📄 Sync analysis exported: {report_path}")
            
            # Получаем анализ
            analysis = self.graphics_logger.analyze_qml_sync()
            
            # Выводим краткую статистику
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
    # Compatibility Properties (для старого кода)
    # ------------------------------------------------------------------
    @property
    def state(self) -> Dict[str, Any]:
        """Прямой доступ к состоянию (для обратной совместимости)"""
        return self.state_manager.state
    
    @property
    def _defaults(self) -> Dict[str, Any]:
        """Доступ к дефолтам (для обратной совместимости)"""
        return self.state_manager._defaults
    
    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        """Обработка закрытия панели"""
        self.logger.info("🛑 GraphicsPanel closing, saving state...")
        try:
            self.save_settings()
        except Exception as e:
            self.logger.error(f"Failed to auto-save settings on close: {e}")
        
        try:
            report_path = self.graphics_logger.export_analysis_report()
            self.logger.info(f"   ✅ Analysis report saved: {report_path}")
        except Exception as e:
            self.logger.error(f"   ❌ Failed to export analysis: {e}")
        
        super().closeEvent(event)
