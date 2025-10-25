[CmdletBinding()]
param(
    [Parameter()]
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'

function Write-Section {
    param([string]$Message)
    Write-Host "[Insiders] $Message" -ForegroundColor Cyan
}

function Invoke-Step {
    param(
        [string]$Message,
        [ScriptBlock]$Action
    )

    Write-Section $Message
    & $Action
}

Write-Section 'Bootstrapping Visual Studio Insiders environment'

if (-not (Test-Path $ProjectRoot)) {
    throw "Project root '$ProjectRoot' was not found."
}

$venvPath = Join-Path $ProjectRoot '.venv'
$pythonExe = Join-Path $venvPath 'Scripts' 'python.exe'

Invoke-Step 'Ensuring Python interpreter is available' {
    if (-not (Test-Path $pythonExe) -or $Force) {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCommand) {
            throw 'Python interpreter was not found on PATH. Install Python 3.13 or update PATH before continuing.'
        }

        Write-Section "Creating virtual environment at '$venvPath'"
        & $pythonCommand.Source '-m' 'venv' $venvPath
    }
}

if (-not (Test-Path $pythonExe)) {
    throw "The Python interpreter expected at '$pythonExe' could not be located."
}

function Invoke-PipInstall {
    param([string[]]$Arguments)
    & $pythonExe '-m' 'pip' @Arguments
}

Invoke-Step 'Upgrading pip' {
    Invoke-PipInstall @('install', '--upgrade', 'pip')
}

$requirementsFiles = @('requirements.txt', 'requirements-dev.txt', 'current_requirements.txt') | ForEach-Object {
    $candidate = Join-Path $ProjectRoot $_
    if (Test-Path $candidate) { $candidate }
}

if ($requirementsFiles.Count -gt 0) {
    Invoke-Step "Installing dependencies from: $($requirementsFiles -join ', ')" {
        foreach ($req in $requirementsFiles) {
            Invoke-PipInstall @('install', '-r', $req)
        }
    }
}

$qtSetupScript = Join-Path $ProjectRoot 'tools' 'setup_qt.py'
if (Test-Path $qtSetupScript) {
    Invoke-Step 'Validating Qt tooling (PySide6) for Insiders profile' {
        & $pythonExe $qtSetupScript '--ensure-installed'
    }
}

$envConfig = [ordered]@{
    QML2_IMPORT_PATH      = "$ProjectRoot\\.venv\\Lib\\site-packages\\PySide6\\qml;$ProjectRoot\\assets\\qml"
    QML_IMPORT_PATH       = "$ProjectRoot\\.venv\\Lib\\site-packages\\PySide6\\qml;$ProjectRoot\\assets\\qml"
    QT_PLUGIN_PATH        = "$ProjectRoot\\.venv\\Lib\\site-packages\\PySide6\\plugins"
    QT_QML_IMPORT_PATH    = "$ProjectRoot\\.venv\\Lib\\site-packages\\PySide6\\qml"
    QT_QUICK_CONTROLS_STYLE = 'Basic'
    PYTHONPATH            = "$ProjectRoot;$ProjectRoot\\src;$ProjectRoot\\tests"
    PNEUMOSTABSIM_PROFILE = 'insiders'
}

$insidersEnvFile = Join-Path $ProjectRoot '.vs' 'insiders.environment.json'

Invoke-Step "Persisting Insiders environment definition to '$insidersEnvFile'" {
    $insidersDir = Split-Path $insidersEnvFile -Parent
    if (-not (Test-Path $insidersDir)) {
        New-Item -ItemType Directory -Path $insidersDir | Out-Null
    }
    $envConfig | ConvertTo-Json -Depth 4 | Set-Content -Path $insidersEnvFile -Encoding UTF8
}

$launcherScript = Join-Path $ProjectRoot 'tools' 'visualstudio' 'launch_insiders.ps1'

Invoke-Step "Generating launch helper at '$launcherScript'" {
    $launcherContent = @'
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path
)

$envFile = Join-Path $ProjectRoot '.vs' 'insiders.environment.json'
if (-not (Test-Path $envFile)) {
    throw "Environment description '$envFile' was not found. Run initialize_insiders_environment.ps1 first."
}

$envData = Get-Content $envFile | ConvertFrom-Json

foreach ($entry in $envData.PSObject.Properties) {
    [System.Environment]::SetEnvironmentVariable($entry.Name, $entry.Value)
    Set-Item -Path env:$($entry.Name) -Value $entry.Value
}

$pythonExe = Join-Path $ProjectRoot '.venv' 'Scripts' 'python.exe'
if (-not (Test-Path $pythonExe)) {
    throw "Python interpreter '$pythonExe' was not found."
}

Write-Host 'Launching PneumoStabSim using Visual Studio Insiders profile...' -ForegroundColor Cyan
& $pythonExe (Join-Path $ProjectRoot 'app.py') @args
'@
    $launcherContent | Set-Content -Path $launcherScript -Encoding UTF8
}

Write-Section 'Visual Studio Insiders environment is ready.'
