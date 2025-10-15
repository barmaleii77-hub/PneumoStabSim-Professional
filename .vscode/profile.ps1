# ========================================================================
# PNEUMOSTABSIM-PROFESSIONAL POWERSHELL ПРОФИЛЬ
# Автоматически загружается при запуске PowerShell в проекте
# ========================================================================

# Проверяем, что мы в правильной директории проекта
if ((Get-Location).Path -like "*PneumoStabSim-Professional*") {
    Write-Host "🚀 Загружен профиль PneumoStabSim-Professional" -ForegroundColor Green
    
    # ====================================================================
    # УСТАНОВКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
    # ====================================================================
    
    $ProjectRoot = Get-Location
    $env:PYTHONPATH = "$ProjectRoot\src;$ProjectRoot\tests;$ProjectRoot\scripts"
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    
    # Qt настройки
    $env:QSG_RHI_BACKEND = "d3d11"
    $env:QT_LOGGING_RULES = "qt.qml.debug=true;js.debug=true"
    
    # ====================================================================
    # АЛИАСЫ ДЛЯ БЫСТРОГО ЗАПУСКА
    # ====================================================================
    
    # Основные команды приложения
    function Run-App { py app.py $args }
    function Run-Debug { py app.py --debug $args }
    function Run-Test { py app.py --test-mode $args }
    function Run-NoBlock { py app.py --no-block $args }
    function Run-Safe { py app.py --safe-mode $args }
    
    Set-Alias -Name app -Value Run-App
    Set-Alias -Name debug -Value Run-Debug
    Set-Alias -Name test -Value Run-Test
    Set-Alias -Name nb -Value Run-NoBlock
    Set-Alias -Name safe -Value Run-Safe
    
    # Тестирование
    function Run-PyTest { py -m pytest tests/ -v --tb=short --color=yes $args }
    function Run-QuickTests { py -m pytest tests/ -v -x --tb=short -k "not ui" $args }
    function Run-PhysicsTests { py -m pytest tests/test_physics*.py tests/test_integration*.py -v $args }
    function Run-UITests { py -m pytest tests/ui/ tests/graphics/ -v --tb=short $args }
    
    Set-Alias -Name pytest -Value Run-PyTest
    Set-Alias -Name qt -Value Run-QuickTests
    Set-Alias -Name pt -Value Run-PhysicsTests
    Set-Alias -Name ut -Value Run-UITests
    
    # Диагностика и отладка
    function Run-QMLDiag { py qml_diagnostic.py $args }
    function Run-HealthCheck { py scripts/health_check.py $args }
    function Run-CompTest { py scripts/comprehensive_test.py $args }
    function Run-QuickFix { py quick_fix.py $args }
    
    Set-Alias -Name qml -Value Run-QMLDiag
    Set-Alias -Name health -Value Run-HealthCheck
    Set-Alias -Name comp -Value Run-CompTest
    Set-Alias -Name fix -Value Run-QuickFix
    
    # Управление зависимостями
    function Install-Deps { py -m pip install -r requirements.txt $args }
    function Update-Deps { py -m pip install --upgrade -r requirements.txt $args }
    function Show-Deps { py -m pip freeze $args }
    function Save-Deps { py -m pip freeze > requirements-current.txt }
    
    Set-Alias -Name install -Value Install-Deps
    Set-Alias -Name update -Value Update-Deps
    Set-Alias -Name deps -Value Show-Deps
    Set-Alias -Name save -Value Save-Deps
    
    # Качество кода
    function Run-Flake8 { py -m flake8 src/ --max-line-length=100 --ignore=E203,W503,E501,F401 $args }
    function Run-Black { py -m black src/ --line-length=100 --target-version=py38 $args }
    function Run-Coverage { py -m pytest --cov=src --cov-report=html --cov-report=term tests/ $args }
    
    Set-Alias -Name lint -Value Run-Flake8
    Set-Alias -Name format -Value Run-Black
    Set-Alias -Name cov -Value Run-Coverage
    
    # Git команды
    function Git-Status { git status --porcelain $args }
    function Git-Info { 
        Write-Host "Текущая ветка:" (git branch --show-current) -ForegroundColor Cyan
        Write-Host "Последний коммит:" (git log -1 --oneline) -ForegroundColor Yellow
        $changedFiles = (git status --porcelain | Measure-Object -Line).Lines
        Write-Host "Статус: $changedFiles измененных файлов" -ForegroundColor Magenta
    }
    
    Set-Alias -Name gs -Value Git-Status
    Set-Alias -Name gi -Value Git-Info
    
    # Утилиты
    function Clear-PyCache {
        Write-Host "🧹 Очистка Python кэша..." -ForegroundColor Yellow
        Get-ChildItem -Path . -Recurse -Name "__pycache__" | ForEach-Object { 
            Remove-Item -Path $_ -Recurse -Force -Verbose 
        }
        Write-Host "✅ Кэш очищен!" -ForegroundColor Green
    }
    
    function Show-ProjectInfo {
        Write-Host "📊 ИНФОРМАЦИЯ О ПРОЕКТЕ PneumoStabSim-Professional" -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Gray
        Write-Host "📁 Корневая папка: $ProjectRoot" -ForegroundColor White
        Write-Host "🐍 Python путь: $env:PYTHONPATH" -ForegroundColor White
        Write-Host "🎨 Qt Backend: $env:QSG_RHI_BACKEND" -ForegroundColor White
        Write-Host ""
        Write-Host "📋 Доступные команды:" -ForegroundColor Yellow
        Write-Host "  app, debug, test, nb, safe  - Запуск приложения" -ForegroundColor White
        Write-Host "  pytest, qt, pt, ut          - Тестирование" -ForegroundColor White
        Write-Host "  qml, health, comp, fix      - Диагностика" -ForegroundColor White
        Write-Host "  install, update, deps, save - Зависимости" -ForegroundColor White
        Write-Host "  lint, format, cov           - Качество кода" -ForegroundColor White
        Write-Host "  gs, gi                      - Git команды" -ForegroundColor White
        Write-Host "  Clear-PyCache, info         - Утилиты" -ForegroundColor White
        Write-Host ""
        Write-Host "🎯 ВАЖНО: Всегда используется main_optimized.qml (v4.2)" -ForegroundColor Green
        Write-Host "  ✅ Исправлено дублирование примитивов" -ForegroundColor Green
        Write-Host "  ✅ Оптимизированная кинематика" -ForegroundColor Green
        Write-Host "=" * 60 -ForegroundColor Gray
    }
    
    Set-Alias -Name cache -Value Clear-PyCache
    Set-Alias -Name info -Value Show-ProjectInfo
    
    # ====================================================================
    # ФУНКЦИИ АВТОЗАВЕРШЕНИЯ
    # ====================================================================
    
    # Автозавершение для pytest
    Register-ArgumentCompleter -CommandName Run-PyTest -ScriptBlock {
        param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
        
        $testFiles = Get-ChildItem -Path "tests" -Filter "test_*.py" -Recurse | 
                    Select-Object -ExpandProperty Name |
                    ForEach-Object { $_ -replace '\.py$', '' }
        
        $testFiles | Where-Object { $_ -like "$wordToComplete*" }
    }
    
    # ====================================================================
    # ЗАГРУЗКА ДОПОЛНИТЕЛЬНЫХ МОДУЛЕЙ
    # ====================================================================
    
    # Импорт модуля для работы с JSON (если нужно)
    if (Get-Module -ListAvailable -Name PowerShellGet) {
        # Можно добавить дополнительные модули
    }
    
    # ====================================================================
    # ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ
    # ====================================================================
    
    Write-Host ""
    Write-Host "🎯 PneumoStabSim-Professional PowerShell Environment" -ForegroundColor Green
    Write-Host "📝 Для справки по командам введите: " -NoNewline
    Write-Host "info" -ForegroundColor Yellow
    Write-Host "🚀 Для быстрого запуска введите: " -NoNewline
    Write-Host "app" -ForegroundColor Cyan
    Write-Host ""
    
    # ====================================================================
    # ПРОВЕРКА ЗАВИСИМОСТЕЙ
    # ====================================================================
    
    # Проверяем, что Python доступен
    try {
        $pythonVersion = py --version 2>$null
        if ($pythonVersion) {
            Write-Host "🐍 $pythonVersion обнаружен" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "⚠️  Python не найден. Убедитесь, что Python установлен и 'py' доступен в PATH" -ForegroundColor Red
    }
    
    # Проверяем виртуальное окружение
    if (Test-Path "venv\Scripts\activate.ps1") {
        Write-Host "📦 Виртуальное окружение найдено в папке 'venv'" -ForegroundColor Green
        Write-Host "💡 Для активации используйте: " -NoNewline
        Write-Host "venv\Scripts\activate.ps1" -ForegroundColor Yellow
    }
    elseif (Test-Path ".venv\Scripts\activate.ps1") {
        Write-Host "📦 Виртуальное окружение найдено в папке '.venv'" -ForegroundColor Green
        Write-Host "💡 Для активации используйте: " -NoNewline
        Write-Host ".venv\Scripts\activate.ps1" -ForegroundColor Yellow
    }
    
    # ====================================================================
    # НАСТРОЙКА КОДИРОВКИ ДЛЯ РУССКОГО ЯЗЫКА
    # ====================================================================
    
    # Устанавливаем UTF-8 кодировку для корректного отображения русского текста
    $OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    
    # Настройка PowerShell для работы с русскими символами
    $Host.UI.RawUI.OutputEncoding = [System.Text.Encoding]::UTF8
    
} else {
    Write-Host "ℹ️  Профиль PneumoStabSim-Professional не активирован (неправильная директория)" -ForegroundColor Yellow
}
