[CmdletBinding()]
param(
    [Parameter()]
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

Set-StrictMode -Version Latest

function Initialize-Encoding {
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)

    try {
        [Console]::OutputEncoding = $utf8NoBom
        [Console]::InputEncoding = $utf8NoBom
        $global:OutputEncoding = $utf8NoBom
    } catch {
        Write-Verbose 'Unable to update console encodings; continuing with defaults.'
    }

    if ($Host -and $Host.UI -and $Host.UI.SupportsVirtualTerminal) {
        $PSStyle.OutputRendering = 'Host'
    }

    if (Get-Module -ListAvailable -Name PSReadLine) {
        try {
            Set-PSReadLineOption -BellStyle None -HistorySearchCursorMovesToEnd:$true -ErrorAction Stop
            Set-PSReadLineOption -PredictionSource HistoryAndPlugin -PredictionViewStyle ListView -ErrorAction Stop
        } catch {
            Write-Verbose 'Unable to tune PSReadLine options; continuing with defaults.'
        }
    }

    $PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
    $PSDefaultParameterValues['*:Encoding'] = 'utf8'

    if (Get-Command chcp -ErrorAction SilentlyContinue) {
        try {
            chcp 65001 | Out-Null
        } catch {
            Write-Verbose 'Failed to switch active code page to UTF-8 via chcp.'
        }
    }
}

Initialize-Encoding

function Get-VsInstallerExecutable {
    $programFilesX86 = ${env:ProgramFiles(x86)}
    if (-not $programFilesX86) {
        return $null
    }

    $candidate = Join-Path $programFilesX86 'Microsoft Visual Studio' 'Installer' 'vs_installer.exe'
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

    $candidate = Join-Path $programFilesX86 'Microsoft Visual Studio' 'Installer' 'vswhere.exe'
    if (Test-Path $candidate) {
        return $candidate
    }

    return $null
}

function Ensure-VisualStudioComponents {
    param(
        [string]$ConfigPath
    )

    if (-not (Test-Path $ConfigPath)) {
        throw "Visual Studio configuration '$ConfigPath' is missing."
    }

    $vsInstaller = Get-VsInstallerExecutable
    if (-not $vsInstaller) {
        Write-Warning 'Visual Studio Installer was not located. Install Visual Studio Installer to process PneumoStabSim Insiders configuration.'
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
            Write-Verbose 'Failed to query Visual Studio instances using vswhere.'
        }
    }

    if (-not $installationPath) {
        Write-Warning 'Visual Studio Insiders installation was not detected; the installer will run with the supplied vsconfig.'
        $arguments = @('install', '--config', "`"$ConfigPath`"", '--passive', '--norestart')
    } else {
        $arguments = @('modify', '--installpath', "`"$installationPath`"", '--config', "`"$ConfigPath`"", '--passive', '--norestart')
    }

    Write-Verbose "Running Visual Studio Installer with arguments: $($arguments -join ' ')"

    $process = Start-Process -FilePath $vsInstaller -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -ne 0) {
        throw "Visual Studio Installer reported exit code $($process.ExitCode)."
    }

    if ($installationPath) {
        $updateArgs = @('update', '--installpath', "`"$installationPath`"", '--passive', '--norestart')
        Write-Verbose "Checking for Visual Studio updates with arguments: $($updateArgs -join ' ')"
        $updateProcess = Start-Process -FilePath $vsInstaller -ArgumentList $updateArgs -Wait -PassThru -WindowStyle Hidden
        if ($updateProcess.ExitCode -ne 0) {
            Write-Warning "Visual Studio update command exited with code $($updateProcess.ExitCode)."
        }
    }
}

function Publish-CopilotManifest {
    param(
        [string]$Destination
    )

    $manifest = [ordered]@{
        project            = 'PneumoStabSim Professional'
        profile            = 'insiders'
        solution           = 'PneumoStabSim-Professional.Insiders.sln'
        entryPoint         = 'app.py'
        languages          = @('Python', 'QML', 'C#')
        tooling            = @('Qt 6.10 / PySide6', 'uv virtual environments', 'pytest', 'ruff', 'mypy', 'qmllint')
        launchScripts      = @('tools/visualstudio/initialize_insiders_environment.ps1', 'tools/visualstudio/launch_insiders.ps1')
        environment        = @{
            PYTHONPATH                     = 'src;tests'
            QT_PLUGIN_PATH                 = '.venv/Lib/site-packages/PySide6/plugins'
            QML_IMPORT_PATH                = '.venv/Lib/site-packages/PySide6/qml;assets/qml'
            QT_QUICK_CONTROLS_STYLE        = 'Basic'
            PNEUMOSTABSIM_PROFILE          = 'insiders'
            LC_ALL                         = 'ru-RU'
            LANG                           = 'ru-RU'
            PYTHONUTF8                     = '1'
        }
        codingGuidelines   = @(
            'Prefer SettingsManager for configuration updates',
            'Use structlog JSON logger for new diagnostics',
            'Maintain Russian/English localisation parity in assets/i18n'
        )
        testCommands       = @('make check', 'pytest -k smoke', 'python qml_diagnostic.py')
        documentationLinks = @(
            'docs/RENOVATION_MASTER_PLAN.md',
            'docs/SETTINGS_ARCHITECTURE.md',
            'README.md'
        )
    }

    $manifest | ConvertTo-Json -Depth 6 | Set-Content -Path $Destination -Encoding UTF8
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

Write-Section 'Bootstrapping Visual Studio Insiders environment'

$preferredLocale = 'ru-RU'
try {
    $culture = [System.Globalization.CultureInfo]::new($preferredLocale)
    [System.Globalization.CultureInfo]::DefaultThreadCurrentCulture = $culture
    [System.Globalization.CultureInfo]::DefaultThreadCurrentUICulture = $culture
} catch {
    Write-Verbose "Unable to switch PowerShell culture to '$preferredLocale'."
}

$globalEnv = [ordered]@{
    PYTHONUTF8                      = '1'
    PYTHONIOENCODING                = 'utf-8'
    LC_ALL                          = $preferredLocale
    LANG                            = $preferredLocale
    PIP_DISABLE_PIP_VERSION_CHECK   = '1'
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT = '0'
}

foreach ($entry in $globalEnv.GetEnumerator()) {
    Set-Item -Path "env:$($entry.Key)" -Value $entry.Value -Force
}

if (-not (Test-Path $ProjectRoot)) {
    throw "Project root '$ProjectRoot' was not found."
}

$vsConfigPath = Join-Path $ProjectRoot 'PneumoStabSim-Professional.insiders.vsconfig'

Invoke-Step 'Synchronizing Visual Studio Insiders components' {
    Ensure-VisualStudioComponents -ConfigPath $vsConfigPath
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

Invoke-Step 'Refreshing Python packages to the latest compatible versions' {
    $outdatedJson = & $pythonExe '-m' 'pip' 'list' '--outdated' '--format' 'json'
    $outdated = @()
    if ($outdatedJson) {
        try {
            $outdated = $outdatedJson | ConvertFrom-Json
        } catch {
            Write-Verbose 'Failed to parse pip outdated packages output.'
        }
    }

    if (-not $outdated -or $outdated.Count -eq 0) {
        Write-Host 'All Python dependencies are already up to date.' -ForegroundColor Green
    } else {
        foreach ($package in $outdated) {
            $name = $package.name
            $latest = $package.latest_version
            Write-Host "Upgrading $name -> $latest" -ForegroundColor Yellow
            Invoke-PipInstall @('install', '--upgrade', $name)
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
    PYTHONIOENCODING      = 'utf-8'
    PYTHONUTF8            = '1'
    LC_ALL                = $preferredLocale
    LANG                  = $preferredLocale
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT = '0'
    COPILOT_PROJECT_MANIFEST = (Join-Path $ProjectRoot 'tools' 'visualstudio' 'copilot_insiders_manifest.json')
}

$insidersEnvFile = Join-Path $ProjectRoot '.vs' 'insiders.environment.json'

Invoke-Step "Persisting Insiders environment definition to '$insidersEnvFile'" {
    $insidersDir = Split-Path $insidersEnvFile -Parent
    if (-not (Test-Path $insidersDir)) {
        New-Item -ItemType Directory -Path $insidersDir | Out-Null
    }
    $envConfig | ConvertTo-Json -Depth 4 | Set-Content -Path $insidersEnvFile -Encoding UTF8
}

$copilotManifest = Join-Path $ProjectRoot 'tools' 'visualstudio' 'copilot_insiders_manifest.json'

Invoke-Step "Publishing Copilot manifest to '$copilotManifest'" {
    Publish-CopilotManifest -Destination $copilotManifest
}

$launcherScript = Join-Path $ProjectRoot 'tools' 'visualstudio' 'launch_insiders.ps1'

Invoke-Step "Generating launch helper at '$launcherScript'" {
    $launcherContent = @'
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
try {
    [Console]::OutputEncoding = $utf8NoBom
    [Console]::InputEncoding = $utf8NoBom
    $global:OutputEncoding = $utf8NoBom
} catch {
    Write-Verbose 'Unable to configure console encodings for launch script.'
}

if ($Host -and $Host.UI -and $Host.UI.SupportsVirtualTerminal) {
    $PSStyle.OutputRendering = 'Host'
}

if (Get-Module -ListAvailable -Name PSReadLine) {
    try {
        Set-PSReadLineOption -BellStyle None -HistorySearchCursorMovesToEnd:$true -ErrorAction Stop
    } catch {
        Write-Verbose 'Unable to tune PSReadLine options; continuing with defaults.'
    }
}

if (Get-Command chcp -ErrorAction SilentlyContinue) {
    try { chcp 65001 | Out-Null } catch { Write-Verbose 'Failed to set code page to UTF-8 during launch.' }
}

$envFile = Join-Path $ProjectRoot '.vs' 'insiders.environment.json'
if (-not (Test-Path $envFile)) {
    Write-Warning "Environment description '$envFile' was not found. Running initializer."
    $initializer = Join-Path $ProjectRoot 'tools' 'visualstudio' 'initialize_insiders_environment.ps1'
    if (-not (Test-Path $initializer)) {
        throw "Initializer script '$initializer' is missing; cannot prepare launch environment."
    }

    & $initializer -ProjectRoot $ProjectRoot | Out-Null

    if (-not (Test-Path $envFile)) {
        throw "Environment description '$envFile' could not be generated by initializer."
    }
}

$envData = Get-Content $envFile -Encoding UTF8 | ConvertFrom-Json

foreach ($entry in $envData.PSObject.Properties) {
    [System.Environment]::SetEnvironmentVariable($entry.Name, $entry.Value)
    Set-Item -Path env:$($entry.Name) -Value $entry.Value -Force
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
