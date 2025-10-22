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

    # Проверка версии Python (требуется 3.11+)
    if ($PythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
        $Major = [int]$Matches[1]
        $Minor = [int]$Matches[2]

        if ($Major -lt 3 -or ($Major -eq 3 -and $Minor -lt 11)) {
            Write-Error "Требуется Python 3.11 или выше! Текущая версия: $PythonVersion"
            Write-Info "Рекомендуется Python 3.13"
            exit 1
        }

        if ($Major -eq 3 -and $Minor -eq 13) {
            Write-Success "Python 3.13 - отлично! (рекомендуемая версия)"
        } elseif ($Major -eq 3 -and $Minor -ge 11) {
            Write-Success "Python $Major.$Minor - поддерживается"
        }
    }
} catch {
    Write-Error "Python не найден! Установите Python 3.13 с python.org"
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
    python -m pip install -r requirements.txt
    Write-Success "Основные зависимости установлены"
} else {
    Write-Warning "Файл requirements.txt не найден!"
}

# Установка dev зависимостей
$DevDeps = @("pytest", "pytest-qt", "black", "mypy", "flake8")
Write-Info "Установка dev зависимостей: $($DevDeps -join ', ')"
# В PowerShell массив корректно разворачивается в аргументы нативной команды
python -m pip install $DevDeps
Write-Success "Dev зависимости установлены"

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
    Write-Warning "Файл .env не найден!"
    Write-Info "Создайте .env файл с переменными окружения"
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

# === ТЕСТОВЫЙ ЗАПУСК ===
Write-Step "Тестовый запуск приложения..."

Write-Info "Попытка импорта основных модулей..."
$TestImport = python -c @"
import sys
sys.path.insert(0, 'src')

try:
    from src.diagnostics.warnings import log_warning, log_error
    print('✅ diagnostics.warnings')

    from src.bootstrap.environment import setup_qtquick3d_environment
    print('✅ bootstrap.environment')

    from src.bootstrap.terminal import configure_terminal_encoding
    print('✅ bootstrap.terminal')

    from src.bootstrap.version_check import check_python_compatibility
    print('✅ bootstrap.version_check')

    print('✅ Все модули импортированы успешно!')
except Exception as e:
    print(f'❌ Ошибка импорта: {e}')
    sys.exit(1)
"@ 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host $TestImport
    Write-Success "Импорт модулей прошел успешно!"
} else {
    Write-Error "Ошибка при импорте модулей:"
    Write-Host $TestImport -ForegroundColor Red
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
Write-Host "📚 Полезные команды (после активации venv):" -ForegroundColor Cyan
Write-Host "  python app.py              - Запуск приложения" -ForegroundColor White
Write-Host "  python app.py --verbose    - Запуск с подробными логами" -ForegroundColor White
Write-Host "  python app.py --test-mode  - Тестовый режим (5 сек)" -ForegroundColor White
Write-Host "  pytest tests/              - Запуск тестов" -ForegroundColor White
Write-Host "  black src/ tests/          - Форматирование кода" -ForegroundColor White
Write-Host "  mypy src/                  - Проверка типов" -ForegroundColor White
Write-Host ""

Write-Success "Готово к работе! 🚀"
