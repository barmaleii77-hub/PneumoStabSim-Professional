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
