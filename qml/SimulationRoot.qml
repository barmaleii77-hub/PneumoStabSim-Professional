pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import "." as Local

/**
 * Minimal root for the standalone simulation panel harness.
 * Provides stub handlers that mirror the desktop application's
 * SimulationRoot API surface so that qmllint does not report
 * missing bindings during local development.
 */
Pane {
    id: root

    width: 960
    height: 640
    padding: 24

    signal geometryUpdatesApplied(var payload)
    signal shaderWarningRegistered(string effectId, string message)
    signal shaderWarningCleared(string effectId)

    /** Cached map of active shader warnings (effectId -> message). */
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

    /**
     * Accepts geometry updates emitted by the Python bridge in production.
     * The stub simply re-emits the payload for tests or tooling to observe.
     */
    function applyGeometryUpdates(params) {
        var payload = params
        if (!payload || typeof payload !== "object")
            payload = {}
        geometryUpdatesApplied(payload)
    }

    /**
     * Mirrors the shader warning bridge used by the production scene.
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

    background: Rectangle {
        radius: 18
        color: Qt.rgba(0.06, 0.09, 0.13, 0.92)
        border.color: Qt.rgba(0.18, 0.24, 0.33, 0.9)
        border.width: 1
    }

    contentItem: Local.SimulationPanel {
        id: simulationPanel
        anchors.fill: parent
    }
}
