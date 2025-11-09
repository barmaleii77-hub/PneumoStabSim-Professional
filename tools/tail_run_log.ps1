[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$LogPath = "logs/run.log",

    [Parameter(Position = 1)]
    [string[]]$Pattern = @(),

    [int]$Tail = 150,

    [switch]$CaseSensitive,

    [ValidateSet('normal', 'debug', 'trace')]
    [string]$LogPreset
)

# Ensure consistent UTF-8 output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

try {
    if (-not $LogPath) {
        throw "Не указан путь к файлу лога."
    }

    $resolvedPath = Resolve-Path -LiteralPath $LogPath -ErrorAction SilentlyContinue
    if (-not $resolvedPath) {
        throw "Файл лога не найден: $LogPath"
    }
    $logFile = $resolvedPath.ProviderPath

    if ($PSBoundParameters.ContainsKey('LogPreset') -and $LogPreset) {
        $env:PSS_LOG_PRESET = $LogPreset
        Write-Host "ℹ️ Logging preset: $LogPreset" -ForegroundColor Cyan
    }

    $tailLines = if ($Tail -gt 0) { [int]$Tail } else { 1 }

    Write-Host "📄 Лог: $logFile" -ForegroundColor Cyan
    Write-Host "➡️  Последние $tailLines строк" -ForegroundColor Cyan
    Write-Host "" 

    Get-Content -LiteralPath $logFile -Tail $tailLines

    if ($Pattern.Count -gt 0) {
        Write-Host "" 
        Write-Host "🔎 Совпадения (Select-String)" -ForegroundColor Yellow

        $selectParams = @{
            Path        = $logFile
            Pattern     = $Pattern
            AllMatches  = $true
            SimpleMatch = $true
        }

        if ($CaseSensitive.IsPresent) {
            $selectParams["CaseSensitive"] = $true
        }

        $matches = Select-String @selectParams | Sort-Object LineNumber

        if ($matches) {
            foreach ($match in $matches) {
                $lineInfo = "[{0}] {1}" -f $match.LineNumber, $match.Line
                Write-Host $lineInfo -ForegroundColor Magenta
            }
        }
        else {
            Write-Host "Совпадения не найдены" -ForegroundColor DarkGray
        }
    }
}
catch {
    Write-Host "❌ $_" -ForegroundColor Red
    exit 1
}
