# ============================================================================
# PneumoStabSim Professional - Полная настройка окружения
# Скрипт автоматической настройки проекта
# ============================================================================

param(
    [switch]$Force,
    [switch]$UpdatePip,
    [switch]$SkipVenv
)

$ErrorActionPreference = "Stop"

# Цвета для вывода
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Step { param($Message) Write-Host "`n🔧 $Message" -ForegroundColor Magenta }

Write-Host @"

╔════════════════════════════════════════════════════════════╗
║  PneumoStabSim Professional - Setup Script                 ║
║  Автоматическая настройка окружения разработки             ║
╚════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# === ПРОВЕРКА PYTHON ===
Write-Step "Проверка Python..."

try {
    $PythonVersion = python --version 2>&1
    Write-Success "Найден: $PythonVersion"

    # Проверка версии Python (поддержка 3.11–3.13)
    if ($PythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
        $Major = [int]$Matches[1]
        $Minor = [int]$Matches[2]

        if ($Major -ne 3 -or $Minor -lt 11 -or $Minor -gt 13) {
            Write-Error "Требуется Python 3.11–3.13! Текущая версия: $PythonVersion"
            exit 1
        }

        if ($Major -eq 3 -and $Minor -eq 13) {
            Write-Success "Python 3.13 - отлично! (рекомендуемая версия)"
        } else {
            Write-Warning "Python $Major.$Minor - поддерживается, но рекомендуется обновиться до 3.13"
        }
    }
} catch {
    Write-Error "Python не найден! Установите Python 3.11–3.13 с python.org"
    Write-Info "Скачать: https://www.python.org/downloads/"
    exit 1
}

# === ВИРТУАЛЬНОЕ ОКРУЖЕНИЕ ===
if (-not $SkipVenv) {
    Write-Step "Настройка виртуального окружения..."

    # Используем .venv как стандарт для проекта
    $VenvPath = ".venv"

    if (Test-Path $VenvPath) {
        if ($Force) {
            Write-Warning "Удаление существующего venv (--Force)..."
            Remove-Item -Path $VenvPath -Recurse -Force
        } else {
            Write-Info "Виртуальное окружение уже существует (используйте --Force для пересоздания)"
        }
    }

    if (-not (Test-Path $VenvPath)) {
        Write-Info "Создание виртуального окружения..."
        python -m venv $VenvPath
        Write-Success "Виртуальное окружение создано: $VenvPath"
    }

    # Активация venv
    Write-Info "Активация виртуального окружения..."
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"

    if (Test-Path $ActivateScript) {
        & $ActivateScript
        Write-Success "Виртуальное окружение активировано"
    } else {
        Write-Error "Не найден скрипт активации: $ActivateScript"
        exit 1
    }
}

# === ОБНОВЛЕНИЕ PIP ===
if ($UpdatePip) {
    Write-Step "Обновление pip, setuptools, wheel..."
    python -m pip install --upgrade pip setuptools wheel
    Write-Success "pip обновлен"
}

# === УСТАНОВКА ЗАВИСИМОСТЕЙ ===
Write-Step "Установка зависимостей проекта..."

if (Test-Path "requirements.txt") {
    Write-Info "Установка из requirements.txt..."
    python -m pip install -r requirements.txt -c requirements-compatible.txt
    Write-Success "Основные зависимости установлены"
} else {
    Write-Warning "Файл requirements.txt не найден!"
}

# Установка dev зависимостей (строго по requirements-dev.txt)
if (Test-Path "requirements-dev.txt") {
    Write-Info "Установка из requirements-dev.txt..."
    python -m pip install -r requirements-dev.txt
    Write-Success "Dev зависимости установлены"
} else {
    Write-Warning "Файл requirements-dev.txt не найден!"
}

# === ПРОВЕРКА УСТАНОВКИ ===
Write-Step "Проверка установленных пакетов..."

# Проверка PySide6
try {
    $PySide6Check = python -c "import PySide6.QtCore as QtCore; print(f'PySide6 {QtCore.__version__} (Qt {QtCore.qVersion()})')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success $PySide6Check
    } else {
        Write-Error "PySide6 не установлен корректно!"
        Write-Info $PySide6Check
    }
} catch {
    Write-Error "Ошибка проверки PySide6: $_"
}

# Проверка NumPy
try {
    $NumpyVersion = python -c "import numpy; print(f'NumPy {numpy.__version__}')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success $NumpyVersion
    }
} catch {
    Write-Warning "NumPy не установлен"
}

# Проверка SciPy
try {
    $ScipyVersion = python -c "import scipy; print(f'SciPy {scipy.__version__}')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success $ScipyVersion
    }
} catch {
    Write-Warning "SciPy не установлен"
}

# === ПРОВЕРКА .ENV ===
Write-Step "Проверка файла .env..."

if (Test-Path ".env") {
    Write-Success "Файл .env найден"

    # Вывод содержимого .env
    Write-Info "Содержимое .env:"
    Get-Content ".env" | Where-Object { $_ -notmatch "^\s*#" -and $_ -notmatch "^\s*$" } | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
} else {
    Write-Warning ".env не найден — выполните скрипт setup_environment.py или создайте файл вручную"
}

# === ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА ===
Write-Step "Проверка структуры проекта..."

$RequiredDirs = @("src", "assets", "tests", ".vscode")
$MissingDirs = @()

foreach ($Dir in $RequiredDirs) {
    if (Test-Path $Dir) {
        Write-Success "Найдена директория: $Dir"
    } else {
        Write-Warning "Отсутствует директория: $Dir"
        $MissingDirs += $Dir
    }
}

# === ПРОВЕРКА ВАЖНЫХ ФАЙЛОВ ===
$RequiredFiles = @("app.py", "requirements.txt", "pyproject.toml", ".gitignore")
foreach ($File in $RequiredFiles) {
    if (Test-Path $File) {
        Write-Success "Найден файл: $File"
    } else {
        Write-Warning "Отсутствует файл: $File"
    }
}

# === НАСТРОЙКА GIT ===
Write-Step "Проверка Git конфигурации..."

if (Test-Path ".git") {
    Write-Success "Git репозиторий инициализирован"

    # Проверка remote
    $RemoteUrl = git remote get-url origin 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Git remote: $RemoteUrl"
    } else {
        Write-Warning "Git remote не настроен"
    }

    # Текущая ветка
    $Branch = git branch --show-current 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Текущая ветка: $Branch"
    }
} else {
    Write-Warning "Git репозиторий не инициализирован"
}

# === ФИНАЛЬНЫЙ ОТЧЕТ ===
Write-Host @"

╔════════════════════════════════════════════════════════════╗
║  НАСТРОЙКА ЗАВЕРШЕНА                                       ║
╚════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Info "Следующие шаги:"
Write-Host "  1. Активируйте venv:      .\\.venv\\Scripts\\Activate.ps1" -ForegroundColor Yellow
Write-Host "  2. Запустите приложение:  python app.py" -ForegroundColor Yellow
Write-Host "  3. Или используйте F5 в VS Code для отладки" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 Подробнее о поддерживаемых конфигурациях: docs/environments.md" -ForegroundColor Cyan

Write-Success "Готово к работе! 🚀"
