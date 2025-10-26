[CmdletBinding()]
param(
    [Parameter()]
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path,

    [switch]$Force,

    [switch]$SkipVisualStudio
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Set-StrictMode -Version Latest

function Set-Utf8Console {
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    try {
        [Console]::InputEncoding = $utf8
        [Console]::OutputEncoding = $utf8
        $global:OutputEncoding = $utf8
    } catch {
        Write-Verbose 'Unable to switch console encodings to UTF-8.'
    }

    if ($Host -and $Host.UI -and $Host.UI.SupportsVirtualTerminal) {
        $PSStyle.OutputRendering = 'Host'
    }

    if (Get-Module -ListAvailable -Name PSReadLine) {
        try {
            Set-PSReadLineOption -PredictionSource HistoryAndPlugin -PredictionViewStyle ListView -ErrorAction Stop
            Set-PSReadLineOption -BellStyle None -ErrorAction Stop
        } catch {
            Write-Verbose 'Failed to adjust PSReadLine options.'
        }
    }

    if (Get-Command chcp -ErrorAction SilentlyContinue) {
        try { chcp 65001 | Out-Null } catch { Write-Verbose 'chcp 65001 failed; continuing with the current codepage.' }
    }

    $PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
    $PSDefaultParameterValues['*:Encoding'] = 'utf8'
}

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

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -Path $Path -ItemType Directory -Force | Out-Null
    }
}

function Invoke-ExternalCommand {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory = $ProjectRoot,
        [switch]$IgnoreExitCode
    )

    Write-Verbose "Running '$FilePath' $($Arguments -join ' ')"

    $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -Wait -PassThru -WindowStyle Hidden
    if (-not $IgnoreExitCode -and $process.ExitCode -ne 0) {
        throw "Command '$FilePath' exited with code $($process.ExitCode)."
    }

    return $process.ExitCode
}

function Get-VsInstallerExecutable {
    $programFilesX86 = ${env:ProgramFiles(x86)}
    if (-not $programFilesX86) {
        return $null
    }

    $path = Join-Path $programFilesX86 'Microsoft Visual Studio' 'Installer'
    $candidate = Join-Path $path 'vs_installer.exe'
    if (Test-Path $candidate) {
        return $candidate
    }

    return $null
}

function Get-VsWhereExecutable {
    $programFilesX86 = ${env:ProgramFiles(x86)}
    if (-not $programFilesX86) {
        return $null
    }

    $path = Join-Path $programFilesX86 'Microsoft Visual Studio' 'Installer'
    $candidate = Join-Path $path 'vswhere.exe'
    if (Test-Path $candidate) {
        return $candidate
    }

    return $null
}

function Ensure-VisualStudioComponents {
    param([string]$ConfigPath)

    if (-not (Test-Path $ConfigPath)) {
        throw "Visual Studio configuration '$ConfigPath' is missing."
    }

    $installer = Get-VsInstallerExecutable
    if (-not $installer) {
        Write-Warning 'Visual Studio Installer was not found; skipping component provisioning.'
        return
    }

    $vsWhere = Get-VsWhereExecutable
    $installationPath = $null
    if ($vsWhere) {
        try {
            $instances = & $vsWhere -prerelease -format json 2>$null | ConvertFrom-Json
            if ($instances) {
                if ($instances -is [array]) {
                    $installationPath = ($instances | Select-Object -First 1).installationPath
                } else {
                    $installationPath = $instances.installationPath
                }
            }
        } catch {
            Write-Verbose 'Unable to query Visual Studio instances via vswhere.'
        }
    }

    $arguments = if ($installationPath) {
        @('modify', '--installpath', "`"$installationPath`"", '--config', "`"$ConfigPath`"", '--passive', '--norestart')
    } else {
        Write-Warning 'Visual Studio Insiders installation not detected; installing with supplied configuration.'
        @('install', '--config', "`"$ConfigPath`"", '--passive', '--norestart')
    }

    Invoke-ExternalCommand -FilePath $installer -Arguments $arguments | Out-Null

    if ($installationPath) {
        Invoke-ExternalCommand -FilePath $installer -Arguments @('update', '--installpath', "`"$installationPath`"", '--passive', '--norestart') -IgnoreExitCode | Out-Null
    }
}

function Ensure-Uv {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) {
        return $uv.Source
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw 'uv is not installed and Python could not be located to install it.'
    }

    Write-Section 'Installing uv package manager'
    Invoke-ExternalCommand -FilePath $python.Source -Arguments @('-m', 'pip', 'install', '--upgrade', 'pip', 'uv') | Out-Null
    $uv = Get-Command uv -ErrorAction Stop
    return $uv.Source
}

function Invoke-Uv {
    param(
        [string[]]$Arguments
    )

    $uvExe = Ensure-Uv
    Invoke-ExternalCommand -FilePath $uvExe -Arguments $Arguments | Out-Null
}

function Ensure-VirtualEnvironment {
    param(
        [string]$ProjectRoot,
        [switch]$Force
    )

    $venvRoot = Join-Path $ProjectRoot '.venv'
    $pythonExe = Join-Path $venvRoot 'Scripts' 'python.exe'

    if (-not $Force -and (Test-Path $pythonExe)) {
        return $pythonExe
    }

    $arguments = @('sync')
    if ($Force) {
        $arguments += '--reinstall'
    }

    Invoke-Uv -Arguments $arguments

    if (-not (Test-Path $pythonExe)) {
        throw "Expected Python interpreter '$pythonExe' was not created."
    }

    return $pythonExe
}

function Update-PythonDependencies {
    Invoke-Uv -Arguments @('pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel')
    if (Test-Path (Join-Path $ProjectRoot 'requirements.txt')) {
        Invoke-Uv -Arguments @('pip', 'install', '--upgrade', '-r', 'requirements.txt')
    }
}

function Write-CopilotManifest {
    param([string]$Destination)

    $manifest = [ordered]@{
        project            = 'PneumoStabSim Professional'
        profile            = 'Visual Studio Insiders'
        solution           = 'PneumoStabSim-Professional.Insiders.sln'
        entryPoint         = 'app.py'
        primaryLanguage    = 'Python'
        additionalLanguages = @('QML', 'C#')
        tooling            = @('uv', 'pytest', 'ruff', 'mypy', 'qmllint', 'Qt 6.10 / PySide6')
        launchScripts      = @('tools/visualstudio/initialize_insiders_environment.ps1', 'tools/visualstudio/launch_insiders.ps1')
        tests              = @('make check', 'pytest -k smoke -v --tb=short')
        documentation      = @('docs/RENOVATION_MASTER_PLAN.md', 'README.md', 'docs/SETTINGS_ARCHITECTURE.md')
        environment        = [ordered]@{
            PYTHONPATH              = 'src;tests'
            QT_PLUGIN_PATH          = '.venv/Lib/site-packages/PySide6/plugins'
            QML_IMPORT_PATH         = '.venv/Lib/site-packages/PySide6/qml;assets/qml'
            QT_QUICK_CONTROLS_STYLE = 'Basic'
            PNEUMOSTABSIM_PROFILE   = 'insiders'
            PYTHONUTF8              = '1'
            PYTHONIOENCODING        = 'utf-8'
            LC_ALL                  = 'ru-RU'
            LANG                    = 'ru-RU'
        }
    }

    $manifest | ConvertTo-Json -Depth 6 | Set-Content -Path $Destination -Encoding UTF8
}

function Write-EnvironmentDescriptor {
    param(
        [string]$ProjectRoot,
        [string]$PythonExe
    )

    $vsDir = Join-Path $ProjectRoot '.vs'
    Ensure-Directory $vsDir

    $envFile = Join-Path $vsDir 'insiders.environment.json'
    $envData = [ordered]@{
        PYTHONPATH              = "$ProjectRoot;$(Join-Path $ProjectRoot 'src')"
        QML2_IMPORT_PATH        = "$(Join-Path $ProjectRoot '.venv' 'Lib' 'site-packages' 'PySide6' 'qml');$(Join-Path $ProjectRoot 'assets' 'qml')"
        QML_IMPORT_PATH         = "$(Join-Path $ProjectRoot '.venv' 'Lib' 'site-packages' 'PySide6' 'qml');$(Join-Path $ProjectRoot 'assets' 'qml')"
        QT_PLUGIN_PATH          = Join-Path $ProjectRoot '.venv' 'Lib' 'site-packages' 'PySide6' 'plugins'
        QT_QML_IMPORT_PATH      = Join-Path $ProjectRoot '.venv' 'Lib' 'site-packages' 'PySide6' 'qml'
        QT_QUICK_CONTROLS_STYLE = 'Basic'
        PNEUMOSTABSIM_PROFILE   = 'insiders'
        PYTHONUTF8              = '1'
        PYTHONIOENCODING        = 'utf-8'
        LC_ALL                  = 'ru-RU'
        LANG                    = 'ru-RU'
        DOTNET_SYSTEM_GLOBALIZATION_INVARIANT = '0'
        PIP_DISABLE_PIP_VERSION_CHECK        = '1'
        COPILOT_PROJECT_MANIFEST             = Join-Path $ProjectRoot 'tools' 'visualstudio' 'copilot_insiders_manifest.json'
        PYTHONHOME             = Split-Path -Parent $PythonExe
    }

    $envData | ConvertTo-Json -Depth 4 | Set-Content -Path $envFile -Encoding UTF8
    return $envFile
}

function Ensure-LauncherScript {
    param([string]$ProjectRoot)

    $launcherPath = Join-Path $ProjectRoot 'tools' 'visualstudio' 'launch_insiders.ps1'
    if (-not (Test-Path $launcherPath)) {
        throw "Expected launcher script '$launcherPath' to exist."
    }
}

Set-Utf8Console
Write-Section 'Bootstrapping Visual Studio Insiders environment'

if (-not $SkipVisualStudio) {
    Invoke-Step 'Synchronising Visual Studio components' {
        Ensure-VisualStudioComponents -ConfigPath (Join-Path $ProjectRoot 'PneumoStabSim-Professional.insiders.vsconfig')
    }
} else {
    Write-Section 'Skipping Visual Studio component provisioning by request.'
}

$pythonExe = $null
Invoke-Step 'Preparing Python environment with uv' {
    $pythonExe = Ensure-VirtualEnvironment -ProjectRoot $ProjectRoot -Force:$Force.IsPresent
}

Invoke-Step 'Upgrading Python tooling' {
    Update-PythonDependencies
}

Invoke-Step 'Publishing Copilot manifest' {
    Write-CopilotManifest -Destination (Join-Path $ProjectRoot 'tools' 'visualstudio' 'copilot_insiders_manifest.json')
}

$envFile = $null
Invoke-Step 'Writing Visual Studio environment descriptor' {
    $envFile = Write-EnvironmentDescriptor -ProjectRoot $ProjectRoot -PythonExe $pythonExe
}

Invoke-Step 'Validating launch helper' {
    Ensure-LauncherScript -ProjectRoot $ProjectRoot
}

Write-Section "Environment descriptor saved to $envFile"
Write-Section 'Visual Studio Insiders environment is ready.'
