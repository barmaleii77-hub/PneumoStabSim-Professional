import QtQuick 6.10
import QtQuick3D 6.10

Node {
    id: root

    property var flowData: ({})
    property var geometryHelper: null
    property real sceneScale: 1.0

    property color intakeColor: "#3fc1ff"
    property color exhaustColor: "#ff6b6b"
    property color inactiveColor: "#3b4252"
    property color reliefColor: "#ffd166"
    property color masterIsolationColor: "#9b5de5"

    property real arrowElevationM: 0.18
    property real bodyLengthM: 0.18
    property real headLengthM: 0.1
    property real arrowRadiusM: 0.045
    property real travelDistanceM: 0.24
    property real defaultMaxLineFlow: 0.05
    property real defaultMaxReliefFlow: 0.08

    property var lineKeys: ["a1", "b1", "a2", "b2"]
    property var sideMap: ({ a1: "fl", b1: "fr", a2: "rl", b2: "rr" })
    property var reliefOffsets: ({
        min: Qt.vector3d(-0.28, 0.14, -0.04),
        stiff: Qt.vector3d(0, 0.18, 0),
        safety: Qt.vector3d(0.28, 0.14, 0.04)
    })
    property vector3d masterOffset: Qt.vector3d(0, 0.28, 0)

    property real lineFlowCeiling: _resolveLineCeiling()
    property real reliefFlowCeiling: _resolveReliefCeiling()
    property bool hasFlowData: !_isEmpty(asObject(flowData))

    visible: hasFlowData

    onFlowDataChanged: {
        lineFlowCeiling = _resolveLineCeiling()
        reliefFlowCeiling = _resolveReliefCeiling()
    }

    function asObject(value) {
        return value && typeof value === "object" ? value : null
    }

    function _isEmpty(value) {
        if (!value || typeof value !== "object")
            return true
        for (var key in value) {
            if (Object.prototype.hasOwnProperty.call(value, key))
                return false
        }
        return true
    }

    function _lines() {
        var data = asObject(flowData)
        if (!data)
            return {}
        if (data.lines && typeof data.lines === "object")
            return data.lines
        if (data.lineFlows && typeof data.lineFlows === "object")
            return data.lineFlows
        return {}
    }

    function _lineEntry(key) {
        var lines = _lines()
        var entry = lines[key]
        return entry && typeof entry === "object" ? entry : {}
    }

    function _netFlow(key) {
        var entry = _lineEntry(key)
        var flows = entry.flows && typeof entry.flows === "object" ? entry.flows : {}
        if (flows.net !== undefined)
            return Number(flows.net)
        var fromValue = flows.fromAtmosphere !== undefined ? Number(flows.fromAtmosphere) : Number(entry.flowFromAtmosphere)
        var toValue = flows.toTank !== undefined ? Number(flows.toTank) : Number(entry.flowToTank)
        var net = fromValue - toValue
        if (!isNaN(net))
            return net
        if (entry.netFlow !== undefined)
            return Number(entry.netFlow)
        return 0.0
    }

    function _lineIntensity(key) {
        var entry = _lineEntry(key)
        if (entry.intensity !== undefined) {
            var value = Number(entry.intensity)
            if (isFinite(value))
                return Math.abs(value)
        }
        return Math.abs(Number(_netFlow(key)))
    }

    function _lineDirection(key) {
        var entry = _lineEntry(key)
        if (typeof entry.direction === "string")
            return entry.direction
        var net = Number(_netFlow(key))
        return net >= 0 ? "intake" : "exhaust"
    }

    function _lineSpeedHint(key) {
        var entry = _lineEntry(key)
        if (entry.animationSpeed !== undefined) {
            var speed = Number(entry.animationSpeed)
            if (isFinite(speed))
                return Math.max(0.0, Math.min(1.0, speed))
        }
        var ceiling = lineFlowCeiling
        if (!(ceiling > 0))
            return 0.0
        return Math.min(_lineIntensity(key) / ceiling, 1.0)
    }

    function _lineIntensityRatio(key) {
        var ceiling = lineFlowCeiling
        if (!(ceiling > 0))
            return 0.0
        return Math.min(Math.max(Math.abs(Number(_lineIntensity(key))) / ceiling, 0.0), 1.0)
    }

    function _blendColors(baseColor, overlayColor, factor) {
        factor = Math.max(0.0, Math.min(1.0, Number(factor)))
        var base = Qt.rgba(baseColor.r, baseColor.g, baseColor.b, 1)
        var overlay = Qt.rgba(overlayColor.r, overlayColor.g, overlayColor.b, 1)
        return Qt.rgba(
            base.r + (overlay.r - base.r) * factor,
            base.g + (overlay.g - base.g) * factor,
            base.b + (overlay.b - base.b) * factor,
            1
        )
    }

    function _lineIntakeColor(key) {
        var entry = _lineEntry(key)
        if (entry && entry.colors && typeof entry.colors === "object" && entry.colors.intake)
            return entry.colors.intake
        var ratio = _lineIntensityRatio(key)
        return _blendColors(intakeColor, Qt.rgba(1, 1, 1, 1), ratio * 0.35)
    }

    function _lineExhaustColor(key) {
        var entry = _lineEntry(key)
        if (entry && entry.colors && typeof entry.colors === "object" && entry.colors.exhaust)
            return entry.colors.exhaust
        var ratio = _lineIntensityRatio(key)
        return _blendColors(exhaustColor, Qt.rgba(1.0, 0.55, 0.2, 1), ratio * 0.25)
    }

    function _lineValveOpen(key) {
        var entry = _lineEntry(key)
        var valves = entry.valves && typeof entry.valves === "object" ? entry.valves : {}
        if (valves.atmosphereOpen !== undefined || valves.tankOpen !== undefined)
            return Boolean(valves.atmosphereOpen) || Boolean(valves.tankOpen)
        if (entry.valveOpen !== undefined)
            return Boolean(entry.valveOpen)
        return Math.abs(_netFlow(key)) > 0.0
    }

    function _lineAnchor(key) {
        var side = sideMap[key]
        var helper = geometryHelper
        if (!side || !helper)
            return Qt.vector3d(0, 0, 0)
        var base = null
        if (typeof helper.armPosition === "function")
            base = helper.armPosition(side)
        else if (typeof helper.cornerArmPosition === "function")
            base = helper.cornerArmPosition(side)
        if (!base)
            return Qt.vector3d(0, 0, 0)
        var x = Number(base.x) * sceneScale
        var y = (Number(base.y) + arrowElevationM) * sceneScale
        var z = Number(base.z) * sceneScale
        return Qt.vector3d(x, y, z)
    }

    function _tankAnchor() {
        var helper = geometryHelper
        var geometryValue = helper && typeof helper.geometryValue === "function" ? helper.geometryValue : null
        var beam = geometryValue ? Number(geometryValue("beamSize")) : 0.0
        var frameHeight = geometryValue ? Number(geometryValue("frameHeight")) : 0.0
        var zOffset = geometryValue ? Number(geometryValue("frameToPivot")) : 0.0
        var x = 0.0
        var y = (beam + frameHeight * 0.5) * sceneScale
        var z = zOffset * sceneScale
        return Qt.vector3d(x, y, z)
    }

    function _orientationForLine(key) {
        var anchor = _lineAnchor(key)
        var tank = _tankAnchor()
        var dx = tank.x - anchor.x
        var dz = tank.z - anchor.z
        if (dx === 0 && dz === 0)
            return Qt.vector3d(0, 0, 0)
        var yaw = Math.atan2(dx, dz) * 180 / Math.PI
        return Qt.vector3d(0, yaw, 0)
    }

    function _lineMaxFlow() {
        var lines = _lines()
        var maxMagnitude = 0.0
        for (var i = 0; i < lineKeys.length; ++i) {
            var key = lineKeys[i]
            if (!Object.prototype.hasOwnProperty.call(lines, key))
                continue
            var net = Math.abs(Number(_netFlow(key)))
            if (isFinite(net))
                maxMagnitude = Math.max(maxMagnitude, net)
        }
        return Math.max(maxMagnitude, defaultMaxLineFlow)
    }

    function _reliefSection() {
        var data = asObject(flowData)
        if (data && data.relief && typeof data.relief === "object")
            return data.relief
        if (data && data.valves && typeof data.valves === "object" && data.valves.relief)
            return data.valves.relief
        return {}
    }

    function _reliefEntry(key) {
        var relief = _reliefSection()
        var entry = relief[key]
        return entry && typeof entry === "object" ? entry : {}
    }

    function _reliefOpen(key) {
        var entry = _reliefEntry(key)
        if (entry.open !== undefined)
            return Boolean(entry.open)
        return Math.abs(Number(entry.flow)) > 0.0
    }

    function _reliefIntensity(key) {
        var entry = _reliefEntry(key)
        var flowValue = entry.intensity !== undefined ? Number(entry.intensity) : Number(entry.flow)
        flowValue = Math.abs(isFinite(flowValue) ? flowValue : 0.0)
        var ceiling = reliefFlowCeiling
        if (!(ceiling > 0))
            return flowValue > 0 ? 1.0 : 0.0
        return Math.min(flowValue / ceiling, 1.0)
    }

    function _reliefDirection(key) {
        var entry = _reliefEntry(key)
        if (typeof entry.direction === "string")
            return entry.direction
        return "exhaust"
    }

    function _reliefMaxFlow() {
        var relief = _reliefSection()
        var maxMagnitude = 0.0
        for (var key in relief) {
            if (!Object.prototype.hasOwnProperty.call(relief, key))
                continue
            var entry = relief[key]
            if (!entry || typeof entry !== "object")
                continue
            var flowValue = entry.intensity !== undefined ? Number(entry.intensity) : Number(entry.flow)
            flowValue = Math.abs(isFinite(flowValue) ? flowValue : 0.0)
            maxMagnitude = Math.max(maxMagnitude, flowValue)
        }
        return Math.max(maxMagnitude, defaultMaxReliefFlow)
    }

    function _resolveLineCeiling() {
        var data = asObject(flowData)
        if (data && data.maxLineIntensity !== undefined) {
            var value = Number(data.maxLineIntensity)
            if (isFinite(value) && value > 0)
                return value
        }
        return _lineMaxFlow()
    }

    function _resolveReliefCeiling() {
        var data = asObject(flowData)
        if (data && data.maxReliefIntensity !== undefined) {
            var value = Number(data.maxReliefIntensity)
            if (isFinite(value) && value > 0)
                return value
        }
        return _reliefMaxFlow()
    }

    function _reliefPosition(key) {
        var offsets = reliefOffsets[key]
        var tank = _tankAnchor()
        if (!offsets)
            offsets = Qt.vector3d(0, 0.12, 0)
        return Qt.vector3d(
            tank.x + offsets.x * sceneScale,
            tank.y + offsets.y * sceneScale,
            tank.z + offsets.z * sceneScale
        )
    }

    function _masterOpen() {
        var data = asObject(flowData)
        if (!data)
            return false
        if (data.masterIsolationOpen !== undefined)
            return Boolean(data.masterIsolationOpen)
        if (data.valves && typeof data.valves === "object" && data.valves.masterIsolationOpen !== undefined)
            return Boolean(data.valves.masterIsolationOpen)
        return false
    }

    function _masterPosition() {
        var tank = _tankAnchor()
        return Qt.vector3d(
            tank.x + masterOffset.x * sceneScale,
            tank.y + masterOffset.y * sceneScale,
            tank.z + masterOffset.z * sceneScale
        )
    }

    FlowArrow {
        id: arrowA1
        objectName: "arrowA1"
        position: root._lineAnchor("a1")
        sceneScale: root.sceneScale
        bodyLengthM: root.bodyLengthM
        headLengthM: root.headLengthM
        radiusM: root.arrowRadiusM
        travelDistanceM: root.travelDistanceM
        flowValue: root._netFlow("a1")
        flowIntensity: root._lineIntensity("a1")
        maxFlow: root.lineFlowCeiling
        maxIntensity: root.lineFlowCeiling
        flowDirection: root._lineDirection("a1")
        valveOpen: root._lineValveOpen("a1")
        orientationEuler: root._orientationForLine("a1")
        intakeColor: root._lineIntakeColor("a1")
        exhaustColor: root._lineExhaustColor("a1")
        inactiveColor: root.inactiveColor
        lineLabel: "A1"
        animationSpeedFactor: root._lineSpeedHint("a1")
    }

    FlowArrow {
        id: arrowB1
        objectName: "arrowB1"
        position: root._lineAnchor("b1")
        sceneScale: root.sceneScale
        bodyLengthM: root.bodyLengthM
        headLengthM: root.headLengthM
        radiusM: root.arrowRadiusM
        travelDistanceM: root.travelDistanceM
        flowValue: root._netFlow("b1")
        flowIntensity: root._lineIntensity("b1")
        maxFlow: root.lineFlowCeiling
        maxIntensity: root.lineFlowCeiling
        flowDirection: root._lineDirection("b1")
        valveOpen: root._lineValveOpen("b1")
        orientationEuler: root._orientationForLine("b1")
        intakeColor: root._lineIntakeColor("b1")
        exhaustColor: root._lineExhaustColor("b1")
        inactiveColor: root.inactiveColor
        lineLabel: "B1"
        animationSpeedFactor: root._lineSpeedHint("b1")
    }

    FlowArrow {
        id: arrowA2
        objectName: "arrowA2"
        position: root._lineAnchor("a2")
        sceneScale: root.sceneScale
        bodyLengthM: root.bodyLengthM
        headLengthM: root.headLengthM
        radiusM: root.arrowRadiusM
        travelDistanceM: root.travelDistanceM
        flowValue: root._netFlow("a2")
        flowIntensity: root._lineIntensity("a2")
        maxFlow: root.lineFlowCeiling
        maxIntensity: root.lineFlowCeiling
        flowDirection: root._lineDirection("a2")
        valveOpen: root._lineValveOpen("a2")
        orientationEuler: root._orientationForLine("a2")
        intakeColor: root._lineIntakeColor("a2")
        exhaustColor: root._lineExhaustColor("a2")
        inactiveColor: root.inactiveColor
        lineLabel: "A2"
        animationSpeedFactor: root._lineSpeedHint("a2")
    }

    FlowArrow {
        id: arrowB2
        objectName: "arrowB2"
        position: root._lineAnchor("b2")
        sceneScale: root.sceneScale
        bodyLengthM: root.bodyLengthM
        headLengthM: root.headLengthM
        radiusM: root.arrowRadiusM
        travelDistanceM: root.travelDistanceM
        flowValue: root._netFlow("b2")
        flowIntensity: root._lineIntensity("b2")
        maxFlow: root.lineFlowCeiling
        maxIntensity: root.lineFlowCeiling
        flowDirection: root._lineDirection("b2")
        valveOpen: root._lineValveOpen("b2")
        orientationEuler: root._orientationForLine("b2")
        intakeColor: root._lineIntakeColor("b2")
        exhaustColor: root._lineExhaustColor("b2")
        inactiveColor: root.inactiveColor
        lineLabel: "B2"
        animationSpeedFactor: root._lineSpeedHint("b2")
    }

    ValveIndicator {
        id: reliefMin
        objectName: "reliefMin"
        position: root._reliefPosition("min")
        sceneScale: root.sceneScale
        radiusM: 0.075
        columnHeightM: 0.22
        activeColor: root.reliefColor
        inactiveColor: root.inactiveColor
        active: root._reliefOpen("min")
        intensity: root._reliefIntensity("min")
        flowDirection: root._reliefDirection("min")
    }

    ValveIndicator {
        id: reliefStiff
        objectName: "reliefStiff"
        position: root._reliefPosition("stiff")
        sceneScale: root.sceneScale
        radiusM: 0.08
        columnHeightM: 0.24
        activeColor: root.reliefColor
        inactiveColor: root.inactiveColor
        active: root._reliefOpen("stiff")
        intensity: root._reliefIntensity("stiff")
        flowDirection: root._reliefDirection("stiff")
    }

    ValveIndicator {
        id: reliefSafety
        objectName: "reliefSafety"
        position: root._reliefPosition("safety")
        sceneScale: root.sceneScale
        radiusM: 0.085
        columnHeightM: 0.26
        activeColor: root.reliefColor
        inactiveColor: root.inactiveColor
        active: root._reliefOpen("safety")
        intensity: root._reliefIntensity("safety")
        flowDirection: root._reliefDirection("safety")
    }

    ValveIndicator {
        id: masterIsolation
        objectName: "masterIsolationValve"
        position: root._masterPosition()
        sceneScale: root.sceneScale
        radiusM: 0.065
        columnHeightM: 0.18
        activeColor: root.masterIsolationColor
        inactiveColor: root.inactiveColor
        active: root._masterOpen()
        intensity: root._masterOpen() ? 1.0 : 0.0
    }
}
