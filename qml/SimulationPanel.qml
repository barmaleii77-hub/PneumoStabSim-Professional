import QtQml 6.10
import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10

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

    // Кэшированные снимки настроек для синхронизации с SettingsManager.
    property var _pneumaticDefaults: ({})
    property var _pneumaticState: ({})
    property var _simulationDefaults: ({})
    property var _simulationState: ({})
    property var _sceneDefaults: ({})
    property var _sceneState: ({})

    readonly property real effectiveMinimum: _minValue(_rangeCandidates(), 0.0)
    readonly property real effectiveMaximum: _maxValue(_rangeCandidates(), 1.0)
    readonly property bool hasValidRange: effectiveMaximum > effectiveMinimum
    readonly property real normalizedPressure: hasValidRange ? _normalize(pressure) : 0.0

    signal pressureChangedExternally(real value)

    Component.onCompleted: {
        _refreshContextSnapshots()
        _updatePressureBindings()
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

    function _pneumaticNumber(section, fallback) {
        var sections = []
        var keys
        if (Array.isArray(section) && Array.isArray(section[0])) {
            sections = section[0]
            keys = section[1]
        } else {
            keys = section
        }
        var value = sections.length ? _valueFromSubsection(_pneumaticSources(), sections, keys) : _valueFromSources(_pneumaticSources(), keys)
        return _coerceNumber(value, fallback)
    }

    function _simulationNumber(section, fallback) {
        var sections = []
        var keys
        if (Array.isArray(section) && Array.isArray(section[0])) {
            sections = section[0]
            keys = section[1]
        } else {
            keys = section
        }
        var value = sections.length ? _valueFromSubsection(_simulationSources(), sections, keys) : _valueFromSources(_simulationSources(), keys)
        return _coerceNumber(value, fallback)
    }

    function _sceneEnvironmentNumber(section, fallback) {
        var sections = []
        var keys
        if (Array.isArray(section) && Array.isArray(section[0])) {
            sections = section[0]
            keys = section[1]
        } else {
            keys = section
        }
        var value = sections.length ? _valueFromSubsection(_sceneEnvironmentSources(), sections, keys) : _valueFromSources(_sceneEnvironmentSources(), keys)
        return _coerceNumber(value, fallback)
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
