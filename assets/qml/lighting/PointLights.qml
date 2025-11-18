import QtQuick
import QtQuick3D

Node {
    id: root

    required property Node worldRoot
    required property Node cameraRig

    property real pointLightBrightness: 50.0
    property color pointLightColor: "#fff7e0"
    property real pointLightX: 0.0
    property real pointLightY: 2.6
    property real pointLightZ: 1.5
    property real pointLightRange: 3.6
    property real constantFade: 1.0
    // Align attenuation defaults with the engine's inverse-square fallback (2 / range)
    // so the UI sliders show the actual brightness behaviour from the start.
    property real linearFade: pointLightRange > 0
                                 ? Math.min(10.0, Math.max(0.0, 2.0 / pointLightRange))
                                 : 0.56
    property real quadraticFade: 1.0
    property bool pointLightCastsShadow: false
    property bool pointLightBindToCamera: false

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
            return false
        }
    }

    function _applyPointProperties() {
        _safeSet(accentLight, "position", Qt.vector3d(pointLightX, pointLightY, pointLightZ))
        _safeSet(accentLight, "brightness", pointLightBrightness)
        _safeSet(accentLight, "color", pointLightColor)
        _safeSet(accentLight, "castsShadow", pointLightCastsShadow)
        _safeSet(accentLight, "range", pointLightRange)
        _safeSet(accentLight, "constantFade", constantFade)
        _safeSet(accentLight, "linearFade", linearFade)
        _safeSet(accentLight, "quadraticFade", quadraticFade)
    }

    PointLight {
        id: accentLight
        parent: root.pointLightBindToCamera ? root.cameraRig : root.worldRoot
        Component.onCompleted: _applyPointProperties()
    }

    onPointLightBrightnessChanged: _applyPointProperties()
    onPointLightColorChanged: _applyPointProperties()
    onPointLightXChanged: _applyPointProperties()
    onPointLightYChanged: _applyPointProperties()
    onPointLightZChanged: _applyPointProperties()
    onPointLightRangeChanged: _applyPointProperties()
    onConstantFadeChanged: _applyPointProperties()
    onLinearFadeChanged: _applyPointProperties()
    onQuadraticFadeChanged: _applyPointProperties()
    onPointLightCastsShadowChanged: _applyPointProperties()
    onPointLightBindToCameraChanged: { accentLight.parent = pointLightBindToCamera ? cameraRig : worldRoot; _applyPointProperties() }

    Component.onCompleted: {
        console.log("💡 PointLights initialized (compat mode):")
        console.log("   Brightness:", pointLightBrightness)
        console.log("   Position: (", pointLightX, ",", pointLightY, ",", pointLightZ, ")")
        console.log("   Range:", pointLightRange)
        console.log("   Fade (const/lin/quad):", constantFade, linearFade, quadraticFade)
        console.log("   Casts shadow:", pointLightCastsShadow)
    }
}
