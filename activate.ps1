# Активация виртуального окружения PneumoStabSim
Write-Host "🐍 Активация виртуального окружения PneumoStabSim..." -ForegroundColor Green
& .venv\Scripts\Activate.ps1
Write-Host "✅ Окружение активировано" -ForegroundColor Green
Write-Host "📋 Доступные команды:" -ForegroundColor Yellow
Write-Host "   python app.py           - Запуск приложения" -ForegroundColor Cyan
Write-Host "   python -m pytest tests/ - Запуск тестов" -ForegroundColor Cyan  
Write-Host "   pip list               - Список пакетов" -ForegroundColor Cyan
Write-Host "   deactivate             - Деактивация окружения" -ForegroundColor Cyan
