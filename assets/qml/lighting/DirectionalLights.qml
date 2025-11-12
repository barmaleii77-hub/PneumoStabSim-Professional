import QtQuick
import QtQuick3D

Node {
    id: root

    required property Node worldRoot
    required property Node cameraRig

    property bool shadowsEnabled: true
    property int shadowResolution: 4096
    property int shadowFilterSamples: 32
    property real shadowBias: 8.0
    property real shadowFactor: 80.0

    // KEY
    property real keyLightBrightness: 1.0
    property color keyLightColor: "#ffffff"
    property real keyLightAngleX: 25.0
    property real keyLightAngleY: 23.5
    property real keyLightAngleZ: 0.0
    property bool keyLightCastsShadow: true
    property bool keyLightBindToCamera: false
    property real keyLightPosX: 0.0
    property real keyLightPosY: 0.0
    property real keyLightPosZ: 0.0

    // FILL
    property real fillLightBrightness: 1.0
    property color fillLightColor: "#f1f4ff"
    property real fillLightAngleX: 0.0
    property real fillLightAngleY: -45.0
    property real fillLightAngleZ: 0.0
    property bool fillLightCastsShadow: false
    property bool fillLightBindToCamera: false
    property real fillLightPosX: 0.0
    property real fillLightPosY: 0.0
    property real fillLightPosZ: 0.0

    // RIM
    property real rimLightBrightness: 1.1
    property color rimLightColor: "#ffe1bd"
    property real rimLightAngleX: 30.0
    property real rimLightAngleY: -135.0
    property real rimLightAngleZ: 0.0
    property bool rimLightCastsShadow: false
    property bool rimLightBindToCamera: false
    property real rimLightPosX: 0.0
    property real rimLightPosY: 0.0
    property real rimLightPosZ: 0.0

    function _safeSet(obj, name, value) {
        if (!obj) return false
        try {
            if (obj.setProperty !== undefined) {
                var r = obj.setProperty(name, value)
                return r === undefined ? true : Boolean(r)
            }
            obj[name] = value
            return true
        } catch (e) {
            return false
        }
    }

    function _shadowQualityFor(res) {
        if (res >= 4096) return Light.ShadowMapQualityUltra || Light.ShadowMapQualityVeryHigh
        if (res >= 2048) return Light.ShadowMapQualityVeryHigh
        if (res >= 1024) return Light.ShadowMapQualityHigh
        if (res >= 512) return Light.ShadowMapQualityMedium
        return Light.ShadowMapQualityLow
    }

    function _shadowFilterFor(samples) {
        var s = Math.floor(samples || 16)
        return s >= 32 ? Light.ShadowFilterPCF32 :
               s >= 16 ? Light.ShadowFilterPCF16 :
               s >= 8  ? Light.ShadowFilterPCF8  :
               s >= 4  ? Light.ShadowFilterPCF4  : Light.ShadowFilterNone
    }

    function _applyKey() {
        _safeSet(keyLight, 'eulerRotation', Qt.vector3d(keyLightAngleX, keyLightAngleY, keyLightAngleZ))
        _safeSet(keyLight, 'position', Qt.vector3d(keyLightPosX, keyLightPosY, keyLightPosZ))
        _safeSet(keyLight, 'brightness', keyLightBrightness)
        _safeSet(keyLight, 'color', keyLightColor)
        _safeSet(keyLight, 'castsShadow', (shadowsEnabled && keyLightCastsShadow))
        _safeSet(keyLight, 'shadowMapQuality', _shadowQualityFor(shadowResolution))
        _safeSet(keyLight, 'shadowFactor', shadowFactor)
        _safeSet(keyLight, 'shadowBias', shadowBias)
        _safeSet(keyLight, 'shadowFilter', _shadowFilterFor(shadowFilterSamples))
    }

    function _applyFill() {
        _safeSet(fillLight, 'eulerRotation', Qt.vector3d(fillLightAngleX, fillLightAngleY, fillLightAngleZ))
        _safeSet(fillLight, 'position', Qt.vector3d(fillLightPosX, fillLightPosY, fillLightPosZ))
        _safeSet(fillLight, 'brightness', fillLightBrightness)
        _safeSet(fillLight, 'color', fillLightColor)
        _safeSet(fillLight, 'castsShadow', (shadowsEnabled && fillLightCastsShadow))
    }

    function _applyRim() {
        _safeSet(rimLight, 'eulerRotation', Qt.vector3d(rimLightAngleX, rimLightAngleY, rimLightAngleZ))
        _safeSet(rimLight, 'position', Qt.vector3d(rimLightPosX, rimLightPosY, rimLightPosZ))
        _safeSet(rimLight, 'brightness', rimLightBrightness)
        _safeSet(rimLight, 'color', rimLightColor)
        _safeSet(rimLight, 'castsShadow', (shadowsEnabled && rimLightCastsShadow))
    }

    DirectionalLight { id: keyLight; parent: keyLightBindToCamera ? cameraRig : worldRoot; Component.onCompleted: _applyKey() }
    DirectionalLight { id: fillLight; parent: fillLightBindToCamera ? cameraRig : worldRoot; Component.onCompleted: _applyFill() }
    DirectionalLight { id: rimLight; parent: rimLightBindToCamera ? cameraRig : worldRoot; Component.onCompleted: _applyRim() }

    // Reactive reapplication
    onKeyLightBrightnessChanged: _applyKey()
    onKeyLightColorChanged: _applyKey()
    onKeyLightAngleXChanged: _applyKey()
    onKeyLightAngleYChanged: _applyKey()
    onKeyLightAngleZChanged: _applyKey()
    onKeyLightPosXChanged: _applyKey()
    onKeyLightPosYChanged: _applyKey()
    onKeyLightPosZChanged: _applyKey()
    onKeyLightCastsShadowChanged: _applyKey()
    onKeyLightBindToCameraChanged: { keyLight.parent = keyLightBindToCamera ? cameraRig : worldRoot; _applyKey() }

    onFillLightBrightnessChanged: _applyFill()
    onFillLightColorChanged: _applyFill()
    onFillLightAngleXChanged: _applyFill()
    onFillLightAngleYChanged: _applyFill()
    onFillLightAngleZChanged: _applyFill()
    onFillLightPosXChanged: _applyFill()
    onFillLightPosYChanged: _applyFill()
    onFillLightPosZChanged: _applyFill()
    onFillLightCastsShadowChanged: _applyFill()
    onFillLightBindToCameraChanged: { fillLight.parent = fillLightBindToCamera ? cameraRig : worldRoot; _applyFill() }

    onRimLightBrightnessChanged: _applyRim()
    onRimLightColorChanged: _applyRim()
    onRimLightAngleXChanged: _applyRim()
    onRimLightAngleYChanged: _applyRim()
    onRimLightAngleZChanged: _applyRim()
    onRimLightPosXChanged: _applyRim()
    onRimLightPosYChanged: _applyRim()
    onRimLightPosZChanged: _applyRim()
    onRimLightCastsShadowChanged: _applyRim()
    onRimLightBindToCameraChanged: { rimLight.parent = rimLightBindToCamera ? cameraRig : worldRoot; _applyRim() }

    onShadowsEnabledChanged: { _applyKey(); _applyFill(); _applyRim() }
    onShadowResolutionChanged: _applyKey()
    onShadowFilterSamplesChanged: _applyKey()
    onShadowBiasChanged: _applyKey()
    onShadowFactorChanged: _applyKey()

    Component.onCompleted: {
        console.log('💡 DirectionalLights initialized (compat dynamic):')
        console.log('   key brightness:', keyLightBrightness)
        console.log('   fill brightness:', fillLightBrightness)
        console.log('   rim brightness:', rimLightBrightness)
        console.log('   shadows:', shadowsEnabled, shadowResolution)
    }
}
