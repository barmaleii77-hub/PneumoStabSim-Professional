#!/usr/bin/env python
"""
Create geometry qmldir file
"""

with open("assets/qml/geometry/qmldir", "w", encoding="utf-8") as f:
    f.write(
        """# QML Module Definition for Geometry Components
# Модули геометрии подвески

module geometry

# Core geometry components
Frame 1.0 Frame.qml
SuspensionCorner 1.0 SuspensionCorner.qml
CylinderGeometry 1.0 CylinderGeometry.qml

# Component descriptions
typeinfo geometry.qmltypes
"""
    )

print("✅ Created assets/qml/geometry/qmldir")
