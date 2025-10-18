import QtQuick
import QtQuick3D

/*
 * PointLights - Модуль точечных источников света
 * Управляет акцентным освещением
 * 
 * Использование:
 *   PointLights {
 *       worldRoot: someNode
 *       cameraRig: cameraNode
 *       pointLightBrightness: 1000.0
 *       ...
 *   }
 */
Node {
    id: root
    
    // ===============================================================
    // REQUIRED PROPERTIES (must be set by parent)
    // ===============================================================
    
    required property Node worldRoot
    required property Node cameraRig
    
    // ===============================================================
    // POINT LIGHT PROPERTIES
    // ===============================================================
    
    property real pointLightBrightness: 1000.0
    property color pointLightColor: "#ffffff"
    property real pointLightX: 0.0
    property real pointLightY: 2200.0
    property real pointLightRange: 3200.0
    property bool pointLightCastsShadow: false
    property bool pointLightBindToCamera: false
    
    // ===============================================================
    // ACCENT POINT LIGHT (акцентный точечный свет)
    // ===============================================================
    
    PointLight {
        id: accentLight
        parent: root.pointLightBindToCamera ? root.cameraRig : root.worldRoot
        
        position: Qt.vector3d(root.pointLightX, root.pointLightY, 1500)
        
        brightness: root.pointLightBrightness
        color: root.pointLightColor
        
        castsShadow: root.pointLightCastsShadow
        
        // ✅ Атеняция (затухание света с расстоянием)
        constantFade: 1.0
        linearFade: 2.0 / Math.max(200.0, root.pointLightRange)
        quadraticFade: 1.0 / Math.pow(Math.max(200.0, root.pointLightRange), 2)
    }
    
    // ===============================================================
    // DEBUG (опционально)
    // ===============================================================
    
    Component.onCompleted: {
        console.log("💡 PointLights initialized:")
        console.log("   Brightness:", pointLightBrightness)
        console.log("   Position: (", pointLightX, ",", pointLightY, ", 1500 )")
        console.log("   Range:", pointLightRange)
        console.log("   Casts shadow:", pointLightCastsShadow)
    }
}
