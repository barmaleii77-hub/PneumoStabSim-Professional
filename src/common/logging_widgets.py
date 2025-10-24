"""
Logging wrappers for all Qt UI widgets
Automatically logs user interactions BEFORE handlers are called
"""

from __future__ import annotations


from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QSlider, QDoubleSpinBox

from src.common.event_logger import get_event_logger


class LoggingCheckBox(QCheckBox):
    """QCheckBox с автоматическим логированием кликов"""

    def __init__(self, text: str, widget_name: str, parent=None):
        super().__init__(text, parent)
        self.widget_name = widget_name
        self.event_logger = get_event_logger()

        # Подключаем логирование ДО пользовательских обработчиков
        self.stateChanged.connect(
            self._on_state_changed_with_logging, Qt.ConnectionType.DirectConnection
        )

    def _on_state_changed_with_logging(self, state: int):
        """Внутренний обработчик с логированием"""
        checked = state == Qt.CheckState.Checked

        # ✅ Логируем КЛИК
        self.event_logger.log_user_click(
            widget_name=self.widget_name,
            widget_type="QCheckBox",
            value=checked,
            text=self.text(),
        )


class LoggingComboBox(QComboBox):
    """QComboBox с автоматическим логированием выбора"""

    def __init__(self, widget_name: str, parent=None):
        super().__init__(parent)
        self.widget_name = widget_name
        self.event_logger = get_event_logger()
        self._previous_value = None

        # Подключаем логирование
        self.currentIndexChanged.connect(
            self._on_index_changed_with_logging, Qt.ConnectionType.DirectConnection
        )

    def _on_index_changed_with_logging(self, index: int):
        """Внутренний обработчик с логированием"""
        new_value = self.currentData()

        # ✅ Логируем ВЫБОР
        self.event_logger.log_user_combo(
            combo_name=self.widget_name,
            old_value=self._previous_value,
            new_value=new_value,
            index=index,
            text=self.currentText(),
        )

        self._previous_value = new_value


class LoggingSlider(QSlider):
    """QSlider с автоматическим логированием изменений"""

    # ✅ Собственный сигнал для value changes
    valueChangedWithLogging = Signal(int)

    def __init__(self, widget_name: str, orientation, parent=None):
        super().__init__(orientation, parent)
        self.widget_name = widget_name
        self.event_logger = get_event_logger()
        self._previous_value = None

        # Подключаем логирование
        self.valueChanged.connect(
            self._on_value_changed_with_logging, Qt.ConnectionType.DirectConnection
        )

    def _on_value_changed_with_logging(self, value: int):
        """Внутренний обработчик с логированием"""
        # ✅ Логируем ИЗМЕНЕНИЕ
        self.event_logger.log_user_slider(
            slider_name=self.widget_name,
            old_value=self._previous_value,
            new_value=value,
            minimum=self.minimum(),
            maximum=self.maximum(),
        )

        self._previous_value = value

        # Эмитим собственный сигнал
        self.valueChangedWithLogging.emit(value)


class LoggingDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox с автоматическим логированием"""

    valueChangedWithLogging = Signal(float)

    def __init__(self, widget_name: str, parent=None):
        super().__init__(parent)
        self.widget_name = widget_name
        self.event_logger = get_event_logger()
        self._previous_value = None

        # Подключаем логирование
        self.valueChanged.connect(
            self._on_value_changed_with_logging, Qt.ConnectionType.DirectConnection
        )

    def _on_value_changed_with_logging(self, value: float):
        """Внутренний обработчик с логированием"""
        # ✅ Логируем ИЗМЕНЕНИЕ
        self.event_logger.log_user_slider(
            slider_name=self.widget_name,
            old_value=self._previous_value,
            new_value=value,
            minimum=self.minimum(),
            maximum=self.maximum(),
        )

        self._previous_value = value
        self.valueChangedWithLogging.emit(value)
