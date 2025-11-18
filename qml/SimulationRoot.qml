#pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import "." as Local

/**
 * Минимальный корневой компонент для стенд‑запуска панели симуляции.
 * Повторяет публичную поверхность API SimulationRoot рабочего приложения,
 * чтобы qmllint/локальные инструменты не ругались на отсутствующие биндинги.
 */
Pane {
    id: root

    width: 960
    height: 640
    padding: 24

    /** Полный снимок телеметрии потоков от симулятора. */
    property var flowTelemetry: ({})

    /** Прокси к внутренним моделям, экспортируемые для автотестов. */
    property alias flowArrowsModel: simulationPanel.flowArrowsModel
    property alias lineValveModel: simulationPanel.lineValveModel
    property alias reliefValveModel: simulationPanel.reliefValveModel

    signal geometryUpdatesApplied(var payload)
    signal shaderWarningRegistered(string effectId, string message)
    signal shaderWarningCleared(string effectId)

    /** Снимок ключевых параметров геометрии, обновляемый из Python. */
    property real geometryWheelbase: NaN
    property real geometryTrack: NaN
    property real geometryLeverLength: NaN
    property real geometryCylinderStroke: NaN
    property real geometryPistonDiameter: NaN
    property real geometryRodDiameter: NaN

    /** Кэш активных предупреждений шейдеров (effectId -> message). */
    property var shaderWarningState: ({})

    function _normalizeEffectId(value) {
        var normalized = "unknown"
        if (value !== undefined && value !== null) {
            normalized = String(value)
            if (!normalized.length)
                normalized = "unknown"
        }
        return normalized
    }

    function _normalizeWarningMessage(value) {
        if (value === undefined || value === null)
            return ""
        return String(value)
    }

    function _cloneWarningState(source) {
        if (!source || typeof source !== "object")
            return ({})
        var clone = {}
        for (var key in source) {
            if (Object.prototype.hasOwnProperty.call(source, key))
                clone[key] = source[key]
        }
        return clone
    }

    function applyFlowTelemetry(payload) {
        flowTelemetry = payload
    }

    onFlowTelemetryChanged: simulationPanel.applyFlowTelemetry(flowTelemetry)

    function _hostWindow() {
        // qmllint disable unqualified
        try {
            if (typeof window !== "undefined" && window)
                return window
        } catch (error) {
        }
        // qmllint enable unqualified
        return null
    }

    function _normalizeGeometryPayload(params) {
        if (!params || typeof params !== "object")
            return ({})

        var normalized = {}
        for (var key in params) {
            if (Object.prototype.hasOwnProperty.call(params, key))
                normalized[key] = params[key]
        }
        return normalized
    }

    /**
     * Принимает обновления геометрии (имитация продакшн‑моста Python→QML).
     * В заглушке просто ретранслируем полезную нагрузку наружу.
     */
    function applyGeometryUpdates(params) {
        var normalized = _normalizeGeometryPayload(params)

        if (Object.prototype.hasOwnProperty.call(normalized, "wheelbase"))
            geometryWheelbase = Number(normalized.wheelbase)
        if (Object.prototype.hasOwnProperty.call(normalized, "track"))
            geometryTrack = Number(normalized.track)
        if (Object.prototype.hasOwnProperty.call(normalized, "lever_length"))
            geometryLeverLength = Number(normalized.lever_length)
        if (Object.prototype.hasOwnProperty.call(normalized, "stroke_m"))
            geometryCylinderStroke = Number(normalized.stroke_m)
        if (Object.prototype.hasOwnProperty.call(normalized, "cyl_diam_m"))
            geometryPistonDiameter = Number(normalized.cyl_diam_m)
        if (Object.prototype.hasOwnProperty.call(normalized, "rod_diameter_m"))
            geometryRodDiameter = Number(normalized.rod_diameter_m)

        geometryUpdatesApplied(normalized)
    }

    /**
     * Интерфейс для регистрации предупреждений шейдеров, совместимый со сценой.
     */
    function registerShaderWarning(effectId, message) {
        var normalizedId = _normalizeEffectId(effectId)
        var normalizedMessage = _normalizeWarningMessage(message)

        var previousState = shaderWarningState
        var nextState = _cloneWarningState(previousState)
        if (nextState[normalizedId] !== normalizedMessage)
            nextState[normalizedId] = normalizedMessage
        shaderWarningState = nextState

        shaderWarningRegistered(normalizedId, normalizedMessage)

        var hostWindow = _hostWindow()
        if (hostWindow && typeof hostWindow.registerShaderWarning === "function") {
            try {
                hostWindow.registerShaderWarning(normalizedId, normalizedMessage)
            } catch (error) {
                console.debug("SimulationRoot (stub): window.registerShaderWarning failed", error)
            }
        }
    }

    function clearShaderWarning(effectId) {
        var normalizedId = _normalizeEffectId(effectId)

        var previousState = shaderWarningState
        var nextState = _cloneWarningState(previousState)
        if (Object.prototype.hasOwnProperty.call(nextState, normalizedId))
            delete nextState[normalizedId]
        shaderWarningState = nextState

        shaderWarningCleared(normalizedId)

        var hostWindow = _hostWindow()
        if (hostWindow && typeof hostWindow.clearShaderWarning === "function") {
            try {
                hostWindow.clearShaderWarning(normalizedId)
            } catch (error) {
                console.debug("SimulationRoot (stub): window.clearShaderWarning failed", error)
            }
        }
    }

    // Оформляем фон панели
    background: Rectangle {
        radius: 18
        color: Qt.rgba(0.06, 0.09, 0.13, 0.92)
        border.color: Qt.rgba(0.18, 0.24, 0.33, 0.9)
        border.width: 1
    }

    // Основной контент — панель симуляции (как прямой потомок, чтобы findChild() находил её)
    contentItem: Local.SimulationPanel {
        id: simulationPanel
        objectName: "simulationPanel"
        anchors.fill: parent
        anchors.margins: 24
    }
}
