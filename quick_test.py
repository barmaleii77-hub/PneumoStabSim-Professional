#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Быстрый тест приложения"""
import sys
import os

# Настройка окружения для Qt Quick 3D  
os.environ['QSG_RHI_BACKEND'] = 'd3d11'
os.environ['QSG_INFO'] = '1'
os.environ['QT_LOGGING_RULES'] = 'js.debug=true;qt.qml.debug=true'

print('🧪 Быстрый тест запуска приложения...')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.ui.main_window import MainWindow

app = QApplication(sys.argv)

print('✅ QApplication создан')
window = MainWindow(use_qml_3d=True)
print('✅ MainWindow создан')

window.show()
print('✅ MainWindow показан')

# Автозакрытие через 3 секунды
timer = QTimer()
timer.setSingleShot(True)
timer.timeout.connect(app.quit)
timer.start(3000)

print('🔄 Запуск на 3 секунды...')
result = app.exec()
print(f'✅ Приложение завершено с кодом: {result}')
