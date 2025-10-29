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

    property real pointLightBrightness: 50.0
    property color pointLightColor: "#fff7e0"
    property real pointLightX: 0.0
    property real pointLightY: 2.6
    property real pointLightZ: 1.5
    property real pointLightRange: 3.6
    property real constantFade: 1.0
    property real linearFade: 0.01
    property real quadraticFade: 1.0
    property bool pointLightCastsShadow: false
    property bool pointLightBindToCamera: false

    // ===============================================================
    // ACCENT POINT LIGHT (акцентный точечный свет)
    // ===============================================================

    PointLight {
        id: accentLight
        parent: root.pointLightBindToCamera ? root.cameraRig : root.worldRoot

        position: Qt.vector3d(root.pointLightX, root.pointLightY, root.pointLightZ)

        brightness: root.pointLightBrightness
        color: root.pointLightColor

        castsShadow: root.pointLightCastsShadow

        // ✅ Атеняция (затухание света с расстоянием)
        constantFade: root.constantFade
        linearFade: root.linearFade
        quadraticFade: root.quadraticFade
    }

    // ===============================================================
    // DEBUG (опционально)
    // ===============================================================

    Component.onCompleted: {
        console.log("💡 PointLights initialized:")
        console.log("   Brightness:", pointLightBrightness)
        console.log("   Position: (", pointLightX, ",", pointLightY, ",", pointLightZ, ")")
        console.log("   Range:", pointLightRange)
        console.log("   Fade (const/lin/quad):", constantFade, linearFade, quadraticFade)
        console.log("   Casts shadow:", pointLightCastsShadow)
    }
}
