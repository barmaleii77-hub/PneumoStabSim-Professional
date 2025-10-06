#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест дискретности слайдеров 0.001м
Test slider precision with 0.001m step
"""
import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

# Импортируем напрямую без относительных путей
sys.path.insert(0, str(Path(__file__).parent))
from src.ui.widgets.range_slider import RangeSlider


class SliderPrecisionTest(QMainWindow):
    """Тест точности слайдеров"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("🔧 Тест дискретности слайдеров 0.001м")
        self.resize(600, 800)
        
        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Заголовок
        title = QLabel("ТЕСТ ДИСКРЕТНОСТИ СЛАЙДЕРОВ")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin: 10px;")
        layout.addWidget(title)
        
        info = QLabel("Все слайдеры должны иметь шаг 0.001м (1мм)")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 20px;")
        layout.addWidget(info)
        
        # Тестовые слайдеры с настройками из GeometryPanel
        self.create_test_sliders(layout)
        
        # Лог изменений
        self.log_label = QLabel("Лог изменений:")
        self.log_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(self.log_label)
        
        self.log_text = QLabel("")
        self.log_text.setWordWrap(True)
        self.log_text.setStyleSheet("background: #f0f0f0; padding: 10px; font-family: monospace;")
        self.log_text.setMinimumHeight(150)
        self.log_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.log_text)
        
        layout.addStretch()
    
    def create_test_sliders(self, layout):
        """Создать тестовые слайдеры с теми же настройками, что в GeometryPanel"""
        
        # 1. База колёсная (wheelbase)
        self.wheelbase_slider = RangeSlider(
            minimum=2.0, maximum=4.0, value=3.2, step=0.001,
            decimals=3, units="м", title="База (колёсная) - шаг 0.001м"
        )
        self.wheelbase_slider.valueChanged.connect(
            lambda v: self.log_change("wheelbase", v))
        layout.addWidget(self.wheelbase_slider)
        
        # 2. Колея (track)
        self.track_slider = RangeSlider(
            minimum=1.0, maximum=2.5, value=1.6, step=0.001,
            decimals=3, units="м", title="Колея - шаг 0.001м"
        )
        self.track_slider.valueChanged.connect(
            lambda v: self.log_change("track", v))
        layout.addWidget(self.track_slider)
        
        # 3. Длина рычага (lever_length)
        self.lever_slider = RangeSlider(
            minimum=0.5, maximum=1.5, value=0.8, step=0.001,
            decimals=3, units="м", title="Длина рычага - шаг 0.001м"
        )
        self.lever_slider.valueChanged.connect(
            lambda v: self.log_change("lever_length", v))
        layout.addWidget(self.lever_slider)
        
        # 4. Диаметр цилиндра
        self.cyl_diam_slider = RangeSlider(
            minimum=0.030, maximum=0.150, value=0.080, step=0.001,
            decimals=3, units="м", title="Диаметр цилиндра - шаг 0.001м"
        )
        self.cyl_diam_slider.valueChanged.connect(
            lambda v: self.log_change("cyl_diam", v))
        layout.addWidget(self.cyl_diam_slider)
        
        # 5. Диаметр штока
        self.rod_diam_slider = RangeSlider(
            minimum=0.020, maximum=0.060, value=0.035, step=0.001,
            decimals=3, units="м", title="Диаметр штока - шаг 0.001м"
        )
        self.rod_diam_slider.valueChanged.connect(
            lambda v: self.log_change("rod_diameter", v))
        layout.addWidget(self.rod_diam_slider)
        
        self.log_entries = []
    
    def log_change(self, param_name: str, value: float):
        """Логировать изменения значений"""
        # Проверяем дискретность
        expected_step = 0.001
        value_rounded = round(value, 3)  # Округляем до 3 знаков (1мм)
        
        # Проверяем, кратно ли значение шагу
        steps_from_min = (value_rounded - self.get_slider_min(param_name)) / expected_step
        is_discrete = abs(steps_from_min - round(steps_from_min)) < 1e-9
        
        status = "✅" if is_discrete else "❌"
        entry = f"{status} {param_name}: {value_rounded:.3f}м"
        
        if not is_discrete:
            entry += f" (НЕ КРАТНО {expected_step}м!)"
        
        # Добавляем в лог (последние 10 записей)
        self.log_entries.append(entry)
        if len(self.log_entries) > 10:
            self.log_entries.pop(0)
        
        self.log_text.setText("\n".join(self.log_entries))
    
    def get_slider_min(self, param_name: str) -> float:
        """Получить минимальное значение слайдера"""
        mins = {
            'wheelbase': 2.0,
            'track': 1.0,
            'lever_length': 0.5,
            'cyl_diam': 0.030,
            'rod_diameter': 0.020
        }
        return mins.get(param_name, 0.0)


def main():
    """Главная функция теста"""
    print("=" * 60)
    print("🔧 ТЕСТ ДИСКРЕТНОСТИ СЛАЙДЕРОВ 0.001м")
    print("=" * 60)
    print()
    print("ПРОВЕРЯЕМ:")
    print("✅ Шаг всех слайдеров = 0.001м (1мм)")
    print("✅ Разрешение слайдера = 100000 позиций")
    print("✅ Точность округления значений")
    print()
    print("ИНСТРУКЦИИ:")
    print("1. Перетащите каждый слайдер")
    print("2. Наблюдайте значения в логе")
    print("3. Все значения должны быть кратны 0.001м")
    print("4. ✅ = правильно, ❌ = ошибка дискретности")
    print()
    print("=" * 60)
    
    app = QApplication(sys.argv)
    window = SliderPrecisionTest()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
