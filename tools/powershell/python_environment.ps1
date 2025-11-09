# ============================================================================
# Shared helper functions for selecting the preferred Python interpreter.
# The logic prefers the highest CPython version installed (>= 3.12 when
# available) and exposes rich metadata for callers.
# ============================================================================

Set-StrictMode -Version Latest

function Get-PythonVersionFromExecutable {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable
    )

    try {
        $result = & $Executable '--version' 2>&1
        if ($LASTEXITCODE -ne 0) {
            return $null
        }

        if ($result -match 'Python\s+(?<version>\d+\.\d+\.\d+)') {
            return [Version]$Matches['version']
        }
    } catch {
        return $null
    }

    return $null
}

function Get-PyLauncherInstallations {
    $installations = @()
    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if (-not $pyLauncher) {
        return $installations
    }

    $output = & $pyLauncher.Source '-0p' 2>$null
    foreach ($line in $output) {
        if ($line -match '^\s*-(?<version>\d+\.\d+)(?:-[^\s]*)?\s+(?<path>[A-Za-z]:\\[^\s*]+python\.exe)') {
            $versionValue = [Version]::Parse("$($Matches['version']).0")
            $pathValue = $Matches['path']
            if (Test-Path $pathValue) {
                $installations += [PSCustomObject]@{
                    Version = $versionValue
                    Path    = $pathValue
                    Source  = 'py'
                }
            }
        }
    }

    return $installations
}

function Get-PathBasedInstallations {
    $installations = @()
    $candidates = @(
        'python3.13',
        'python3.12',
        'python3.11',
        'python3',
        'python'
    )

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $command) {
            continue
        }

        $path = $command.Source
        if (-not (Test-Path $path)) {
            continue
        }

        if ($installations | Where-Object { $_.Path -eq $path }) {
            continue
        }

        $version = Get-PythonVersionFromExecutable -Executable $path
        if ($null -ne $version) {
            $installations += [PSCustomObject]@{
                Version = $version
                Path    = $path
                Source  = 'path'
            }
        }
    }

    return $installations
}

function Get-AvailablePythonInstallations {
    $fromLauncher = Get-PyLauncherInstallations
    $fromPath = Get-PathBasedInstallations

    $all = $fromLauncher + $fromPath
    if (-not $all) {
        return @()
    }

    $unique = $all | Group-Object -Property Path | ForEach-Object {
        $_.Group | Sort-Object -Property Version -Descending | Select-Object -First 1
    }

    return $unique | Sort-Object -Property Version -Descending
}

function Get-PreferredPython {
    param(
        [Version]$MinimumVersion = [Version]'3.12.0'
    )

    $installations = Get-AvailablePythonInstallations
    if (-not $installations) {
        return $null
    }

    $preferred = $installations |
        Where-Object { $_.Version -ge $MinimumVersion } |
        Sort-Object -Property Version -Descending |
        Select-Object -First 1

    if (-not $preferred) {
        $preferred = $installations | Select-Object -First 1
    }

    return $preferred
}

function Set-PSSLoggingPreset {
    param(
        [ValidateSet('normal', 'debug', 'trace')]
        [string]$Preset = 'normal'
    )

    $env:PSS_LOG_PRESET = $Preset
    return $Preset
}

