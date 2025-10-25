param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8
try {
    chcp.com 65001 | Out-Null
} catch {
    Write-Warning "Unable to switch code page to UTF-8: $($_.Exception.Message)"
}
Set-Item -Path env:PYTHONUTF8 -Value '1'
Set-Item -Path env:PYTHONIOENCODING -Value 'utf-8'
Set-Item -Path env:PIP_DISABLE_PIP_VERSION_CHECK -Value '1'
Set-Item -Path env:PIP_NO_PYTHON_VERSION_WARNING -Value '1'
Set-Item -Path env:LC_ALL -Value 'C.UTF-8'
Set-Item -Path env:LANG -Value 'en_US.UTF-8'

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
