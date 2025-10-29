import QtQuick
import QtQuick3D

Node {
    id: rig

    property real keyLightAngleX: -45
    property real keyLightAngleY: 45
    property real keyLightBrightness: 2.5
    property color keyLightColor: "#ffffff"
    property bool shadowsEnabled: true
    property int shadowQualityIndex: 2
    property real shadowSoftness: 0.5

    property real fillLightAngleX: -60
    property real fillLightAngleY: 135
    property real fillLightBrightness: 0.8
    property color fillLightColor: "#f0f0ff"

    property real pointLightHeight: 2000.0
    property real pointLightZOffset: 1.5
    property real pointLightBrightness: 1.5
    property color pointLightColor: "#ffffff"
    property real pointLightQuadraticFade: 0.00008

    function resolveShadowQuality(index) {
        const qualities = [
                    Light.ShadowMapQualityLow,
                    Light.ShadowMapQualityMedium,
                    Light.ShadowMapQualityHigh
                ]
        const boundedIndex = Math.max(0, Math.min(qualities.length - 1, Math.floor(index)))
        return qualities[boundedIndex]
    }

    DirectionalLight {
        id: keyLight
        eulerRotation.x: rig.keyLightAngleX
        eulerRotation.y: rig.keyLightAngleY
        brightness: rig.keyLightBrightness
        color: rig.keyLightColor
        castsShadow: rig.shadowsEnabled
        shadowMapQuality: rig.resolveShadowQuality(rig.shadowQualityIndex)
        shadowFactor: 75
        shadowBias: rig.shadowSoftness * 0.001
    }

    DirectionalLight {
        id: fillLight
        eulerRotation.x: rig.fillLightAngleX
        eulerRotation.y: rig.fillLightAngleY
        brightness: rig.fillLightBrightness
        color: rig.fillLightColor
        castsShadow: false
    }

    PointLight {
        id: pointLight
        position: Qt.vector3d(0, rig.pointLightHeight, rig.pointLightZOffset)
        brightness: rig.pointLightBrightness
        color: rig.pointLightColor
        quadraticFade: rig.pointLightQuadraticFade
    }
}
