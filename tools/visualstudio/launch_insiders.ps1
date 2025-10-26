param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path,
    [switch]$ForceBootstrap,
    [string]$Script = 'app.py',
    [string[]]$ScriptArguments
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$utf8 = [System.Text.UTF8Encoding]::new($false)
try {
    [Console]::OutputEncoding = $utf8
    [Console]::InputEncoding = $utf8
    $global:OutputEncoding = $utf8
} catch {
    Write-Verbose 'Unable to update console encodings; continuing with defaults.'
}

if ($Host -and $Host.UI -and $Host.UI.SupportsVirtualTerminal) {
    $PSStyle.OutputRendering = 'Host'
}

if (Get-Module -ListAvailable -Name PSReadLine) {
    try {
        Set-PSReadLineOption -PredictionSource HistoryAndPlugin -PredictionViewStyle ListView -ErrorAction Stop
        Set-PSReadLineOption -BellStyle None -ErrorAction Stop
    } catch {
        Write-Verbose 'PSReadLine tuning failed; continuing with defaults.'
    }
}

if (Get-Command chcp -ErrorAction SilentlyContinue) {
    try { chcp 65001 | Out-Null } catch { Write-Verbose 'Unable to switch console codepage to UTF-8.' }
}

function Ensure-Environment {
    param(
        [string]$ProjectRoot,
        [switch]$Force
    )

    $initializer = Join-Path $ProjectRoot 'tools' 'visualstudio' 'initialize_insiders_environment.ps1'
    if (-not (Test-Path $initializer)) {
        throw "Initializer script '$initializer' is missing."
    }

    $envFile = Join-Path $ProjectRoot '.vs' 'insiders.environment.json'
    if ($Force -or -not (Test-Path $envFile)) {
        Write-Host '[Insiders] Refreshing environment descriptor...' -ForegroundColor Cyan
        & $initializer -ProjectRoot $ProjectRoot -Force:$Force.IsPresent | Out-Null
        if (-not (Test-Path $envFile)) {
            throw "Initialization did not produce environment file '$envFile'."
        }
    }

    return $envFile
}

$envFile = Ensure-Environment -ProjectRoot $ProjectRoot -Force:$ForceBootstrap
$envData = Get-Content $envFile -Encoding UTF8 | ConvertFrom-Json

foreach ($property in $envData.PSObject.Properties) {
    [Environment]::SetEnvironmentVariable($property.Name, $property.Value)
    Set-Item -Path env:$($property.Name) -Value $property.Value -Force
}

$pythonExe = Join-Path $ProjectRoot '.venv' 'Scripts' 'python.exe'
if (-not (Test-Path $pythonExe)) {
    throw "Python interpreter '$pythonExe' was not found. Run the initializer to materialise the virtual environment."
}

$scriptPath = Join-Path $ProjectRoot $Script
if (-not (Test-Path $scriptPath)) {
    throw "Launch script '$scriptPath' was not found."
}

Write-Host '[Insiders] Launching PneumoStabSim...' -ForegroundColor Cyan
& $pythonExe $scriptPath @ScriptArguments
