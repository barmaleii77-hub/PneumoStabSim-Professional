@echo off
echo 🐍 Активация виртуального окружения PneumoStabSim...
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Виртуальное окружение не найдено!
    echo Запустите: python create_venv.py
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo.
echo ✅ Виртуальное окружение активировано
echo 🏗️  Python версия:
python --version
echo.
echo 📋 Доступные команды:
echo    python app.py              - Запуск приложения
echo    python setup_venv.py       - Проверка окружения
echo    python -m pytest tests/    - Запуск тестов  
echo    pip list                   - Список пакетов
echo    pip install package_name   - Установка пакета
echo    deactivate                 - Деактивация окружения
echo.
echo 🚀 Для запуска приложения введите: python app.py
echo.

cmd /k
