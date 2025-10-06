#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест подключения всех параметров геометрии к анимированной схеме
Test connection of all geometry parameters to animated scene
"""
import sys
import os
from pathlib import Path

# Добавим src в путь
sys.path.insert(0, str(Path(__file__).parent / 'src'))

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer

from src.ui.panels.panel_geometry import GeometryPanel


class GeometryConnectionTest(QMainWindow):
    """Тест подключения параметров геометрии"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("🔧 Тест подключения параметров геометрии к 3D схеме")
        self.resize(600, 900)
        
        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Заголовок
        title = QLabel("ТЕСТ ПОДКЛЮЧЕНИЯ ВСЕХ ПАРАМЕТРОВ ГЕОМЕТРИИ")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin: 10px;")
        layout.addWidget(title)
        
        info = QLabel("Изменяйте параметры - проверяйте лог в консоли")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 20px;")
        layout.addWidget(info)
        
        # Панель геометрии
        self.geometry_panel = GeometryPanel()
        layout.addWidget(self.geometry_panel)
        
        # Лог изменений
        self.log_label = QLabel("Лог изменений (последние 10):")
        self.log_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(self.log_label)
        
        self.log_text = QLabel("")
        self.log_text.setWordWrap(True)
        self.log_text.setStyleSheet("background: #f0f0f0; padding: 10px; font-family: monospace; font-size: 10px;")
        self.log_text.setMinimumHeight(200)
        self.log_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.log_text)
        
        # Кнопки тестирования
        buttons_layout = QHBoxLayout()
        
        test_all_btn = QPushButton("🧪 Тест всех параметров")
        test_all_btn.clicked.connect(self.test_all_parameters)
        buttons_layout.addWidget(test_all_btn)
        
        clear_log_btn = QPushButton("🗑️ Очистить лог")
        clear_log_btn.clicked.connect(self.clear_log)
        buttons_layout.addWidget(clear_log_btn)
        
        layout.addLayout(buttons_layout)
        
        # Подключаем сигналы панели геометрии
        self.connect_signals()
        
        # Лог изменений
        self.log_entries = []
        
        # Счетчик изменений
        self.change_count = 0
    
    def connect_signals(self):
        """Подключить сигналы панели геометрии"""
        print("🔧 Подключение сигналов GeometryPanel...")
        
        # 1. parameter_changed - для отдельных параметров
        self.geometry_panel.parameter_changed.connect(self.on_parameter_changed)
        print("  ✅ parameter_changed подключен")
        
        # 2. geometry_updated - для обновления всей геометрии
        self.geometry_panel.geometry_updated.connect(self.on_geometry_updated)
        print("  ✅ geometry_updated подключен")
        
        # 3. geometry_changed - для 3D сцены (основной сигнал!)
        self.geometry_panel.geometry_changed.connect(self.on_geometry_changed)
        print("  ✅ geometry_changed подключен (→3D сцена)")
        
        print("🎯 ВСЕ СИГНАЛЫ ПОДКЛЮЧЕНЫ!")
    
    def on_parameter_changed(self, param_name: str, value: float):
        """Обработка изменения отдельного параметра"""
        self.change_count += 1
        entry = f"#{self.change_count:03d} PARAM: {param_name} = {value:.3f}"
        self.add_log_entry(entry)
        print(f"📊 {entry}")
    
    def on_geometry_updated(self, params: dict):
        """Обработка обновления всей геометрии"""
        self.change_count += 1
        param_names = list(params.keys())[:5]  # Первые 5 параметров
        entry = f"#{self.change_count:03d} UPDATE: {len(params)} параметров [{', '.join(param_names)}...]"
        self.add_log_entry(entry)
        print(f"🔄 {entry}")
    
    def on_geometry_changed(self, geometry_3d: dict):
        """Обработка изменения геометрии для 3D сцены (ОСНОВНОЙ МЕТОД!)"""
        self.change_count += 1
        
        # Извлекаем ключевые параметры
        frame_length = geometry_3d.get('frameLength', 0)
        lever_length = geometry_3d.get('leverLength', 0)
        cyl_diam = geometry_3d.get('cylDiamM', 0)
        rod_diam = geometry_3d.get('rodDiameterM', 0)
        
        entry = f"#{self.change_count:03d} 3D→QML: Рама={frame_length:.0f}мм, Рычаг={lever_length:.0f}мм, Цил={cyl_diam:.1f}мм, Шток={rod_diam:.1f}мм"
        self.add_log_entry(entry, is_3d=True)
        print(f"🎬 {entry}")
        
        # Симулируем отправку в QML
        print(f"   📤 Отправка в QML: {len(geometry_3d)} параметров")
        for key, value in list(geometry_3d.items())[:3]:  # Показываем первые 3
            print(f"      {key}: {value}")
        if len(geometry_3d) > 3:
            print(f"      ... и еще {len(geometry_3d) - 3} параметров")
    
    def add_log_entry(self, entry: str, is_3d: bool = False):
        """Добавить запись в лог"""
        if is_3d:
            entry = f"🎬 {entry}"
        else:
            entry = f"📊 {entry}"
            
        self.log_entries.append(entry)
        if len(self.log_entries) > 10:
            self.log_entries.pop(0)
        
        self.log_text.setText("\n".join(self.log_entries))
    
    def test_all_parameters(self):
        """Протестировать все параметры"""
        print("\n🧪 ТЕСТИРОВАНИЕ ВСЕХ ПАРАМЕТРОВ...")
        
        # Получаем текущие параметры
        current = self.geometry_panel.get_parameters()
        print(f"📊 Текущие параметры: {len(current)}")
        
        # Тестируем каждый параметр
        test_values = {
            'wheelbase': 3.5,
            'track': 1.8,
            'lever_length': 0.9,
            'cylinder_length': 0.4,
            'cyl_diam_m': 0.100,
            'rod_diameter_m': 0.040,
            'stroke_m': 0.350,
            'dead_gap_m': 0.010,
        }
        
        for param_name, test_value in test_values.items():
            if param_name in current:
                print(f"🧪 Тест: {param_name} → {test_value}")
                # Программно меняем значение через внутренний метод
                self.geometry_panel._on_parameter_changed(param_name, test_value)
        
        print("✅ Тест всех параметров завершен")
    
    def clear_log(self):
        """Очистить лог"""
        self.log_entries.clear()
        self.log_text.setText("")
        self.change_count = 0
        print("🗑️ Лог очищен")


def main():
    """Главная функция теста"""
    print("=" * 70)
    print("🔧 ТЕСТ ПОДКЛЮЧЕНИЯ ПАРАМЕТРОВ ГЕОМЕТРИИ К 3D СХЕМЕ")
    print("=" * 70)
    print()
    print("ПРОВЕРЯЕМ:")
    print("✅ Все 12 параметров GeometryPanel подключены")
    print("✅ Сигнал geometry_changed передает данные в QML")
    print("✅ Конвертация м→мм для QML работает")
    print("✅ Новые параметры (МШ-1, МШ-2) поддерживаются")
    print()
    print("ИНСТРУКЦИИ:")
    print("1. Изменяйте слайдеры - смотрите консоль")
    print("2. Нажмите 'Тест всех параметров' для автотеста")
    print("3. Проверьте, что geometry_changed вызывается")
    print()
    print("=" * 70)
    
    app = QApplication(sys.argv)
    window = GeometryConnectionTest()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
