[CmdletBinding()]
param(
    [switch]$SkipUvSync,
    [switch]$SkipUvInstall,
    [switch]$SkipSystem,
    [switch]$SkipQt,
    [string]$QtVersion,
    [string]$PythonPath,
    [string]$SummaryPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$platform = [System.Environment]::OSVersion.Platform
Write-Host "[setup_windows] Detected platform: $platform ($([System.Environment]::OSVersion.VersionString))"
if ($platform -ne [System.PlatformID]::Win32NT) {
    throw "setup_windows.ps1 is only supported on Windows hosts"
}

if (-not $QtVersion) {
    if ($env:QT_VERSION) {
        $QtVersion = $env:QT_VERSION
    } else {
        $QtVersion = '6.10.0'
    }
}

if (-not $SummaryPath -and $env:GITHUB_STEP_SUMMARY) {
    $SummaryPath = $env:GITHUB_STEP_SUMMARY
}

function Write-SetupLog {
    param([string]$Message)
    Write-Host "[setup_windows] $Message"
}

function Invoke-ChocoInstall {
    param(
        [string]$Package
    )

    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-SetupLog "Chocolatey not available; skipping install of $Package"
        return
    }

    try {
        Write-SetupLog "Ensuring Chocolatey package $Package"
        choco install $Package --no-progress -y | Out-Null
    } catch {
        Write-SetupLog "Failed to install $Package via Chocolatey: $_"
    }
}

function Resolve-PythonCommand {
    param([string]$PreferredPath)

    if ($PreferredPath) {
        if (-not (Test-Path $PreferredPath)) {
            throw "Provided PythonPath '$PreferredPath' does not exist"
        }
        return $PreferredPath
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python must be installed before running setup_windows.ps1"
    }
    return $python.Source
}

$pythonPath = Resolve-PythonCommand -PreferredPath $PythonPath
Write-SetupLog "Using Python from $pythonPath"

if (-not $SkipUvInstall -and -not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-SetupLog "uv not found; installing via pip"
    & $pythonPath -m pip install --upgrade pip
    & $pythonPath -m pip install uv
}

if (-not $SkipSystem) {
    Invoke-ChocoInstall -Package 'directx'
    Invoke-ChocoInstall -Package 'vcredist140'
} else {
    Write-SetupLog "Skipping Windows system package installation"
}

if (-not $SkipUvSync) {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-SetupLog "Synchronising Python environment via uv"
        uv sync --extra dev
    } else {
        Write-SetupLog "uv not found; using pip fallback"
        & $pythonPath -m pip install --upgrade pip
        & $pythonPath -m pip install -r requirements-dev.txt
    }
} else {
    Write-SetupLog "Skipping uv sync (per flag)"
}

Write-SetupLog "Installing mandatory Qt/PySide6 wheels"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv pip install --upgrade --no-cache-dir `
        'PySide6>=6.10,<7' `
        'PySide6-Addons>=6.10,<7' `
        'PySide6-Essentials>=6.10,<7' `
        'shiboken6>=6.10,<7' `
        'PyOpenGL==3.1.10' `
        'PyOpenGL-accelerate==3.1.10' `
        'aqtinstall>=3.2.1,<3.3' `
        'pytest-qt'
} else {
    & $pythonPath -m pip install --upgrade --no-cache-dir `
        'PySide6>=6.10,<7' `
        'PySide6-Addons>=6.10,<7' `
        'PySide6-Essentials>=6.10,<7' `
        'shiboken6>=6.10,<7' `
        'PyOpenGL==3.1.10' `
        'PyOpenGL-accelerate==3.1.10' `
        'aqtinstall>=3.2.1,<3.3' `
        'pytest-qt'
}

Write-SetupLog "Provisioning Qt runtime (version $QtVersion)"
$qtBin = $null
$qtPlugins = $null
$qtQml = $null
if (-not $SkipQt) {
    if (-not (Test-Path 'tools/setup_qt.py')) {
        Write-SetupLog "tools/setup_qt.py not found; skipping Qt provisioning"
    } else {
        try {
            & $pythonPath tools/setup_qt.py --qt-version $QtVersion --prune-archives | Out-Null
        } catch {
            Write-SetupLog "Qt provisioning failed: $_"
        }

        $qtArch = 'win64_msvc2019_64'
        $qtRoot = Join-Path (Join-Path (Get-Location) 'Qt') $QtVersion
        $qtArchPath = Join-Path $qtRoot $qtArch
        if (Test-Path $qtArchPath) {
            $qtBin = Join-Path $qtArchPath 'bin'
            $qtPlugins = Join-Path $qtArchPath 'plugins'
            $qtQml = Join-Path $qtArchPath 'qml'
            if ($env:GITHUB_PATH -and (Test-Path $qtBin)) {
                Write-SetupLog "Registering Qt bin path with GITHUB_PATH"
                Add-Content -Path $env:GITHUB_PATH -Value $qtBin
            } elseif (Test-Path $qtBin) {
                Write-SetupLog "Prepending Qt bin to current session PATH"
                $env:PATH = "$qtBin;$($env:PATH)"
            }
        } else {
            Write-SetupLog "Qt arch path $qtArchPath not found after provisioning"
        }
    }
} else {
    Write-SetupLog "Skipping Qt runtime provisioning per flag"
}

if (-not $qtBin) {
    $fallbackArch = 'win64_msvc2019_64'
    $fallbackRoot = Join-Path (Join-Path (Get-Location) 'Qt') $QtVersion
    $fallbackArchPath = Join-Path $fallbackRoot $fallbackArch
    if (Test-Path $fallbackArchPath) {
        Write-SetupLog "Reusing existing Qt runtime at $fallbackArchPath"
        $qtBin = Join-Path $fallbackArchPath 'bin'
        $qtPlugins = Join-Path $fallbackArchPath 'plugins'
        $qtQml = Join-Path $fallbackArchPath 'qml'
        if ($env:GITHUB_PATH -and (Test-Path $qtBin)) {
            Write-SetupLog "Registering Qt bin path with GITHUB_PATH (fallback)"
            Add-Content -Path $env:GITHUB_PATH -Value $qtBin
        } elseif (Test-Path $qtBin) {
            Write-SetupLog "Prepending Qt bin to current session PATH (fallback)"
            $env:PATH = "$qtBin;$($env:PATH)"
        }
    }
}

Write-SetupLog "Exporting headless Qt defaults"
$envContent = @(
    'QT_QPA_PLATFORM=offscreen',
    'QT_QUICK_BACKEND=rhi',
    'QSG_RHI_BACKEND=d3d11',
    'QT_OPENGL=software',
    'QT_LOGGING_RULES=*.debug=false;qt.scenegraph.general=false',
    'QT_QUICK_CONTROLS_STYLE=Fusion',
    'QT_AUTO_SCREEN_SCALE_FACTOR=1',
    'QT_ENABLE_HIGHDPI_SCALING=1',
    'QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough',
    'QT_ASSUME_STDERR_HAS_CONSOLE=1',
    'PSS_HEADLESS=1',
    "QT_VERSION=$QtVersion"
)

if ($qtPlugins) {
    $envContent += "QT_PLUGIN_PATH=$qtPlugins"
}

if ($qtQml) {
    $envContent += "QML2_IMPORT_PATH=$qtQml"
}

$envFile = $env:GITHUB_ENV
if (-not [string]::IsNullOrWhiteSpace($envFile)) {
    Write-SetupLog "Writing environment variables to $envFile"
    foreach ($line in $envContent) {
        Add-Content -Path $envFile -Value $line
    }
} else {
    Write-SetupLog "Applying environment variables to current session"
    foreach ($line in $envContent) {
        $parts = $line.Split('=')
        [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1], 'Process')
    }
}

if ($SummaryPath) {
    Write-SetupLog "Appending setup summary to $SummaryPath"

    $pythonVersion = 'unavailable'
    try {
        $pythonVersion = (& $pythonPath - <<'PY').Trim()
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
PY
    } catch {
        $pythonVersion = "unavailable ($($_.Exception.GetType().Name))"
    }

    $pysideVersion = 'missing'
    try {
        $pysideVersion = (& $pythonPath - <<'PY').Trim()
try:
    import PySide6  # noqa: F401
except Exception as exc:  # pragma: no cover - runtime probe
    print(f"unavailable ({exc.__class__.__name__})")
else:
    import PySide6
    print(getattr(PySide6, '__version__', 'unknown'))
PY
    } catch {
        $pysideVersion = "unavailable ($($_.Exception.GetType().Name))"
    }

    $uvVersion = 'unavailable'
    try {
        $uvVersion = (uv --version) -join ' '
    } catch {
        $uvVersion = "unavailable ($($_.Exception.GetType().Name))"
    }

    $systemPackages = $SkipSystem ? '<skipped>' : 'directx, vcredist140'
    $summaryLines = @(
        '### setup_windows.ps1 summary',
        "- Platform: $platform ($([System.Environment]::OSVersion.VersionString))",
        "- Qt version requested: $QtVersion (SkipQt=$SkipQt)",
        "- System packages targeted: $systemPackages",
        "- Python ($pythonPath): $pythonVersion",
        "- uv: $uvVersion",
        "- PySide6: $pysideVersion",
        "- QT_PLUGIN_PATH: $($qtPlugins ?? '<empty>')",
        "- QML2_IMPORT_PATH: $($qtQml ?? '<empty>')",
        ""
    )

    Add-Content -Path $SummaryPath -Value $summaryLines -Encoding UTF8
}

Write-SetupLog "Windows environment bootstrap complete"
