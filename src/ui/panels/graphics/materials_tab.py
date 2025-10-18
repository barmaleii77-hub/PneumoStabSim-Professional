# -*- coding: utf-8 -*-
"""
Materials Tab - вкладка настроек PBR материалов всех компонентов
Part of modular GraphicsPanel restructuring

СТРУКТУРА ТОЧНО ПОВТОРЯЕТ МОНОЛИТ panel_graphics.py (строки 1373-1520):
- Селектор компонента (ComboBox) - 8 материалов
- Единая форма с ПОЛНЫМ набором PBR параметров (17 параметров):
  * base_color, metalness, roughness, specular, specular_tint
  * clearcoat, clearcoat_roughness
  * transmission, opacity, ior
  * attenuation_distance, attenuation_color
  * emissive_color, emissive_intensity
  * warning_color, ok_color, error_color
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel,
    QComboBox, QHBoxLayout, QGridLayout
)
from PySide6.QtCore import Signal
from typing import Dict, Any

from .widgets import ColorButton, LabeledSlider


class MaterialsTab(QWidget):
    """Вкладка настроек материалов: 8 компонентов с полным PBR набором
    
    Signals:
        material_changed: Dict[str, Any] - параметры материалов изменились
    """
    
    material_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Контролы UI
        self._controls: Dict[str, Any] = {}
        self._updating_ui = False
        
        # Названия материалов - ТОЧНО КАК В МОНОЛИТЕ
        self._material_labels = {
            "frame": "Рама",
            "lever": "Рычаг",
            "tail": "Хвостовик",
            "cylinder": "Цилиндр (стекло)",
            "piston_body": "Корпус поршня",
            "piston_rod": "Шток",
            "joint_tail": "Шарнир хвостовика",
            "joint_arm": "Шарнир рычага",
        }
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Построить UI вкладки - ТОЧНО КАК В МОНОЛИТЕ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # ✅ ТОЧНО КАК В МОНОЛИТЕ - селектор компонента
        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Компонент", self))
        self._material_selector = QComboBox(self)
        for key, label in self._material_labels.items():
            self._material_selector.addItem(label, key)
        self._material_selector.currentIndexChanged.connect(self._on_material_selection_changed)
        selector_row.addWidget(self._material_selector, 1)
        selector_row.addStretch(1)
        layout.addLayout(selector_row)
        
        # ✅ ТОЧНО КАК В МОНОЛИТЕ - группа параметров материала
        group = QGroupBox("Параметры материала", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        
        row = 0
        
        # Base color
        row = self._add_color_control(grid, row, "Базовый цвет", "base_color")
        
        # Metalness
        row = self._add_slider_control(grid, row, "Металличность", "metalness", 0.0, 1.0, 0.01)
        
        # Roughness
        row = self._add_slider_control(grid, row, "Шероховатость", "roughness", 0.0, 1.0, 0.01)
        
        # Specular
        row = self._add_slider_control(grid, row, "Specular", "specular", 0.0, 1.0, 0.01)
        
        # Specular Tint
        row = self._add_slider_control(grid, row, "Specular Tint", "specular_tint", 0.0, 1.0, 0.01)
        
        # Clearcoat
        row = self._add_slider_control(grid, row, "Clearcoat", "clearcoat", 0.0, 1.0, 0.01)
        
        # Clearcoat roughness
        row = self._add_slider_control(grid, row, "Шероховатость лака", "clearcoat_roughness", 0.0, 1.0, 0.01)
        
        # Transmission
        row = self._add_slider_control(grid, row, "Пропускание", "transmission", 0.0, 1.0, 0.01)
        
        # Opacity
        row = self._add_slider_control(grid, row, "Непрозрачность", "opacity", 0.0, 1.0, 0.01)
        
        # Index of Refraction
        row = self._add_slider_control(grid, row, "Index of Refraction", "ior", 1.0, 3.0, 0.01)
        
        # Attenuation distance
        row = self._add_slider_control(grid, row, "Attenuation distance", "attenuation_distance", 0.0, 10000.0, 10.0, decimals=1)
        
        # Attenuation color
        row = self._add_color_control(grid, row, "Attenuation color", "attenuation_color")
        
        # Emissive color
        row = self._add_color_control(grid, row, "Излучающий цвет", "emissive_color")
        
        # Emissive intensity
        row = self._add_slider_control(grid, row, "Яркость излучения", "emissive_intensity", 0.0, 5.0, 0.05)
        
        # Warning color
        row = self._add_color_control(grid, row, "Цвет предупреждения", "warning_color")
        
        # OK color
        row = self._add_color_control(grid, row, "Цвет OK", "ok_color")
        
        # Error color
        row = self._add_color_control(grid, row, "Цвет ошибки", "error_color")
        
        layout.addWidget(group)
        layout.addStretch(1)
    
    def _add_color_control(self, grid: QGridLayout, row: int, title: str, key: str) -> int:
        """Добавить контрол выбора цвета"""
        container = QWidget(self)
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(6)
        hbox.addWidget(QLabel(title, self))
        button = ColorButton()
        button.color_changed.connect(lambda c: self._on_control_changed(key, c))
        self._controls[key] = button
        hbox.addWidget(button)
        hbox.addStretch(1)
        grid.addWidget(container, row, 0, 1, 2)
        return row + 1
    
    def _add_slider_control(
        self,
        grid: QGridLayout,
        row: int,
        title: str,
        key: str,
        minimum: float,
        maximum: float,
        step: float,
        *,
        decimals: int = 2,
    ) -> int:
        """Добавить контрол слайдера"""
        slider = LabeledSlider(title, minimum, maximum, step, decimals=decimals)
        slider.valueChanged.connect(lambda v: self._on_control_changed(key, v))
        self._controls[key] = slider
        grid.addWidget(slider, row, 0, 1, 2)
        return row + 1
    
    # ========== ОБРАБОТЧИКИ ИЗМЕНЕНИЙ ==========
    
    def _on_material_selection_changed(self) -> None:
        """Обработчик изменения выбранного материала - КАК В МОНОЛИТЕ"""
        # Этот метод вызывается при смене материала в селекторе
        # НЕ эмитим сигнал, только обновляем UI (если нужно загрузить состояние извне)
        pass
    
    def _on_control_changed(self, key: str, value: Any) -> None:
        """Обработчик изменения любого контрола"""
        if self._updating_ui:
            return
        
        # Эмитим сигнал с полным состоянием ВСЕХ материалов
        self.material_changed.emit(self.get_state())
    
    # ========== ГЕТТЕРЫ/СЕТТЕРЫ СОСТОЯНИЯ ==========
    
    def get_current_material_key(self) -> str:
        """Получить ключ текущего выбранного материала"""
        return self._material_selector.currentData()
    
    def get_current_material_state(self) -> Dict[str, Any]:
        """Получить состояние ТЕКУЩЕГО выбранного материала
        
        Returns:
            Словарь с параметрами одного материала (17 параметров)
        """
        return {
            "base_color": self._controls["base_color"].color().name(),
            "metalness": self._controls["metalness"].value(),
            "roughness": self._controls["roughness"].value(),
            "specular": self._controls["specular"].value(),
            "specular_tint": self._controls["specular_tint"].value(),
            "clearcoat": self._controls["clearcoat"].value(),
            "clearcoat_roughness": self._controls["clearcoat_roughness"].value(),
            "transmission": self._controls["transmission"].value(),
            "opacity": self._controls["opacity"].value(),
            "ior": self._controls["ior"].value(),
            "attenuation_distance": self._controls["attenuation_distance"].value(),
            "attenuation_color": self._controls["attenuation_color"].color().name(),
            "emissive_color": self._controls["emissive_color"].color().name(),
            "emissive_intensity": self._controls["emissive_intensity"].value(),
            "warning_color": self._controls["warning_color"].color().name(),
            "ok_color": self._controls["ok_color"].color().name(),
            "error_color": self._controls["error_color"].color().name(),
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Получить полное состояние ВСЕХ материалов
        
        Возвращает структуру:
        {
            "current_material": "frame",  # текущий выбранный материал
            "materials": {
                "frame": {...},  # 17 параметров
                "lever": {...},
                ...
            }
        }
        """
        # Эмитим только состояние ТЕКУЩЕГО материала и его ключ
        current_key = self.get_current_material_key()
        current_state = self.get_current_material_state()
        
        return {
            "current_material": current_key,
            current_key: current_state,
        }
    
    def set_material_state(self, material_key: str, state: Dict[str, Any]):
        """Установить состояние ОДНОГО материала
        
        Args:
            material_key: Ключ материала (frame, lever, tail, ...)
            state: Словарь с параметрами материала
        """
        # Переключаемся на нужный материал
        index = self._material_selector.findData(material_key)
        if index >= 0:
            self._material_selector.setCurrentIndex(index)
        
        # Блокируем сигналы
        self._updating_ui = True
        for control in self._controls.values():
            try:
                control.blockSignals(True)
            except:
                pass
        
        try:
            # Устанавливаем параметры
            if "base_color" in state:
                self._controls["base_color"].set_color(state["base_color"])
            if "metalness" in state:
                self._controls["metalness"].set_value(state["metalness"])
            if "roughness" in state:
                self._controls["roughness"].set_value(state["roughness"])
            if "specular" in state:
                self._controls["specular"].set_value(state["specular"])
            if "specular_tint" in state:
                self._controls["specular_tint"].set_value(state["specular_tint"])
            if "clearcoat" in state:
                self._controls["clearcoat"].set_value(state["clearcoat"])
            if "clearcoat_roughness" in state:
                self._controls["clearcoat_roughness"].set_value(state["clearcoat_roughness"])
            if "transmission" in state:
                self._controls["transmission"].set_value(state["transmission"])
            if "opacity" in state:
                self._controls["opacity"].set_value(state["opacity"])
            if "ior" in state:
                self._controls["ior"].set_value(state["ior"])
            if "attenuation_distance" in state:
                self._controls["attenuation_distance"].set_value(state["attenuation_distance"])
            if "attenuation_color" in state:
                self._controls["attenuation_color"].set_color(state["attenuation_color"])
            if "emissive_color" in state:
                self._controls["emissive_color"].set_color(state["emissive_color"])
            if "emissive_intensity" in state:
                self._controls["emissive_intensity"].set_value(state["emissive_intensity"])
            if "warning_color" in state:
                self._controls["warning_color"].set_color(state["warning_color"])
            if "ok_color" in state:
                self._controls["ok_color"].set_color(state["ok_color"])
            if "error_color" in state:
                self._controls["error_color"].set_color(state["error_color"])
        
        finally:
            # Разблокируем сигналы
            for control in self._controls.values():
                try:
                    control.blockSignals(False)
                except:
                    pass
            self._updating_ui = False
    
    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря
        
        Args:
            state: Словарь со ВСЕМИ материалами
            Формат: {"frame": {...}, "lever": {...}, ...}
        """
        # Устанавливаем каждый материал
        for material_key, material_state in state.items():
            if material_key in self._material_labels:
                self.set_material_state(material_key, material_state)
    
    def get_controls(self) -> Dict[str, Any]:
        """Получить словарь контролов для внешнего управления"""
        return self._controls
    
    def set_updating_ui(self, updating: bool) -> None:
        """Установить флаг обновления UI"""
        self._updating_ui = updating
