[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path,

    [Parameter(Mandatory = $false)]
    [string]$ProfilePath = (Join-Path $PSScriptRoot 'copilot_insiders_profile.json')
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ProfilePath)) {
    Write-Warning "Copilot profile '$ProfilePath' was not found."
    return
}

$profileContent = Get-Content -Raw -Path $ProfilePath | ConvertFrom-Json
$profileContent.projectRoot = $ProjectRoot
$profileContent.lastUpdated = (Get-Date).ToString('o')

$copilotDir = $null
if ($env:APPDATA) {
    $copilotDir = Join-Path $env:APPDATA 'GitHubCopilot'
} elseif ($env:LOCALAPPDATA) {
    $copilotDir = Join-Path $env:LOCALAPPDATA 'GitHubCopilot'
} else {
    $copilotDir = Join-Path $ProjectRoot '.vs' 'copilot-cache'
}

if (-not (Test-Path $copilotDir)) {
    New-Item -ItemType Directory -Path $copilotDir -Force | Out-Null
}

$targetFile = Join-Path $copilotDir 'PneumoStabSim-Professional-insiders.json'
$profileContent | ConvertTo-Json -Depth 8 | Set-Content -Path $targetFile -Encoding UTF8

Set-Item -Path env:GITHUB_COPILOT_METADATA_PATH -Value $targetFile

Write-Host "[Copilot] Updated project metadata at '$targetFile'" -ForegroundColor DarkGreen
