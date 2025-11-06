import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import "../Panels/Common" as Common

Pane {
    id: root

    property var controller: null
    property var modesMetadata: (typeof metadata !== "undefined" ? metadata : (typeof modesMetadata !== "undefined" ? modesMetadata : {}))
    property var initialModes: (typeof initialModesSettings !== "undefined" ? initialModesSettings : {})
    property var initialAnimation: (typeof initialAnimationSettings !== "undefined" ? initialAnimationSettings : {})
    property var initialPneumatic: (typeof initialPneumaticSettings !== "undefined" ? initialPneumaticSettings : {})
    property var initialSimulation: (typeof initialSimulationSettings !== "undefined" ? initialSimulationSettings : {})
    property var initialCylinder: (typeof initialCylinderSettings !== "undefined" ? initialCylinderSettings : {})

    property bool isReady: false
    property bool simulationRunning: false
    property string statusText: simulationRunning ? qsTr("▶ Запущено") : qsTr("⏹ Остановлено")

    property var _presetModel: []
    property string _activePresetId: ""
    property bool _updatingFromPython: false

    readonly property var _defaultRanges: (modesMetadata && modesMetadata.parameterRanges) ? modesMetadata.parameterRanges : {}

    signal simulationControlRequested(string command)
    signal modesPresetSelected(string presetId)
    signal modesModeChanged(string modeType, string newMode)
    signal modesPhysicsChanged(var toggles)
    signal modesAnimationChanged(var payload)
    signal pneumaticSettingsChanged(var payload)
    signal simulationSettingsChanged(var payload)
    signal cylinderSettingsChanged(var payload)

    padding: 16
    width: 420
    clip: true

    background: Rectangle {
        radius: 12
        color: Qt.rgba(0.07, 0.09, 0.13, 0.9)
        border.color: Qt.rgba(0.24, 0.29, 0.37, 0.9)
        border.width: 1
    }

    Component.onCompleted: {
        _presetModel = _buildPresetModel()
        applyModesSettings(initialModes)
        applyAnimationSettings(initialAnimation)
        applyPneumaticSettings(initialPneumatic)
        applySimulationSettings(initialSimulation)
        applyCylinderSettings(initialCylinder)
        isReady = true
        if (controller && typeof controller._onSimulationPanelReady === "function")
            controller._onSimulationPanelReady()
    }

    function _cloneObject(source) {
        if (!source || typeof source !== "object")
            return {}
        return JSON.parse(JSON.stringify(source))
    }

    function _buildPresetModel() {
        var metadata = modesMetadata || {}
        var presets = metadata.presets || []
        if (!presets.length)
            return []
        return presets.map(function(entry) {
            var label = entry.label || entry.name || entry.id || (qsTr("Пресет") + " " + (entry.index !== undefined ? entry.index : ""))
            return {
                id: String(entry.id || ""),
                label: label,
                description: entry.description || "",
                descriptionKey: entry.descriptionKey || "",
                labelKey: entry.labelKey || ""
            }
        })
    }

    function _formatValue(value, decimals) {
        if (value === undefined || value === null)
            return ""
        var d = Math.max(0, Math.min(6, Number(decimals || 0)))
        return Number(value).toLocaleString(Qt.locale(), { maximumFractionDigits: d, minimumFractionDigits: d })
    }

    function _setSliderValue(slider, value, fallback) {
        if (!slider)
            return
        if (value === undefined || value === null) {
            if (fallback !== undefined && fallback !== null)
                try {
                    slider.value = fallback
                } catch (error) {
                    console.warn("⚠️ SimulationPanel: fallback slider assignment failed", error)
                }
            return
        }
        var numeric = Number(value)
        if (Number.isFinite(numeric)) {
            try {
                slider.value = numeric
            } catch (error) {
                console.warn("⚠️ SimulationPanel: slider assignment failed", error)
            }
        } else if (fallback !== undefined && fallback !== null) {
            try {
                slider.value = fallback
            } catch (error) {
                console.warn("⚠️ SimulationPanel: slider fallback assignment failed", error)
            }
        }
    }

    function _setCheckBox(checkBox, value, fallback) {
        if (!checkBox)
            return
        if (value === undefined || value === null)
            checkBox.checked = !!fallback
        else
            checkBox.checked = !!value
    }

    function _setComboValue(combo, value, fallback) {
        if (!combo)
            return
        var target = (value === undefined || value === null || value === "") ? fallback : value
        if (target === undefined || target === null)
            target = ""
        var targetText = String(target).toUpperCase()
        var foundIndex = -1
        for (var i = 0; i < combo.count; ++i) {
            var candidate = combo.model[i]
            var candidateValue = candidate.value !== undefined ? candidate.value : candidate
            if (String(candidateValue).toUpperCase() === targetText) {
                foundIndex = i
                break
            }
        }
        if (foundIndex >= 0)
            combo.currentIndex = foundIndex
    }

    function _coerceNumeric(value) {
        var numeric = Number(value)
        return Number.isFinite(numeric) ? numeric : undefined
    }

    function _assignSpinValue(spin, rawValue, options) {
        if (!spin)
            return
        var opts = options || {}
        var numeric = _coerceNumeric(rawValue)
        var logKey = opts.key || "value"
        if (numeric === undefined) {
            console.warn("⚠️ SimulationPanel: ignoring non-numeric", logKey, rawValue)
            return
        }
        var finalValue = opts.forceInt ? Math.round(numeric) : numeric
        try {
            spin.value = finalValue
        } catch (error) {
            console.warn("⚠️ SimulationPanel: spin assignment failed for", logKey, "→", finalValue, error)
            if (!opts.forceInt) {
                var fallback = Math.round(numeric)
                if (fallback !== finalValue) {
                    try {
                        spin.value = fallback
                        console.warn("ℹ️ SimulationPanel: coerced", logKey, "to integer", fallback)
                        return
                    } catch (fallbackError) {
                        console.warn("⚠️ SimulationPanel: integer fallback failed for", logKey, fallbackError)
                    }
                }
            }
        }
    }

    function _emitAnimationPayload(extra) {
        var payload = {
            amplitude: amplitudeSlider.value,
            frequency: frequencySlider.value,
            phase: phaseSlider.value,
            lf_phase: lfPhaseSlider.value,
            rf_phase: rfPhaseSlider.value,
            lr_phase: lrPhaseSlider.value,
            rr_phase: rrPhaseSlider.value,
            smoothing_enabled: smoothingEnabledCheck.checked,
            smoothing_duration_ms: smoothingDurationSlider.value,
            smoothing_angle_snap_deg: smoothingAngleSlider.value,
            smoothing_piston_snap_m: smoothingPistonSlider.value,
            smoothing_easing: smoothingCombo.model[smoothingCombo.currentIndex].value
        }
        if (extra) {
            for (var key in extra) {
                if (Object.prototype.hasOwnProperty.call(extra, key))
                    payload[key] = extra[key]
            }
        }
        modesAnimationChanged(payload)
    }

    function _emitPhysicsOptions() {
        modesPhysicsChanged({
            include_springs: springsCheck.checked,
            include_dampers: dampersCheck.checked,
            include_pneumatics: pneumaticsCheck.checked
        })
    }

    function _emitPneumaticChange(key, value) {
        var payload = {}
        payload[key] = value
        pneumaticSettingsChanged(payload)
    }

    function _emitSimulationChange(key, value) {
        var payload = {}
        payload[key] = value
        simulationSettingsChanged(payload)
    }

    function _emitCylinderChange(key, value) {
        var payload = {}
        payload[key] = value
        cylinderSettingsChanged(payload)
    }

    function applyModesSettings(payload) {
        var data = payload || {}
        _updatingFromPython = true
        if (data.mode_preset !== undefined)
            _activePresetId = String(data.mode_preset || "")
        if (data.sim_type !== undefined)
            _setComboValue(simTypeCombo, data.sim_type, "KINEMATICS")
        if (data.thermo_mode !== undefined)
            _setComboValue(thermoCombo, data.thermo_mode, "ISOTHERMAL")
        if (data.physics) {
            _setCheckBox(springsCheck, data.physics.include_springs, true)
            _setCheckBox(dampersCheck, data.physics.include_dampers, true)
            _setCheckBox(pneumaticsCheck, data.physics.include_pneumatics, true)
        }
        _updatingFromPython = false
        return true
    }

    function applyAnimationSettings(payload) {
        var data = payload || {}
        _updatingFromPython = true
        if (data.amplitude !== undefined)
            _setSliderValue(amplitudeSlider, data.amplitude, amplitudeSlider.value)
        if (data.frequency !== undefined)
            _setSliderValue(frequencySlider, data.frequency, frequencySlider.value)
        if (data.phase !== undefined)
            _setSliderValue(phaseSlider, data.phase, phaseSlider.value)
        if (data.lf_phase !== undefined)
            _setSliderValue(lfPhaseSlider, data.lf_phase, lfPhaseSlider.value)
        if (data.rf_phase !== undefined)
            _setSliderValue(rfPhaseSlider, data.rf_phase, rfPhaseSlider.value)
        if (data.lr_phase !== undefined)
            _setSliderValue(lrPhaseSlider, data.lr_phase, lrPhaseSlider.value)
        if (data.rr_phase !== undefined)
            _setSliderValue(rrPhaseSlider, data.rr_phase, rrPhaseSlider.value)
        if (data.smoothing_enabled !== undefined)
            _setCheckBox(smoothingEnabledCheck, data.smoothing_enabled, true)
        if (data.smoothing_duration_ms !== undefined)
            _setSliderValue(smoothingDurationSlider, data.smoothing_duration_ms, smoothingDurationSlider.value)
        if (data.smoothing_angle_snap_deg !== undefined)
            _setSliderValue(smoothingAngleSlider, data.smoothing_angle_snap_deg, smoothingAngleSlider.value)
        if (data.smoothing_piston_snap_m !== undefined)
            _setSliderValue(smoothingPistonSlider, data.smoothing_piston_snap_m, smoothingPistonSlider.value)
        var easing = data.smoothing_easing || data.smoothingEasing || data.smoothingEasingName
        if (easing !== undefined)
            _setComboValue(smoothingCombo, easing, smoothingCombo.model[0].value)
        if (data.is_running !== undefined)
            simulationRunning = !!data.is_running
        _updatingFromPython = false
        return true
    }

    function applyPneumaticSettings(payload) {
        var data = payload || {}
        _updatingFromPython = true
        if (data.volume_mode !== undefined)
            _setComboValue(volumeModeCombo, data.volume_mode, "MANUAL")
        if (Object.prototype.hasOwnProperty.call(data, "receiver_volume"))
            _setSliderValue(receiverVolumeSlider, data.receiver_volume, receiverVolumeSlider.value)
        if (Object.prototype.hasOwnProperty.call(data, "cv_atmo_dp"))
            _assignSpinValue(cvAtmoDpSpin, data.cv_atmo_dp, { forceInt: true, key: "cv_atmo_dp" })
        if (Object.prototype.hasOwnProperty.call(data, "cv_tank_dp"))
            _assignSpinValue(cvTankDpSpin, data.cv_tank_dp, { forceInt: true, key: "cv_tank_dp" })
        if (Object.prototype.hasOwnProperty.call(data, "cv_atmo_dia"))
            _assignSpinValue(cvAtmoDiaSpin, data.cv_atmo_dia, { key: "cv_atmo_dia" })
        if (Object.prototype.hasOwnProperty.call(data, "cv_tank_dia"))
            _assignSpinValue(cvTankDiaSpin, data.cv_tank_dia, { key: "cv_tank_dia" })
        if (Object.prototype.hasOwnProperty.call(data, "relief_min_pressure"))
            _assignSpinValue(reliefMinSpin, data.relief_min_pressure, { forceInt: true, key: "relief_min_pressure" })
        if (Object.prototype.hasOwnProperty.call(data, "relief_stiff_pressure"))
            _assignSpinValue(reliefStiffSpin, data.relief_stiff_pressure, { forceInt: true, key: "relief_stiff_pressure" })
        if (Object.prototype.hasOwnProperty.call(data, "relief_safety_pressure"))
            _assignSpinValue(reliefSafetySpin, data.relief_safety_pressure, { forceInt: true, key: "relief_safety_pressure" })
        if (Object.prototype.hasOwnProperty.call(data, "throttle_min_dia"))
            _assignSpinValue(throttleMinSpin, data.throttle_min_dia, { key: "throttle_min_dia" })
        if (Object.prototype.hasOwnProperty.call(data, "throttle_stiff_dia"))
            _assignSpinValue(throttleStiffSpin, data.throttle_stiff_dia, { key: "throttle_stiff_dia" })
        if (Object.prototype.hasOwnProperty.call(data, "atmo_temp"))
            _assignSpinValue(atmoTempSpin, data.atmo_temp, { forceInt: true, key: "atmo_temp" })
        if (Object.prototype.hasOwnProperty.call(data, "master_isolation_open"))
            masterIsolationCheck.checked = !!data.master_isolation_open
        _updatingFromPython = false
        return true
    }

    function applySimulationSettings(payload) {
        var data = payload || {}
        _updatingFromPython = true
        if (Object.prototype.hasOwnProperty.call(data, "physics_dt"))
            _assignSpinValue(physicsDtSpin, data.physics_dt, { key: "physics_dt" })
        if (Object.prototype.hasOwnProperty.call(data, "render_vsync_hz"))
            _assignSpinValue(vsyncSpin, data.render_vsync_hz, { forceInt: true, key: "render_vsync_hz" })
        if (Object.prototype.hasOwnProperty.call(data, "max_steps_per_frame"))
            _assignSpinValue(maxStepsSpin, data.max_steps_per_frame, { forceInt: true, key: "max_steps_per_frame" })
        if (Object.prototype.hasOwnProperty.call(data, "max_frame_time"))
            _assignSpinValue(maxFrameTimeSpin, data.max_frame_time, { key: "max_frame_time" })
        _updatingFromPython = false
        return true
    }

    function applyCylinderSettings(payload) {
        var data = payload || {}
        _updatingFromPython = true
        if (Object.prototype.hasOwnProperty.call(data, "dead_zone_head_m3"))
            _assignSpinValue(deadZoneHeadSpin, data.dead_zone_head_m3, { key: "dead_zone_head_m3" })
        if (Object.prototype.hasOwnProperty.call(data, "dead_zone_rod_m3"))
            _assignSpinValue(deadZoneRodSpin, data.dead_zone_rod_m3, { key: "dead_zone_rod_m3" })
        _updatingFromPython = false
        return true
    }

    function _onControl(command) {
        if (!command)
            return
        if (command === "start")
            simulationRunning = true
        else if (command === "pause")
            simulationRunning = false
        else if (command === "stop")
            simulationRunning = false
        else if (command === "reset")
            simulationRunning = false

        if (command === "start")
            statusText = qsTr("▶ Запущено")
        else if (command === "pause")
            statusText = qsTr("⏸ Пауза")
        else if (command === "reset")
            statusText = qsTr("🔄 Сброс")
        else
            statusText = simulationRunning ? qsTr("▶ Запущено") : qsTr("⏹ Остановлено")

        simulationControlRequested(command)
    }

    function _applyVolumeLimits(value) {
        var limits = (initialPneumatic && initialPneumatic.receiver_volume_limits) ? initialPneumatic.receiver_volume_limits : {}
        var minValue = limits.min_m3 !== undefined ? Number(limits.min_m3) : receiverVolumeSlider.from
        var maxValue = limits.max_m3 !== undefined ? Number(limits.max_m3) : receiverVolumeSlider.to
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            return receiverVolumeSlider.value
        if (numeric < minValue)
            return minValue
        if (numeric > maxValue)
            return maxValue
        return numeric
    }

    ScrollView {
        id: scrollView
        anchors.fill: parent
        clip: true

        ColumnLayout {
            id: contentColumn
            width: scrollView.availableWidth
            spacing: 12

            GroupBox {
                title: qsTr("Управление симуляцией")
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Button {
                            text: qsTr("▶ Старт")
                            Layout.fillWidth: true
                            onClicked: _onControl("start")
                            enabled: !simulationRunning
                        }
                        Button {
                            text: qsTr("⏹ Стоп")
                            Layout.fillWidth: true
                            onClicked: _onControl("stop")
                            enabled: simulationRunning
                        }
                        Button {
                            text: qsTr("⏸ Пауза")
                            Layout.fillWidth: true
                            onClicked: _onControl("pause")
                            enabled: simulationRunning
                        }
                        Button {
                            text: qsTr("🔄 Сброс")
                            Layout.fillWidth: true
                            onClicked: _onControl("reset")
                            enabled: !simulationRunning
                        }
                    }

                    Label {
                        text: qsTr("Статус: %1").arg(statusText)
                        font.bold: true
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                    }

                    Label {
                        text: qsTr("Используйте кнопки выше или горячие клавиши: Space — старт/пауза, R — сброс.")
                        wrapMode: Text.WordWrap
                        color: Qt.rgba(0.75, 0.78, 0.86, 1.0)
                        font.pointSize: 9
                        Layout.fillWidth: true
                    }
                }
            }

            GroupBox {
                title: qsTr("Режим и пресеты")
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Common.PresetButtons {
                        id: presetButtons
                        Layout.fillWidth: true
                        title: qsTr("Быстрые пресеты")
                        model: root._presetModel
                        activePresetId: root._activePresetId
                        onPresetActivated: function(presetId) {
                            if (root._updatingFromPython)
                                return
                            root._activePresetId = presetId
                            modesPresetSelected(presetId)
                        }
                    }

                    ComboBox {
                        id: simTypeCombo
                        Layout.fillWidth: true
                        model: [
                            { text: qsTr("Кинематика"), value: "KINEMATICS" },
                            { text: qsTr("Динамика"), value: "DYNAMICS" }
                        ]
                        textRole: "text"
                        valueRole: "value"
                        onActivated: {
                            if (root._updatingFromPython)
                                return
                            var entry = model[index]
                            if (!entry)
                                return
                            root._activePresetId = "custom"
                            modesModeChanged("sim_type", entry.value)
                        }
                    }

                    ComboBox {
                        id: thermoCombo
                        Layout.fillWidth: true
                        model: [
                            { text: qsTr("Изотермический"), value: "ISOTHERMAL" },
                            { text: qsTr("Адиабатический"), value: "ADIABATIC" }
                        ]
                        textRole: "text"
                        valueRole: "value"
                        onActivated: {
                            if (root._updatingFromPython)
                                return
                            var entry = model[index]
                            if (!entry)
                                return
                            root._activePresetId = "custom"
                            modesModeChanged("thermo_mode", entry.value)
                        }
                    }
                }
            }

            GroupBox {
                title: qsTr("Опции физики")
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    CheckBox {
                        id: springsCheck
                        text: qsTr("Учитывать пружины")
                        onToggled: {
                            if (root._updatingFromPython)
                                return
                            root._activePresetId = "custom"
                            _emitPhysicsOptions()
                        }
                    }
                    CheckBox {
                        id: dampersCheck
                        text: qsTr("Учитывать демпферы")
                        onToggled: {
                            if (root._updatingFromPython)
                                return
                            root._activePresetId = "custom"
                            _emitPhysicsOptions()
                        }
                    }
                    CheckBox {
                        id: pneumaticsCheck
                        text: qsTr("Учитывать пневматику")
                        onToggled: {
                            if (root._updatingFromPython)
                                return
                            root._activePresetId = "custom"
                            _emitPhysicsOptions()
                        }
                    }
                }
            }

            GroupBox {
                title: qsTr("Дорожное воздействие")
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: qsTr("Амплитуда (м)")
                            Layout.preferredWidth: 150
                        }
                        Slider {
                            id: amplitudeSlider
                            from: (_defaultRanges.amplitude ? _defaultRanges.amplitude.min : 0.0)
                            to: (_defaultRanges.amplitude ? _defaultRanges.amplitude.max : 0.2)
                            stepSize: (_defaultRanges.amplitude ? _defaultRanges.amplitude.step : 0.001)
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitAnimationPayload()
                            }
                        }
                        SpinBox {
                            Layout.preferredWidth: 96
                            from: amplitudeSlider.from
                            to: amplitudeSlider.to
                            stepSize: amplitudeSlider.stepSize
                            value: amplitudeSlider.value
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, _defaultRanges.amplitude ? _defaultRanges.amplitude.decimals : 3) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: amplitudeSlider.value = value
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: qsTr("Частота (Гц)")
                            Layout.preferredWidth: 150
                        }
                        Slider {
                            id: frequencySlider
                            from: (_defaultRanges.frequency ? _defaultRanges.frequency.min : 0.1)
                            to: (_defaultRanges.frequency ? _defaultRanges.frequency.max : 10.0)
                            stepSize: (_defaultRanges.frequency ? _defaultRanges.frequency.step : 0.1)
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitAnimationPayload()
                            }
                        }
                        SpinBox {
                            Layout.preferredWidth: 96
                            from: frequencySlider.from
                            to: frequencySlider.to
                            stepSize: frequencySlider.stepSize
                            value: frequencySlider.value
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, _defaultRanges.frequency ? _defaultRanges.frequency.decimals : 1) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: frequencySlider.value = value
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: qsTr("Глобальная фаза (°)")
                            Layout.preferredWidth: 150
                        }
                        Slider {
                            id: phaseSlider
                            from: (_defaultRanges.phase ? _defaultRanges.phase.min : 0.0)
                            to: (_defaultRanges.phase ? _defaultRanges.phase.max : 360.0)
                            stepSize: (_defaultRanges.phase ? _defaultRanges.phase.step : 15.0)
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitAnimationPayload()
                            }
                        }
                        SpinBox {
                            Layout.preferredWidth: 96
                            from: phaseSlider.from
                            to: phaseSlider.to
                            stepSize: phaseSlider.stepSize
                            value: phaseSlider.value
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, _defaultRanges.phase ? _defaultRanges.phase.decimals : 0) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: phaseSlider.value = value
                        }
                    }

                    GridLayout {
                        columns: 2
                        columnSpacing: 12
                        rowSpacing: 8
                        Layout.fillWidth: true

                        Label { text: qsTr("Фаза ЛП (°)") }
                        Slider {
                            id: lfPhaseSlider
                            from: (_defaultRanges.wheel_phase ? _defaultRanges.wheel_phase.min : 0.0)
                            to: (_defaultRanges.wheel_phase ? _defaultRanges.wheel_phase.max : 360.0)
                            stepSize: (_defaultRanges.wheel_phase ? _defaultRanges.wheel_phase.step : 15.0)
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitAnimationPayload()
                            }
                        }

                        Label { text: qsTr("Фаза ПП (°)") }
                        Slider {
                            id: rfPhaseSlider
                            from: lfPhaseSlider.from
                            to: lfPhaseSlider.to
                            stepSize: lfPhaseSlider.stepSize
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitAnimationPayload()
                            }
                        }

                        Label { text: qsTr("Фаза ЛЗ (°)") }
                        Slider {
                            id: lrPhaseSlider
                            from: lfPhaseSlider.from
                            to: lfPhaseSlider.to
                            stepSize: lfPhaseSlider.stepSize
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitAnimationPayload()
                            }
                        }

                        Label { text: qsTr("Фаза ПЗ (°)") }
                        Slider {
                            id: rrPhaseSlider
                            from: lfPhaseSlider.from
                            to: lfPhaseSlider.to
                            stepSize: lfPhaseSlider.stepSize
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitAnimationPayload()
                            }
                        }
                    }

                    CheckBox {
                        id: smoothingEnabledCheck
                        text: qsTr("Плавное сглаживание движения")
                        onToggled: {
                            if (root._updatingFromPython)
                                return
                            _emitAnimationPayload({ smoothing_enabled: smoothingEnabledCheck.checked })
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: qsTr("Длительность сглаживания (мс)")
                            Layout.preferredWidth: 210
                        }
                        Slider {
                            id: smoothingDurationSlider
                            from: (_defaultRanges.smoothing_duration_ms ? _defaultRanges.smoothing_duration_ms.min : 0.0)
                            to: (_defaultRanges.smoothing_duration_ms ? _defaultRanges.smoothing_duration_ms.max : 600.0)
                            stepSize: (_defaultRanges.smoothing_duration_ms ? _defaultRanges.smoothing_duration_ms.step : 10.0)
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitAnimationPayload()
                            }
                        }
                        SpinBox {
                            Layout.preferredWidth: 96
                            from: smoothingDurationSlider.from
                            to: smoothingDurationSlider.to
                            stepSize: smoothingDurationSlider.stepSize
                            value: smoothingDurationSlider.value
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, _defaultRanges.smoothing_duration_ms ? _defaultRanges.smoothing_duration_ms.decimals : 0) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: smoothingDurationSlider.value = value
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: qsTr("Угол привязки (°)")
                            Layout.preferredWidth: 210
                        }
                        Slider {
                            id: smoothingAngleSlider
                            from: (_defaultRanges.smoothing_angle_snap_deg ? _defaultRanges.smoothing_angle_snap_deg.min : 0.0)
                            to: (_defaultRanges.smoothing_angle_snap_deg ? _defaultRanges.smoothing_angle_snap_deg.max : 180.0)
                            stepSize: (_defaultRanges.smoothing_angle_snap_deg ? _defaultRanges.smoothing_angle_snap_deg.step : 5.0)
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitAnimationPayload()
                            }
                        }
                        SpinBox {
                            Layout.preferredWidth: 96
                            from: smoothingAngleSlider.from
                            to: smoothingAngleSlider.to
                            stepSize: smoothingAngleSlider.stepSize
                            value: smoothingAngleSlider.value
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, _defaultRanges.smoothing_angle_snap_deg ? _defaultRanges.smoothing_angle_snap_deg.decimals : 0) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: smoothingAngleSlider.value = value
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: qsTr("Порог хода поршня (м)")
                            Layout.preferredWidth: 210
                        }
                        Slider {
                            id: smoothingPistonSlider
                            from: (_defaultRanges.smoothing_piston_snap_m ? _defaultRanges.smoothing_piston_snap_m.min : 0.0)
                            to: (_defaultRanges.smoothing_piston_snap_m ? _defaultRanges.smoothing_piston_snap_m.max : 0.3)
                            stepSize: (_defaultRanges.smoothing_piston_snap_m ? _defaultRanges.smoothing_piston_snap_m.step : 0.005)
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitAnimationPayload()
                            }
                        }
                        SpinBox {
                            Layout.preferredWidth: 96
                            from: smoothingPistonSlider.from
                            to: smoothingPistonSlider.to
                            stepSize: smoothingPistonSlider.stepSize
                            value: smoothingPistonSlider.value
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, _defaultRanges.smoothing_piston_snap_m ? _defaultRanges.smoothing_piston_snap_m.decimals : 3) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: smoothingPistonSlider.value = value
                        }
                    }

                    ComboBox {
                        id: smoothingCombo
                        Layout.fillWidth: true
                        model: [
                            { text: qsTr("OutCubic"), value: "OutCubic" },
                            { text: qsTr("OutQuad"), value: "OutQuad" },
                            { text: qsTr("Linear"), value: "Linear" },
                            { text: qsTr("InOutSine"), value: "InOutSine" }
                        ]
                        textRole: "text"
                        valueRole: "value"
                        onActivated: {
                            if (root._updatingFromPython)
                                return
                            _emitAnimationPayload({ smoothing_easing: model[index].value })
                        }
                    }
                }
            }

            GroupBox {
                title: qsTrId("simulation.panel.section.pneumatics") || qsTr("Пневматика")
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    ComboBox {
                        id: volumeModeCombo
                        Layout.fillWidth: true
                        model: [
                            {
                                text: qsTrId("simulation.panel.volumeMode.manual")
                                    || qsTr("Ручной объём"),
                                value: "MANUAL"
                            },
                            {
                                text: qsTrId("simulation.panel.volumeMode.geometric")
                                    || qsTr("Геометрический расчёт"),
                                value: "GEOMETRIC"
                            }
                        ]
                        textRole: "text"
                        valueRole: "value"
                        onActivated: {
                            if (root._updatingFromPython)
                                return
                            var entry = model[index]
                            if (!entry)
                                return
                            _emitPneumaticChange("volume_mode", entry.value)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: qsTrId("simulation.panel.receiverVolume")
                                || qsTr("Объём ресивера (м³)")
                            Layout.preferredWidth: 200
                        }
                        Slider {
                            id: receiverVolumeSlider
                            from: (initialPneumatic && initialPneumatic.receiver_volume_limits && initialPneumatic.receiver_volume_limits.min_m3 !== undefined) ? Number(initialPneumatic.receiver_volume_limits.min_m3) : 0.001
                            to: (initialPneumatic && initialPneumatic.receiver_volume_limits && initialPneumatic.receiver_volume_limits.max_m3 !== undefined) ? Number(initialPneumatic.receiver_volume_limits.max_m3) : 1.0
                            stepSize: 0.0005
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                _emitPneumaticChange("receiver_volume", value)
                            }
                        }
                        SpinBox {
                            Layout.preferredWidth: 110
                            from: receiverVolumeSlider.from
                            to: receiverVolumeSlider.to
                            stepSize: receiverVolumeSlider.stepSize
                            value: receiverVolumeSlider.value
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, 4) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: receiverVolumeSlider.value = _applyVolumeLimits(value)
                        }
                    }

                    GridLayout {
                        columns: 2
                        columnSpacing: 12
                        rowSpacing: 6
                        Layout.fillWidth: true

                        Label {
                            text: qsTrId("simulation.panel.cvAtmoDp")
                                || qsTr("ΔP атмосферного клапана (Па)")
                        }
                        SpinBox {
                            id: cvAtmoDpSpin
                            from: 0
                            to: 5000000
                            stepSize: 100
                            value: 1000
                            editable: true
                            onValueModified: if (!root._updatingFromPython) _emitPneumaticChange("cv_atmo_dp", value)
                        }

                        Label {
                            text: qsTrId("simulation.panel.cvTankDp")
                                || qsTr("ΔP клапана ресивера (Па)")
                        }
                        SpinBox {
                            id: cvTankDpSpin
                            from: 0
                            to: 5000000
                            stepSize: 100
                            value: 1000
                            editable: true
                            onValueModified: if (!root._updatingFromPython) _emitPneumaticChange("cv_tank_dp", value)
                        }

                        Label {
                            text: qsTrId("simulation.panel.cvAtmoDia")
                                || qsTr("Диаметр атмосферного клапана (м)")
                        }
                        SpinBox {
                            id: cvAtmoDiaSpin
                            from: 0.0001
                            to: 0.02
                            stepSize: 0.0001
                            value: 0.003
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, 4) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: if (!root._updatingFromPython) _emitPneumaticChange("cv_atmo_dia", value)
                        }

                        Label {
                            text: qsTrId("simulation.panel.cvTankDia")
                                || qsTr("Диаметр клапана ресивера (м)")
                        }
                        SpinBox {
                            id: cvTankDiaSpin
                            from: 0.0001
                            to: 0.02
                            stepSize: 0.0001
                            value: 0.003
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, 4) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: if (!root._updatingFromPython) _emitPneumaticChange("cv_tank_dia", value)
                        }

                        Label {
                            text: qsTrId("simulation.panel.reliefMin")
                                || qsTr("Порог открытия сброса (Па)")
                        }
                        SpinBox {
                            id: reliefMinSpin
                            from: 0
                            to: 10000000
                            stepSize: 1000
                            value: 250000
                            editable: true
                            onValueModified: if (!root._updatingFromPython) _emitPneumaticChange("relief_min_pressure", value)
                        }

                        Label {
                            text: qsTrId("simulation.panel.reliefStiff")
                                || qsTr("Жёсткий сброс (Па)")
                        }
                        SpinBox {
                            id: reliefStiffSpin
                            from: 0
                            to: 20000000
                            stepSize: 1000
                            value: 1500000
                            editable: true
                            onValueModified: if (!root._updatingFromPython) _emitPneumaticChange("relief_stiff_pressure", value)
                        }

                        Label {
                            text: qsTrId("simulation.panel.reliefSafety")
                                || qsTr("Аварийный сброс (Па)")
                        }
                        SpinBox {
                            id: reliefSafetySpin
                            from: 0
                            to: 50000000
                            stepSize: 1000
                            value: 5000000
                            editable: true
                            onValueModified: if (!root._updatingFromPython) _emitPneumaticChange("relief_safety_pressure", value)
                        }

                        Label {
                            text: qsTrId("simulation.panel.throttleMin")
                                || qsTr("Диаметр дросселя min (м)")
                        }
                        SpinBox {
                            id: throttleMinSpin
                            from: 0.0001
                            to: 0.02
                            stepSize: 0.0001
                            value: 0.001
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, 4) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: if (!root._updatingFromPython) _emitPneumaticChange("throttle_min_dia", value)
                        }

                        Label {
                            text: qsTrId("simulation.panel.throttleStiff")
                                || qsTr("Диаметр дросселя жёстк. (м)")
                        }
                        SpinBox {
                            id: throttleStiffSpin
                            from: 0.0001
                            to: 0.02
                            stepSize: 0.0001
                            value: 0.0015
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value, 4) }
                            valueFromText: function(text, locale) { return Number(text) }
                            onValueModified: if (!root._updatingFromPython) _emitPneumaticChange("throttle_stiff_dia", value)
                        }

                        Label {
                            text: qsTrId("simulation.panel.airTemperature")
                                || qsTr("Температура воздуха (°C)")
                        }
                        SpinBox {
                            id: atmoTempSpin
                            from: -50
                            to: 150
                            stepSize: 1
                            value: 20
                            editable: true
                            onValueModified: if (!root._updatingFromPython) _emitPneumaticChange("atmo_temp", value)
                        }
                    }

                    CheckBox {
                        id: masterIsolationCheck
                        text: qsTrId("simulation.panel.masterIsolation")
                            || qsTr("Главный отсечной клапан открыт")
                        onToggled: {
                            if (root._updatingFromPython)
                                return
                            _emitPneumaticChange("master_isolation_open", masterIsolationCheck.checked)
                        }
                    }
                }
            }

            GroupBox {
                title: qsTrId("simulation.panel.section.simulation")
                    || qsTr("Настройки симуляции")
                Layout.fillWidth: true

                GridLayout {
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 8
                    Layout.fillWidth: true

                    Label {
                        text: qsTrId("simulation.panel.physicsDt")
                            || qsTr("Шаг физики dt (с)")
                    }
                    SpinBox {
                        id: physicsDtSpin
                        from: 0.0001
                        to: 0.02
                        stepSize: 0.0001
                        value: 0.001
                        editable: true
                        textFromValue: function(value, locale) { return root._formatValue(value, 4) }
                        valueFromText: function(text, locale) { return Number(text) }
                        onValueModified: if (!root._updatingFromPython) _emitSimulationChange("physics_dt", value)
                    }

                    Label {
                        text: qsTrId("simulation.panel.vsync")
                            || qsTr("Ограничение FPS (Гц)")
                    }
                    SpinBox {
                        id: vsyncSpin
                        from: 15
                        to: 360
                        stepSize: 1
                        value: 60
                        editable: true
                        onValueModified: if (!root._updatingFromPython) _emitSimulationChange("render_vsync_hz", value)
                    }

                    Label {
                        text: qsTrId("simulation.panel.stepsPerFrame")
                            || qsTr("Шагов на кадр (шт)")
                    }
                    SpinBox {
                        id: maxStepsSpin
                        from: 1
                        to: 120
                        stepSize: 1
                        value: 10
                        editable: true
                        onValueModified: if (!root._updatingFromPython) _emitSimulationChange("max_steps_per_frame", value)
                    }

                    Label {
                        text: qsTrId("simulation.panel.maxFrameTime")
                            || qsTr("Макс. время кадра (с)")
                    }
                    SpinBox {
                        id: maxFrameTimeSpin
                        from: 0.001
                        to: 0.2
                        stepSize: 0.001
                        value: 0.05
                        editable: true
                        textFromValue: function(value, locale) { return root._formatValue(value, 3) }
                        valueFromText: function(text, locale) { return Number(text) }
                        onValueModified: if (!root._updatingFromPython) _emitSimulationChange("max_frame_time", value)
                    }
                }
            }

            GroupBox {
                title: qsTrId("simulation.panel.section.cylinder")
                    || qsTr("Мёртвые зоны цилиндров")
                Layout.fillWidth: true

                GridLayout {
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 6
                    Layout.fillWidth: true

                    Label {
                        text: qsTrId("simulation.panel.deadZoneHead")
                            || qsTr("Головная камера (м³)")
                    }
                    SpinBox {
                        id: deadZoneHeadSpin
                        from: 0.0
                        to: 0.01
                        stepSize: 0.0001
                        value: 0.001
                        editable: true
                        textFromValue: function(value, locale) { return root._formatValue(value, 4) }
                        valueFromText: function(text, locale) { return Number(text) }
                        onValueModified: if (!root._updatingFromPython) _emitCylinderChange("dead_zone_head_m3", value)
                    }

                    Label {
                        text: qsTrId("simulation.panel.deadZoneRod")
                            || qsTr("Штоковая камера (м³)")
                    }
                    SpinBox {
                        id: deadZoneRodSpin
                        from: 0.0
                        to: 0.01
                        stepSize: 0.0001
                        value: 0.001
                        editable: true
                        textFromValue: function(value, locale) { return root._formatValue(value, 4) }
                        valueFromText: function(text, locale) { return Number(text) }
                        onValueModified: if (!root._updatingFromPython) _emitCylinderChange("dead_zone_rod_m3", value)
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 8
            }
        }
    }
}
