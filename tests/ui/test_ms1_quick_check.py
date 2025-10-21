#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Быстрая проверка МШ-1: Изменения геометрии цилиндра
"""

import sys
from PySide6.QtWidgets import QApplication

# Создать приложение
app = QApplication.instance() or QApplication(sys.argv)

# Импортировать панель
from src.ui.panels.panel_geometry import GeometryPanel

print("=" * 60)
print("МШ-1: ПРОВЕРКА ИЗМЕНЕНИЙ ГЕОМЕТРИИ ЦИЛИНДРА")
print("=" * 60)

# Создать панель
panel = GeometryPanel()

# Проверка1: Наличие новых слайдеров
print("\n? ПРОВЕРКА1: Новые слайдеры")
print(f" cyl_diam_m_slider: {hasattr(panel, 'cyl_diam_m_slider')}")
print(f" stroke_m_slider: {hasattr(panel, 'stroke_m_slider')}")
print(f" dead_gap_m_slider: {hasattr(panel, 'dead_gap_m_slider')}")

# Проверка2: Отсутствие старых слайдеров
print("\n? ПРОВЕРКА2: Старые слайдеры удалены")
print(f" bore_head_slider: {not hasattr(panel, 'bore_head_slider')} (должно бытьTrue)")
print(f" bore_rod_slider: {not hasattr(panel, 'bore_rod_slider')} (должно бытьTrue)")

# Проверка3: Параметры слайдеров
if hasattr(panel, 'cyl_diam_m_slider'):
    print("\n?? ПРОВЕРКА3a: Параметры cyl_diam_m_slider")
    slider = panel.cyl_diam_m_slider
    print(f" minimum: {slider.minimum()} (ожидается0.030)")
    print(f" maximum: {slider.maximum()} (ожидается0.150)")
    print(f" value: {slider.value()} (ожидается0.080)")
    print(f" step: {slider.step()} (ожидается0.001)")
    print(f" decimals: {slider.decimals()} (ожидается3)")
    print(f" units: '{slider.units()}' (ожидается'м')")

if hasattr(panel, 'stroke_m_slider'):
    print("\n?? ПРОВЕРКА3b: Параметры stroke_m_slider")
    slider = panel.stroke_m_slider
    print(f" minimum: {slider.minimum()} (ожидается0.100)")
    print(f" maximum: {slider.maximum()} (ожидается0.500)")
    print(f" value: {slider.value()} (ожидается0.300)")
    print(f" step: {slider.step()} (ожидается0.001)")
    print(f" decimals: {slider.decimals()} (ожидается3)")
    print(f" units: '{slider.units()}' (ожидается'м')")

if hasattr(panel, 'dead_gap_m_slider'):
    print("\n?? ПРОВЕРКА3c: Параметры dead_gap_m_slider")
    slider = panel.dead_gap_m_slider
    print(f" minimum: {slider.minimum()} (ожидается0.000)")
    print(f" maximum: {slider.maximum()} (ожидается0.020)")
    print(f" value: {slider.value()} (ожидается0.005)")
    print(f" step: {slider.step()} (ожидается0.001)")
    print(f" decimals: {slider.decimals()} (ожидается3)")
    print(f" units: '{slider.units()}' (ожидается'м')")

# Проверка4: Параметры в словаре
print("\n?? ПРОВЕРКА4: Параметры в словаре")
params = panel.get_parameters()
print(f" 'cyl_diam_m' в parameters: {('cyl_diam_m' in params)} = {params.get('cyl_diam_m', 'НЕ НАЙДЕНО')}")
print(f" 'stroke_m' в parameters: {('stroke_m' in params)} = {params.get('stroke_m', 'НЕ НАЙДЕНО')}")
print(f" 'dead_gap_m' в parameters: {('dead_gap_m' in params)} = {params.get('dead_gap_m', 'НЕ НАЙДЕНО')}")
print(f" 'bore_head' ОТСУТСТВУЕТ: {('bore_head' not in params)} (должно бытьTrue)")
print(f" 'bore_rod' ОТСУТСТВУЕТ: {('bore_rod' not in params)} (должно бытьTrue)")

# Итоговая проверка
print("\n" + "=" * 60)
all_checks = [
    hasattr(panel, 'cyl_diam_m_slider'),
    hasattr(panel, 'stroke_m_slider'),
    hasattr(panel, 'dead_gap_m_slider'),
    not hasattr(panel, 'bore_head_slider'),
    not hasattr(panel, 'bore_rod_slider'),
    'cyl_diam_m' in params,
    'stroke_m' in params,
    'dead_gap_m' in params,
    'bore_head' not in params,
    'bore_rod' not in params,
]

if all(all_checks):
    print("?? МШ-1: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)
    sys.exit(0)
else:
    print("? МШ-1: НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
    print(f" Пройдено: {sum(all_checks)}/{len(all_checks)}")
    print("=" * 60)
    sys.exit(1)
