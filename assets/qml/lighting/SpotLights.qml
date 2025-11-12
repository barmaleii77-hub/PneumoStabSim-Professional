import QtQuick
import QtQuick3D

Node {
    id: root

    required property Node worldRoot
    required property Node cameraRig

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
    readonly property real _innerCone: Math.max(0.0, Math.min(spotLightInnerConeAngle, _outerCone - 0.1))

    function _safeSet(target, name, value) {
        if (!target) return
        try {
            if (target.setProperty !== undefined) {
                var r = target.setProperty(name, value)
                return r === undefined ? true : Boolean(r)
            }
            target[name] = value
            return true
        } catch (e) {
            // тихо игнорируем отсутствующие свойства
            return false
        }
    }

    function _applySpotProperties() {
        _safeSet(spotLight, "position", Qt.vector3d(spotLightX, spotLightY, spotLightZ))
        _safeSet(spotLight, "eulerRotation", Qt.vector3d(spotLightAngleX, spotLightAngleY, spotLightAngleZ))
        _safeSet(spotLight, "brightness", spotLightBrightness)
        _safeSet(spotLight, "color", spotLightColor)
        _safeSet(spotLight, "range", spotLightRange)
        _safeSet(spotLight, "coneAngle", _outerCone)
        _safeSet(spotLight, "innerConeAngle", _innerCone)
        _safeSet(spotLight, "castsShadow", spotLightCastsShadow)
    }

    SpotLight {
        id: spotLight
        parent: root.spotLightBindToCamera ? root.cameraRig : root.worldRoot
        Component.onCompleted: _applySpotProperties()
    }

    onSpotLightBrightnessChanged: _applySpotProperties()
    onSpotLightColorChanged: _applySpotProperties()
    onSpotLightXChanged: _applySpotProperties()
    onSpotLightYChanged: _applySpotProperties()
    onSpotLightZChanged: _applySpotProperties()
    onSpotLightRangeChanged: _applySpotProperties()
    onSpotLightAngleXChanged: _applySpotProperties()
    onSpotLightAngleYChanged: _applySpotProperties()
    onSpotLightAngleZChanged: _applySpotProperties()
    onSpotLightConeAngleChanged: _applySpotProperties()
    onSpotLightInnerConeAngleChanged: _applySpotProperties()
    onSpotLightCastsShadowChanged: _applySpotProperties()
    onSpotLightBindToCameraChanged: { spotLight.parent = spotLightBindToCamera ? cameraRig : worldRoot; _applySpotProperties() }

    Component.onCompleted: {
        console.log("💡 SpotLights initialized (compat mode):")
        console.log("   Brightness:", spotLightBrightness)
        console.log("   Color:", spotLightColor)
        console.log("   Position:", spotLightX, spotLightY, spotLightZ)
        console.log("   Angles:", spotLightAngleX, spotLightAngleY, spotLightAngleZ)
        console.log("   Range:", spotLightRange)
        console.log("   Cone (inner/outer):", _innerCone, _outerCone)
        console.log("   Casts shadow:", spotLightCastsShadow)
    }
}
