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

    // Shared integer scaling factor for spin boxes representing metre-based fractions
    readonly property int _floatScale: 10000
    readonly property var _defaultRanges: (modesMetadata && modesMetadata.parameterRanges) ? modesMetadata.parameterRanges : {}
    readonly property var _roadProfiles: [
        { text: qsTr("Гладкое шоссе"), value: "smooth_highway" },
        { text: qsTr("Городские улицы"), value: "city_streets" },
        { text: qsTr("Пересечённая местность"), value: "off_road" },
        { text: qsTr("Горный серпантин"), value: "mountain_serpentine" },
        { text: qsTr("Пользовательский"), value: "custom" }
    ]

    function _tr(id, fallback) {
        const resolved = qsTrId(id)
        if (resolved && resolved.length > 0) {
            return resolved
        }
        return fallback !== undefined ? fallback : ""
    }

    signal simulationControlRequested(string command)
    signal modesPresetSelected(string presetId)
    signal modesModeChanged(string modeType, string newMode)
    signal modesPhysicsChanged(var toggles)
    signal modesAnimationChanged(var payload)
    signal pneumaticSettingsChanged(var payload)
    signal simulationSettingsChanged(var payload)
    signal cylinderSettingsChanged(var payload)
    signal accordionPresetActivated(string panelId, string presetId)
    signal accordionFieldCommitted(string panelId, string field, var value)

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

    function _asScaledInt(value, scale) {
        var numeric = Number(value)
        var factor = Number(scale)
        if (!Number.isFinite(numeric) || !Number.isFinite(factor))
            return 0
        return Math.round(numeric * factor)
    }

    // Assign values coming from Python to SpinBox controls. We rely on the step size and
    // range metadata exposed by the control to decide whether the value should be coerced
    // to an integer, keeping the logic declarative instead of using the old forceInt helper.
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
        var scale = Number(spin.valueScale !== undefined ? spin.valueScale : 1)
        if (!Number.isFinite(scale) || scale <= 0)
            scale = 1
        var finalValue
        var requiresInteger = false
        if (scale !== 1) {
            finalValue = _asScaledInt(numeric, scale)
        } else {
            var step = Number(spin.stepSize)
            var fromValue = Number(spin.from)
            var toValue = Number(spin.to)
            if (Number.isFinite(step) && Number.isFinite(fromValue) && Number.isFinite(toValue)
                    && Math.round(step) === step
                    && Math.round(fromValue) === fromValue
                    && Math.round(toValue) === toValue) {
                finalValue = Math.round(numeric)
                requiresInteger = true
            } else {
                finalValue = numeric
            }
        }
        try {
            spin.value = finalValue
        } catch (error) {
            console.warn("⚠️ SimulationPanel: spin assignment failed for", logKey, "→", finalValue, error)
            if (scale !== 1) {
                var scaledFallback = _asScaledInt(numeric, scale)
                if (scaledFallback !== finalValue) {
                    try {
                        spin.value = scaledFallback
                        console.warn("ℹ️ SimulationPanel: coerced", logKey, "to scaled integer", scaledFallback)
                        return
                    } catch (scaledError) {
                        console.warn("⚠️ SimulationPanel: scaled fallback failed for", logKey, scaledError)
                    }
                }
            } else if (requiresInteger) {
                var fallback = Math.round(numeric)
                if (fallback !== finalValue) {
                    try {
                        spin.value = fallback
                        console.warn("ℹ️ SimulationPanel: coerced", logKey, "to rounded integer", fallback)
                        return
                    } catch (fallbackError) {
                        console.warn("⚠️ SimulationPanel: integer fallback failed for", logKey, fallbackError)
                    }
                }
            }
        }
    }

    function _assignScaledSpinValue(spin, rawValue, options) {
        if (!spin)
            return
        var numeric = _coerceNumeric(rawValue)
        if (numeric === undefined)
            return
        var scale = Number(spin.valueScale !== undefined ? spin.valueScale : 1)
        if (scale !== 1 && Math.round(numeric) === numeric && Math.abs(numeric) >= 1)
            numeric = numeric / scale
        _assignSpinValue(spin, numeric, options)
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
        if (roadProfileCombo) {
            payload.road_profile = roadProfileCombo.currentValue || roadProfileCombo.currentText
        }
        if (customProfileField) {
            payload.custom_profile_path = customProfileField.text
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
            include_pneumatics: pneumaticsCheck.checked,
            include_springs_kinematics: kinematicSpringsCheck.checked,
            include_dampers_kinematics: kinematicDampersCheck.checked
        })
    }

    function _emitAmbientTemperature(value) {
        if (value === undefined || value === null)
            return
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            return
        modesModeChanged("ambient_temperature_c", numeric)
        pneumaticSettingsChanged({ atmo_temp: numeric })
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
        if (data.road_profile !== undefined)
            _setComboValue(roadProfileCombo, data.road_profile, _roadProfiles[0].value)
        if (Object.prototype.hasOwnProperty.call(data, "custom_profile_path"))
            customProfileField.text = data.custom_profile_path || ""
        if (roadProfileCombo)
            customProfileField.enabled = (roadProfileCombo.currentValue || roadProfileCombo.currentText) === "custom"
        if (Object.prototype.hasOwnProperty.call(data, "check_interference"))
            _setCheckBox(interferenceCheck, data.check_interference, false)
        if (Object.prototype.hasOwnProperty.call(data, "ambient_temperature_c"))
            ambientTemperatureField.value = Number(data.ambient_temperature_c) || 0.0
        if (data.physics) {
            _setCheckBox(springsCheck, data.physics.include_springs, true)
            _setCheckBox(dampersCheck, data.physics.include_dampers, true)
            _setCheckBox(pneumaticsCheck, data.physics.include_pneumatics, true)
            _setCheckBox(
                kinematicSpringsCheck,
                data.physics.include_springs_kinematics,
                true
            )
            _setCheckBox(
                kinematicDampersCheck,
                data.physics.include_dampers_kinematics,
                true
            )
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
        if (data.road_profile !== undefined)
            _setComboValue(roadProfileCombo, data.road_profile, _roadProfiles[0].value)
        if (Object.prototype.hasOwnProperty.call(data, "custom_profile_path"))
            customProfileField.text = data.custom_profile_path || ""
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
            _assignSpinValue(cvAtmoDpSpin, data.cv_atmo_dp, { key: "cv_atmo_dp" })
        if (Object.prototype.hasOwnProperty.call(data, "cv_tank_dp"))
            _assignSpinValue(cvTankDpSpin, data.cv_tank_dp, { key: "cv_tank_dp" })
        if (Object.prototype.hasOwnProperty.call(data, "cv_atmo_dia"))
            _assignScaledSpinValue(cvAtmoDiaSpin, data.cv_atmo_dia, { key: "cv_atmo_dia" })
        if (Object.prototype.hasOwnProperty.call(data, "cv_tank_dia"))
            _assignScaledSpinValue(cvTankDiaSpin, data.cv_tank_dia, { key: "cv_tank_dia" })
        if (Object.prototype.hasOwnProperty.call(data, "relief_min_pressure"))
            _assignSpinValue(reliefMinSpin, data.relief_min_pressure, { key: "relief_min_pressure" })
        if (Object.prototype.hasOwnProperty.call(data, "relief_stiff_pressure"))
            _assignSpinValue(reliefStiffSpin, data.relief_stiff_pressure, { key: "relief_stiff_pressure" })
        if (Object.prototype.hasOwnProperty.call(data, "relief_safety_pressure"))
            _assignSpinValue(reliefSafetySpin, data.relief_safety_pressure, { key: "relief_safety_pressure" })
        if (Object.prototype.hasOwnProperty.call(data, "throttle_min_dia"))
            _assignScaledSpinValue(throttleMinSpin, data.throttle_min_dia, { key: "throttle_min_dia" })
        if (Object.prototype.hasOwnProperty.call(data, "throttle_stiff_dia"))
            _assignScaledSpinValue(throttleStiffSpin, data.throttle_stiff_dia, { key: "throttle_stiff_dia" })
        if (Object.prototype.hasOwnProperty.call(data, "diagonal_coupling_dia"))
            _assignScaledSpinValue(diagonalCouplingSpin, data.diagonal_coupling_dia, { key: "diagonal_coupling_dia" })
        if (Object.prototype.hasOwnProperty.call(data, "atmo_temp"))
            _assignSpinValue(atmoTempSpin, data.atmo_temp, { key: "atmo_temp" })
        if (Object.prototype.hasOwnProperty.call(data, "master_isolation_open"))
            masterIsolationCheck.checked = !!data.master_isolation_open
        _updatingFromPython = false
        return true
    }

    function applySimulationSettings(payload) {
        var data = payload || {}
        _updatingFromPython = true
        if (Object.prototype.hasOwnProperty.call(data, "physics_dt"))
            _assignScaledSpinValue(physicsDtSpin, data.physics_dt, { key: "physics_dt" })
        if (Object.prototype.hasOwnProperty.call(data, "render_vsync_hz"))
            _assignSpinValue(vsyncSpin, data.render_vsync_hz, { key: "render_vsync_hz" })
        if (Object.prototype.hasOwnProperty.call(data, "max_steps_per_frame"))
            _assignSpinValue(maxStepsSpin, data.max_steps_per_frame, { key: "max_steps_per_frame" })
        if (Object.prototype.hasOwnProperty.call(data, "max_frame_time"))
            _assignScaledSpinValue(maxFrameTimeSpin, data.max_frame_time, { key: "max_frame_time" })
        _updatingFromPython = false
        return true
    }

    function applyCylinderSettings(payload) {
        var data = payload || {}
        _updatingFromPython = true
        if (Object.prototype.hasOwnProperty.call(data, "dead_zone_head_m3"))
            _assignScaledSpinValue(deadZoneHeadSpin, data.dead_zone_head_m3, { key: "dead_zone_head_m3" })
        if (Object.prototype.hasOwnProperty.call(data, "dead_zone_rod_m3"))
            _assignScaledSpinValue(deadZoneRodSpin, data.dead_zone_rod_m3, { key: "dead_zone_rod_m3" })
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
                            accordionPresetActivated("modes", presetId)
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
                    CheckBox {
                        id: kinematicSpringsCheck
                        text: qsTr("Пружины в кинематике")
                        onToggled: {
                            if (root._updatingFromPython)
                                return
                            root._activePresetId = "custom"
                            _emitPhysicsOptions()
                        }
                    }
                    CheckBox {
                        id: kinematicDampersCheck
                        text: qsTr("Демпферы в кинематике")
                        onToggled: {
                            if (root._updatingFromPython)
                                return
                            root._activePresetId = "custom"
                            _emitPhysicsOptions()
                        }
                    }
                    CheckBox {
                        id: interferenceCheck
                        text: qsTr("Проверять пересечения")
                        onToggled: {
                            if (root._updatingFromPython)
                                return
                            root._activePresetId = "custom"
                            _emitPhysicsOptions()
                            modesModeChanged("check_interference", interferenceCheck.checked)
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
                            text: qsTr("Профиль дороги")
                            Layout.preferredWidth: 150
                        }
                        ComboBox {
                            id: roadProfileCombo
                            Layout.fillWidth: true
                            model: _roadProfiles
                            textRole: "text"
                            valueRole: "value"
                            onActivated: {
                                if (root._updatingFromPython)
                                    return
                                root._activePresetId = "custom"
                                customProfileField.enabled = currentValue === "custom"
                                _emitAnimationPayload()
                            }
                        }
                    }

                    TextField {
                        id: customProfileField
                        Layout.fillWidth: true
                        enabled: roadProfileCombo.currentValue === "custom"
                        placeholderText: qsTr("Путь или идентификатор пользовательского профиля")
                        onEditingFinished: {
                            if (root._updatingFromPython)
                                return
                            root._activePresetId = "custom"
                            _emitAnimationPayload()
                        }
                    }

                    Common.ValidatedField {
                        id: ambientTemperatureField
                        Layout.fillWidth: true
                        labelText: qsTr("Температура среды")
                        settingsKey: "ambient_temperature_c"
                        from: -80
                        to: 150
                        stepSize: 0.5
                        decimals: 1
                        unit: "°C"
                        helperText: qsTr("Доступный диапазон соответствует значениям из SettingsManager")
                        value: 20

                        onValueCommitted: function(key, numericValue) {
                            if (root._updatingFromPython)
                                return
                            root._activePresetId = "custom"
                            _emitAmbientTemperature(numericValue)
                            accordionFieldCommitted("modes", key, numericValue)
                        }

                        onValidationFailed: function(key, reason) {
                            console.warn("Validation error for", key, reason)
                        }
                    }

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
                            readonly property int valueScale: 1000
                            from: Math.round(amplitudeSlider.from * valueScale)
                            to: Math.round(amplitudeSlider.to * valueScale)
                            stepSize: Math.max(1, Math.round(amplitudeSlider.stepSize * valueScale))
                            value: Math.round(amplitudeSlider.value * valueScale)
                            editable: true
                            textFromValue: function(value, locale) {
                                return root._formatValue(value / valueScale, _defaultRanges.amplitude ? _defaultRanges.amplitude.decimals : 3)
                            }
                            valueFromText: function(text, locale) {
                                var numeric = Number(text)
                                return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                            }
                            onValueModified: amplitudeSlider.value = value / valueScale
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
                            readonly property int valueScale: 10
                            from: Math.round(frequencySlider.from * valueScale)
                            to: Math.round(frequencySlider.to * valueScale)
                            stepSize: Math.max(1, Math.round(frequencySlider.stepSize * valueScale))
                            value: Math.round(frequencySlider.value * valueScale)
                            editable: true
                            textFromValue: function(value, locale) {
                                return root._formatValue(value / valueScale, _defaultRanges.frequency ? _defaultRanges.frequency.decimals : 1)
                            }
                            valueFromText: function(text, locale) {
                                var numeric = Number(text)
                                return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                            }
                            onValueModified: frequencySlider.value = value / valueScale
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
                            readonly property int valueScale: 1000
                            from: Math.round(smoothingPistonSlider.from * valueScale)
                            to: Math.round(smoothingPistonSlider.to * valueScale)
                            stepSize: Math.max(1, Math.round(smoothingPistonSlider.stepSize * valueScale))
                            value: Math.round(smoothingPistonSlider.value * valueScale)
                            editable: true
                            textFromValue: function(value, locale) {
                                return root._formatValue(value / valueScale, _defaultRanges.smoothing_piston_snap_m ? _defaultRanges.smoothing_piston_snap_m.decimals : 3)
                            }
                            valueFromText: function(text, locale) {
                                var numeric = Number(text)
                                return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                            }
                            onValueModified: smoothingPistonSlider.value = value / valueScale
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
                title: root._tr("simulation.panel.section.pneumatics", qsTr("Пневматика"))
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    ComboBox {
                        id: volumeModeCombo
                        Layout.fillWidth: true
                        model: [
                            {
                                text: root._tr("simulation.panel.volumeMode.manual", qsTr("Ручной объём")),
                                value: "MANUAL"
                            },
                            {
                                text: root._tr("simulation.panel.volumeMode.geometric", qsTr("Геометрический расчёт")),
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
                            root._emitPneumaticChange("volume_mode", entry.value)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: root._tr("simulation.panel.receiverVolume", qsTr("Объём ресивера (м³)"))
                            Layout.preferredWidth: 200
                        }
                        Slider {
                            id: receiverVolumeSlider
                            from: (root.initialPneumatic && root.initialPneumatic.receiver_volume_limits && root.initialPneumatic.receiver_volume_limits.min_m3 !== undefined) ? Number(root.initialPneumatic.receiver_volume_limits.min_m3) : 0.001
                            to: (root.initialPneumatic && root.initialPneumatic.receiver_volume_limits && root.initialPneumatic.receiver_volume_limits.max_m3 !== undefined) ? Number(root.initialPneumatic.receiver_volume_limits.max_m3) : 1.0
                            stepSize: 0.0005
                            Layout.fillWidth: true
                            onValueChanged: {
                                if (root._updatingFromPython)
                                    return
                                root._emitPneumaticChange("receiver_volume", value)
                            }
                        }
                        SpinBox {
                            Layout.preferredWidth: 110
                            readonly property int valueScale: root._floatScale
                            from: Math.round(receiverVolumeSlider.from * valueScale)
                            to: Math.round(receiverVolumeSlider.to * valueScale)
                            stepSize: Math.max(1, Math.round(receiverVolumeSlider.stepSize * valueScale))
                            value: Math.round(receiverVolumeSlider.value * valueScale)
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value / valueScale, 4) }
                            valueFromText: function(text, locale) {
                                var numeric = Number(text)
                                return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                            }
                            onValueModified: receiverVolumeSlider.value = root._applyVolumeLimits(value / valueScale)
                        }
                    }

                    GridLayout {
                        columns: 2
                        columnSpacing: 12
                        rowSpacing: 6
                        Layout.fillWidth: true

                        Label {
                            text: root._tr("simulation.panel.cvAtmoDp", qsTr("ΔP атмосферного клапана (Па)"))
                        }
                        SpinBox {
                            id: cvAtmoDpSpin
                            from: 0
                            to: 5000000
                            stepSize: 100
                            value: 1000
                            editable: true
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("cv_atmo_dp", value)
                        }

                        Label {
                            text: root._tr("simulation.panel.cvTankDp", qsTr("ΔP клапана ресивера (Па)"))
                        }
                        SpinBox {
                            id: cvTankDpSpin
                            from: 0
                            to: 5000000
                            stepSize: 100
                            value: 1000
                            editable: true
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("cv_tank_dp", value)
                        }

                        Label {
                            text: root._tr("simulation.panel.cvAtmoDia", qsTr("Диаметр атмосферного клапана (м)"))
                        }
                        SpinBox {
                            id: cvAtmoDiaSpin
                            readonly property int valueScale: root._floatScale
                            from: 1
                            to: 200
                            stepSize: 1
                            value: root._asScaledInt(0.003, valueScale)
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value / valueScale, 4) }
                            valueFromText: function(text, locale) {
                                var numeric = Number(text)
                                return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                            }
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("cv_atmo_dia", value / valueScale)
                        }

                        Label {
                            text: root._tr("simulation.panel.cvTankDia", qsTr("Диаметр клапана ресивера (м)"))
                        }
                        SpinBox {
                            id: cvTankDiaSpin
                            readonly property int valueScale: root._floatScale
                            from: 1
                            to: 200
                            stepSize: 1
                            value: root._asScaledInt(0.003, valueScale)
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value / valueScale, 4) }
                            valueFromText: function(text, locale) {
                                var numeric = Number(text)
                                return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                            }
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("cv_tank_dia", value / valueScale)
                        }

                        Label {
                            text: root._tr("simulation.panel.reliefMin", qsTr("Порог открытия сброса (Па)"))
                        }
                        SpinBox {
                            id: reliefMinSpin
                            from: 0
                            to: 10000000
                            stepSize: 1000
                            value: 250000
                            editable: true
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("relief_min_pressure", value)
                        }

                        Label {
                            text: root._tr("simulation.panel.reliefStiff", qsTr("Жёсткий сброс (Па)"))
                        }
                        SpinBox {
                            id: reliefStiffSpin
                            from: 0
                            to: 20000000
                            stepSize: 1000
                            value: 1500000
                            editable: true
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("relief_stiff_pressure", value)
                        }

                        Label {
                            text: root._tr("simulation.panel.reliefSafety", qsTr("Аварийный сброс (Па)"))
                        }
                        SpinBox {
                            id: reliefSafetySpin
                            from: 0
                            to: 50000000
                            stepSize: 1000
                            value: 5000000
                            editable: true
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("relief_safety_pressure", value)
                        }

                        Label {
                            text: root._tr("simulation.panel.throttleMin", qsTr("Диаметр дросселя min (м)"))
                        }
                        SpinBox {
                            id: throttleMinSpin
                            readonly property int valueScale: root._floatScale
                            from: 1
                            to: 200
                            stepSize: 1
                            value: root._asScaledInt(0.001, valueScale)
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value / valueScale, 4) }
                            valueFromText: function(text, locale) {
                                var numeric = Number(text)
                                return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                            }
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("throttle_min_dia", value / valueScale)
                        }

                        Label {
                            text: root._tr("simulation.panel.throttleStiff", qsTr("Диаметр дросселя жёстк. (м)"))
                        }
                        SpinBox {
                            id: throttleStiffSpin
                            readonly property int valueScale: root._floatScale
                            from: 1
                            to: 200
                            stepSize: 1
                            value: root._asScaledInt(0.0015, valueScale)
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value / valueScale, 4) }
                            valueFromText: function(text, locale) {
                                var numeric = Number(text)
                                return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                            }
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("throttle_stiff_dia", value / valueScale)
                        }

                        Label {
                            text: root._tr("simulation.panel.diagonalThrottle", qsTr("Диаметр дросселя диагоналей (м)"))
                        }
                        SpinBox {
                            id: diagonalCouplingSpin
                            readonly property int valueScale: root._floatScale
                            from: 0
                            to: 200
                            stepSize: 1
                            value: root._asScaledInt(0.0008, valueScale)
                            editable: true
                            textFromValue: function(value, locale) { return root._formatValue(value / valueScale, 4) }
                            valueFromText: function(text, locale) {
                                var numeric = Number(text)
                                return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                            }
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("diagonal_coupling_dia", value / valueScale)
                        }

                        Label {
                            text: root._tr("simulation.panel.airTemperature", qsTr("Температура воздуха (°C)"))
                        }
                        SpinBox {
                            id: atmoTempSpin
                            from: -50
                            to: 150
                            stepSize: 1
                            value: 20
                            editable: true
                            onValueModified: if (!root._updatingFromPython) root._emitPneumaticChange("atmo_temp", value)
                        }
                    }

                    CheckBox {
                        id: masterIsolationCheck
                        text: root._tr("simulation.panel.masterIsolation", qsTr("Главный отсечной клапан открыт"))
                        onToggled: {
                            if (root._updatingFromPython)
                                return
                            root._emitPneumaticChange("master_isolation_open", masterIsolationCheck.checked)
                        }
                    }
                }
            }

            GroupBox {
                title: root._tr("simulation.panel.section.simulation", qsTr("Настройки симуляции"))
                Layout.fillWidth: true

                GridLayout {
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 8
                    Layout.fillWidth: true

                    Label {
                        text: root._tr("simulation.panel.physicsDt", qsTr("Шаг физики dt (с)"))
                    }
                    SpinBox {
                        id: physicsDtSpin
                        readonly property int valueScale: root._floatScale
                        from: 1
                        to: 200
                        stepSize: 1
                        value: root._asScaledInt(0.001, valueScale)
                        editable: true
                        textFromValue: function(value, locale) { return root._formatValue(value / valueScale, 4) }
                        valueFromText: function(text, locale) {
                            var numeric = Number(text)
                            return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                        }
                        onValueModified: if (!root._updatingFromPython) root._emitSimulationChange("physics_dt", value / valueScale)
                    }

                    Label {
                        text: root._tr("simulation.panel.vsync", qsTr("Ограничение FPS (Гц)"))
                    }
                    SpinBox {
                        id: vsyncSpin
                        from: 15
                        to: 360
                        stepSize: 1
                        value: 60
                        editable: true
                        onValueModified: if (!root._updatingFromPython) root._emitSimulationChange("render_vsync_hz", value)
                    }

                    Label {
                        text: root._tr("simulation.panel.stepsPerFrame", qsTr("Шагов на кадр (шт)"))
                    }
                    SpinBox {
                        id: maxStepsSpin
                        from: 1
                        to: 120
                        stepSize: 1
                        value: 10
                        editable: true
                        onValueModified: if (!root._updatingFromPython) root._emitSimulationChange("max_steps_per_frame", value)
                    }

                    Label {
                        text: root._tr("simulation.panel.maxFrameTime", qsTr("Макс. время кадра (с)"))
                    }
                    SpinBox {
                        id: maxFrameTimeSpin
                        readonly property int valueScale: 1000
                        from: 1
                        to: 200
                        stepSize: 1
                        value: root._asScaledInt(0.05, valueScale)
                        editable: true
                        textFromValue: function(value, locale) { return root._formatValue(value / valueScale, 3) }
                        valueFromText: function(text, locale) {
                            var numeric = Number(text)
                            return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                        }
                        onValueModified: if (!root._updatingFromPython) root._emitSimulationChange("max_frame_time", value / valueScale)
                    }
                }
            }

            GroupBox {
                title: root._tr("simulation.panel.section.cylinder", qsTr("Мёртвые зоны цилиндров"))
                Layout.fillWidth: true

                GridLayout {
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 6
                    Layout.fillWidth: true

                    Label {
                        text: root._tr("simulation.panel.deadZoneHead", qsTr("Головная камера (м³)"))
                    }
                    SpinBox {
                        id: deadZoneHeadSpin
                        readonly property int valueScale: root._floatScale
                        from: 0
                        to: 100
                        stepSize: 1
                        value: root._asScaledInt(0.001, valueScale)
                        editable: true
                        textFromValue: function(value, locale) { return root._formatValue(value / valueScale, 4) }
                        valueFromText: function(text, locale) {
                            var numeric = Number(text)
                            return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                        }
                        onValueModified: if (!root._updatingFromPython) root._emitCylinderChange("dead_zone_head_m3", value / valueScale)
                    }

                    Label {
                        text: root._tr("simulation.panel.deadZoneRod", qsTr("Штоковая камера (м³)"))
                    }
                    SpinBox {
                        id: deadZoneRodSpin
                        readonly property int valueScale: root._floatScale
                        from: 0
                        to: 100
                        stepSize: 1
                        value: root._asScaledInt(0.001, valueScale)
                        editable: true
                        textFromValue: function(value, locale) { return root._formatValue(value / valueScale, 4) }
                        valueFromText: function(text, locale) {
                            var numeric = Number(text)
                            return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                        }
                        onValueModified: if (!root._updatingFromPython) root._emitCylinderChange("dead_zone_rod_m3", value / valueScale)
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
