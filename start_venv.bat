@echo off
echo.
echo 🐍 ========== АКТИВАЦИЯ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ ==========
echo 📁 Проект: PneumoStabSim - Симулятор пневмостабилизатора
echo 🔧 Python: 3.13.7 ^| PySide6: 6.9.3 ^| Qt Quick 3D
echo.
echo ⚡ Активация окружения...
call .venv\Scripts\activate.bat

echo.
echo ✅ ОКРУЖЕНИЕ АКТИВИРОВАНО!
echo.
echo 📋 ДОСТУПНЫЕ КОМАНДЫ:
echo    🚀 python app.py                    - Запуск основного приложения
echo    🧪 python test_geometry_connection.py - Тест подключения параметров
echo    📊 python test_slider_precision.py   - Тест точности слайдеров  
echo    📦 pip list                         - Список установленных пакетов
echo    🔍 python setup_venv.py            - Проверка окружения
echo    ❌ deactivate                       - Выход из окружения
echo.
echo 🎯 ДЛЯ БЫСТРОГО ЗАПУСКА: python app.py
echo ========================================================
echo.

rem Оставляем командную строку открытой
cmd /k
