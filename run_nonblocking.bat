@echo off
REM Quick non-blocking launcher for PneumoStabSim
echo 🚀 PneumoStabSim - Неблокирующий запуск
echo.
echo Запуск приложения в фоновом режиме...
python app.py --no-block
echo.
echo ✅ Приложение должно запуститься в отдельном окне
echo    Терминал остается свободным для других команд
echo    Для закрытия приложения используйте его окно
echo.
pause
