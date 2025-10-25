[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path,

    [Parameter(Mandatory = $false)]
    [string]$VsConfigPath = (Join-Path $ProjectRoot 'PneumoStabSim-Professional.insiders.vsconfig')
)

$ErrorActionPreference = 'Stop'

function Write-Info {
    param([string]$Message)
    Write-Host "[VS Components] $Message" -ForegroundColor DarkCyan
}

if (-not (Test-Path $VsConfigPath)) {
    Write-Info "Visual Studio configuration '$VsConfigPath' not found. Skipping component validation."
    return
}

$vsConfig = Get-Content -Raw -Path $VsConfigPath | ConvertFrom-Json
$requiredComponents = @()
if ($vsConfig.components) {
    $requiredComponents = @($vsConfig.components | Sort-Object -Unique)
}

if (-not $requiredComponents) {
    Write-Info 'No components declared in the VS configuration. Nothing to validate.'
    return
}

$vswhereCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\\Installer\\vswhere.exe'),
    (Join-Path ${env:ProgramFiles} 'Microsoft Visual Studio\\Installer\\vswhere.exe')
) | Where-Object { $_ -and (Test-Path $_) }

if (-not $vswhereCandidates) {
    Write-Info 'vswhere.exe was not located. Install Visual Studio Installer to enable automatic workload validation.'
    return
}

$vswhere = $vswhereCandidates | Select-Object -First 1
$installerExe = Join-Path (Split-Path $vswhere) 'vs_installer.exe'

if (-not (Test-Path $installerExe)) {
    Write-Info "Visual Studio installer binary '$installerExe' was not found."
    return
}

$instanceJson = & $vswhere -prerelease -format json 2>$null
if (-not $instanceJson) {
    Write-Info 'No Visual Studio instances detected via vswhere. Ensure Visual Studio Insiders is installed.'
    return
}

$instances = $instanceJson | ConvertFrom-Json
if ($instances -isnot [System.Collections.IEnumerable]) {
    $instances = @($instances)
}

$insidersInstance = $instances | Where-Object {
    $_.catalog.channelId -like '*Preview*' -or $_.isPrerelease -eq $true
} | Sort-Object -Property @{Expression = 'installationVersion'; Descending = $true} | Select-Object -First 1

if (-not $insidersInstance) {
    Write-Info 'Could not locate a Visual Studio Insiders/Preview instance. Skipping workload validation.'
    return
}

$installedPackages = @()
if ($insidersInstance.packages) {
    $installedPackages = @($insidersInstance.packages | Select-Object -ExpandProperty id)
}

$missing = $requiredComponents | Where-Object { $_ -notin $installedPackages }

if ($missing) {
    Write-Info "Installing missing Visual Studio components: $($missing -join ', ')"
    $args = @(
        'modify',
        "--installPath", $insidersInstance.installationPath,
        '--passive',
        '--norestart'
    )
    foreach ($component in $missing) {
        $args += '--add'
        $args += $component
    }
    & $installerExe @args
} else {
    Write-Info 'All required Visual Studio components are already present.'
}

Write-Info 'Requesting Visual Studio Insiders update check (passive).'
& $installerExe 'update' '--passive' '--norestart' '--quiet' '--installPath' $insidersInstance.installationPath 2>$null
