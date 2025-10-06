@echo off
echo 🐍 Активация виртуального окружения PneumoStabSim...
call .venv\Scripts\activate.bat
echo ✅ Окружение активировано
echo 📋 Доступные команды:
echo    python app.py           - Запуск приложения
echo    python -m pytest tests/ - Запуск тестов  
echo    pip list               - Список пакетов
echo    deactivate             - Деактивация окружения
cmd /k
