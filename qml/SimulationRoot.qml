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
        shaderWarningRegistered(String(effectId), message !== undefined && message !== null ? String(message) : "")
    }

    function clearShaderWarning(effectId) {
        shaderWarningCleared(String(effectId))
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
