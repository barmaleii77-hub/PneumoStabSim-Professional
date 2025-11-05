# ========================================================================
# PneumoStabSim Professional • VS Code PowerShell profile
# Автоматически настраивает среду терминала Windows для проекта
# ========================================================================

if ((Get-Location).Path -like "*PneumoStabSim-Professional*") {
    Write-Host "🚀 PneumoStabSim-Professional PowerShell profile loaded" -ForegroundColor Green

    $ProjectRoot = Get-Location
    $env:PYTHONPATH = "$ProjectRoot\src;$ProjectRoot\tests;$ProjectRoot\tools"
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    $env:QT_QUICK_CONTROLS_STYLE = "Basic"
    $env:QT_LOGGING_RULES = "js.debug=true;qt.qml.debug=true"
    $env:QSG_RHI_BACKEND = "opengl"
    $env:QT_SCALE_FACTOR_ROUNDING_POLICY = "PassThrough"

    function Invoke-Uv {
        param(
            [Parameter(ValueFromRemainingArguments = $true)]
            [string[]]$Args
        )

        $uv = Get-Command uv -ErrorAction SilentlyContinue
        if (-not $uv) {
            Write-Warning "uv не найден. Установите его: python -m pip install uv"
            return
        }

        & $uv @Args
    }

    function Invoke-Make {
        param(
            [Parameter(ValueFromRemainingArguments = $true)]
            [string[]]$Args
        )

        $make = Get-Command make -ErrorAction SilentlyContinue
        if (-not $make) {
            Write-Warning "make не найден. Установите GNU Make (см. docs/SETUP_GUIDE.md)"
            return
        }

        & $make @Args
    }

    function Sync-Uv {
        Invoke-Uv @('sync')
    }

    function Start-PneumoApp {
        param(
            [Parameter(ValueFromRemainingArguments = $true)]
            [string[]]$Args
        )

        Invoke-Uv (@('run', 'python', 'app.py') + $Args)
    }

    function Start-PneumoAppVerbose {
        param(
            [Parameter(ValueFromRemainingArguments = $true)]
            [string[]]$Args
        )

        Invoke-Uv (@('run', 'python', 'app.py', '--verbose') + $Args)
    }

    function Run-SmokeTests {
        param(
            [Parameter(ValueFromRemainingArguments = $true)]
            [string[]]$Args
        )

        Invoke-Uv (@('run', 'pytest', 'tests/smoke', '-vv', '--maxfail=1') + $Args)
    }

    function Run-AllTests {
        param(
            [Parameter(ValueFromRemainingArguments = $true)]
            [string[]]$Args
        )

        Invoke-Make (@('test') + $Args)
    }

    function Run-QualityGate {
        Invoke-Make @('check')
    }

    function Run-Ruff {
        Invoke-Uv @('run', 'python', '-m', 'ruff', 'check', 'src', 'tests', 'tools', 'app.py')
    }

    function Run-RuffFormatCheck {
        Invoke-Uv @('run', 'python', '-m', 'ruff', 'format', '--check', 'src', 'tests', 'tools', 'app.py')
    }

    function Run-Mypy {
        Invoke-Uv @('run', 'python', '-m', 'tools.ci_tasks', 'typecheck')
    }

    function Run-QmlLint {
        Invoke-Make @('qml-lint')
    }

    Set-Alias -Name uvsync -Value Sync-Uv
    Set-Alias -Name app -Value Start-PneumoApp
    Set-Alias -Name appv -Value Start-PneumoAppVerbose
    Set-Alias -Name smoke -Value Run-SmokeTests
    Set-Alias -Name testall -Value Run-AllTests
    Set-Alias -Name check -Value Run-QualityGate
    Set-Alias -Name ruff -Value Run-Ruff
    Set-Alias -Name rufffmt -Value Run-RuffFormatCheck
    Set-Alias -Name mypy -Value Run-Mypy
    Set-Alias -Name qmllint -Value Run-QmlLint

    Write-Host ""
    Write-Host "📦 uv sync → обновление зависимостей" -ForegroundColor Yellow
    Write-Host "🧪 smoke     → быстрые smoke-тесты" -ForegroundColor Yellow
    Write-Host "✅ check     → полный quality gate (make check)" -ForegroundColor Yellow
    Write-Host "🎨 ruff      → проверка стиля Ruff" -ForegroundColor Yellow
    Write-Host "🛠 app       → запуск приложения" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Справка: docs/SETUP_GUIDE.md" -ForegroundColor Cyan
} else {
    Write-Host "ℹ️  PneumoStabSim-Professional profile skipped (не в корне проекта)" -ForegroundColor Yellow
}
