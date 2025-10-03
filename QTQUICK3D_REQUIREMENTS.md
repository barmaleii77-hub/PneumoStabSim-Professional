# Qt Quick 3D Dependencies for PneumoStabSim

## CRITICAL: Qt Quick 3D requires PySide6-Addons

Install with:
```
pip install PySide6-Addons
```

This provides:
- QtQuick
- QtQml  
- QtQuick3D (for View3D, PBR materials, lighting)

## Full dependency list:
```
PySide6>=6.8.0
PySide6-Addons>=6.8.0
numpy>=2.0.0
scipy>=1.14.0
```

## Verification:
```python
from PySide6 import QtQuick, QtQml
from PySide6.QtQuick3D import *
print("? Qt Quick 3D available")
```

## Backend verification:
After running app.py, console should show:
```
rhi: backend: D3D11
```

If it shows "OpenGL" instead, check:
1. QSG_RHI_BACKEND=d3d11 env var is set before Qt import
2. Graphics drivers support Direct3D 11
