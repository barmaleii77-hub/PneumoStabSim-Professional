param(
  [string]$Target = 'tests'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Подготовка каталогов отчетов
$reportsDir = Join-Path -Path (Get-Location) -ChildPath 'reports/tests'
New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null

# Разрешаем загрузку нужных pytest-плагинов (pytest-qt для qtbot)
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = ''

# Опционально: подготовить Qt окружение для Windows
if (Test-Path -LiteralPath 'scripts/load_cipilot_env.ps1') {
  try { powershell -ExecutionPolicy Bypass -File scripts/load_cipilot_env.ps1 | Tee-Object -FilePath (Join-Path $reportsDir 'env_setup.txt') } catch { }
}

# Запуск pytest (включаем явно плагин pytest-qt на случай частично заблокированной автозагрузки)
$pytestLog = Join-Path $reportsDir 'pytest_console.txt'
Write-Host "[tests] Running pytest target: $Target"
python -m pytest -q -p pytestqt.plugin $Target 2>&1 | Tee-Object -FilePath $pytestLog

# Пробрасываем код возврата
exit $LASTEXITCODE
