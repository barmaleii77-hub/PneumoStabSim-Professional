# Активация виртуального окружения PneumoStabSim
Write-Host "🐍 Активация виртуального окружения PneumoStabSim..." -ForegroundColor Green

if (!(Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Виртуальное окружение не найдено!" -ForegroundColor Red
    Write-Host "Запустите: python create_venv.py" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

& .venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "✅ Виртуальное окружение активировано" -ForegroundColor Green
Write-Host "🏗️  Python версия:" -ForegroundColor Cyan
python --version
Write-Host ""
Write-Host "📋 Доступные команды:" -ForegroundColor Yellow
Write-Host "   python app.py              - Запуск приложения" -ForegroundColor Cyan
Write-Host "   python setup_venv.py       - Проверка окружения" -ForegroundColor Cyan
Write-Host "   python -m pytest tests/    - Запуск тестов" -ForegroundColor Cyan
Write-Host "   pip list                   - Список пакетов" -ForegroundColor Cyan
Write-Host "   pip install package_name   - Установка пакета" -ForegroundColor Cyan
Write-Host "   deactivate                 - Деактивация окружения" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Для запуска приложения введите: python app.py" -ForegroundColor Green
Write-Host ""
