#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправления для панели графики - размеры и компоновка
Graphics panel layout fixes
"""

def fix_graphics_panel_layout():
    """Применить исправления к GraphicsPanel"""
    
    # В методе setup_ui() GraphicsPanel:
    
    # 1. Установить максимальную ширину для панели
    # self.setMaximumWidth(580)  # Оставить место для полос прокрутки
    
    # 2. Улучшить настройки QScrollArea
    # scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    # scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    # scroll.setWidgetResizable(True)
    
    # 3. Оптимизировать QGridLayout
    # layout.setContentsMargins(5, 5, 5, 5)
    # layout.setSpacing(5)  # Уменьшить отступы
    
    # 4. Ограничить размеры элементов управления
    # spinbox.setMaximumWidth(80)
    # label.setMaximumWidth(120)
    
    pass

def fix_main_window_splitter():
    """Исправить настройки сплиттера в главном окне"""
    
    # В _setup_tabs() MainWindow:
    
    # 1. Увеличить минимальную ширину TabWidget
    # self.tab_widget.setMinimumWidth(350)  # Было 300
    # self.tab_widget.setMaximumWidth(650)  # Было 600
    
    # 2. Настроить stretch factors
    # self.main_horizontal_splitter.setStretchFactor(0, 2)  # Меньше для 3D
    # self.main_horizontal_splitter.setStretchFactor(1, 1)  # Больше для панелей
    
    pass
