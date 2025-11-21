<#!
.SYNOPSIS
  PowerShell wrapper for make.bat so you can run 'make <target>' directly in PS.
.DESCRIPTION
  Fixes issue where PowerShell does not search current directory automatically.
  Usage:
    make render-diagnostics --qml-snapshot
    make verify
.NOTES
  Add this directory to PATH or create an alias for persistent usage.
#>
[CmdletBinding()]param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $scriptDir 'make.bat'
if (-not (Test-Path $bat)) { Write-Error "make.bat not found at $bat"; exit 1 }
& $bat @Args
$exitCode = $LASTEXITCODE
exit $exitCode
