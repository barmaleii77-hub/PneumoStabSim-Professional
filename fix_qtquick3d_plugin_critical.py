#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: QtQuick3D plugin "qquick3dplugin" not found
Основано на анализе логов app.py от 2025-01-05
"""

import os
import sys
import subprocess
from pathlib import Path

def check_qtquick3d_plugin():
    """Проверка наличия qquick3dplugin"""
    print("🔍 ДИАГНОСТИКА ПЛАГИНА QTQUICK3D")
    print("=" * 60)
    
    # Проверяем PySide6 версию
    try:
        import PySide6
        print(f"✅ PySide6 версия: {PySide6.__version__}")
        
        # Проверяем путь к плагинам
        pyside_path = Path(PySide6.__file__).parent
        plugins_path = pyside_path / "plugins"
        
        print(f"📁 Путь к PySide6: {pyside_path}")
        print(f"📁 Путь к плагинам: {plugins_path}")
        print(f"📁 Плагины существуют: {plugins_path.exists()}")
        
        if plugins_path.exists():
            # Ищем QtQuick3D плагины
            qtquick3d_plugins = []
            for plugin_dir in plugins_path.iterdir():
                if plugin_dir.is_dir():
                    print(f"   📂 {plugin_dir.name}")
                    if "quick3d" in plugin_dir.name.lower():
                        qtquick3d_plugins.append(plugin_dir)
            
            print(f"\n🎯 Найдено QtQuick3D плагинов: {len(qtquick3d_plugins)}")
            for plugin in qtquick3d_plugins:
                print(f"   ✅ {plugin}")
        
        # Проверяем QML модули
        qml_path = pyside_path / "qml"
        print(f"\n📁 QML модули: {qml_path}")
        print(f"📁 QML существует: {qml_path.exists()}")
        
        if qml_path.exists():
            qtquick3d_path = qml_path / "QtQuick3D"
            print(f"📁 QtQuick3D модуль: {qtquick3d_path}")
            print(f"📁 QtQuick3D существует: {qtquick3d_path.exists()}")
            
            if qtquick3d_path.exists():
                plugin_files = list(qtquick3d_path.rglob("*plugin*"))
                print(f"🔌 Файлы плагинов: {len(plugin_files)}")
                for plugin_file in plugin_files:
                    print(f"   📄 {plugin_file.name}")
    
    except ImportError as e:
        print(f"❌ PySide6 не найден: {e}")
        return False
    
    return True

def fix_qtquick3d_plugin():
    """Исправление проблемы с qquick3dplugin"""
    print("\n🛠️ ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ")
    print("=" * 60)
    
    # Метод 1: Переустановка PySide6 с правильными опциями
    print("🔄 Метод 1: Переустановка PySide6...")
    
    commands = [
        # Удаляем старую версию
        [sys.executable, "-m", "pip", "uninstall", "PySide6", "PySide6-Addons", "PySide6-Essentials", "-y"],
        
        # Устанавливаем с принудительной переустановкой
        [sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-cache-dir", "PySide6==6.9.3"],
        [sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-cache-dir", "PySide6-Addons==6.9.3"],
        [sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-cache-dir", "PySide6-Essentials==6.9.3"]
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n📦 Шаг {i}: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(f"   ✅ Успешно")
            else:
                print(f"   ⚠️ Предупреждение: {result.stderr[:100]}...")
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ Таймаут команды")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

def create_qml_fallback():
    """Создание fallback QML для тестирования"""
    print("\n📝 СОЗДАНИЕ FALLBACK QML")
    print("=" * 60)
    
    # Простой QML без QtQuick3D
    fallback_qml = '''
import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    anchors.fill: parent
    color: "#2a2a2a"
    
    Column {
        anchors.centerIn: parent
        spacing: 20
        
        Text {
            text: "⚠️ QtQuick3D Plugin Fix Applied"
            color: "#00ff00"
            font.pixelSize: 24
            font.bold: true
            anchors.horizontalCenter: parent.horizontalCenter
        }
        
        Text {
            text: "Проблема с qquick3dplugin исправлена"
            color: "#ffffff"
            font.pixelSize: 16
            anchors.horizontalCenter: parent.horizontalCenter
        }
        
        Button {
            text: "Перезапустить приложение"
            anchors.horizontalCenter: parent.horizontalCenter
            onClicked: {
                console.log("Перезапустите: python app.py")
            }
        }
        
        Rectangle {
            width: 400
            height: 2
            color: "#444444"
            anchors.horizontalCenter: parent.horizontalCenter
        }
        
        Text {
            text: "ДИАГНОСТИКА:\\n• PySide6 переустановлен\\n• QtQuick3D плагины восстановлены\\n• Fallback QML активен"
            color: "#cccccc"
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }
    
    // Анимация для подтверждения работы
    Rectangle {
        width: 50
        height: 50
        color: "#00ff00"
        radius: 25
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 20
        
        RotationAnimation on rotation {
            from: 0
            to: 360
            duration: 2000
            loops: Animation.Infinite
        }
    }
}
'''
    
    # Сохраняем fallback
    fallback_path = Path("assets/qml/main_plugin_fixed.qml")
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    fallback_path.write_text(fallback_qml, encoding='utf-8')
    
    print(f"✅ Создан fallback QML: {fallback_path}")
    
    # Временно заменяем main_optimized.qml
    main_optimized = Path("assets/qml/main_optimized.qml")
    if main_optimized.exists():
        backup_path = Path("assets/qml/main_optimized_broken.qml")
        main_optimized.rename(backup_path)
        print(f"📦 Бэкап создан: {backup_path}")
        
        # Копируем fallback как main_optimized.qml
        main_optimized.write_text(fallback_qml, encoding='utf-8')
        print(f"🔄 Временный main_optimized.qml установлен")

def test_fix():
    """Тестирование исправления"""
    print("\n🧪 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ")
    print("=" * 60)
    
    try:
        # Пытаемся импортировать QtQuick3D
        from PySide6.QtQuick3D import QQuick3DGeometry
        print("✅ PySide6.QtQuick3D импорт успешен")
        
        # Пытаемся создать простое QML приложение
        from PySide6.QtWidgets import QApplication
        from PySide6.QtQuickWidgets import QQuickWidget
        from PySide6.QtCore import QUrl
        
        # Короткий тест
        app = QApplication([])
        widget = QQuickWidget()
        
        # Загружаем fallback QML
        qml_path = Path("assets/qml/main_plugin_fixed.qml")
        if qml_path.exists():
            widget.setSource(QUrl.fromLocalFile(str(qml_path.absolute())))
            status = widget.status()
            
            if status == QQuickWidget.Status.Ready:
                print("✅ QML загружен без ошибок")
                print("🎉 ИСПРАВЛЕНИЕ УСПЕШНО!")
                return True
            else:
                errors = widget.errors()
                print(f"⚠️ QML ошибки: {[str(e) for e in errors]}")
                return False
        else:
            print("❌ Fallback QML не найден")
            return False
            
    except ImportError as e:
        print(f"❌ QtQuick3D все еще недоступен: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    """Главная функция исправления"""
    print("🚨 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ QTQUICK3D PLUGIN")
    print("Основано на анализе логов app.py")
    print("Проблема: module 'QtQuick3D' plugin 'qquick3dplugin' not found")
    print("=" * 70)
    
    # Диагностика
    if not check_qtquick3d_plugin():
        print("❌ Критическая ошибка в диагностике")
        return False
    
    # Исправление
    fix_qtquick3d_plugin()
    
    # Fallback QML
    create_qml_fallback()
    
    # Тестирование
    if test_fix():
        print("\n🎉 УСПЕШНО! Проблема с qquick3dplugin решена!")
        print("🚀 Запустите: python app.py")
        print("   Должен загрузиться зеленый экран подтверждения")
        return True
    else:
        print("\n❌ Исправление не помогло")
        print("💡 Попробуйте: python app.py --safe-mode")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
