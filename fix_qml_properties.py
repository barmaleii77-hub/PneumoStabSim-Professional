#!/usr/bin/env python3
"""
Fix QML property name mismatches
"""
from pathlib import Path

MAIN_QML = Path("assets/qml/main.qml")

content = MAIN_QML.read_text(encoding="utf-8")

# Replace property names
replacements = {
    "depthOfFieldEnabled: root.depthOfFieldEnabled": "internalDepthOfFieldEnabled: root.depthOfFieldEnabled",
    "vignetteEnabled: root.vignetteEnabled": "internalVignetteEnabled: root.vignetteEnabled",
    "vignetteStrength: root.vignetteStrength": "internalVignetteStrength: root.vignetteStrength",
    "lensFlareEnabled: root.lensFlareEnabled": "internalLensFlareEnabled: root.lensFlareEnabled",
}

for old, new in replacements.items():
    content = content.replace(old, new)

MAIN_QML.write_text(content, encoding="utf-8")
print("✅ Fixed property names in main.qml")
