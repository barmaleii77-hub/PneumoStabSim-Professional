$userPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
$uniquePaths = $userPath -split ';' | Where-Object { $_ -ne '' } | Select-Object -Unique
$cleanPaths = @()
$lmstudioAdded = $false

foreach ($p in $uniquePaths) {
    if ($p -like '*lmstudio*') {
        if (-not $lmstudioAdded) {
            $cleanPaths += 'C:\Users\Алексей\.lmstudio\bin'
            $lmstudioAdded = $true
        }
    } else {
        $cleanPaths += $p
    }
}

$pythonBase = 'C:\Users\Алексей\AppData\Local\Programs\Python\Python313'
if (Test-Path $pythonBase) {
    if ($cleanPaths -notcontains $pythonBase) {
        $cleanPaths += $pythonBase
    }
    if ($cleanPaths -notcontains "$pythonBase\Scripts") {
        $cleanPaths += "$pythonBase\Scripts"
    }
}

$newPath = ($cleanPaths -join ';')
[Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
Write-Host "✅ PATH cleaned and Python added"
