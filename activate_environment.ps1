# ============================================================================
# PneumoStabSim Professional - Environment Activation Script
# Активация окружения в текущей PowerShell сессии
# ============================================================================

$ProjectRoot = $PSScriptRoot

# Import .env file if exists
$envFile = Join-Path $ProjectRoot ".env"
if (Test-Path $envFile) {
    Write-Host "📋 Loading environment from .env..." -ForegroundColor Cyan
    
    Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
  $name = $matches[1].Trim()
         $value = $matches[2].Trim()

        # Remove quotes if present
            $value = $value -replace '^"(.*)"$', '$1'
            $value = $value -replace "^'(.*)'$", '$1'
       
      Set-Item -Path "env:$name" -Value $value
         Write-Host "  ✅ $name" -ForegroundColor Green
    }
    }
    
    Write-Host "`n✅ Environment activated!" -ForegroundColor Green
    Write-Host "📦 PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
    Write-Host "🎨 QT Backend: $env:QSG_RHI_BACKEND" -ForegroundColor Gray
    
} else {
    Write-Host "⚠️  .env file not found. Run setup_all_paths.ps1 first." -ForegroundColor Yellow
}
