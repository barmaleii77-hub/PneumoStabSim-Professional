# Активация виртуального окружения PneumoStabSim (PowerShell)
Write-Host ""
Write-Host "🐍 ========== АКТИВАЦИЯ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ ==========" -ForegroundColor Green
Write-Host "📁 Проект: PneumoStabSim - Симулятор пневмостабилизатора" -ForegroundColor Cyan
Write-Host "🔧 Python: 3.13.7 | PySide6: 6.9.3 | Qt Quick 3D" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚡ Активация окружения..." -ForegroundColor Yellow

& .venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "✅ ОКРУЖЕНИЕ АКТИВИРОВАНО!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 ДОСТУПНЫЕ КОМАНДЫ:" -ForegroundColor Yellow
Write-Host "   🚀 python app.py                    - Запуск основного приложения" -ForegroundColor Cyan
Write-Host "   🧪 python test_geometry_connection.py - Тест подключения параметров" -ForegroundColor Cyan
Write-Host "   📊 python test_slider_precision.py   - Тест точности слайдеров" -ForegroundColor Cyan
Write-Host "   📦 pip list                         - Список установленных пакетов" -ForegroundColor Cyan
Write-Host "   🔍 python setup_venv.py            - Проверка окружения" -ForegroundColor Cyan
Write-Host "   ❌ deactivate                       - Выход из окружения" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 ДЛЯ БЫСТРОГО ЗАПУСКА: python app.py" -ForegroundColor Green
Write-Host "========================================================"
Write-Host ""
