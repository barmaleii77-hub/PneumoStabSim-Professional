import QtQuick
import QtQuick3D

/*
 * DirectionalLights - Модуль направленных источников света
 * Управляет Key, Fill и Rim освещением
 *
 * Использование:
 *   DirectionalLights {
 *       worldRoot: someNode
 *       cameraRig: cameraNode
 *       keyLightBrightness: 1.2
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
    required property bool shadowsEnabled
    required property string shadowResolution
    required property int shadowFilterSamples
    required property real shadowBias
    required property real shadowFactor

    // ===============================================================
    // KEY LIGHT PROPERTIES
    // ===============================================================

    property real keyLightBrightness: 1.2
    property color keyLightColor: "#ffffff"
    property real keyLightAngleX: -35
    property real keyLightAngleY: -40
    property bool keyLightCastsShadow: true
    property bool keyLightBindToCamera: false
    property real keyLightPosX: 0.0
    property real keyLightPosY: 0.0

    // ===============================================================
    // FILL LIGHT PROPERTIES
    // ===============================================================

    property real fillLightBrightness: 0.7
    property color fillLightColor: "#dfe7ff"
    property bool fillLightCastsShadow: false
    property bool fillLightBindToCamera: false
    property real fillLightPosX: 0.0
    property real fillLightPosY: 0.0

    // ===============================================================
    // RIM LIGHT PROPERTIES
    // ===============================================================

    property real rimLightBrightness: 1.0
    property color rimLightColor: "#ffe2b0"
    property bool rimLightCastsShadow: false
    property bool rimLightBindToCamera: false
    property real rimLightPosX: 0.0
    property real rimLightPosY: 0.0

    // ===============================================================
    // KEY LIGHT (основной источник освещения)
    // ===============================================================

    DirectionalLight {
        id: keyLight
        parent: root.keyLightBindToCamera ? root.cameraRig : root.worldRoot

        eulerRotation.x: root.keyLightAngleX
        eulerRotation.y: root.keyLightAngleY
        position: Qt.vector3d(root.keyLightPosX, root.keyLightPosY, 0)

        brightness: root.keyLightBrightness
        color: root.keyLightColor

        castsShadow: (root.shadowsEnabled && root.keyLightCastsShadow)

        // ✅ Shadow quality mapping
        shadowMapQuality: root.shadowResolution === "4096" ? Light.ShadowMapQualityVeryHigh :
                          root.shadowResolution === "2048" ? Light.ShadowMapQualityVeryHigh :
                          root.shadowResolution === "1024" ? Light.ShadowMapQualityHigh :
                          root.shadowResolution === "512"  ? Light.ShadowMapQualityMedium :
                                                               Light.ShadowMapQualityLow

        shadowFactor: root.shadowFactor
        shadowBias: root.shadowBias

        // ✅ Shadow filter mapping
        shadowFilter: {
            var samples = Math.floor(root.shadowFilterSamples || 16)
            return samples === 32 ? Light.ShadowFilterPCF32 :
                   samples === 16 ? Light.ShadowFilterPCF16 :
                   samples === 8  ? Light.ShadowFilterPCF8  :
                   samples === 4  ? Light.ShadowFilterPCF4  :
                                    Light.ShadowFilterNone
        }
    }

    // ===============================================================
    // FILL LIGHT (заполняющий свет)
    // ===============================================================

    DirectionalLight {
        id: fillLight
        parent: root.fillLightBindToCamera ? root.cameraRig : root.worldRoot

        eulerRotation.x: -60
        eulerRotation.y: 135
        position: Qt.vector3d(root.fillLightPosX, root.fillLightPosY, 0)

        brightness: root.fillLightBrightness
        color: root.fillLightColor

        castsShadow: (root.shadowsEnabled && root.fillLightCastsShadow)
    }

    // ===============================================================
    // RIM LIGHT (контровой свет)
    // ===============================================================

    DirectionalLight {
        id: rimLight
        parent: root.rimLightBindToCamera ? root.cameraRig : root.worldRoot

        eulerRotation.x: 15
        eulerRotation.y: 180
        position: Qt.vector3d(root.rimLightPosX, root.rimLightPosY, 0)

        brightness: root.rimLightBrightness
        color: root.rimLightColor

        castsShadow: (root.shadowsEnabled && root.rimLightCastsShadow)
    }

    // ===============================================================
    // DEBUG (опционально)
    // ===============================================================

    Component.onCompleted: {
        console.log("💡 DirectionalLights initialized:")
        console.log("   Key:", keyLightBrightness, keyLightColor)
        console.log("   Fill:", fillLightBrightness, fillLightColor)
        console.log("   Rim:", rimLightBrightness, rimLightColor)
        console.log("   Shadows:", shadowsEnabled, shadowResolution)
    }
}
