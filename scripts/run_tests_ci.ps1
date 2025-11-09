param(
  [string]$Target = 'tests'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-PssHeadless {
  param([string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
  $normalised = $Value.Trim().ToLowerInvariant()
  return @('1', 'true', 'yes', 'on') -contains $normalised
}

$pssHeadless = Test-PssHeadless $env:PSS_HEADLESS
if ($pssHeadless) {
  if (-not $env:QT_QPA_PLATFORM) { $env:QT_QPA_PLATFORM = 'offscreen' }
  if (-not $env:QT_QUICK_BACKEND) { $env:QT_QUICK_BACKEND = 'software' }
  $env:PSS_HEADLESS = '1'
} elseif (-not $env:QSG_RHI_BACKEND) {
  $env:QSG_RHI_BACKEND = 'd3d11'
}

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
$pytestArgs = @('-q', '-p', 'pytestqt.plugin', $Target)
if ($pssHeadless) {
  $pytestArgs = @('--pss-headless') + $pytestArgs
}
python -m pytest @pytestArgs 2>&1 | Tee-Object -FilePath $pytestLog

# Пробрасываем код возврата
exit $LASTEXITCODE
