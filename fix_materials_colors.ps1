# Скрипт восстановления цветов материалов
$json = Get-Content config/app_settings.json | ConvertFrom-Json

# Правильные цвета
$correctColors = @{
    'frame' = '#7dff69'
    'lever' = '#ff2e66'
    'tail' = '#ff0004'
    'cylinder' = '#5bff3e'
    'piston_body' = '#2f44ff'
    'piston_rod' = '#5bff3e'
    'joint_tail' = '#ff0004'
    'joint_arm' = '#1eff5e'
    'joint_rod' = '#00ff55'
}

# Восстанавливаем в current
foreach ($mat in $correctColors.Keys) {
    $json.current.graphics.materials.$mat.base_color = $correctColors[$mat]
}

# Восстанавливаем в defaults
foreach ($mat in $correctColors.Keys) {
    $json.defaults_snapshot.graphics.materials.$mat.base_color = $correctColors[$mat]
}

# Сохраняем
$json | ConvertTo-Json -Depth 20 | Set-Content config/app_settings.json -Encoding UTF8

Write-Host "OK - Materials colors restored!"
