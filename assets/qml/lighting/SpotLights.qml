import QtQuick
import QtQuick3D

/*
 * SpotLights - Модуль прожекторного освещения
 * Управляет направленным источником с ограниченным конусом
 *
 * Использование:
 *   SpotLights {
 *       worldRoot: someNode
 *       cameraRig: cameraNode
 *       spotLightBrightness: 1200.0
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
    // SPOT LIGHT PROPERTIES
    // ===============================================================

    property real spotLightBrightness: 0.0
    property color spotLightColor: "#ffffff"
    property real spotLightX: 0.0
    property real spotLightY: 1.0
    property real spotLightZ: 0.0
    property real spotLightRange: 5.0
    property real spotLightAngleX: 0.0
    property real spotLightAngleY: 0.0
    property real spotLightAngleZ: 0.0
    property real spotLightConeAngle: 30.0
    property real spotLightInnerConeAngle: 15.0
    property bool spotLightCastsShadow: false
    property bool spotLightBindToCamera: false

    readonly property real _outerCone: Math.max(1.0, spotLightConeAngle)
    readonly property real _innerCone: Math.max(
        0.0,
        Math.min(spotLightInnerConeAngle, _outerCone - 0.1)
    )

    SpotLight {
        id: spotLight
        parent: root.spotLightBindToCamera ? root.cameraRig : root.worldRoot

        position: Qt.vector3d(root.spotLightX, root.spotLightY, root.spotLightZ)
        eulerRotation: Qt.vector3d(
            root.spotLightAngleX,
            root.spotLightAngleY,
            root.spotLightAngleZ
        )

        brightness: root.spotLightBrightness
        color: root.spotLightColor
        range: root.spotLightRange
        coneAngle: root._outerCone
        innerConeAngle: root._innerCone
        castsShadow: root.spotLightCastsShadow
    }

    Component.onCompleted: {
        console.log("💡 SpotLights initialized:")
        console.log("   Brightness:", spotLightBrightness)
        console.log("   Color:", spotLightColor)
        console.log("   Position:", spotLightX, spotLightY, spotLightZ)
        console.log("   Angles:", spotLightAngleX, spotLightAngleY, spotLightAngleZ)
        console.log("   Range:", spotLightRange)
        console.log("   Cone (inner/outer):", _innerCone, _outerCone)
        console.log("   Casts shadow:", spotLightCastsShadow)
    }
}
