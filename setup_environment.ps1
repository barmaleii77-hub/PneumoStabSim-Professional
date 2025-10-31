# ============================================================================
# PneumoStabSim Professional - Полная настройка окружения
# Скрипт автоматической настройки проекта (Windows + uv)
# ============================================================================

param(
    [switch]$Force,
    [switch]$UpdatePip,
    [switch]$SkipVenv
)

$ErrorActionPreference = "Stop"

# Цвета для вывода
function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Step { param($Message) Write-Host "`n[STEP] $Message" -ForegroundColor Magenta }

function Get-PreferredPython {
    $candidates = @(
        @{ Command = "py"; Args = @("-3.13") },
        @{ Command = "python3.13"; Args = @() },
        @{ Command = "py"; Args = @("-3.12") },
        @{ Command = "python3.12"; Args = @() },
        @{ Command = "python3"; Args = @() },
        @{ Command = "py"; Args = @("-3") },
        @{ Command = "python"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        try {
            $args = @()
            if ($candidate.Args) { $args += $candidate.Args }
            $args += "--version"
            $output = & $candidate.Command @args 2>&1
            if ($LASTEXITCODE -ne 0) { continue }
            $match = [regex]::Match($output, "Python (\d+)\.(\d+)\.(\d+)")
            if (-not $match.Success) { continue }

            $version = [Version]::new([int]$match.Groups[1].Value, [int]$match.Groups[2].Value, [int]$match.Groups[3].Value)
            if ($version.Major -ne 3 -or $version.Minor -lt 11 -or $version.Minor -gt 13) {
                continue
            }

            $pathArgs = @()
            if ($candidate.Args) { $pathArgs += $candidate.Args }
            $pathArgs += "-c"
            $pathArgs += "import sys; print(sys.executable)"
            $exePath = (& $candidate.Command @pathArgs 2>&1).Trim()
            if (-not $exePath) { continue }

            $display = if ($candidate.Args -and $candidate.Args.Count -gt 0) {
                "$($candidate.Command) $($candidate.Args -join ' ')"
            } else {
                $candidate.Command
            }

            return [PSCustomObject]@{
                Executable = $exePath
                Version    = $version
                Display    = $display
                RawVersion = $output.Trim()
            }
        } catch {
            continue
        }
    }

    return $null
}

function Ensure-Uv {
    param(
        [string]$PythonExecutable
    )

    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCommand) {
        return $uvCommand.Source
    }

    Write-Step "Установка uv (ускоренный менеджер пакетов)..."
    try {
        & $PythonExecutable '-m' 'pip' 'install' '--upgrade' '--user' 'uv'
    } catch {
        Write-Warning "Не удалось установить uv автоматически: $_"
    }

    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCommand) {
        return $uvCommand.Source
    }

    try {
        $userBase = (& $PythonExecutable '-c' 'import site; print(site.getuserbase())' 2>&1).Trim()
        if ($userBase) {
            $candidate = Join-Path $userBase 'Scripts'
            $uvExe = Join-Path $candidate 'uv.exe'
            if (Test-Path $uvExe) {
                Write-Info "Используем uv из $uvExe"
                return $uvExe
            }
        }
    } catch {
        Write-Warning "Не удалось определить пользовательскую установку uv: $_"
    }

    Write-Warning "uv недоступен. Будут использованы стандартные инструменты pip."
    return $null
}

function Update-EnvFile {
    param(
        [string]$ProjectRoot
    )

    $envPath = Join-Path $ProjectRoot '.env'
    $resolvedRoot = (Resolve-Path $ProjectRoot).Path
    $pythonPaths = @()
    foreach ($name in @('src', 'tests', 'scripts')) {
        $fullPath = Join-Path $resolvedRoot $name
        try {
            $resolved = (Resolve-Path $fullPath -ErrorAction Stop).Path
            $pythonPaths += $resolved
        } catch {
            $pythonPaths += $fullPath
        }
    }
    $pythonPathValue = $pythonPaths -join ';'

    $content = @"
# PneumoStabSim Professional Environment (Автоматически обновлено)
PYTHONPATH=$pythonPathValue
PYTHONIOENCODING=utf-8
PYTHONDONTWRITEBYTECODE=1

# Qt Configuration
QSG_RHI_BACKEND=d3d11
QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true
QSG_INFO=1

# Project Paths
PROJECT_ROOT=$resolvedRoot
SOURCE_DIR=src
TEST_DIR=tests
SCRIPT_DIR=scripts

# Development Mode
DEVELOPMENT_MODE=true
DEBUG_ENABLED=true

# Russian Localization
LANG=ru_RU.UTF-8
COPILOT_LANGUAGE=ru
"@

    try {
        Set-Content -Path $envPath -Value $content -Encoding UTF8
        Write-Success "Файл .env обновлен: $envPath"
    } catch {
        Write-Warning "Не удалось обновить .env: $_"
    }

    return $envPath
}

function Ensure-Directories {
    param(
        [string]$ProjectRoot,
        [string[]]$Directories
    )

    foreach ($dir in $Directories) {
        $fullPath = Join-Path $ProjectRoot $dir
        if (-not (Test-Path $fullPath)) {
            try {
                New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
                Write-Success "Создана директория: $fullPath"
            } catch {
                Write-Warning "Не удалось создать директорию $fullPath: $_"
            }
        } else {
            Write-Info "Директория уже существует: $fullPath"
        }
    }
}

function Test-Package {
    param(
        [string]$PythonExecutable,
        [string]$Description,
        [string]$Command,
        [switch]$Optional
    )

    try {
        $output = & $PythonExecutable '-c' $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            if ($output) {
                Write-Success "$Description: $output"
            } else {
                Write-Success "$Description установлен"
            }
        } else {
            if ($Optional) {
                Write-Warning "$Description не прошел проверку"
                if ($output) { Write-Info $output }
            } else {
                Write-Error "$Description не прошел проверку"
                if ($output) { Write-Info $output }
            }
        }
    } catch {
        if ($Optional) {
            Write-Warning "$Description вызвал исключение: $_"
        } else {
            Write-Error "$Description вызвал исключение: $_"
        }
    }
}

function Show-DotEnv {
    param(
        [string]$EnvPath
    )

    if (Test-Path $EnvPath) {
        Write-Info "Содержимое .env:"
        Get-Content $EnvPath -Encoding UTF8 | Where-Object { $_ -and (-not $_.StartsWith('#')) } | ForEach-Object {
            Write-Host "  $_" -ForegroundColor Gray
        }
    } else {
        Write-Warning ".env не найден"
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PneumoStabSim Professional - Setup Script" -ForegroundColor Cyan
Write-Host "Автоматическая настройка окружения разработки" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Info "Корневая папка проекта: $projectRoot"

Write-Step "Поиск установленного Python (3.11–3.13)..."
$pythonInfo = Get-PreferredPython
if (-not $pythonInfo) {
    Write-Error "Python 3.11–3.13 не найден. Установите Python 3.13 с https://www.python.org/downloads/"
    exit 1
}

Write-Success "Найден интерпретатор: $($pythonInfo.RawVersion) [$($pythonInfo.Executable)]"
if ($pythonInfo.Version.Minor -eq 13) {
    Write-Success "Python 3.13 — рекомендованная версия"
} else {
    Write-Warning "Поддерживаемая версия Python обнаружена, но рекомендуется обновиться до 3.13"
}

$uvExecutable = Ensure-Uv -PythonExecutable $pythonInfo.Executable
if ($uvExecutable) {
    Write-Info "uv найден: $uvExecutable"
}

$venvPath = Join-Path $projectRoot '.venv'
$venvPython = $null
$dependenciesInstalled = $false

if ($SkipVenv) {
    Write-Step "Установка зависимостей в текущем интерпретаторе (SkipVenv)..."
    if ($UpdatePip) {
        Write-Info "Обновление pip/setuptools/wheel..."
        & $pythonInfo.Executable '-m' 'pip' 'install' '--upgrade' 'pip' 'setuptools' 'wheel'
        Write-Success "pip обновлен"
    }

    $requirements = Join-Path $projectRoot 'requirements.txt'
    if (Test-Path $requirements) {
        $constraints = Join-Path $projectRoot 'requirements-compatible.txt'
        $args = @('-m', 'pip', 'install', '-r', $requirements)
        if (Test-Path $constraints) { $args += @('-c', $constraints) }
        & $pythonInfo.Executable @args
        Write-Success "Основные зависимости установлены"
    } else {
        Write-Warning "Файл requirements.txt не найден"
    }

    $devLock = Join-Path $projectRoot 'requirements-dev.lock'
    if (Test-Path $devLock) {
        & $pythonInfo.Executable '-m' 'pip' 'install' '-r' $devLock
        Write-Success "Dev зависимости установлены"
    } elseif (Test-Path (Join-Path $projectRoot 'requirements-dev.txt')) {
        & $pythonInfo.Executable '-m' 'pip' 'install' '-r' (Join-Path $projectRoot 'requirements-dev.txt')
        Write-Success "Dev зависимости установлены"
    } else {
        Write-Warning "Файл requirements-dev.lock не найден"
    }

    $venvPython = $pythonInfo.Executable
    $dependenciesInstalled = $true
} else {
    Write-Step "Настройка виртуального окружения (.venv)..."
    if (Test-Path $venvPath) {
        if ($Force) {
            Write-Warning "Удаление существующего .venv (--Force)"
            Remove-Item -Path $venvPath -Recurse -Force
        } else {
            Write-Info "Найдено существующее .venv (используйте --Force для пересоздания)"
        }
    }

    if ($uvExecutable) {
        Write-Info "Запуск uv sync (extras: dev)..."
        $oldUvPython = $env:UV_PYTHON
        $env:UV_PYTHON = $pythonInfo.Executable
        Push-Location $projectRoot
        try {
            & $uvExecutable 'sync' '--extra' 'dev' '--locked'
            if ($LASTEXITCODE -eq 0) {
                Write-Success "uv sync завершен успешно"
                $dependenciesInstalled = $true
            } else {
                Write-Warning "uv sync завершился с кодом $LASTEXITCODE"
            }
        } catch {
            Write-Warning "Ошибка выполнения uv sync: $_"
        } finally {
            Pop-Location
            if ($null -ne $oldUvPython) {
                $env:UV_PYTHON = $oldUvPython
            } else {
                Remove-Item Env:UV_PYTHON -ErrorAction SilentlyContinue
            }
        }
    }

    if (-not (Test-Path $venvPath)) {
        Write-Info "Создание виртуального окружения через python -m venv..."
        & $pythonInfo.Executable '-m' 'venv' $venvPath
        Write-Success "Виртуальное окружение создано: $venvPath"
    }

    $venvPythonPath = Join-Path $venvPath 'Scripts\python.exe'
    if (-not (Test-Path $venvPythonPath)) {
        Write-Error "Не найден интерпретатор в .venv: $venvPythonPath"
        exit 1
    }
    $venvPython = $venvPythonPath

    if (-not $dependenciesInstalled) {
        if ($UpdatePip) {
            Write-Info "Обновление pip/setuptools/wheel внутри .venv..."
            & $venvPython '-m' 'pip' 'install' '--upgrade' 'pip' 'setuptools' 'wheel'
            Write-Success "pip обновлен"
        }

        $requirements = Join-Path $projectRoot 'requirements.txt'
        if (Test-Path $requirements) {
            Write-Info "Установка из requirements.txt..."
            $constraints = Join-Path $projectRoot 'requirements-compatible.txt'
            $args = @('-m', 'pip', 'install', '-r', $requirements)
            if (Test-Path $constraints) { $args += @('-c', $constraints) }
            & $venvPython @args
            Write-Success "Основные зависимости установлены"
        } else {
            Write-Warning "Файл requirements.txt не найден"
        }

        $devLock = Join-Path $projectRoot 'requirements-dev.lock'
        if (Test-Path $devLock) {
            Write-Info "Установка dev зависимостей (requirements-dev.lock)..."
            & $venvPython '-m' 'pip' 'install' '-r' $devLock
            Write-Success "Dev зависимости установлены"
        } elseif (Test-Path (Join-Path $projectRoot 'requirements-dev.txt')) {
            Write-Info "Установка dev зависимостей (requirements-dev.txt)..."
            & $venvPython '-m' 'pip' 'install' '-r' (Join-Path $projectRoot 'requirements-dev.txt')
            Write-Success "Dev зависимости установлены"
        } else {
            Write-Warning "Файл requirements-dev.lock не найден"
        }
    } elseif ($UpdatePip) {
        Write-Info "Обновление pip/setuptools/wheel внутри .venv..."
        & $venvPython '-m' 'pip' 'install' '--upgrade' 'pip' 'setuptools' 'wheel'
        Write-Success "pip обновлен"
    }

    $activateScript = Join-Path $venvPath 'Scripts\Activate.ps1'
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Success "Виртуальное окружение активировано"
    } else {
        Write-Warning "Не найден скрипт активации: $activateScript"
    }
}

Write-Step "Обновление конфигурации .env и директорий..."
$envFilePath = Update-EnvFile -ProjectRoot $projectRoot
Ensure-Directories -ProjectRoot $projectRoot -Directories @('logs', 'reports', 'temp', '.cache')
Show-DotEnv -EnvPath $envFilePath

Write-Step "Проверка структуры проекта..."
$requiredDirs = @('src', 'assets', 'tests', '.vscode')
foreach ($dir in $requiredDirs) {
    $fullPath = Join-Path $projectRoot $dir
    if (Test-Path $fullPath) {
        Write-Success "Найдена директория: $dir"
    } else {
        Write-Warning "Отсутствует директория: $dir"
    }
}

$requiredFiles = @('app.py', 'requirements.txt', 'pyproject.toml', '.gitignore')
foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        Write-Success "Найден файл: $file"
    } else {
        Write-Warning "Отсутствует файл: $file"
    }
}

if ($venvPython) {
    Write-Step "Проверка установленных пакетов..."
    Test-Package -PythonExecutable $venvPython -Description 'PySide6' -Command "import PySide6.QtCore as QtCore; print(f'PySide6 {QtCore.__version__} (Qt {QtCore.qVersion()})')"
    Test-Package -PythonExecutable $venvPython -Description 'NumPy' -Command "import numpy; print(f'NumPy {numpy.__version__}')" -Optional
    Test-Package -PythonExecutable $venvPython -Description 'SciPy' -Command "import scipy; print(f'SciPy {scipy.__version__}')" -Optional
    Test-Package -PythonExecutable $venvPython -Description 'Matplotlib' -Command "import matplotlib; print(f'Matplotlib {matplotlib.__version__}')" -Optional
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Настройка завершена" -ForegroundColor Cyan
Write-Host "Активированное окружение: $venvPython" -ForegroundColor Cyan
Write-Host "Запустите run.ps1 или python app.py для проверки" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
