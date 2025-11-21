pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Controls.Basic 6.10
import QtQuick.Dialogs 6.10
import QtQuick.Layouts 6.10

Item {
    id: root
    implicitWidth: 560
    implicitHeight: 680

    property color accentColor: "#4FC3F7"
    property color backgroundColor: "#101821"
    property color surfaceColor: "#182434"
    property color borderColor: "#293542"
    property color textColor: "#E6EEF5"
    property color mutedTextColor: "#A9B7C6"

    /**
     * Снапшот сценических параметров, которые нужно редактировать через UI.
     * Ожидается структура config/app_settings.json → current.graphics.scene.
     */
    property var sceneSettings: ({})
    /**
     * Базовые значения для отображения подсказок и кнопки Reset.
     */
    property var sceneDefaults: ({})
    /**
     * Сигнал обновления состояния (для привязки к SettingsManager/QML bridge).
     */
    signal sceneChanged(var payload)

    property var _sceneState: ({})
    property bool _syncingSceneControls: false
    property var _sceneControls: null

    // ✅ Диапазоны пользовательских параметров
    property var _ranges: ({}) // {paramName:{min:Number,max:Number}}

    property alias currentTab: tabBar.currentIndex
    readonly property var tabs: [
        {
            key: "lighting",
            title: "Lighting",
            sections: [
                {
                    key: "keyLighting",
                    title: "Key light",
                    hint: "Control the key light's intensity, direction, and color."
                },
                {
                    key: "fillLighting",
                    title: "Fill light",
                    hint: "Soften contrast by adjusting the contribution from fill lights."
                }
            ]
        },
        {
            key: "environment",
            title: "Environment",
            sections: [
                {
                    key: "skyEnvironment",
                    title: "Sky and HDRI",
                    hint: "Select environment maps and balance sky illumination."
                },
                {
                    key: "fogEnvironment",
                    title: "Fog and atmosphere",
                    hint: "Shape volumetric fog density, falloff, and horizon height."
                }
            ]
        },
        {
            key: "quality",
            title: "Quality",
            sections: [
                {
                    key: "renderQuality",
                    title: "Render pipeline quality",
                    hint: "Configure anti-aliasing, shadow resolution, and texture filtering."
                },
                {
                    key: "optimization",
                    title: "Performance safeguards",
                    hint: "Limit frame rate and render scale to safeguard performance."
                }
            ]
        },
        {
            key: "scene",
            title: "Scene",
            sections: [
                {
                    key: "sceneDefaults",
                    title: "Scene defaults",
                    hint: "Manage default animation states and global scene toggles."
                },
                {
                    key: "motionBlur",
                    title: "Motion blur",
                    hint: "Balance motion blur with shutter duration and vector strength."
                }
            ]
        },
        {
            key: "camera",
            title: "Camera",
            sections: [
                {
                    key: "cameraRig",
                    title: "Camera rig",
                    hint: "Configure orbit rig sensitivity, pivot behaviour, and damping."
                },
                {
                    key: "dofControls",
                    title: "Depth of field",
                    hint: "Focus the camera with distance, aperture, and bokeh controls."
                }
            ]
        },
        {
            key: "materials",
            title: "Materials",
            sections: [
                {
                    key: "surfaceMaterials",
                    title: "Surface response",
                    hint: "Tune base color, roughness, and metallic response."
                },
                {
                    key: "clearcoat",
                    title: "Clear coat",
                    hint: "Layer clear coat strength, tint, and Fresnel behaviour."
                }
            ]
        },
        {
            key: "effects",
            title: "Effects",
            sections: [
                {
                    key: "postEffects",
                    title: "Post-processing",
                    hint: "Enable bloom, vignette, and exposure adaptation."
                },
                {
                    key: "postToneMapping",
                    title: "Tone mapping",
                    hint: "Select tone mapping curves and white point to balance highlights."
                }
            ]
        }
    ]

    function _clone(value) {
        return value === undefined || value === null ? {} : JSON.parse(JSON.stringify(value))
    }

    function _mergeSceneState(base, override) {
        var target = _clone(base)
        var patch = _clone(override)
        for (var key in patch) {
            if (key === "suspension" && patch[key] && typeof patch[key] === "object") {
                target.suspension = target.suspension && typeof target.suspension === "object"
                    ? target.suspension
                    : {}
                for (var nested in patch[key])
                    target.suspension[nested] = patch[key][nested]
                continue
            }
            target[key] = patch[key]
        }
        if (!target.suspension)
            target.suspension = {}
        return target
    }

    function _sceneNumber(key, fallback) {
        var candidate = _sceneState[key]
        var numeric = Number(candidate)
        return Number.isFinite(numeric) ? numeric : fallback
    }

    function _sceneColor(key, fallback) {
        var candidate = _sceneState[key]
        if (typeof candidate === "string" && candidate.length)
            return candidate
        return fallback
    }

    function _setSceneValue(key, value) {
        if (_syncingSceneControls) return
        _sceneState[key] = value
        sceneSettings = exportSceneSettings()
        sceneChanged(sceneSettings)
    }

    function _setSuspensionValue(key, value) {
        if (_syncingSceneControls) return
        _sceneState.suspension = _sceneState.suspension || {}
        _sceneState.suspension[key] = value
        sceneSettings = exportSceneSettings()
        sceneChanged(sceneSettings)
    }

    // ✅ Управление диапазонами
    function _setRange(key, minValue, maxValue) {
        if (!_sceneState.range_overrides)
            _sceneState.range_overrides = {}
        _sceneState.range_overrides[key] = { min: Number(minValue), max: Number(maxValue) }
        _ranges[key] = { min: Number(minValue), max: Number(maxValue) }
        sceneSettings = exportSceneSettings()
        sceneChanged(sceneSettings)
        _applyRangeToControl(key)
    }
    function _applyRangeToControl(key) {
        if (!_sceneControls) return
        var c = _sceneControls[key]
        if (!c) return
        var r = _ranges[key] || (_sceneState.range_overrides ? _sceneState.range_overrides[key] : null)
        if (r) {
            if (isFinite(r.min)) c.from = r.min
            if (isFinite(r.max)) c.to = r.max
        }
    }
    function _applyAllRanges() {
        if (_sceneState.range_overrides) {
            for (var k in _sceneState.range_overrides) {
                if (!_ranges[k]) _ranges[k] = { min: _sceneState.range_overrides[k].min, max: _sceneState.range_overrides[k].max }
            }
        }
        for (var rk in _ranges) _applyRangeToControl(rk)
    }

    function exportSceneSettings() {
        var snap = JSON.parse(JSON.stringify(_sceneState || {}))
        if (_sceneState.range_overrides)
            snap.range_overrides = JSON.parse(JSON.stringify(_sceneState.range_overrides))
        return snap
    }

    function applySceneState(payload) {
        var incoming = payload || sceneSettings
        sceneSettings = incoming
        _sceneState = _mergeSceneState(sceneDefaults, incoming)
        _syncSceneControls()
    }

    function resetSceneToDefaults() {
        _sceneState = _mergeSceneState(sceneDefaults, {})
        _syncSceneControls()
        sceneSettings = exportSceneSettings()
        sceneChanged(sceneSettings)
    }

    function _syncSceneControls() {
        var controls = _sceneControls
        if (!controls) return
        _syncingSceneControls = true
        try {
            if (controls.scaleSlider) controls.scaleSlider.value = Number(_sceneState.scale_factor) || 1.0
            if (controls.exposureSlider) controls.exposureSlider.value = Number(_sceneState.exposure) || 1.0
            if (controls.clearColorSwatch) controls.clearColorSwatch.color = _sceneState.default_clear_color || "#1b1f27"
            if (controls.baseColorSwatch) controls.baseColorSwatch.color = _sceneState.model_base_color || "#9da3aa"
            if (controls.roughnessSlider) controls.roughnessSlider.value = Number(_sceneState.model_roughness) || 0.42
            if (controls.metalnessSlider) controls.metalnessSlider.value = Number(_sceneState.model_metalness) || 0.82
            if (controls.suspensionThresholdSlider) controls.suspensionThresholdSlider.value = Number(_sceneState.suspension && _sceneState.suspension.rod_warning_threshold_m) || 0.001
            if (controls.postEffectsBypass) controls.postEffectsBypass.checked = !!_sceneState.effects_bypass
            if (controls.postEffectsReason) controls.postEffectsReason.text = _sceneState.effects_bypass_reason || ""
            _applyAllRanges()
        } finally { _syncingSceneControls = false }
    }

    // ✅ Редактор диапазона
    Component { id: rangeEditorComponent
        RowLayout {
            required property var targetSlider
            required property string paramKey
            spacing: 4
            TextField { id: minField; Layout.preferredWidth: 60; placeholderText: "min"; text: targetSlider.from.toFixed(3)
                onEditingFinished: { var v = Number(text); if (isFinite(v)) root._setRange(paramKey, v, maxField.text.length?Number(maxField.text):targetSlider.to) }
            }
            TextField { id: maxField; Layout.preferredWidth: 60; placeholderText: "max"; text: targetSlider.to.toFixed(3)
                onEditingFinished: { var v = Number(text); if (isFinite(v)) root._setRange(paramKey, minField.text.length?Number(minField.text):targetSlider.from, v) }
            }
        }
    }

    // ✅ Постэффекты (только эффекты камеры и изображения, без tonemap/DOF/motionBlur/fog)
    Component { id: postEffectsComponent
        ColumnLayout { Layout.fillWidth: true; spacing: 12
            GroupBox { Layout.fillWidth: true; title: qsTr("Bloom")
                ColumnLayout { spacing: 6; Layout.fillWidth: true
                    CheckBox { id: bloomEnabled; text: qsTr("Enabled"); onToggled: { root._setSceneValue("bloomEnabled", checked); } }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Intensity"); color: root.textColor; Layout.preferredWidth: 110 }
                        Slider { id: bloomIntensity; Layout.fillWidth: true; from: 0.0; to: 3.0; stepSize: 0.01; onValueChanged: root._setSceneValue("bloomIntensity", value) }
                        Label { text: bloomIntensity.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 54 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: bloomIntensity; property string paramKey: "bloomIntensity" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Threshold"); color: root.textColor; Layout.preferredWidth: 110 }
                        Slider { id: bloomThreshold; Layout.fillWidth: true; from: 0.0; to: 4.0; stepSize: 0.01; onValueChanged: root._setSceneValue("bloomThreshold", value) }
                        Label { text: bloomThreshold.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 54 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: bloomThreshold; property string paramKey: "bloomThreshold" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Secondary Bloom"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: bloomSecondaryBloom; Layout.fillWidth: true; from: 0.0; to: 2.0; stepSize: 0.01; onValueChanged: root._setSceneValue("bloomSecondaryBloom", value) }
                        Label { text: bloomSecondaryBloom.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: bloomSecondaryBloom; property string paramKey: "bloomSecondaryBloom" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Glow Strength"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: bloomStrength; Layout.fillWidth: true; from: 0.0; to: 4.0; stepSize: 0.01; onValueChanged: root._setSceneValue("bloomStrength", value) }
                        Label { text: bloomStrength.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: bloomStrength; property string paramKey: "bloomStrength" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("HDR Maximum"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: glowHdrMaximumValue; Layout.fillWidth: true; from: 0.0; to: 16.0; stepSize: 0.1; onValueChanged: root._setSceneValue("glowHdrMaximumValue", value) }
                        Label { text: glowHdrMaximumValue.value.toFixed(1); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: glowHdrMaximumValue; property string paramKey: "glowHdrMaximumValue" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("HDR Scale"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: glowHdrScale; Layout.fillWidth: true; from: 0.0; to: 4.0; stepSize: 0.01; onValueChanged: root._setSceneValue("glowHdrScale", value) }
                        Label { text: glowHdrScale.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: glowHdrScale; property string paramKey: "glowHdrScale" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Quality High"); color: root.textColor; Layout.preferredWidth: 140 }
                        CheckBox { id: glowQualityHighEnabled; text: glowQualityHighEnabled.checked ? qsTr("On") : qsTr("Off"); onToggled: root._setSceneValue("glowQualityHighEnabled", checked) }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Bicubic Upscale"); color: root.textColor; Layout.preferredWidth: 140 }
                        CheckBox { id: glowUseBicubic; text: glowUseBicubic.checked ? qsTr("On") : qsTr("Off"); onToggled: root._setSceneValue("glowUseBicubic", checked) }
                    }
                }
            }
            GroupBox { Layout.fillWidth: true; title: qsTr("SSAO")
                ColumnLayout { spacing: 6; Layout.fillWidth: true
                    CheckBox { id: ssaoEnabled; text: qsTr("Enabled"); onToggled: root._setSceneValue("ssaoEnabled", checked) }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Intensity"); color: root.textColor; Layout.preferredWidth: 100 }
                        Slider { id: ssaoIntensity; Layout.fillWidth: true; from: 0.0; to: 4.0; stepSize: 0.01; onValueChanged: root._setSceneValue("ssaoIntensity", value) }
                        Label { text: ssaoIntensity.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 50 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: ssaoIntensity; property string paramKey: "ssaoIntensity" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Radius"); color: root.textColor; Layout.preferredWidth: 100 }
                        Slider { id: ssaoRadius; Layout.fillWidth: true; from: 0.001; to: 0.05; stepSize: 0.0005; onValueChanged: root._setSceneValue("ssaoRadius", value) }
                        Label { text: ssaoRadius.value.toFixed(4); color: root.textColor; Layout.preferredWidth: 70 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: ssaoRadius; property string paramKey: "ssaoRadius" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Softness"); color: root.textColor; Layout.preferredWidth: 100 }
                        Slider { id: ssaoSoftness; Layout.fillWidth: true; from: 0.0; to: 40.0; stepSize: 0.1; onValueChanged: root._setSceneValue("ssaoSoftness", value) }
                        Label { text: ssaoSoftness.value.toFixed(1); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: ssaoSoftness; property string paramKey: "ssaoSoftness" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Bias"); color: root.textColor; Layout.preferredWidth: 100 }
                        Slider { id: ssaoBias; Layout.fillWidth: true; from: 0.0; to: 0.2; stepSize: 0.001; onValueChanged: root._setSceneValue("ssaoBias", value) }
                        Label { text: ssaoBias.value.toFixed(3); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: ssaoBias; property string paramKey: "ssaoBias" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Sample Rate"); color: root.textColor; Layout.preferredWidth: 100 }
                        Slider { id: ssaoSampleRate; Layout.fillWidth: true; from: 1; to: 64; stepSize: 1; onValueChanged: root._setSceneValue("ssaoSampleRate", value) }
                        Label { text: ssaoSampleRate.value.toFixed(0); color: root.textColor; Layout.preferredWidth: 50 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: ssaoSampleRate; property string paramKey: "ssaoSampleRate" }
                    }
                    CheckBox { id: ssaoDither; text: qsTr("Dither"); onToggled: root._setSceneValue("ssaoDither", checked) }
                }
            }
            GroupBox { Layout.fillWidth: true; title: qsTr("Lens Flare")
                ColumnLayout { spacing: 6; Layout.fillWidth: true
                    CheckBox { id: lensFlareActive; text: qsTr("Active"); onToggled: root._setSceneValue("lensFlareActive", checked) }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Ghosts"); color: root.textColor; Layout.preferredWidth: 120 }
                        Slider { id: lensFlareGhosts; Layout.fillWidth: true; from: 0; to: 12; stepSize: 1; onValueChanged: root._setSceneValue("lensFlareGhosts", value) }
                        Label { text: lensFlareGhosts.value.toFixed(0); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: lensFlareGhosts; property string paramKey: "lensFlareGhosts" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Ghost Dispersal"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: lensFlareGhostDispersalValue; Layout.fillWidth: true; from: 0.0; to: 2.0; stepSize: 0.01; onValueChanged: root._setSceneValue("lensFlareGhostDispersalValue", value) }
                        Label { text: lensFlareGhostDispersalValue.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 70 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: lensFlareGhostDispersalValue; property string paramKey: "lensFlareGhostDispersalValue" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Halo Width"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: lensFlareHaloWidthValue; Layout.fillWidth: true; from: 0.0; to: 1.0; stepSize: 0.01; onValueChanged: root._setSceneValue("lensFlareHaloWidthValue", value) }
                        Label { text: lensFlareHaloWidthValue.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 70 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: lensFlareHaloWidthValue; property string paramKey: "lensFlareHaloWidthValue" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Bloom Bias"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: lensFlareBloomBiasValue; Layout.fillWidth: true; from: 0.0; to: 1.0; stepSize: 0.01; onValueChanged: root._setSceneValue("lensFlareBloomBiasValue", value) }
                        Label { text: lensFlareBloomBiasValue.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 70 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: lensFlareBloomBiasValue; property string paramKey: "lensFlareBloomBiasValue" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Stretch"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: lensFlareStretchValue; Layout.fillWidth: true; from: 0.0; to: 1.0; stepSize: 0.01; onValueChanged: root._setSceneValue("lensFlareStretchValue", value) }
                        Label { text: lensFlareStretchValue.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 70 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: lensFlareStretchValue; property string paramKey: "lensFlareStretchValue" }
                    }
                }
            }
            GroupBox { Layout.fillWidth: true; title: qsTr("Color Adjustments")
                ColumnLayout { spacing: 6; Layout.fillWidth: true
                    RowLayout { Layout.fillWidth: true
                        CheckBox { id: colorAdjustmentsEnabled; text: qsTr("Enabled"); onToggled: root._setSceneValue("colorAdjustmentsEnabled", checked) }
                        CheckBox { id: colorAdjustmentsActive; text: qsTr("Active"); onToggled: root._setSceneValue("colorAdjustmentsActive", checked) }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Brightness"); color: root.textColor; Layout.preferredWidth: 120 }
                        Slider { id: adjustmentBrightness; Layout.fillWidth: true; from: -2.0; to: 2.0; stepSize: 0.01; onValueChanged: root._setSceneValue("adjustmentBrightness", value) }
                        Label { text: adjustmentBrightness.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: adjustmentBrightness; property string paramKey: "adjustmentBrightness" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Contrast"); color: root.textColor; Layout.preferredWidth: 120 }
                        Slider { id: adjustmentContrast; Layout.fillWidth: true; from: -2.0; to: 2.0; stepSize: 0.01; onValueChanged: root._setSceneValue("adjustmentContrast", value) }
                        Label { text: adjustmentContrast.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: adjustmentContrast; property string paramKey: "adjustmentContrast" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Saturation"); color: root.textColor; Layout.preferredWidth: 120 }
                        Slider { id: adjustmentSaturation; Layout.fillWidth: true; from: -2.0; to: 2.0; stepSize: 0.01; onValueChanged: root._setSceneValue("adjustmentSaturation", value) }
                        Label { text: adjustmentSaturation.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: adjustmentSaturation; property string paramKey: "adjustmentSaturation" }
                    }
                }
            }
            GroupBox { Layout.fillWidth: true; title: qsTr("Vignette")
                ColumnLayout { spacing: 6; Layout.fillWidth: true
                    CheckBox { id: vignetteActive; text: qsTr("Active"); onToggled: root._setSceneValue("vignetteActive", checked) }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Strength"); color: root.textColor; Layout.preferredWidth: 120 }
                        Slider { id: vignetteStrengthValue; Layout.fillWidth: true; from: 0.0; to: 1.0; stepSize: 0.01; onValueChanged: root._setSceneValue("vignetteStrengthValue", value) }
                        Label { text: vignetteStrengthValue.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: vignetteStrengthValue; property string paramKey: "vignetteStrengthValue" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Radius"); color: root.textColor; Layout.preferredWidth: 120 }
                        Slider { id: vignetteRadiusValue; Layout.fillWidth: true; from: 0.0; to: 1.0; stepSize: 0.01; onValueChanged: root._setSceneValue("vignetteRadiusValue", value) }
                        Label { text: vignetteRadiusValue.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: vignetteRadiusValue; property string paramKey: "vignetteRadiusValue" }
                    }
                }
            }
        }
    }

    Component { id: dofComponent
        ColumnLayout { Layout.fillWidth: true; spacing: 10
            GroupBox { Layout.fillWidth: true; title: qsTr("Depth of Field")
                ColumnLayout { spacing: 6; Layout.fillWidth: true
                    CheckBox { id: depthOfFieldActive; text: qsTr("Active"); onToggled: root._setSceneValue("depthOfFieldActive", checked) }
                    CheckBox { id: depthOfFieldAutoFocus; text: qsTr("Auto Focus"); onToggled: root._setSceneValue("depthOfFieldAutoFocus", checked) }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Focus Distance"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: depthOfFieldFocusDistanceValue; Layout.fillWidth: true; from: 0.1; to: 50.0; stepSize: 0.1; onValueChanged: root._setSceneValue("depthOfFieldFocusDistanceValue", value) }
                        Label { text: depthOfFieldFocusDistanceValue.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 70 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: depthOfFieldFocusDistanceValue; property string paramKey: "depthOfFieldFocusDistanceValue" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Focus Range"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: depthOfFieldFocusRangeValue; Layout.fillWidth: true; from: 0.01; to: 20.0; stepSize: 0.05; onValueChanged: root._setSceneValue("depthOfFieldFocusRangeValue", value) }
                        Label { text: depthOfFieldFocusRangeValue.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 70 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: depthOfFieldFocusRangeValue; property string paramKey: "depthOfFieldFocusRangeValue" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Blur Amount"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: depthOfFieldBlurAmountValue; Layout.fillWidth: true; from: 0.0; to: 10.0; stepSize: 0.05; onValueChanged: root._setSceneValue("depthOfFieldBlurAmountValue", value) }
                        Label { text: depthOfFieldBlurAmountValue.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 70 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: depthOfFieldBlurAmountValue; property string paramKey: "depthOfFieldBlurAmountValue" }
                    }
                }
            }
        }
    }

    // ✅ Motion Blur отделён
    Component { id: motionBlurComponent
        ColumnLayout { Layout.fillWidth: true; spacing: 10
            GroupBox { Layout.fillWidth: true; title: qsTr("Motion Blur")
                ColumnLayout { spacing: 6; Layout.fillWidth: true
                    CheckBox { id: motionBlurEnabled; text: qsTr("Enabled"); onToggled: root._setSceneValue("motionBlurEnabled", checked) }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Strength"); color: root.textColor; Layout.preferredWidth: 100 }
                        Slider { id: motionBlurStrength; Layout.fillWidth: true; from: 0.0; to: 1.0; stepSize: 0.01; onValueChanged: root._setSceneValue("motionBlurStrength", value) }
                        Label { text: motionBlurStrength.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 50 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: motionBlurStrength; property string paramKey: "motionBlurStrength" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Samples"); color: root.textColor; Layout.preferredWidth: 100 }
                        Slider { id: motionBlurSamples; Layout.fillWidth: true; from: 1; to: 64; stepSize: 1; onValueChanged: root._setSceneValue("motionBlurSamples", value) }
                        Label { text: motionBlurSamples.value.toFixed(0); color: root.textColor; Layout.preferredWidth: 50 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: motionBlurSamples; property string paramKey: "motionBlurSamples" }
                    }
                }
            }
        }
    }

    // ✅ Окружение + Fog (перенесён сюда)
    Component { id: environmentComponent
        ColumnLayout { Layout.fillWidth: true; spacing: 10
            GroupBox { Layout.fillWidth: true; title: qsTr("IBL / Skybox")
                ColumnLayout { spacing: 6; Layout.fillWidth: true
                    CheckBox { id: iblLightingEnabled; text: qsTr("Lighting Enabled"); onToggled: root._setSceneValue("iblLightingEnabled", checked) }
                    CheckBox { id: iblBackgroundEnabled; text: qsTr("Background Enabled"); onToggled: root._setSceneValue("iblBackgroundEnabled", checked) }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Intensity"); color: root.textColor; Layout.preferredWidth: 100 }
                        Slider { id: iblIntensity; Layout.fillWidth: true; from: 0.0; to: 8.0; stepSize: 0.05; onValueChanged: root._setSceneValue("iblIntensity", value) }
                        Label { text: iblIntensity.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: iblIntensity; property string paramKey: "iblIntensity" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Skybox Brightness"); color: root.textColor; Layout.preferredWidth: 140 }
                        Slider { id: skyboxBrightness; Layout.fillWidth: true; from: 0.0; to: 8.0; stepSize: 0.05; onValueChanged: root._setSceneValue("skyboxBrightness", value) }
                        Label { text: skyboxBrightness.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: skyboxBrightness; property string paramKey: "skyboxBrightness" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Horizon"); color: root.textColor; Layout.preferredWidth: 100 }
                        Slider { id: probeHorizon; Layout.fillWidth: true; from: -2.0; to: 2.0; stepSize: 0.01; onValueChanged: root._setSceneValue("probeHorizon", value) }
                        Label { text: probeHorizon.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: probeHorizon; property string paramKey: "probeHorizon" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Pitch"); color: root.textColor; Layout.preferredWidth: 80 }
                        Slider { id: iblRotationPitchDeg; Layout.fillWidth: true; from: -180.0; to: 180.0; stepSize: 0.5; onValueChanged: root._setSceneValue("iblRotationPitchDeg", value) }
                        Label { text: iblRotationPitchDeg.value.toFixed(1); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: iblRotationPitchDeg; property string paramKey: "iblRotationPitchDeg" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Yaw"); color: root.textColor; Layout.preferredWidth: 80 }
                        Slider { id: iblRotationDeg; Layout.fillWidth: true; from: -180.0; to: 180.0; stepSize: 0.5; onValueChanged: root._setSceneValue("iblRotationDeg", value) }
                        Label { text: iblRotationDeg.value.toFixed(1); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: iblRotationDeg; property string paramKey: "iblRotationDeg" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Roll"); color: root.textColor; Layout.preferredWidth: 80 }
                        Slider { id: iblRotationRollDeg; Layout.fillWidth: true; from: -180.0; to: 180.0; stepSize: 0.5; onValueChanged: root._setSceneValue("iblRotationRollDeg", value) }
                        Label { text: iblRotationRollDeg.value.toFixed(1); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: iblRotationRollDeg; property string paramKey: "iblRotationRollDeg" }
                    }
                    CheckBox { id: iblBindToCamera; text: qsTr("Bind To Camera"); onToggled: root._setSceneValue("iblBindToCamera", checked) }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Skybox Blur"); color: root.textColor; Layout.preferredWidth: 120 }
                        Slider { id: skyboxBlur; Layout.fillWidth: true; from: 0.0; to: 1.0; stepSize: 0.01; onValueChanged: root._setSceneValue("skyboxBlur", value) }
                        Label { text: skyboxBlur.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: skyboxBlur; property string paramKey: "skyboxBlur" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("HDR Path"); color: root.textColor; Layout.preferredWidth: 100 }
                        TextField { id: hdrPathField; Layout.fillWidth: true; placeholderText: qsTr("assets/hdr/studio.hdr"); onEditingFinished: root._setSceneValue("hdriPath", text) }
                    }
                }
            }
            GroupBox { Layout.fillWidth: true; title: qsTr("Fog")
                ColumnLayout { spacing: 6; Layout.fillWidth: true
                    CheckBox { id: fogEnabled; text: qsTr("Enabled"); onToggled: root._setSceneValue("fogEnabled", checked) }
                    Button { text: qsTr("Color"); onClicked: fogColorDialog.open() }
                    Rectangle { id: fogColorSwatch; width: 40; height: 20; radius: 4; border.color: root.borderColor; color: _sceneState.fogColor || "#aab9cf" }
                    ColorDialog { id: fogColorDialog; title: qsTr("Fog Color"); onAccepted: { fogColorSwatch.color = selectedColor; root._setSceneValue("fogColor", selectedColor.toString()) } }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Density"); color: root.textColor; Layout.preferredWidth: 90 }
                        Slider { id: fogDensity; Layout.fillWidth: true; from: 0.0; to: 1.0; stepSize: 0.001; onValueChanged: root._setSceneValue("fogDensity", value) }
                        Label { text: fogDensity.value.toFixed(3); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: fogDensity; property string paramKey: "fogDensity" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Near"); color: root.textColor; Layout.preferredWidth: 60 }
                        Slider { id: fogNear; Layout.fillWidth: true; from: 0.0; to: 200.0; stepSize: 0.5; onValueChanged: root._setSceneValue("fogDepthNear", value) }
                        Label { text: fogNear.value.toFixed(1); color: root.textColor; Layout.preferredWidth: 50 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: fogNear; property string paramKey: "fogDepthNear" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Far"); color: root.textColor; Layout.preferredWidth: 60 }
                        Slider { id: fogFar; Layout.fillWidth: true; from: 0.0; to: 2000.0; stepSize: 1.0; onValueChanged: root._setSceneValue("fogDepthFar", value) }
                        Label { text: fogFar.value.toFixed(0); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: fogFar; property string paramKey: "fogDepthFar" }
                    }
                    CheckBox { id: fogHeightEnabled; text: qsTr("Height Enabled"); onToggled: root._setSceneValue("fogHeightEnabled", checked) }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Least Y"); color: root.textColor; Layout.preferredWidth: 90 }
                        Slider { id: fogLeast; Layout.fillWidth: true; from: -50.0; to: 200.0; stepSize: 0.5; onValueChanged: root._setSceneValue("fogLeastIntenseY", value) }
                        Label { text: fogLeast.value.toFixed(1); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: fogLeast; property string paramKey: "fogLeastIntenseY" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Most Y"); color: root.textColor; Layout.preferredWidth: 90 }
                        Slider { id: fogMost; Layout.fillWidth: true; from: -50.0; to: 400.0; stepSize: 0.5; onValueChanged: root._setSceneValue("fogMostIntenseY", value) }
                        Label { text: fogMost.value.toFixed(1); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: fogMost; property string paramKey: "fogMostIntenseY" }
                    }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Height Curve"); color: root.textColor; Layout.preferredWidth: 120 }
                        Slider { id: fogHeightCurve; Layout.fillWidth: true; from: 0.0; to: 4.0; stepSize: 0.01; onValueChanged: root._setSceneValue("fogHeightCurve", value) }
                        Label { text: fogHeightCurve.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: fogHeightCurve; property string paramKey: "fogHeightCurve" }
                    }
                    CheckBox { id: fogTransmitEnabled; text: qsTr("Transmit Enabled"); onToggled: root._setSceneValue("fogTransmitEnabled", checked) }
                    RowLayout { Layout.fillWidth: true
                        Label { text: qsTr("Transmit Curve"); color: root.textColor; Layout.preferredWidth: 130 }
                        Slider { id: fogTransmitCurve; Layout.fillWidth: true; from: 0.0; to: 4.0; stepSize: 0.01; onValueChanged: root._setSceneValue("fogTransmitCurve", value) }
                        Label { text: fogTransmitCurve.value.toFixed(2); color: root.textColor; Layout.preferredWidth: 60 }
                        Loader { sourceComponent: rangeEditorComponent; property var targetSlider: fogTransmitCurve; property string paramKey: "fogTransmitCurve" }
                    }
                }
            }
        }
    }

    Component {
        id: sceneDefaultsComponent
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Label {
                    text: qsTr("Scale")
                    color: root.textColor
                    Layout.preferredWidth: 120
                }
                Slider {
                    id: scaleSlider
                    Layout.fillWidth: true
                    from: 0.25
                    to: 5.0
                    stepSize: 0.05
                    onValueChanged: root._setSceneValue("scale_factor", value)
                }
                Label {
                    id: scaleValueLabel
                    text: scaleSlider.value.toFixed(2)
                    color: root.textColor
                    Layout.preferredWidth: 60
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Label {
                    text: qsTr("Exposure")
                    color: root.textColor
                    Layout.preferredWidth: 120
                }
                Slider {
                    id: exposureSlider
                    Layout.fillWidth: true
                    from: 0.0
                    to: 16.0
                    stepSize: 0.1
                    onValueChanged: root._setSceneValue("exposure", value)
                }
                Label {
                    id: exposureValueLabel
                    text: exposureSlider.value.toFixed(2)
                    color: root.textColor
                    Layout.preferredWidth: 60
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Label {
                    text: qsTr("Clear color")
                    color: root.textColor
                    Layout.preferredWidth: 120
                }
                Rectangle {
                    id: clearColorSwatch
                    Layout.preferredWidth: 48
                    Layout.preferredHeight: 24
                    radius: 4
                    border.color: root.borderColor
                    border.width: 1
                }
                Button {
                    text: qsTr("Choose")
                    onClicked: clearColorDialog.open()
                }
                ColorDialog {
                    id: clearColorDialog
                    title: qsTr("Select clear color")
                    selectedColor: clearColorSwatch.color
                    onAccepted: root._setSceneValue(
                                    "default_clear_color",
                                    clearColorDialog.selectedColor.toString()
                                )
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Label {
                    text: qsTr("Model base color")
                    color: root.textColor
                    Layout.preferredWidth: 120
                }
                Rectangle {
                    id: baseColorSwatch
                    Layout.preferredWidth: 48
                    Layout.preferredHeight: 24
                    radius: 4
                    border.color: root.borderColor
                    border.width: 1
                }
                Button {
                    text: qsTr("Choose")
                    onClicked: baseColorDialog.open()
                }
                ColorDialog {
                    id: baseColorDialog
                    title: qsTr("Select model color")
                    selectedColor: baseColorSwatch.color
                    onAccepted: root._setSceneValue(
                                    "model_base_color",
                                    baseColorDialog.selectedColor.toString()
                                )
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Label {
                    text: qsTr("Roughness")
                    color: root.textColor
                    Layout.preferredWidth: 120
                }
                Slider {
                    id: roughnessSlider
                    Layout.fillWidth: true
                    from: 0.0
                    to: 1.0
                    stepSize: 0.01
                    onValueChanged: root._setSceneValue("model_roughness", value)
                }
                Label {
                    text: roughnessSlider.value.toFixed(2)
                    color: root.textColor
                    Layout.preferredWidth: 60
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Label {
                    text: qsTr("Metalness")
                    color: root.textColor
                    Layout.preferredWidth: 120
                }
                Slider {
                    id: metalnessSlider
                    Layout.fillWidth: true
                    from: 0.0
                    to: 1.0
                    stepSize: 0.01
                    onValueChanged: root._setSceneValue("model_metalness", value)
                }
                Label {
                    text: metalnessSlider.value.toFixed(2)
                    color: root.textColor
                    Layout.preferredWidth: 60
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Label {
                    text: qsTr("Rod warning threshold (m)")
                    color: root.textColor
                    Layout.preferredWidth: 180
                }
                Slider {
                    id: suspensionThresholdSlider
                    Layout.fillWidth: true
                    from: 0.0001
                    to: 0.02
                    stepSize: 0.0001
                    onValueChanged: root._setSuspensionValue(
                                      "rod_warning_threshold_m",
                                      value
                                  )
                }
                Label {
                    text: suspensionThresholdSlider.value.toFixed(4)
                    color: root.textColor
                    Layout.preferredWidth: 80
                }
            }

            GroupBox {
                Layout.fillWidth: true
                title: qsTr("Post-processing overrides")
                background: Rectangle {
                    radius: 6
                    color: Qt.darker(root.surfaceColor, 1.1)
                    border.color: root.borderColor
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    CheckBox {
                        id: postEffectsBypass
                        text: qsTr("Bypass post-effects")
                        checked: false
                        onToggled: root._setSceneValue("effects_bypass", checked)
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Label {
                            text: qsTr("Bypass reason")
                            color: root.textColor
                            Layout.preferredWidth: 140
                        }
                        TextField {
                            id: postEffectsReason
                            Layout.fillWidth: true
                            placeholderText: qsTr("Describe why post-processing is bypassed")
                            onEditingFinished: root._setSceneValue(
                                                   "effects_bypass_reason",
                                                   text
                                               )
                        }
                    }
                }
            }

            Component.onCompleted: root._registerSceneControls({
                scaleSlider: scaleSlider,
                exposureSlider: exposureSlider,
                clearColorSwatch: clearColorSwatch,
                baseColorSwatch: baseColorSwatch,
                roughnessSlider: roughnessSlider,
                metalnessSlider: metalnessSlider,
                suspensionThresholdSlider: suspensionThresholdSlider,
                postEffectsBypass: postEffectsBypass,
                postEffectsReason: postEffectsReason
            })
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: 10
        color: root.backgroundColor
        border.color: root.borderColor
        border.width: 1
        z: -1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        TabBar {
            id: tabBar
            objectName: "tabBar"
            Layout.fillWidth: true
            currentIndex: Math.min(currentIndex, count - 1)
            focusPolicy: Qt.StrongFocus
            Accessible.role: Accessible.PageTabList
            Accessible.name: qsTr("Graphics configuration categories")

            background: Rectangle {
                implicitHeight: 42
                radius: 8
                color: root.surfaceColor
                border.width: tabBar.activeFocus ? 2 : 1
                border.color: tabBar.activeFocus ? root.accentColor : root.borderColor
            }

            Repeater {
                model: root.tabs
                TabButton {
                    id: tabButton
                    required property var modelData
                    readonly property var tab: modelData
                    objectName: "tabButton_" + tab.key
                    text: qsTr(tab.title)
                    focusPolicy: Qt.StrongFocus
                    Accessible.role: Accessible.PageTab
                    Accessible.name: text
                    Accessible.description: tab.sections
                        .map(function(section) { return qsTr(section.title); })
                        .join(", ")

                    contentItem: Label {
                        text: tabButton.text
                        font.bold: tabButton.checked
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                        color: tabButton.checked || tabButton.activeFocus ? root.accentColor : root.textColor
                    }

                    background: Rectangle {
                        implicitHeight: 34
                        radius: 6
                        color: tabButton.checked ? Qt.lighter(root.surfaceColor, 1.2) : "transparent"
                        border.width: tabButton.activeFocus ? 2 : 1
                        border.color: tabButton.activeFocus ? root.accentColor : root.borderColor
                    }
                }
            }
        }

        StackLayout {
            id: tabStack
            objectName: "tabStack"
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            Repeater {
                model: root.tabs
                ScrollView {
                    id: tabPage
                    required property var modelData
                    readonly property var tab: modelData

                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: availableWidth
                    focusPolicy: Qt.StrongFocus
                    Accessible.role: Accessible.Pane
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical: ScrollBar {
                        id: verticalBar
                        policy: ScrollBar.AsNeeded
                        active: tabPage.activeFocus
                        background: Rectangle {
                            color: "transparent"
                        }
                        contentItem: Rectangle {
                            radius: 4
                            implicitWidth: 6
                            color: verticalBar.pressed || verticalBar.hovered
                                ? root.accentColor
                                : Qt.lighter(root.surfaceColor, 1.6)
                        }
                    }

                    ColumnLayout {
                        width: parent.width
                        spacing: 12

                        Repeater {
                            model: tabPage.tab.sections
                            GroupBox {
                                id: sectionGroup
                                required property var modelData
                                readonly property var section: modelData

                                Layout.fillWidth: true
                                objectName: "section_" + sectionGroup.section.key
                                title: qsTr(sectionGroup.section.title)
                                focusPolicy: Qt.StrongFocus
                                Accessible.role: Accessible.Grouping
                                Accessible.name: qsTr("%1 section").arg(sectionGroup.section.title)
                                Accessible.description: qsTr(sectionGroup.section.hint)

                                background: Rectangle {
                                    radius: 8
                                    color: root.surfaceColor
                                    border.width: sectionGroup.activeFocus ? 2 : 1
                                    border.color: sectionGroup.activeFocus ? root.accentColor : root.borderColor
                                }

                                ColumnLayout {
                                    width: parent.width
                                    spacing: 6

                                    Label {
                                        objectName: "hint_" + sectionGroup.section.key
                                        Layout.fillWidth: true
                                        text: qsTr(sectionGroup.section.hint)
                                        color: root.mutedTextColor
                                        wrapMode: Text.WordWrap
                                        Accessible.role: Accessible.StaticText
                                        Accessible.name: qsTr(sectionGroup.section.hint)
                                    }

                                    Loader {
                                        Layout.fillWidth: true
                                        active: sectionGroup.section.key === "sceneDefaults"
                                        sourceComponent: sceneDefaultsComponent
                                    }
