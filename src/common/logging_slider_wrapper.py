"""
Logging wrapper for LabeledSlider in panel_graphics.py
Wraps existing LabeledSlider to add automatic event logging
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from src.common.event_logger import get_event_logger


class LoggingLabeledSlider:
    """
    Wrapper для LabeledSlider с автоматическим логированием

    Использование:
        slider = LabeledSlider("Яркость", 0.0, 1.0, 0.01)
        logging_slider = LoggingLabeledSlider(slider, "brightness")
        slider.valueChanged.connect(handler)  # Подключаемся к ОРИГИНАЛЬНОМУ слайдеру
    """

    def __init__(self, wrapped_slider, widget_name: str):
        """
        Args:
            wrapped_slider: Экземпляр LabeledSlider
            widget_name: Имя виджета для логирования (например, "key.brightness")
        """
        self._slider = wrapped_slider
        self.widget_name = widget_name
        self.event_logger = get_event_logger()
        self._previous_value: Optional[float] = None

        # ✅ ИСПРАВЛЕНО: Подключаем внутренний обработчик к ОРИГИНАЛЬНОМУ слайдеру
        self._slider.valueChanged.connect(self._on_value_changed_with_logging)

    def _on_value_changed_with_logging(self, value: float):
        """Внутренний обработчик с логированием"""
        # ✅ Логируем ИЗМЕНЕНИЕ СЛАЙДЕРА
        self.event_logger.log_user_slider(
            slider_name=self.widget_name,
            old_value=self._previous_value
            if self._previous_value is not None
            else value,
            new_value=value,
            title=self._slider._title,
            unit=self._slider._unit,
        )

        self._previous_value = value

        # ⚠️ НЕ эмитим свой сигнал - логирование уже произошло
        # Пользовательский обработчик получит событие от ОРИГИНАЛЬНОГО слайдера

    # Пробрасываем методы исходного слайдера
    def set_value(self, value: float) -> None:
        """Установить значение (без логирования - это не действие пользователя)"""
        self._slider.set_value(value)

    def value(self) -> float:
        """Получить текущее значение"""
        return self._slider.value()

    def set_enabled(self, enabled: bool) -> None:
        """Включить/выключить слайдер"""
        self._slider.set_enabled(enabled)

    def __getattr__(self, name: str):
        """Проброс остальных атрибутов к исходному слайдеру"""
        return getattr(self._slider, name)


class LoggingColorButton:
    """
    Wrapper для ColorButton с автоматическим логированием
    """

    def __init__(self, wrapped_button, widget_name: str):
        """
        Args:
            wrapped_button: Экземпляр ColorButton
            widget_name: Имя виджета для логирования
        """
        self._button = wrapped_button
        self.widget_name = widget_name
        self.event_logger = get_event_logger()
        self._previous_color: Optional[str] = None

        # Пробрасываем сигнал с логированием
        self.color_changed = Signal(str)

        # Подключаем внутренний обработчик
        self._button.color_changed.connect(self._on_color_changed_with_logging)

    def _on_color_changed_with_logging(self, color: str):
        """Внутренний обработчик с логированием"""
        # ✅ Логируем ВЫБОР ЦВЕТА
        self.event_logger.log_user_color(
            color_name=self.widget_name,
            old_color=self._previous_color
            if self._previous_color is not None
            else color,
            new_color=color,
        )

        self._previous_color = color

    # Пробрасываем методы
    def set_color(self, color_str: str) -> None:
        """Установить цвет (без логирования)"""
        self._button.set_color(color_str)

    def color(self):
        """Получить текущий цвет"""
        return self._button.color()

    def __getattr__(self, name: str):
        """Проброс остальных атрибутов"""
        return getattr(self._button, name)


def create_logging_slider(
    title: str,
    minimum: float,
    maximum: float,
    step: float,
    widget_name: str,
    *,
    decimals: int = 2,
    unit: str | None = None,
    parent: QWidget | None = None,
):
    """
    Фабрика для создания LabeledSlider с логированием

    Usage:
        slider = create_logging_slider(
            "Яркость", 0.0, 1.0, 0.01,
            widget_name="key.brightness",
            decimals=2,
            parent=self
        )
        slider.valueChanged.connect(lambda v: self._update_lighting("key", "brightness", v))

    Returns:
        Tuple[LabeledSlider, LoggingLabeledSlider] - (исходный слайдер, wrapper с логированием)
    """
    # ⚠️ Важно: импортируем здесь, чтобы избежать циклических импортов
    from src.ui.panels.panel_graphics import LabeledSlider

    # Создаем исходный слайдер
    base_slider = LabeledSlider(
        title, minimum, maximum, step, decimals=decimals, unit=unit, parent=parent
    )

    # Оборачиваем в logging wrapper
    logging_wrapper = LoggingLabeledSlider(base_slider, widget_name)

    # ✅ ИСПРАВЛЕНО: НЕ подключаем сигналы здесь - это сделает сам wrapper
    # Пользователь подключится к base_slider.valueChanged напрямую
    # (логирование уже произойдет внутри wrapper'а)

    return base_slider, logging_wrapper
