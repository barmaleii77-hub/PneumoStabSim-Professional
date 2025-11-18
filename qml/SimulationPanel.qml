pragma ComponentBehavior: Bound

import QtQml 6.10
import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import "components" as Components

Item {
    id: root
    objectName: "simulationPanel"

    implicitWidth: layout.implicitWidth
    implicitHeight: layout.implicitHeight

    readonly property var uiConstants: Components.UiConstants
    readonly property var objectHasOwn: ({}).hasOwnProperty

    /**
     * Контекстный снимок настроек из SettingsManager.
     * См. config/app_settings.json → current.pneumatic / defaults_snapshot.pneumo.
     */
    // qmllint disable unqualified
    property var contextPneumatic: typeof initialPneumaticSettings !== "undefined" ? initialPneumaticSettings : ({})

    /**
     * Контекстный снимок общих параметров симуляции (давление/температура газа).
     * См. config/app_settings.json → current.simulation, defaults_snapshot.pneumo.gas.
     */
    property var contextSimulation: typeof initialSimulationSettings !== "undefined" ? initialSimulationSettings : ({})

    /**
     * Контекст сцены с графическими настройками (фон/атмосфера) для определения давления атмосферы.
     * См. config/app_settings.json → current.scene.environment.
     */
    property var contextScene: typeof initialSceneSettings !== "undefined" ? initialSceneSettings : ({})

    property var contextModes: typeof initialModesSettings !== "undefined" ? initialModesSettings : ({})
    property var contextAnimation: typeof initialAnimationSettings !== "undefined" ? initialAnimationSettings : ({})
    property var modesMetadata: ({})

    /**
     * Центральная шина обновлений настроек. Экспортируется python UISetup через SettingsEventBus.
     */
    property var settingsEventBus: typeof settingsEvents !== "undefined" ? settingsEvents : null
    // qmllint enable unqualified

    property string title: qsTr("Резервуар давления")
    property real pressure: 0.0
    property real minPressure: Number(uiConstants.pressure.min || 0.0)
    property real maxPressure: Number(uiConstants.pressure.max || 250000.0)
    property real userMinPressure: Number(uiConstants.pressure.userMin || minPressure)
    property real userMaxPressure: Number(uiConstants.pressure.userMax || maxPressure)
    property real atmosphericPressure: 101325.0
    property real reservoirPressure: pressure
    property var pressureMarkers: []
    property var flowTelemetry: ({})
    property bool masterIsolationValveOpen: false
    property var linePressureMap: ({})
    property var lineValveStateMap: ({})
    property var lineIntensityMap: ({})
    property var pressureGradientStops: []
    property bool _hasTelemetryGradient: false
    readonly property var _simTypeOptions: [
        { value: "KINEMATICS", label: qsTr("Кинематика") },
        { value: "DYNAMICS", label: qsTr("Динамика") }
    ]
    readonly property var _thermoModeOptions: [
        { value: "ISOTHERMAL", label: qsTr("Изотермический") },
        { value: "ADIABATIC", label: qsTr("Адиабатический") }
    ]
    readonly property var _roadProfileOptions: [
        { value: "smooth_highway", label: qsTr("Гладкое шоссе") },
        { value: "city_streets", label: qsTr("Городские улицы") },
        { value: "off_road", label: qsTr("Пересечённая местность") },
        { value: "mountain_serpentine", label: qsTr("Горный серпантин") },
        { value: "custom", label: qsTr("Пользовательский профиль") }
    ]

    readonly property real _tankTemperatureMin: Number(uiConstants.temperature.tankMin || 200.0)
    readonly property real _tankTemperatureMax: Number(uiConstants.temperature.tankMax || 450.0)
    readonly property real _ambientTemperatureMin: Number(uiConstants.temperature.ambientMin || -80.0)
    readonly property real _ambientTemperatureMax: Number(uiConstants.temperature.ambientMax || 150.0)

    // Кэшированные снимки настроек для синхронизации с SettingsManager.
    property var _pneumaticDefaults: ({})
    property var _pneumaticState: ({})
    property var _simulationDefaults: ({})
    property var _simulationState: ({})
    property var _sceneDefaults: ({})
    property var _sceneState: ({})
    property var _modesDefaults: ({})
    property var _modesState: ({})
    property var _animationDefaults: ({})
    property var _animationState: ({})
    property var _flowState: ({})
    property string _activePresetId: ""
    property real _telemetryEffectiveMinimum: NaN
    property real _telemetryEffectiveMaximum: NaN

    /** Internal snapshots exposed for tests */
    property var pneumaticStateSnapshot: _pneumaticState
    property var animationStateSnapshot: _animationState

    readonly property real effectiveMinimum: Number.isFinite(_telemetryEffectiveMinimum)
        ? _telemetryEffectiveMinimum
        : (function() {
        var list = [
            Number(minPressure),
            Number(maxPressure),
            Number(userMinPressure),
            Number(userMaxPressure),
            Number(atmosphericPressure),
            Number(reservoirPressure),
            Number(pressure)
        ]
        var filtered = []
        for (var i = 0; i < list.length; ++i) {
            if (Number.isFinite(list[i]))
                filtered.push(list[i])
        }
        return _minValue(filtered, 0.0)
    })()
    readonly property real effectiveMaximum: Number.isFinite(_telemetryEffectiveMaximum)
        ? _telemetryEffectiveMaximum
        : (function() {
        var list = [
            Number(minPressure),
            Number(maxPressure),
            Number(userMinPressure),
            Number(userMaxPressure),
            Number(atmosphericPressure),
            Number(reservoirPressure),
            Number(pressure)
        ]
        var filtered = []
        for (var i = 0; i < list.length; ++i) {
            if (Number.isFinite(list[i]))
                filtered.push(list[i])
        }
        return _maxValue(filtered, 1.0)
    })()
    readonly property bool hasValidRange: effectiveMaximum > effectiveMinimum
    readonly property real normalizedPressure: hasValidRange ? _normalize(pressure) : 0.0

    signal pressureChangedExternally(real value)
    signal simulationControlRequested(string command)
    signal modesPresetSelected(string presetId)
    signal modesModeChanged(string modeType, string newMode)
    signal modesPhysicsChanged(var payload)
    signal modesAnimationChanged(var payload)
    signal pneumaticSettingsChanged(var payload)
    signal simulationSettingsChanged(var payload)
    signal cylinderSettingsChanged(var payload)

    ListModel { id: presetModel }
    ListModel { id: flowModel }
    ListModel { id: lineValveListModel }
    ListModel { id: reliefValveListModel }
    QtObject {
        id: flowModelProxy
        property alias model: flowModel
        property list<var> entriesForPython: []
        function rowCount() { return flowModel.count }
        function get(index) {
            if (index >= 0 && index < entriesForPython.length)
                return entriesForPython[index]
            return ({})
        }
    }
    // Экспорт внутренних моделей как свойства для доступа из тестов
    property alias flowArrowsModel: flowModelProxy
    property alias lineValveModel: lineValveListModel
    property alias reliefValveModel: reliefValveListModel

    Instantiator {
        model: flowModelProxy.entriesForPython
        delegate: QtObject {
            required property var modelData

            objectName: "flowArrowProxy-" + (modelData.label || index)
            property real effectivePressureRatio: Number(modelData.pressureRatio)
            property real minPressure: root.minPressure
            property real maxPressure: root.maxPressure
        }
    }

    Component.onCompleted: {
        _refreshContextSnapshots()
        _rebuildPresetModel()
        _updatePressureBindings()
        _updateModesBindings()
        _updateAnimationBindings()
        _rebuildFlowModels()
    }

    onContextModesChanged: {
        _refreshContextSnapshots()
        _updateModesBindings()
    }

    onContextAnimationChanged: {
        _refreshContextSnapshots()
        _updateAnimationBindings()
    }

    onModesMetadataChanged: {
        _rebuildPresetModel()
        _updateModesBindings()
    }

    function _minValue(values, fallback) {
        if (!values.length)
            return fallback
        var min = values[0]
        for (var i = 1; i < values.length; ++i) {
            if (values[i] < min)
                min = values[i]
        }
        return min
    }

    function _maxValue(values, fallback) {
        if (!values.length)
            return fallback
        var max = values[0]
        for (var i = 1; i < values.length; ++i) {
            if (values[i] > max)
                max = values[i]
        }
        return max
    }

    function _normalize(value) {
        var min = effectiveMinimum
        var max = effectiveMaximum
        if (!hasValidRange)
            return 0.0
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = min
        var ratio = (numeric - min) / (max - min)
        if (!Number.isFinite(ratio))
            ratio = 0.0
        if (ratio < 0.0)
            ratio = 0.0
        else if (ratio > 1.0)
            ratio = 1.0
        return ratio
    }

    function _refreshContextSnapshots() {
        _pneumaticDefaults = _cloneObject(contextPneumatic)
        _pneumaticState = _cloneObject(_pneumaticDefaults)
        _simulationDefaults = _cloneObject(contextSimulation)
        _simulationState = _cloneObject(_simulationDefaults)
        _sceneDefaults = _cloneObject(contextScene)
        _sceneState = _cloneObject(_sceneDefaults)
        var modesSource = _cloneObject(contextModes)
        var metadataDefaults = _isPlainObject(modesMetadata) ? modesMetadata.defaults || modesMetadata.defaultValues || {} : {}
        _modesDefaults = _mergeObjects(metadataDefaults, modesSource)
        _modesState = _cloneObject(_modesDefaults)
        _animationDefaults = _cloneObject(contextAnimation)
        _animationState = _cloneObject(_animationDefaults)
        _flowState = {}
    }

    onPressureMarkersChanged: _updatePressureGradientScale()

    function _updatePressureBindings() {
        var candidatePressures = []

        function pushNumber(value) {
            var numeric = Number(value)
            if (Number.isFinite(numeric))
                candidatePressures.push(numeric)
        }

        pushNumber(_pneumaticNumber(["relief_min_pressure", "reliefMinPressure"], null))
        pushNumber(_pneumaticNumber(["relief_stiff_pressure", "reliefStiffPressure"], null))
        pushNumber(_pneumaticNumber(["relief_safety_pressure", "reliefSafetyPressure"], null))
        pushNumber(_pneumaticNumber([["receiver", "tank"], ["initial_pressure_pa", "initialPressurePa"]], null))
        pushNumber(_simulationNumber([["gas"], ["tank_pressure_initial_pa", "tankPressureInitialPa"]], null))
        pushNumber(_simulationNumber([["gas"], ["initial_pressure_pa", "initialPressurePa"]], null))

        var minCandidate = candidatePressures.length ? candidatePressures[0] : 0.0
        var maxCandidate = candidatePressures.length ? candidatePressures[0] : 1.0
        for (var i = 1; i < candidatePressures.length; ++i) {
            var value = candidatePressures[i]
            if (value < minCandidate)
                minCandidate = value
            if (value > maxCandidate)
                maxCandidate = value
        }

        if (!candidatePressures.length) {
            minCandidate = 0.0
            maxCandidate = 250000.0
        } else if (minCandidate === maxCandidate) {
            maxCandidate = minCandidate + 1000.0
        }

        var userMin = _pneumaticNumber([["receiver"], ["user_min_pressure_pa", "userMinPressurePa"]], minCandidate)
        var userMax = _pneumaticNumber([["receiver"], ["user_max_pressure_pa", "userMaxPressurePa"]], maxCandidate)
        var atmosphere = _sceneEnvironmentNumber([["atmosphere"], ["pressure", "pressurePa"]], 101325.0)
        atmosphere = Number.isFinite(atmosphere) ? atmosphere : 101325.0
        var receiver = _pneumaticNumber([["receiver", "tank"], ["initial_pressure_pa", "pressure_pa", "pressurePa", "initialPressurePa"]], pressure)

        minPressure = minCandidate
        maxPressure = maxCandidate
        userMinPressure = Number.isFinite(userMin) ? userMin : minCandidate
        userMaxPressure = Number.isFinite(userMax) ? userMax : maxCandidate
        atmosphericPressure = atmosphere
        reservoirPressure = Number.isFinite(receiver) ? receiver : minCandidate
        if (!Number.isFinite(pressure) || Math.abs(pressure - reservoirPressure) < 0.001)
            pressure = reservoirPressure
        pressureMarkers = [
            { value: minCandidate, color: Qt.rgba(0.46, 0.86, 0.52, 0.95), label: qsTr("Мин") },
            { value: maxCandidate, color: Qt.rgba(0.95, 0.55, 0.4, 0.95), label: qsTr("Макс") },
            { value: atmosphere, color: Qt.rgba(0.42, 0.72, 0.96, 0.95), label: qsTr("Атм") },
            { value: reservoirPressure, color: Qt.rgba(0.99, 0.83, 0.43, 0.95), label: qsTr("Рез") }
        ]
        _updatePressureGradientScale()
    }

    function _updatePressureGradientScale() {
        if (_hasTelemetryGradient)
            return
        var list = Array.isArray(pressureMarkers) && pressureMarkers.length ? pressureMarkers : []
        var stops = []
        for (var i = 0; i < list.length; ++i) {
            var entry = list[i] || {}
            var value = Number(entry.value)
            if (!Number.isFinite(value))
                continue
            stops.push({
                value: value,
                color: entry.color !== undefined ? entry.color : Qt.rgba(0.28, 0.5, 0.82, 0.65),
                label: entry.label !== undefined ? entry.label : ""
            })
        }
        if (stops.length < 2) {
            stops = [
                { value: minPressure, color: Qt.rgba(0.22, 0.45, 0.78, 0.65), label: qsTr("Мин") },
                { value: pressure, color: Qt.rgba(0.99, 0.83, 0.43, 0.9), label: qsTr("Тек") },
                { value: maxPressure, color: Qt.rgba(0.88, 0.42, 0.34, 0.75), label: qsTr("Макс") }
            ]
        }
        pressureGradientStops = stops
    }

    function _parameterRange(name) {
        var metadata = modesMetadata || {}
        var ranges = metadata.parameterRanges || metadata.parameter_ranges || {}
        var key = String(name)
        if (key === "phase_global")
            key = "phase"
        if (key === "phase" && !ranges[key])
            key = "phase"
        if ((key === "lf_phase" || key === "rf_phase" || key === "lr_phase" || key === "rr_phase") && ranges["wheel_phase"])
            key = "wheel_phase"
        var entry = ranges[key]
        if (!entry && ranges[key && key.toLowerCase ? key.toLowerCase() : key])
            entry = ranges[key.toLowerCase()]
        if (!entry && ranges[key && key.toUpperCase ? key.toUpperCase() : key])
            entry = ranges[key.toUpperCase()]
        return entry || {}
    }

    function _clampAnimationValue(name, value) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            return null
        var range = _parameterRange(name)
        if (range.min !== undefined) {
            var minValue = Number(range.min)
            if (Number.isFinite(minValue) && numeric < minValue)
                numeric = minValue
        }
        if (range.max !== undefined) {
            var maxValue = Number(range.max)
            if (Number.isFinite(maxValue) && numeric > maxValue)
                numeric = maxValue
        }
        return numeric
    }

    function _clampToRange(value, minValue, maxValue, fallback) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            return fallback
        var min = Number(minValue)
        var max = Number(maxValue)
        if (Number.isFinite(min) && numeric < min)
            numeric = min
        if (Number.isFinite(max) && numeric > max)
            numeric = max
        return numeric
    }

    function _rebuildPresetModel() {
        if (!presetModel)
            return
        while (presetModel.count > 0)
            presetModel.remove(0)
        var metadata = modesMetadata || {}
        var presets = metadata.presets || []
        if (Array.isArray(presets) && presets.length) {
            for (var i = 0; i < presets.length; ++i) {
                var entry = presets[i] || {}
                var idValue = entry.id !== undefined ? entry.id : (entry.name !== undefined ? entry.name : entry.index)
                var idText = String(idValue !== undefined ? idValue : ("preset_" + i)).trim()
                if (!idText.length)
                    idText = "preset_" + i
                presetModel.append({
                    id: idText,
                    label: entry.label || entry.name || idText,
                    description: entry.description || ""
                })
            }
        } else {
            presetModel.append({ id: "standard", label: qsTr("Стандартный"), description: "" })
        }
    }

    function _findPresetIndex(presetId) {
        if (!presetModel)
            return -1
        var normalized = String(presetId || "").trim().toLowerCase()
        for (var i = 0; i < presetModel.count; ++i) {
            var entry = presetModel.get(i)
            var idText = String(entry.id || "").trim().toLowerCase()
            if (idText === normalized)
                return i
        }
        return -1
    }

    function _modesValue(path, fallback) {
        var source = _modesState || ({})
        var keys = Array.isArray(path) ? path : [path]
        var current = source
        for (var i = 0; i < keys.length; ++i) {
            if (!_isPlainObject(current))
                return fallback
            var key = keys[i]
            if (current[key] === undefined)
                return fallback
            current = current[key]
        }
        return current !== undefined ? current : fallback
    }

    function _modeOrAnimationValue(path, fallback) {
        var value = _modesValue(path, undefined)
        if (value !== undefined)
            return value
        return _animationValue(path, fallback)
    }

    function _animationValue(key, fallback) {
        if (_animationState && _animationState[key] !== undefined)
            return _animationState[key]
        if (_modesState && _modesState[key] !== undefined)
            return _modesState[key]
        return fallback
    }

    function _formatNumeric(value, decimals) {
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = 0.0
        var fractionDigits = Number(decimals)
        if (!Number.isFinite(fractionDigits))
            fractionDigits = 2
        return Qt.locale().toString(numeric, "f", fractionDigits)
    }

    function _findOptionIndex(options, value) {
        var target = String(value || "").toUpperCase()
        for (var i = 0; i < options.length; ++i) {
            var entry = options[i]
            var candidate = String(entry.value || "").toUpperCase()
            if (candidate === target)
                return i
        }
        return -1
    }

    function _updateModesBindings() {
        var presetId = String(_modesValue("mode_preset", ""))
        if (!presetId.length && presetModel && presetModel.count > 0)
            presetId = presetModel.get(0).id
        _activePresetId = presetId
        if (presetCombo && presetModel) {
            var index = _findPresetIndex(presetId)
            presetCombo.currentIndex = index >= 0 ? index : 0
        }
        if (simTypeCombo) {
            var simValue = String(_modesValue("sim_type", "KINEMATICS")).toUpperCase()
            var simIndex = _findOptionIndex(_simTypeOptions, simValue)
            simTypeCombo.currentIndex = simIndex >= 0 ? simIndex : 0
        }
        if (thermoModeCombo) {
            var thermoValue = String(_modesValue("thermo_mode", "ISOTHERMAL")).toUpperCase()
            var thermoIndex = _findOptionIndex(_thermoModeOptions, thermoValue)
            thermoModeCombo.currentIndex = thermoIndex >= 0 ? thermoIndex : 0
        }
        if (roadProfileCombo) {
            var roadProfileValue = String(_modeOrAnimationValue("road_profile", "smooth_highway")).toLowerCase()
            var roadIndex = _findOptionIndex(_roadProfileOptions, roadProfileValue)
            roadProfileCombo.currentIndex = roadIndex >= 0 ? roadIndex : 0
        }
        if (customProfileField) {
            customProfileField.text = String(_modeOrAnimationValue("custom_profile_path", ""))
            customProfileField.enabled = roadProfileCombo && String(roadProfileCombo.currentValue || roadProfileCombo.displayText).toLowerCase() === "custom"
        }
        if (interferenceSwitch)
            interferenceSwitch.checked = !!_modeOrAnimationValue("check_interference", false)
        if (springsSwitch)
            springsSwitch.checked = !!_modesValue(["physics", "include_springs"], true)
        if (dampersSwitch)
            dampersSwitch.checked = !!_modesValue(["physics", "include_dampers"], true)
        if (pneumaticsSwitch)
            pneumaticsSwitch.checked = !!_modesValue(["physics", "include_pneumatics"], true)
        if (kinematicSpringsSwitch)
            kinematicSpringsSwitch.checked = !!_modesValue(["physics", "include_springs_kinematics"], true)
        if (kinematicDampersSwitch)
            kinematicDampersSwitch.checked = !!_modesValue(["physics", "include_dampers_kinematics"], true)
    }

    function _updateAnimationBindings() {
        if (amplitudeField)
            amplitudeField.text = _formatNumeric(_animationValue("amplitude", 0.05), 3)
        if (frequencyField)
            frequencyField.text = _formatNumeric(_animationValue("frequency", 1.0), 2)
        if (phaseField)
            phaseField.text = _formatNumeric(_animationValue("phase", _animationValue("phase_global", 0.0)), 1)
        if (temperatureField)
            temperatureField.text = _formatNumeric(_pneumaticNumber([["gas"], ["tank_temperature_initial_k", "tankTemperatureInitialK"]], 293.15), 1)
        if (ambientTemperatureField)
            ambientTemperatureField.text = _formatNumeric(_pneumaticNumber("atmo_temp", 20.0), 1)
        if (smoothingSwitch)
            smoothingSwitch.checked = !!_animationValue("smoothing_enabled", true)
        if (smoothingDurationField)
            smoothingDurationField.text = _formatNumeric(_animationValue("smoothing_duration_ms", 120.0), 0)
        if (smoothingAngleField)
            smoothingAngleField.text = _formatNumeric(_animationValue("smoothing_angle_snap_deg", 65.0), 0)
        if (smoothingPistonField)
            smoothingPistonField.text = _formatNumeric(_animationValue("smoothing_piston_snap_m", 0.05), 3)
    }

    function _emitAnimationNumericChange(name, rawValue) {
        var numeric = _clampAnimationValue(name, rawValue)
        if (numeric === null)
            return
        if (!_animationState)
            _animationState = {}
        _animationState[name] = numeric
        var payload = {}
        payload[name] = numeric
        root.modesAnimationChanged(payload)
        _updateAnimationBindings()
    }

    function _emitAnimationToggle(name, checked) {
        if (!_animationState)
            _animationState = {}
        _animationState[name] = !!checked
        var payload = {}
        payload[name] = !!checked
        root.modesAnimationChanged(payload)
    }

    function _emitTemperatureChange(rawValue) {
        var numeric = _clampToRange(rawValue, _tankTemperatureMin, _tankTemperatureMax, null)
        if (numeric === null)
            return
        _pneumaticState = _mergeObjects(_pneumaticState, { gas: { tank_temperature_initial_k: numeric } })
        root.pneumaticSettingsChanged({ gas: { tank_temperature_initial_k: numeric } })
        _updateAnimationBindings()
    }

    function _emitAmbientTemperatureChange(rawValue) {
        var numeric = _clampToRange(rawValue, _ambientTemperatureMin, _ambientTemperatureMax, null)
        if (numeric === null)
            return
        _pneumaticState = _mergeObjects(_pneumaticState, { atmo_temp: numeric })
        root.pneumaticSettingsChanged({ atmo_temp: numeric })
        _updateAnimationBindings()
    }

    function _emitRoadProfileChange(value) {
        var normalized = String(value || "").toLowerCase()
        var known = _findOptionIndex(_roadProfileOptions, normalized) >= 0
        var resolved = known ? normalized : (_roadProfileOptions.length ? _roadProfileOptions[0].value : "smooth_highway")
        _modesState = _mergeObjects(_modesState, { road_profile: resolved })
        root.modesModeChanged("road_profile", resolved)
        _updateModesBindings()
    }

    function _emitCustomProfileChange(value) {
        var text = String(value || "").trim()
        var currentProfile = String(_modeOrAnimationValue("road_profile", "")).toLowerCase()
        if (currentProfile !== "custom")
            _emitRoadProfileChange("custom")
        _modesState = _mergeObjects(_modesState, { custom_profile_path: text })
        root.modesModeChanged("custom_profile_path", text)
    }

    function _emitInterferenceChange(checked) {
        var enabled = !!checked
        _modesState = _mergeObjects(_modesState, { check_interference: enabled })
        root.modesModeChanged("check_interference", enabled)
    }

    function _emitPhysicsPayload() {
        var payload = {
            include_springs: springsSwitch ? !!springsSwitch.checked : true,
            include_dampers: dampersSwitch ? !!dampersSwitch.checked : true,
            include_pneumatics: pneumaticsSwitch ? !!pneumaticsSwitch.checked : true,
            include_springs_kinematics: kinematicSpringsSwitch ? !!kinematicSpringsSwitch.checked : true,
            include_dampers_kinematics: kinematicDampersSwitch ? !!kinematicDampersSwitch.checked : true
        }
        _modesState = _mergeObjects(_modesState, { physics: _mergeObjects(_modesValue("physics", {}), payload) })
        root.modesPhysicsChanged(payload)
    }

    function _clearModel(model) {
        if (!model)
            return
        while (model.count > 0)
            model.remove(0)
    }

    function _appendValveEntry(model, entry) {
        if (!model)
            return
        model.append(entry)
    }

    function _normalizeFlowPayload(payload) {
        var source = _cloneObject(payload || ({}))
        if (_isPlainObject(source.flowNetwork))
            return source.flowNetwork
        if (_isPlainObject(source.flow_network))
            return source.flow_network
        if (_isPlainObject(source.flownetwork))
            return source.flownetwork
        return source
    }

    function _rebuildFlowModels(payload) {
        _clearModel(flowModel)
        _clearModel(lineValveListModel)
        _clearModel(reliefValveListModel)
        _hasTelemetryGradient = false
        _telemetryEffectiveMinimum = NaN
        _telemetryEffectiveMaximum = NaN
        var normalized = _normalizeFlowPayload(payload !== undefined ? payload : flowTelemetry)
        if (!_isPlainObject(normalized))
            return
        var pythonEntries = []
        _flowState = normalized
        _applyFlowTelemetryState(normalized)
        var linesNode = normalized.lines || normalized.Lines || {}
        var lineKeys = []
        if (_isPlainObject(linesNode))
            lineKeys = Object.keys(linesNode)
        lineKeys.sort()
        var maxIntensity = Number(normalized.maxLineIntensity)
        if (!Number.isFinite(maxIntensity) || maxIntensity <= 0)
            maxIntensity = 0.0
        var pressureMap = {}
        var intensityMap = {}
        var valveStateMap = {}
        var linePressuresNode = _isPlainObject(normalized.linePressures) ? normalized.linePressures : {}
        var receiverNode = normalized.receiver
        if (!_isPlainObject(receiverNode) && _isPlainObject(normalized.flowNetwork))
            receiverNode = normalized.flowNetwork.receiver
        var receiverPressures = _isPlainObject(receiverNode) ? receiverNode.pressures : {}
        for (var i = 0; i < lineKeys.length; ++i) {
            var key = lineKeys[i]
            var entry = linesNode[key] || {}
            if (!_isPlainObject(entry))
                continue
            var direction = String(entry.direction || entry.flowDirection || "")
            var flows = entry.flows || {}
            var net = entry.netFlow !== undefined ? entry.netFlow : (flows.net !== undefined ? flows.net : 0.0)
            var netNumeric = Number(net)
            if (!Number.isFinite(netNumeric))
                netNumeric = 0.0
            var intensity = entry.flowIntensity !== undefined ? Number(entry.flowIntensity) : Math.abs(netNumeric)
            if (!Number.isFinite(intensity))
                intensity = Math.abs(netNumeric)
            if (maxIntensity <= 0 && intensity > maxIntensity)
                maxIntensity = intensity
            var normalized = maxIntensity > 0 ? Math.max(0.0, Math.min(1.0, intensity / maxIntensity)) : 0.0
            var label = String(key || "line").toUpperCase()
            if (!direction.length)
                direction = netNumeric >= 0 ? "intake" : "exhaust"
            var rawPressure = Number(_lookupMapValue(linePressuresNode, key))
            if (!Number.isFinite(rawPressure))
                rawPressure = Number(_lookupMapValue(receiverPressures, key))
            if (!Number.isFinite(rawPressure))
                rawPressure = Number(reservoirPressure)
            if (!Number.isFinite(rawPressure))
                rawPressure = 0.0
            var pressureRatio = hasValidRange ? Math.max(0.0, Math.min(1.0, _normalize(rawPressure))) : 0.0
            var animationSpeed = entry.animationSpeed !== undefined ? Number(entry.animationSpeed) : Number(entry.speedHint)
            if (!Number.isFinite(animationSpeed))
                animationSpeed = normalized
            if (animationSpeed < 0.0)
                animationSpeed = 0.0
            else if (animationSpeed > 1.0)
                animationSpeed = 1.0
            var modelEntry = {
                label: label,
                direction: direction,
                flow: netNumeric,
                intensity: normalized,
                animationSpeed: animationSpeed,
                pressure: rawPressure,
                pressureRatio: pressureRatio
            }
            flowModel.append(modelEntry)
            pythonEntries.push(_cloneObject(modelEntry))
            var valves = entry.valves || {}
            var flowAtmo = Number(flows.fromAtmosphere || flows.from_atmosphere || 0.0)
            if (!Number.isFinite(flowAtmo))
                flowAtmo = 0.0
            var flowTank = Number(flows.toTank || flows.to_tank || 0.0)
            if (!Number.isFinite(flowTank))
                flowTank = 0.0
            pressureMap[label] = rawPressure
            intensityMap[label] = normalized
            valveStateMap[label] = {
                atmosphereOpen: !!valves.atmosphereOpen,
                tankOpen: !!valves.tankOpen
            }
            _appendValveEntry(lineValveListModel, {
                label: label + " • " + qsTr("Атмосфера"),
                open: !!valves.atmosphereOpen,
                direction: "intake",
                flowValue: flowAtmo,
                hint: qsTr("Подача из внешней среды")
            })
            _appendValveEntry(lineValveListModel, {
                label: label + " • " + qsTr("Танк"),
                open: !!valves.tankOpen,
                direction: "exhaust",
                flowValue: flowTank,
                hint: qsTr("Подача в резервуар")
            })
        }
        var relief = normalized.relief || {}
        var reliefKeys = ["min", "stiff", "safety"]
        for (var r = 0; r < reliefKeys.length; ++r) {
            var reliefKey = reliefKeys[r]
            var reliefEntry = relief[reliefKey] || {}
            if (!_isPlainObject(reliefEntry))
                continue
            var flow = Number(reliefEntry.flow || 0.0)
            if (!Number.isFinite(flow))
                flow = 0.0
            _appendValveEntry(reliefValveListModel, {
                label: qsTr("Клапан %1").arg(reliefKey.toUpperCase()),
                open: !!reliefEntry.open,
                direction: reliefEntry.direction || (flow >= 0 ? "exhaust" : "intake"),
                flowValue: flow,
                hint: qsTr("Резервуар → Атмосфера")
            })
        }
        var masterState = normalized.masterIsolationOpen
        if (masterState === undefined)
            masterState = normalized.master_isolation_open
        masterIsolationValveOpen = !!masterState
        linePressureMap = pressureMap
        lineIntensityMap = intensityMap
        lineValveStateMap = valveStateMap
        flowModelProxy.entriesForPython = pythonEntries
    }

    function _applyFlowTelemetryState(payload) {
        var telemetryApplied = false
        var source = _normalizeFlowPayload(payload !== undefined ? payload : flowTelemetry)
        if (!_isPlainObject(source))
            return
        var receiver = source.receiver
        if (!_isPlainObject(receiver) && _isPlainObject(source.flowNetwork))
            receiver = source.flowNetwork.receiver
        if (_isPlainObject(receiver)) {
            var tankPressure = Number(receiver.tankPressure !== undefined ? receiver.tankPressure : receiver.pressure)
            if (Number.isFinite(tankPressure)) {
                reservoirPressure = tankPressure
                pressure = tankPressure
            }
            var minP = Number(receiver.minPressure)
            var maxP = Number(receiver.maxPressure)
            if (Number.isFinite(minP) && Number.isFinite(maxP) && maxP > minP) {
                minPressure = minP
                maxPressure = maxP
            }
            telemetryApplied = true
            var thresholds = receiver.thresholds || receiver.pressureThresholds || receiver.gradientStops
            if (Array.isArray(thresholds) && thresholds.length) {
                var resolvedStops = []
                for (var j = 0; j < thresholds.length; ++j) {
                    var thresholdEntry = thresholds[j] || {}
                    var thresholdValue = thresholdEntry.value !== undefined ? thresholdEntry.value : thresholdEntry.position || thresholdEntry.level
                    var numericValue = Number(thresholdValue)
                    if (!Number.isFinite(numericValue))
                        continue
                    resolvedStops.push({
                        value: numericValue,
                        color: thresholdEntry.color !== undefined ? thresholdEntry.color : Qt.rgba(0.25 + 0.12 * j, 0.55, 0.92, 0.7),
                        label: thresholdEntry.label !== undefined ? thresholdEntry.label : String(thresholdEntry.name || (qsTr("Порог") + " " + (j + 1)))
                    })
                }
                if (resolvedStops.length >= 2) {
                    _hasTelemetryGradient = true
                    pressureGradientStops = resolvedStops
                }
            }
        }
        var tank = source.tank
        if (_isPlainObject(tank)) {
            var directPressure = Number(tank.pressure)
            if (Number.isFinite(directPressure)) {
                reservoirPressure = directPressure
                pressure = directPressure
            }
            telemetryApplied = true
        }
        if (telemetryApplied) {
            _telemetryEffectiveMinimum = minPressure
            _telemetryEffectiveMaximum = maxPressure
        } else {
            _telemetryEffectiveMinimum = NaN
            _telemetryEffectiveMaximum = NaN
            _updatePressureBindings()
        }
    }

    function applyFlowTelemetry(payload) {
        var normalized = _normalizeFlowPayload(payload)
        flowTelemetry = _cloneObject(normalized)
        masterIsolationValveOpen = !!((normalized && normalized.masterIsolationOpen !== undefined)
            ? normalized.masterIsolationOpen
            : normalized && normalized.master_isolation_open)
    }


    function _isPlainObject(value) {
        return value && typeof value === "object" && !Array.isArray(value)
    }

    function _lookupMapValue(map, key) {
        if (!_isPlainObject(map))
            return undefined
        var variants = []
        var base = String(key || "")
        if (base.length)
            variants.push(base)
        var lower = base.toLowerCase()
        if (lower.length && variants.indexOf(lower) === -1)
            variants.push(lower)
        var upper = base.toUpperCase()
        if (upper.length && variants.indexOf(upper) === -1)
            variants.push(upper)
        for (var i = 0; i < variants.length; ++i) {
            var candidate = variants[i]
            if (Object.prototype.hasOwnProperty.call(map, candidate))
                return map[candidate]
        }
        return undefined
    }

    function _cloneObject(value) {
        if (value === undefined || value === null)
            return ({})
        try {
            return JSON.parse(JSON.stringify(value))
        } catch (error) {
            console.debug("SimulationPanel: failed to clone context", error)
            var result = {}
            for (var key in value) {
                if (root.objectHasOwn.call(value, key))
                    result[key] = value[key]
            }
            return result
        }
    }

    function _mergeObjects(base, payload) {
        var result = _cloneObject(base)
        if (_isPlainObject(payload)) {
            for (var key in payload) {
                if (!root.objectHasOwn.call(payload, key))
                    continue
                var value = payload[key]
                if (_isPlainObject(value))
                    result[key] = _mergeObjects(result[key], value)
                else
                    result[key] = value
            }
        }
        return result
    }

    function _normaliseKeyList(names) {
        var list = []
        function add(name) {
            if (name && list.indexOf(name) === -1)
                list.push(name)
        }
        function pushVariants(raw) {
            if (raw === undefined || raw === null)
                return
            var text = String(raw)
            if (!text.length)
                return
            add(text)
            add(text.toLowerCase())
            add(text.replace(/([A-Z])/g, function(match) { return "_" + match.toLowerCase() }))
            add(text.replace(/_([a-zA-Z0-9])/g, function(_, chr) { return chr.toUpperCase() }))
        }
        if (Array.isArray(names)) {
            for (var i = 0; i < names.length; ++i)
                pushVariants(names[i])
        } else {
            pushVariants(names)
        }
        return list
    }

    function _resolveMapEntry(source, nameOptions) {
        if (!_isPlainObject(source))
            return undefined
        var names = _normaliseKeyList(nameOptions)
        for (var i = 0; i < names.length; ++i) {
            var candidateName = names[i]
            if (candidateName && root.objectHasOwn.call(source, candidateName))
                return source[candidateName]
        }
        return undefined
    }

    function _valueFromSubsection(sources, sectionNames, keyNames) {
        var sectionList = []
        if (Array.isArray(sectionNames))
            sectionList = sectionNames
        else if (sectionNames !== undefined && sectionNames !== null)
            sectionList = [sectionNames]
        var keys = _normaliseKeyList(keyNames)
        for (var i = 0; i < sources.length; ++i) {
            var current = sources[i]
            var valid = true
            for (var j = 0; j < sectionList.length; ++j) {
                current = _resolveMapEntry(current, sectionList[j])
                if (!_isPlainObject(current)) {
                    valid = false
                    break
                }
            }
            if (!valid)
                continue
            for (var k = 0; k < keys.length; ++k) {
                var candidate = current[keys[k]]
                if (candidate !== undefined)
                    return candidate
            }
        }
        return undefined
    }

    function _valueFromSources(sources, keyNames) {
        return _valueFromSubsection(sources, [], keyNames)
    }

    function _pneumaticSources() {
        return [_pneumaticState || ({}), _pneumaticDefaults || ({})]
    }

    function _simulationSources() {
        return [_simulationState || ({}), _simulationDefaults || ({})]
    }

    function _sceneSources() {
        return [_sceneState || ({}), _sceneDefaults || ({})]
    }

    function _sceneEnvironmentSources() {
        var sources = []
        var baseSources = _sceneSources()
        for (var i = 0; i < baseSources.length; ++i) {
            var base = baseSources[i]
            var direct = _resolveMapEntry(base, "environment")
            if (_isPlainObject(direct))
                sources.push(direct)
            var graphics = _resolveMapEntry(base, "graphics")
            if (_isPlainObject(graphics)) {
                var nested = _resolveMapEntry(graphics, "environment")
                if (_isPlainObject(nested))
                    sources.push(nested)
            }
        }
        return sources
    }

    function _coerceNumber(value, fallback) {
        var numeric = Number(value)
        return Number.isFinite(numeric) ? numeric : fallback
    }

    function _numberFromSources(sourceAccessor, section, fallback) {
        var sections = []
        var keys
        if (Array.isArray(section) && Array.isArray(section[0])) {
            sections = section[0]
            keys = section[1]
        } else {
            keys = section
        }
        var sources = sourceAccessor()
        var value = sections.length ? _valueFromSubsection(sources, sections, keys) : _valueFromSources(sources, keys)
        return _coerceNumber(value, fallback)
    }

    function _pneumaticNumber(section, fallback) {
        return _numberFromSources(_pneumaticSources, section, fallback)
    }

    function _simulationNumber(section, fallback) {
        return _numberFromSources(_simulationSources, section, fallback)
    }

    function _sceneEnvironmentNumber(section, fallback) {
        return _numberFromSources(_sceneEnvironmentSources, section, fallback)
    }

    function _applySettingsPayload(payload) {
        if (!payload || typeof payload !== "object")
            return

        var pneumoUpdate = _extractCategory(payload, ["pneumatic", "pneumo"])
        var hasPneumoUpdate = _isPlainObject(pneumoUpdate)
        if (hasPneumoUpdate)
            _pneumaticState = _mergeObjects(_pneumaticState, pneumoUpdate)

        var simulationUpdate = _extractCategory(payload, ["simulation", "sim"], ["gas", "receiver"])
        if (_isPlainObject(simulationUpdate))
            _simulationState = _mergeObjects(_simulationState, simulationUpdate)

        var modesUpdate = _extractCategory(payload, ["modes"], ["physics"])
        if (_isPlainObject(modesUpdate)) {
            _modesState = _mergeObjects(_modesState, modesUpdate)
            if (modesUpdate.mode_preset !== undefined)
                _activePresetId = String(modesUpdate.mode_preset)
            _updateModesBindings()
        }

        var animationUpdate = _extractCategory(payload, ["animation"]) || _resolveMapEntry(payload, "animation")
        if (_isPlainObject(animationUpdate)) {
            _animationState = _mergeObjects(_animationState, animationUpdate)
            _updateAnimationBindings()
        }

        var sceneUpdate = _extractSceneCategory(payload)
        if (_isPlainObject(sceneUpdate))
            _sceneState = _mergeObjects(_sceneState, sceneUpdate)

        if (hasPneumoUpdate)
            _updateAnimationBindings()
        _updatePressureBindings()
    }

    function _extractSceneCategory(payload) {
        if (_isPlainObject(payload.environment))
            return { environment: payload.environment }
        if (_isPlainObject(payload.scene))
            return payload.scene
        if (_isPlainObject(payload.graphics) && _isPlainObject(payload.graphics.environment))
            return { environment: payload.graphics.environment }
        if (_isPlainObject(payload.current) && _isPlainObject(payload.current.scene))
            return payload.current.scene
        if (typeof payload.category === "string") {
            var cat = payload.category.toLowerCase()
            if ((cat === "environment" || cat === "scene") && _isPlainObject(payload.newValue))
                return payload.newValue
        }
        return null
    }

    function _extractCategory(payload, names, nestedKeys) {
        for (var i = 0; i < names.length; ++i) {
            var name = names[i]
            if (_isPlainObject(payload[name]))
                return payload[name]
        }
        if (_isPlainObject(payload.current)) {
            for (var j = 0; j < names.length; ++j) {
                var currentName = names[j]
                if (_isPlainObject(payload.current[currentName]))
                    return payload.current[currentName]
            }
        }
        if (typeof payload.category === "string" && _isPlainObject(payload.newValue)) {
            var category = payload.category.toLowerCase()
            for (var k = 0; k < names.length; ++k) {
                if (category === names[k].toLowerCase())
                    return payload.newValue
            }
        }
        if (nestedKeys && _isPlainObject(payload)) {
            for (var n = 0; n < nestedKeys.length; ++n) {
                var nested = nestedKeys[n]
                if (_isPlainObject(payload[nested]))
                    return payload[nested]
            }
        }
        return null
    }

    ColumnLayout {
        id: layout
        anchors.fill: parent
        spacing: 12

        Text {
            id: titleLabel
            text: root.title
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 18
            color: "#f1f3f7"
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            PressureScale {
                id: scale
                objectName: "pressureScale"
                Layout.preferredWidth: 120
                Layout.fillHeight: true
                minPressure: root.minPressure
                maxPressure: root.maxPressure
                userMinPressure: root.userMinPressure
                userMaxPressure: root.userMaxPressure
                atmosphericPressure: root.atmosphericPressure
                pressure: root.pressure
                tickCount: 6
                markers: root.pressureMarkers
                gradientStops: root.pressureGradientStops
            }

            Reservoir {
                id: reservoirView
                objectName: "reservoirView"
                Layout.fillWidth: true
                Layout.fillHeight: true
                minPressure: root.minPressure
                maxPressure: root.maxPressure
                userMinPressure: root.userMinPressure
                userMaxPressure: root.userMaxPressure
                atmosphericPressure: root.atmosphericPressure
                pressure: root.reservoirPressure
                markers: root.pressureMarkers
                gradientStops: root.pressureGradientStops
                linePressures: root.linePressureMap
                lineValveStates: root.lineValveStateMap
                lineIntensities: root.lineIntensityMap
            }

            ColumnLayout {
                id: flowColumn
                Layout.preferredWidth: 240
                Layout.fillHeight: true
                spacing: 8

                Rectangle {
                    id: flowCard
                    Layout.fillWidth: true
                    Layout.preferredHeight: 200
                    radius: 12
                    color: Qt.rgba(0.08, 0.12, 0.18, 0.92)
                    border.width: 1
                    border.color: Qt.rgba(0.22, 0.29, 0.4, 0.9)

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 6

                        Label {
                            text: qsTr("Потоки линий")
                            font.pixelSize: 15
                            font.bold: true
                            color: "#dfe6f4"
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 4

                            Repeater {
                                model: flowModel
                                  delegate: Components.FlowArrow {
                                      required property var modelData

                                      Layout.fillWidth: true
                                      Component.onCompleted: {
                                          objectName = "flowArrow-" + (modelData.label || index)
                                      }
                                      label: modelData.label
                                    direction: modelData.direction
                                    flowValue: modelData.flow
                                    intensity: modelData.intensity
                                    animationSpeed: modelData.animationSpeed
                                    minPressure: root.minPressure
                                    maxPressure: root.maxPressure
                                    linePressure: modelData.pressure
                                    referencePressure: root.reservoirPressure
                                    pressureRatio: modelData.pressureRatio
                                }
                            }

                            Label {
                                visible: flowModel.count === 0
                                text: qsTr("Нет активных потоков")
                                color: "#95a1b5"
                                font.pixelSize: 12
                            }
                        }
                    }
                }

                Rectangle {
                    id: valvesCard
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 12
                    color: Qt.rgba(0.08, 0.12, 0.18, 0.92)
                    border.width: 1
                    border.color: Qt.rgba(0.22, 0.29, 0.4, 0.9)

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 6

                        Label {
                            text: qsTr("Состояние клапанов")
                            font.pixelSize: 15
                            font.bold: true
                            color: "#dfe6f4"
                        }

                        Components.ValveIndicator {
                            id: masterIsolationIndicator
                            Layout.fillWidth: true
                            label: qsTr("Главный отсечной")
                            open: root.masterIsolationValveOpen
                            direction: root.masterIsolationValveOpen ? "intake" : "exhaust"
                            flowValue: 0.0
                            hint: qsTr("Изоляция резервуара")
                        }

                        Repeater {
                            model: lineValveListModel
                            delegate: Components.ValveIndicator {
                                required property var modelData

                                Layout.fillWidth: true
                                label: modelData.label
                                open: !!modelData.open
                                direction: modelData.direction
                                flowValue: modelData.flowValue
                                hint: modelData.hint
                            }
                        }

                        Repeater {
                            model: reliefValveListModel
                            delegate: Components.ValveIndicator {
                                required property var modelData

                                Layout.fillWidth: true
                                label: modelData.label
                                open: !!modelData.open
                                direction: modelData.direction
                                flowValue: modelData.flowValue
                                hint: modelData.hint
                            }
                        }
                    }
                }
            }
        }

        Text {
            id: rangeLabel
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            color: "#cdd6e5"
            text: {
                if (!root.hasValidRange)
                    return qsTr("Недостаточно данных для нормализации")
                var locale = Qt.locale()
                var minText = locale.toString(Number(root.effectiveMinimum), "f", 0)
                var maxText = locale.toString(Number(root.effectiveMaximum), "f", 0)
                return qsTr("Диапазон: %1 – %2 Па").arg(minText).arg(maxText)
            }
        }

        Rectangle {
            id: modesCard
            Layout.fillWidth: true
            radius: 12
            color: Qt.rgba(0.08, 0.12, 0.18, 0.92)
            border.width: 1
            border.color: Qt.rgba(0.22, 0.29, 0.4, 0.9)

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Label {
                    text: qsTr("Режимы симуляции")
                    font.pixelSize: 16
                    font.bold: true
                    color: "#e2e8f5"
                }

                ComboBox {
                    id: presetCombo
                    Layout.fillWidth: true
                    model: presetModel
                    textRole: "label"
                    valueRole: "id"
                    displayText: currentIndex >= 0 && currentIndex < presetModel.count
                        ? presetModel.get(currentIndex).label
                        : qsTr("Пресет")
                    onActivated: function(index) {
                        if (index >= 0 && index < presetModel.count) {
                            var entry = presetModel.get(index)
                            root._activePresetId = entry.id
                            root._modesState = root._mergeObjects(root._modesState, { mode_preset: entry.id })
                            root.modesPresetSelected(entry.id)
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    ComboBox {
                        id: simTypeCombo
                        Layout.fillWidth: true
                        model: root._simTypeOptions
                        textRole: "label"
                        onActivated: function(index) {
                            if (index >= 0 && index < root._simTypeOptions.length) {
                                var selected = root._simTypeOptions[index].value
                                root._modesState = root._mergeObjects(root._modesState, { sim_type: selected })
                                root.modesModeChanged("sim_type", selected)
                            }
                        }
                    }

                    ComboBox {
                        id: thermoModeCombo
                        Layout.fillWidth: true
                        model: root._thermoModeOptions
                        textRole: "label"
                        onActivated: function(index) {
                            if (index >= 0 && index < root._thermoModeOptions.length) {
                                var thermoSelected = root._thermoModeOptions[index].value
                                root._modesState = root._mergeObjects(root._modesState, { thermo_mode: thermoSelected })
                                root.modesModeChanged("thermo_mode", thermoSelected)
                            }
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    ComboBox {
                        id: roadProfileCombo
                        objectName: "roadProfileCombo"
                        Layout.fillWidth: true
                        model: root._roadProfileOptions
                        textRole: "label"
                        valueRole: "value"
                        onActivated: function(index) {
                            if (index >= 0 && index < root._roadProfileOptions.length) {
                                var selectedProfile = root._roadProfileOptions[index].value
                                root._emitRoadProfileChange(selectedProfile)
                            }
                        }
                        onCurrentValueChanged: function(value) {
                            if (value === undefined || value === null)
                                return
                            var normalized = String(value).toLowerCase()
                            customProfileField.enabled = normalized === "custom"
                        }
                    }

                    TextField {
                        id: customProfileField
                        objectName: "customProfileField"
                        Layout.fillWidth: true
                        placeholderText: qsTr("Путь к профилю дороги…")
                        inputMethodHints: Qt.ImhPreferLowercase | Qt.ImhNoAutoUppercase
                        onEditingFinished: function() { root._emitCustomProfileChange(text) }
                    }

                    Switch {
                        id: interferenceSwitch
                        text: qsTr("Проверять пересечения")
                        onToggled: function() { root._emitInterferenceChange(interferenceSwitch.checked) }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Switch {
                        id: springsSwitch
                        text: qsTr("Пружины")
                        onToggled: function() { root._emitPhysicsPayload() }
                    }

                    Switch {
                        id: dampersSwitch
                        text: qsTr("Демпферы")
                        onToggled: function() { root._emitPhysicsPayload() }
                    }

                    Switch {
                        id: pneumaticsSwitch
                        text: qsTr("Пневматика")
                        onToggled: function() { root._emitPhysicsPayload() }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Switch {
                        id: kinematicSpringsSwitch
                        text: qsTr("Пружины в кинематике")
                        onToggled: function() { root._emitPhysicsPayload() }
                    }

                    Switch {
                        id: kinematicDampersSwitch
                        text: qsTr("Демпферы в кинематике")
                        onToggled: function() { root._emitPhysicsPayload() }
                    }
                }
            }
        }

        Rectangle {
            id: animationCard
            Layout.fillWidth: true
            radius: 12
            color: Qt.rgba(0.08, 0.12, 0.18, 0.92)
            border.width: 1
            border.color: Qt.rgba(0.22, 0.29, 0.4, 0.9)

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Label {
                    text: qsTr("Профили дороги и сглаживание")
                    font.pixelSize: 16
                    font.bold: true
                    color: "#e2e8f5"
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    TextField {
                        id: amplitudeField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Амплитуда, м")
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        validator: DoubleValidator {
                            bottom: Number(root._parameterRange("amplitude").min || 0.0)
                            top: Number(root._parameterRange("amplitude").max || 1.0)
                            decimals: 3
                        }
                        onEditingFinished: function() { root._emitAnimationNumericChange("amplitude", text) }
                    }

                    TextField {
                        id: frequencyField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Частота, Гц")
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        validator: DoubleValidator {
                            bottom: Number(root._parameterRange("frequency").min || 0.1)
                            top: Number(root._parameterRange("frequency").max || 10.0)
                            decimals: 2
                        }
                        onEditingFinished: function() { root._emitAnimationNumericChange("frequency", text) }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    TextField {
                        id: phaseField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Фаза, °")
                        inputMethodHints: Qt.ImhDigitsOnly
                        validator: DoubleValidator {
                            bottom: Number(root._parameterRange("phase").min || 0.0)
                            top: Number(root._parameterRange("phase").max || 360.0)
                            decimals: 1
                        }
                        onEditingFinished: function() { root._emitAnimationNumericChange("phase", text) }
                    }

                    Switch {
                        id: smoothingSwitch
                        text: qsTr("Сглаживание")
                        onToggled: function() { root._emitAnimationToggle("smoothing_enabled", smoothingSwitch.checked) }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    TextField {
                        id: smoothingDurationField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Время, мс")
                        inputMethodHints: Qt.ImhDigitsOnly
                        validator: DoubleValidator {
                            bottom: Number(root._parameterRange("smoothing_duration_ms").min || 0.0)
                            top: Number(root._parameterRange("smoothing_duration_ms").max || 600.0)
                            decimals: 0
                        }
                        onEditingFinished: function() { root._emitAnimationNumericChange("smoothing_duration_ms", text) }
                    }

                    TextField {
                        id: smoothingAngleField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Угол, °")
                        inputMethodHints: Qt.ImhDigitsOnly
                        validator: DoubleValidator {
                            bottom: Number(root._parameterRange("smoothing_angle_snap_deg").min || 0.0)
                            top: Number(root._parameterRange("smoothing_angle_snap_deg").max || 180.0)
                            decimals: 0
                        }
                        onEditingFinished: function() { root._emitAnimationNumericChange("smoothing_angle_snap_deg", text) }
                    }

                    TextField {
                        id: smoothingPistonField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Поршень, м")
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        validator: DoubleValidator {
                            bottom: Number(root._parameterRange("smoothing_piston_snap_m").min || 0.0)
                            top: Number(root._parameterRange("smoothing_piston_snap_m").max || 0.3)
                            decimals: 3
                        }
                        onEditingFinished: function() { root._emitAnimationNumericChange("smoothing_piston_snap_m", text) }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label {
                        text: qsTr("Температура резервуара, K")
                        color: "#cdd6e5"
                        Layout.alignment: Qt.AlignVCenter
                    }

                    TextField {
                        id: temperatureField
                        objectName: "temperatureField"
                        Layout.fillWidth: true
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        validator: DoubleValidator {
                            bottom: 200.0
                            top: 450.0
                            decimals: 1
                        }
                        onEditingFinished: function() { root._emitTemperatureChange(text) }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label {
                        text: qsTr("Температура среды, °C")
                        color: "#cdd6e5"
                        Layout.alignment: Qt.AlignVCenter
                    }

                    TextField {
                        id: ambientTemperatureField
                        objectName: "ambientTemperatureField"
                        Layout.fillWidth: true
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        validator: DoubleValidator {
                            bottom: -80.0
                            top: 150.0
                            decimals: 1
                        }
                        onEditingFinished: function() { root._emitAmbientTemperatureChange(text) }
                    }
                }
            }
        }
    }

    onFlowTelemetryChanged: {
        var normalized = _normalizeFlowPayload(flowTelemetry)
        masterIsolationValveOpen = !!((normalized && normalized.masterIsolationOpen !== undefined)
            ? normalized.masterIsolationOpen
            : normalized && normalized.master_isolation_open)
        _applyFlowTelemetryState(normalized)
        _rebuildFlowModels(normalized)
    }

    onPressureChanged: pressureChangedExternally(pressure)

    Connections {
        target: root.settingsEventBus
        enabled: !!target

        function onSettingsBatchUpdated(payload) {
            root._applySettingsPayload(payload)
        }

        function onSettingChanged(payload) {
            root._applySettingsPayload(payload)
        }
    }
}
