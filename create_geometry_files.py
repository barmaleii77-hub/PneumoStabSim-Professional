#!/usr/bin/env python3
"""Create missing geometry QML files"""
from pathlib import Path

# Frame.qml
frame_qml = '''import QtQuick
import QtQuick3D

Node {
    id: frame
    required property Node worldRoot
    required property real beamSize
    required property real frameHeight
    required property real frameLength
    required property var frameMaterial
    
    Model {
        parent: worldRoot
        source: "#Cube"
        position: Qt.vector3d(0, beamSize/2, frameLength/2)
        scale: Qt.vector3d(beamSize/100, beamSize/100, frameLength/100)
        materials: [frameMaterial]
    }
    
    Model {
        parent: worldRoot
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, beamSize/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: [frameMaterial]
    }
    
    Model {
        parent: worldRoot
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, frameLength - beamSize/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: [frameMaterial]
    }
}
'''

# CylinderGeometry.qml (placeholder)
cylinder_qml = '''import QtQuick
import QtQuick3D

Model {
    id: cylinderGeometry
    source: "#Cylinder"
}
'''

# SuspensionCorner.qml (placeholder - will use inline version from main.qml)
suspension_qml = '''import QtQuick
import QtQuick3D

// TODO: Extract from main.qml OptimizedSuspensionCorner
Node {
    id: suspensionCorner
}
'''

# Write files
Path('assets/qml/geometry/Frame.qml').write_text(frame_qml, encoding='utf-8')
Path('assets/qml/geometry/CylinderGeometry.qml').write_text(cylinder_qml, encoding='utf-8')
Path('assets/qml/geometry/SuspensionCorner.qml').write_text(suspension_qml, encoding='utf-8')

print("✅ Created 3 geometry QML files")
