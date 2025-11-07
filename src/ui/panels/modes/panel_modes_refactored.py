"""
ModesPanel refactored - Координатор вкладок
Тонкий координатор для управления режимами симуляции
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QSizePolicy
from PySide6.QtCore import Signal

from .state_manager import ModesStateManager
from .control_tab import ControlTab
from .simulation_tab import SimulationTab
from .physics_tab import PhysicsTab
from .road_excitation_tab import RoadExcitationTab


class ModesPanel(QWidget):
    """Панель режимов симуляции - REFACTORED VERSION

    Тонкий координатор с делегированием функциональности в специализированные вкладки.
    """

    # ===============================================================
    # SIGNALS (сохраняем совместимость с оригиналом)
    # ===============================================================

    simulation_control = Signal(str)  # "start", "stop", "reset", "pause"
    mode_changed = Signal(str, str)  # mode_type, new_mode
    parameter_changed = Signal(str, float)  # parameter_name, new_value
    physics_options_changed = Signal(dict)  # Physics option toggles
    animation_changed = Signal(dict)  # Animation parameters changed

    def __init__(self, parent=None):
        super().__init__(parent)

        # State manager
        self.state_manager = ModesStateManager()

        # Create UI
        self._setup_ui()

        # Connect tab signals
        self._connect_tab_signals()

        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        print("✅ ModesPanel (refactored): Инициализация завершена")

    def _setup_ui(self):
        """Создать UI с вкладками"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Create tabs
        self.control_tab = ControlTab(self.state_manager)
        self.simulation_tab = SimulationTab(self.state_manager)
        self.physics_tab = PhysicsTab(self.state_manager)
        self.road_tab = RoadExcitationTab(self.state_manager)

        # Add tabs
        self.tabs.addTab(self.control_tab, "🎮 Управление")
        self.tabs.addTab(self.simulation_tab, "⚙️ Режим")
        self.tabs.addTab(self.physics_tab, "🔧 Физика")
        self.tabs.addTab(self.road_tab, "🛣️ Дорога")

        layout.addWidget(self.tabs)

    def _connect_tab_signals(self):
        """Подключить сигналы вкладок к сигналам панели"""
        # Control tab
        self.control_tab.simulation_control.connect(self._on_simulation_control)

        # Simulation tab
        self.simulation_tab.mode_changed.connect(self._on_mode_changed)
        self.simulation_tab.preset_changed.connect(self._on_preset_changed)

        # Physics tab
        self.physics_tab.physics_options_changed.connect(
            self._on_physics_options_changed
        )

        # Road tab
        self.road_tab.parameter_changed.connect(self._on_parameter_changed)
        self.road_tab.animation_changed.connect(self._on_animation_changed)

    # ===============================================================
    # SIGNAL HANDLERS (транслируем сигналы от вкладок)
    # ===============================================================

    def _on_simulation_control(self, command: str):
        """Обработать команду управления симуляцией"""
        print(f"🎮 ModesPanel: Команда управления '{command}'")

        # Update UI state based on command
        if command == "start":
            self._set_running_state(True)
        elif command in ["stop", "pause", "reset"]:
            self._set_running_state(False)

        # Emit signal
        self.simulation_control.emit(command)

    def _on_mode_changed(self, mode_type: str, new_mode: str):
        """Обработать изменение режима"""
        print(f"⚙️ ModesPanel: Режим '{mode_type}' изменён на '{new_mode}'")
        self.mode_changed.emit(mode_type, new_mode)

    def _on_preset_changed(self, preset_index: int):
        """Обработать изменение пресета"""
        print(f"📋 ModesPanel: Применён пресет #{preset_index}")

        # Update physics tab from state
        self.physics_tab._apply_current_state()

    def _on_physics_options_changed(self, options: dict):
        """Обработать изменение опций физики"""
        print(f"🔧 ModesPanel: Опции физики обновлены: {options}")
        self.physics_options_changed.emit(options)

    def _on_parameter_changed(self, param_name: str, value: float):
        """Обработать изменение параметра"""
        # print(f"🔧 ModesPanel: Параметр '{param_name}' = {value}")
        self.parameter_changed.emit(param_name, value)

    def _on_animation_changed(self, params: dict):
        """Обработать изменение параметров анимации"""
        print("🎬 ModesPanel: Параметры анимации обновлены")
        self.animation_changed.emit(params)

    def _set_running_state(self, running: bool):
        """Обновить состояние UI в зависимости от статуса симуляции"""
        self.control_tab.set_simulation_running(running)
        self.simulation_tab.set_enabled_for_running(running)
        self.physics_tab.set_enabled_for_running(running)

    # ===============================================================
    # PUBLIC API (совместимость с оригинальным ModesPanel)
    # ===============================================================

    def get_parameters(self) -> dict:
        """Получить текущие параметры"""
        return self.state_manager.get_parameters()

    def get_physics_options(self) -> dict:
        """Получить текущие опции физики"""
        return self.state_manager.get_physics_options()

    def set_simulation_running(self, running: bool):
        """Установить состояние симуляции извне"""
        self._set_running_state(running)

    def validate_state(self):
        """Валидация текущего состояния"""
        errors = self.state_manager.validate_state()
        if errors:
            print("⚠️ ModesPanel: Найдены ошибки валидации:")
            for error in errors:
                print(f"   • {error}")
        return errors
