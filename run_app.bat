@echo off
echo.
echo 🚀 ========== ЗАПУСК PNEUMOSTABSIM ==========
echo 📁 Активация виртуального окружения...

call .venv\Scripts\activate.bat

echo.
echo ✅ Окружение активировано
echo 🎬 Запуск приложения PneumoStabSim...
echo.

python app.py

echo.
echo 📊 Приложение завершено (код: %ERRORLEVEL%)
echo 🔄 Нажмите любую клавишу для выхода...
pause > nul
