# -*- coding: utf-8 -*-
"""
Control tab for ModesPanel
Вкладка управления симуляцией (Play/Pause/Stop/Reset)
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QLabel,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from .state_manager import ModesStateManager


class ControlTab(QWidget):
    """Вкладка управления симуляцией"""

    # Signals
    simulation_control = Signal(str)  # "start", "stop", "pause", "reset"

    def __init__(self, state_manager: ModesStateManager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self._simulation_running = False
        self._setup_ui()

    def _setup_ui(self):
        """Создать UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Title
        title_label = QLabel("Управление симуляцией")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Control buttons group
        control_group = self._create_control_group()
        layout.addWidget(control_group)

        # Status info
        status_group = self._create_status_group()
        layout.addWidget(status_group)

        layout.addStretch()

    def _create_control_group(self) -> QGroupBox:
        """Создать группу кнопок управления"""
        group = QGroupBox("Основные команды")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Main control buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.start_button = QPushButton("▶ Старт")
        self.stop_button = QPushButton("⏹ Стоп")
        self.pause_button = QPushButton("⏸ Пауза")
        self.reset_button = QPushButton("🔄 Сброс")

        # Style buttons
        for btn in [
            self.start_button,
            self.stop_button,
            self.pause_button,
            self.reset_button,
        ]:
            btn.setMinimumHeight(35)
            font = btn.font()
            font.setPointSize(10)
            btn.setFont(font)

        # Tooltips
        self.start_button.setToolTip("Запустить симуляцию (Space)")
        self.stop_button.setToolTip("Остановить симуляцию")
        self.pause_button.setToolTip("Приостановить симуляцию (Space)")
        self.reset_button.setToolTip("Сбросить симуляцию к начальному состоянию (R)")

        # Connect signals
        self.start_button.clicked.connect(lambda: self._on_control("start"))
        self.stop_button.clicked.connect(lambda: self._on_control("stop"))
        self.pause_button.clicked.connect(lambda: self._on_control("pause"))
        self.reset_button.clicked.connect(lambda: self._on_control("reset"))

        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.reset_button)

        layout.addLayout(buttons_layout)

        # Initial state
        self._update_button_states()

        return group

    def _create_status_group(self) -> QGroupBox:
        """Создать группу информации о статусе"""
        group = QGroupBox("Статус")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        self.status_label = QLabel("⏸ Остановлено")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(10)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        layout.addWidget(self.status_label)

        # Info text
        info_label = QLabel(
            "Используйте кнопки выше для управления симуляцией.\n"
            "Горячие клавиши: Space - старт/пауза, R - сброс"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888888;")
        info_font = QFont()
        info_font.setPointSize(8)
        info_label.setFont(info_font)
        layout.addWidget(info_label)

        return group

    def _on_control(self, command: str):
        """Обработать команду управления"""
        print(f"🎮 ControlTab: Команда '{command}'")

        # Update internal state
        if command == "start":
            self._simulation_running = True
            self.status_label.setText("▶ Запущено")
        elif command == "stop":
            self._simulation_running = False
            self.status_label.setText("⏹ Остановлено")
        elif command == "pause":
            self._simulation_running = False
            self.status_label.setText("⏸ Пауза")
        elif command == "reset":
            self._simulation_running = False
            self.status_label.setText("🔄 Сброс...")

        # Update button states
        self._update_button_states()

        # Emit signal
        self.simulation_control.emit(command)

    def _update_button_states(self):
        """Обновить состояние кнопок в зависимости от статуса симуляции"""
        self.start_button.setEnabled(not self._simulation_running)
        self.stop_button.setEnabled(self._simulation_running)
        self.pause_button.setEnabled(self._simulation_running)
        self.reset_button.setEnabled(not self._simulation_running)

    def set_simulation_running(self, running: bool):
        """Установить статус симуляции извне"""
        self._simulation_running = running
        self._update_button_states()

        if running:
            self.status_label.setText("▶ Запущено")
        else:
            self.status_label.setText("⏹ Остановлено")
