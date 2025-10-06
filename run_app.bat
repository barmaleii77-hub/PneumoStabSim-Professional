@echo off
echo 🚀 Запуск PneumoStabSim...

if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Виртуальное окружение не найдено!
    echo Сначала запустите: python create_venv.py
    pause
    exit /b 1
)

echo 🐍 Активация окружения...
call .venv\Scripts\activate.bat

echo 🎮 Запуск приложения...
python app.py

echo.
echo 📝 Приложение завершено
pause
