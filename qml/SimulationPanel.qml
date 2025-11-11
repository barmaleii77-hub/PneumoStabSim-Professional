import QtQml 6.10
import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import "components" as Components

Item {
    id: root

    implicitWidth: layout.implicitWidth
    implicitHeight: layout.implicitHeight

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
    property var modesMetadata: typeof modesMetadata !== "undefined" ? modesMetadata : ({})

    /**
     * Центральная шина обновлений настроек. Экспортируется python UISetup через SettingsEventBus.
     */
    property var settingsEventBus: typeof settingsEvents !== "undefined" ? settingsEvents : null
    // qmllint enable unqualified

    property string title: qsTr("Резервуар давления")
    property real pressure: 0.0
    property real minPressure: 0.0
    property real maxPressure: 250000.0
    property real userMinPressure: minPressure
    property real userMaxPressure: maxPressure
    property real atmosphericPressure: 101325.0
    property real reservoirPressure: pressure
    property var pressureMarkers: []
    property var flowTelemetry: ({})
    property bool masterIsolationValveOpen: false
    readonly property var _simTypeOptions: [
        { value: "KINEMATICS", label: qsTr("Кинематика") },
        { value: "DYNAMICS", label: qsTr("Динамика") }
    ]
    readonly property var _thermoModeOptions: [
        { value: "ISOTHERMAL", label: qsTr("Изотермический") },
        { value: "ADIABATIC", label: qsTr("Адиабатический") }
    ]

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

    readonly property real effectiveMinimum: _minValue(_rangeCandidates(), 0.0)
    readonly property real effectiveMaximum: _maxValue(_rangeCandidates(), 1.0)
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
    ListModel { id: flowArrowsModel }
    ListModel { id: lineValveModel }
    ListModel { id: reliefValveModel }

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

    function _rangeCandidates() {
        var values = []
        function push(value) {
            var numeric = Number(value)
            if (Number.isFinite(numeric))
                values.push(numeric)
        }
        push(minPressure)
        push(maxPressure)
        push(userMinPressure)
        push(userMaxPressure)
        push(atmosphericPressure)
        push(reservoirPressure)
        if (values.length === 0) {
            values.push(0.0)
            values.push(1.0)
        } else if (values.length === 1) {
            values.push(values[0] + 1.0)
        }
        return values
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
        return numeric.toLocaleString(Qt.locale(), {
            maximumFractionDigits: fractionDigits,
            minimumFractionDigits: fractionDigits
        })
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
        if (springsSwitch)
            springsSwitch.checked = !!_modesValue(["physics", "include_springs"], true)
        if (dampersSwitch)
            dampersSwitch.checked = !!_modesValue(["physics", "include_dampers"], true)
        if (pneumaticsSwitch)
            pneumaticsSwitch.checked = !!_modesValue(["physics", "include_pneumatics"], true)
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
        var numeric = Number(rawValue)
        if (!Number.isFinite(numeric))
            return
        _pneumaticState = _mergeObjects(_pneumaticState, { gas: { tank_temperature_initial_k: numeric } })
        root.pneumaticSettingsChanged({ gas: { tank_temperature_initial_k: numeric } })
        _updateAnimationBindings()
    }

    function _emitPhysicsPayload() {
        var payload = {
            include_springs: springsSwitch ? !!springsSwitch.checked : true,
            include_dampers: dampersSwitch ? !!dampersSwitch.checked : true,
            include_pneumatics: pneumaticsSwitch ? !!pneumaticsSwitch.checked : true
        }
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

    function _rebuildFlowModels() {
        _clearModel(flowArrowsModel)
        _clearModel(lineValveModel)
        _clearModel(reliefValveModel)
        var payload = flowTelemetry || {}
        if (!_isPlainObject(payload))
            return
        _flowState = payload
        _applyFlowTelemetryState(payload)
        var linesNode = payload.lines || payload.Lines || {}
        var lineKeys = []
        if (_isPlainObject(linesNode))
            lineKeys = Object.keys(linesNode)
        lineKeys.sort()
        var maxIntensity = Number(payload.maxLineIntensity)
        if (!Number.isFinite(maxIntensity) || maxIntensity <= 0)
            maxIntensity = 0.0
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
            flowArrowsModel.append({
                label: label,
                direction: direction,
                flow: netNumeric,
                intensity: normalized
            })
            var valves = entry.valves || {}
            var flowAtmo = Number(flows.fromAtmosphere || flows.from_atmosphere || 0.0)
            if (!Number.isFinite(flowAtmo))
                flowAtmo = 0.0
            var flowTank = Number(flows.toTank || flows.to_tank || 0.0)
            if (!Number.isFinite(flowTank))
                flowTank = 0.0
            _appendValveEntry(lineValveModel, {
                label: label + " • " + qsTr("Атмосфера"),
                open: !!valves.atmosphereOpen,
                direction: "intake",
                flowValue: flowAtmo,
                hint: qsTr("Подача из внешней среды")
            })
            _appendValveEntry(lineValveModel, {
                label: label + " • " + qsTr("Танк"),
                open: !!valves.tankOpen,
                direction: "exhaust",
                flowValue: flowTank,
                hint: qsTr("Подача в резервуар")
            })
        }
        var relief = payload.relief || {}
        var reliefKeys = ["min", "stiff", "safety"]
        for (var r = 0; r < reliefKeys.length; ++r) {
            var reliefKey = reliefKeys[r]
            var reliefEntry = relief[reliefKey] || {}
            if (!_isPlainObject(reliefEntry))
                continue
            var flow = Number(reliefEntry.flow || 0.0)
            if (!Number.isFinite(flow))
                flow = 0.0
            _appendValveEntry(reliefValveModel, {
                label: qsTr("Клапан %1").arg(reliefKey.toUpperCase()),
                open: !!reliefEntry.open,
                direction: reliefEntry.direction || (flow >= 0 ? "exhaust" : "intake"),
                flowValue: flow,
                hint: qsTr("Резервуар → Атмосфера")
            })
        }
        masterIsolationValveOpen = !!payload.masterIsolationOpen
    }

    function _applyFlowTelemetryState(payload) {
        if (!_isPlainObject(payload))
            return
        var receiver = payload.receiver
        if (!_isPlainObject(receiver) && _isPlainObject(payload.flowNetwork))
            receiver = payload.flowNetwork.receiver
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
        }
        var tank = payload.tank
        if (_isPlainObject(tank)) {
            var directPressure = Number(tank.pressure)
            if (Number.isFinite(directPressure)) {
                reservoirPressure = directPressure
                pressure = directPressure
            }
        }
        _updatePressureBindings()
    }

    function applyFlowTelemetry(payload) {
        flowTelemetry = _cloneObject(payload || ({}))
    }


    function _isPlainObject(value) {
        return value && typeof value === "object" && !Array.isArray(value)
    }

    function _cloneObject(value) {
        if (!_isPlainObject(value))
            return ({})
        try {
            return JSON.parse(JSON.stringify(value))
        } catch (error) {
            console.debug("SimulationPanel: failed to clone context", error)
            var result = {}
            for (var key in value) {
                if (Object.prototype.hasOwnProperty.call(value, key))
                    result[key] = value[key]
            }
            return result
        }
    }

    function _mergeObjects(base, payload) {
        var result = _cloneObject(base)
        if (_isPlainObject(payload)) {
            for (var key in payload) {
                if (!Object.prototype.hasOwnProperty.call(payload, key))
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
            if (candidateName && Object.prototype.hasOwnProperty.call(source, candidateName))
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
        if (_isPlainObject(pneumoUpdate))
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

        Label {
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
            }

            Reservoir {
                id: reservoirView
                Layout.fillWidth: true
                Layout.fillHeight: true
                minPressure: root.minPressure
                maxPressure: root.maxPressure
                userMinPressure: root.userMinPressure
                userMaxPressure: root.userMaxPressure
                atmosphericPressure: root.atmosphericPressure
                pressure: root.reservoirPressure
                markers: root.pressureMarkers
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
                                model: flowArrowsModel
                                delegate: Components.FlowArrow {
                                    required property var modelData

                                    Layout.fillWidth: true
                                    label: modelData.label
                                    direction: modelData.direction
                                    flowValue: modelData.flow
                                    intensity: modelData.intensity
                                }
                            }

                            Label {
                                visible: flowArrowsModel.count === 0
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
                            model: lineValveModel
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
                            model: reliefValveModel
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

        Label {
            id: rangeLabel
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            color: "#cdd6e5"
            text: {
                if (!root.hasValidRange)
                    return qsTr("Недостаточно данных для нормализации")
                var locale = Qt.locale()
                var minText = Number(root.effectiveMinimum).toLocaleString(locale, { maximumFractionDigits: 0, minimumFractionDigits: 0 })
                var maxText = Number(root.effectiveMaximum).toLocaleString(locale, { maximumFractionDigits: 0, minimumFractionDigits: 0 })
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
            }
        }
    }

    onFlowTelemetryChanged: {
        _applyFlowTelemetryState(flowTelemetry)
        _rebuildFlowModels()
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
