#!/usr/bin/env pwsh
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
$ErrorActionPreference = 'Stop'
& "$PSScriptRoot/activate_venv.bat" | Out-Null
python "$PSScriptRoot/app.py" @Args
