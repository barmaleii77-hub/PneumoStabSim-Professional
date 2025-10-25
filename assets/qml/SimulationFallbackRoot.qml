import QtQuick 6.5
import QtQuick.Controls 6.5

/*
 * PneumoStabSim fallback scene used when the full QtQuick3D assets are missing.
 *
 * The component deliberately mirrors the API expected by the Python bridge:
 *  - property pendingPythonUpdates triggers applyBatchedUpdates
 *  - functions apply{Category}Updates handle incremental updates
 *  - signal batchUpdatesApplied notifies Python once a batch has been processed
 */
Item {
    id: root
    anchors.fill: parent

    // ------------------------------------------------------------------
    // Synchronisation contract with Python
    // ------------------------------------------------------------------
    signal batchUpdatesApplied(var summary)

    property var pendingPythonUpdates: ({})
    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates || typeof pendingPythonUpdates !== "object") {
            return
        }
        applyBatchedUpdates(pendingPythonUpdates)
    }

    // Animation state that Python can toggle
    property real animationTime: 0
    property bool isRunning: false

    // Diagnostics payloads
    property var lastGeometry: ({})
    property var lastAnimation: ({})
    property var lastLighting: ({})
    property var lastMaterials: ({})
    property var lastEnvironment: ({})
    property var lastQuality: ({})
    property var lastCamera: ({})
    property var lastEffects: ({})
    property var lastSimulation: ({})
    property var lastThreeD: ({})

    // ------------------------------------------------------------------
    // Helper utilities
    // ------------------------------------------------------------------
    function logQmlEvent(eventType, name) {
        if (typeof window === "undefined" || !window) {
            return
        }
        if (typeof window.logQmlEvent === "function") {
            try {
                window.logQmlEvent(eventType, name)
            } catch (err) {
                console.debug("logQmlEvent failed", err)
            }
        }
    }

    function normaliseNumber(value, fallback) {
        if (value === undefined || value === null) {
            return fallback
        }
        var num = Number(value)
        if (Number.isNaN(num)) {
            return fallback
        }
        return num
    }

    function merge(target, source) {
        if (!source || typeof source !== "object") {
            return target
        }
        var keys = Object.keys(source)
        for (var i = 0; i < keys.length; ++i) {
            var key = keys[i]
            var value = source[key]
            if (
                value && typeof value === "object" && !Array.isArray(value)
            ) {
                if (!target[key] || typeof target[key] !== "object") {
                    target[key] = {}
                }
                merge(target[key], value)
            } else {
                target[key] = value
            }
        }
        return target
    }

    // ------------------------------------------------------------------
    // Batch handling
    // ------------------------------------------------------------------
    function applyBatchedUpdates(updates) {
        logQmlEvent("signal_received", "applyBatchedUpdates")
        var categories = []
        if (!updates || typeof updates !== "object") {
            return
        }

        if (updates.geometry) {
            categories.push("geometry")
            applyGeometryUpdates(updates.geometry)
        }
        if (updates.animation) {
            categories.push("animation")
            applyAnimationUpdates(updates.animation)
        }
        if (updates.lighting) {
            categories.push("lighting")
            applyLightingUpdates(updates.lighting)
        }
        if (updates.materials) {
            categories.push("materials")
            applyMaterialUpdates(updates.materials)
        }
        if (updates.environment) {
            categories.push("environment")
            applyEnvironmentUpdates(updates.environment)
        }
        if (updates.quality) {
            categories.push("quality")
            applyQualityUpdates(updates.quality)
        }
        if (updates.camera) {
            categories.push("camera")
            applyCameraUpdates(updates.camera)
        }
        if (updates.effects) {
            categories.push("effects")
            applyEffectsUpdates(updates.effects)
        }
        if (updates.simulation) {
            categories.push("simulation")
            applySimulationUpdates(updates.simulation)
        }
        if (updates.threeD) {
            categories.push("threeD")
            applyThreeDUpdates(updates.threeD)
        }

        batchUpdatesApplied({
            timestamp: Date.now(),
            categories: categories
        })
    }

    function applyGeometryUpdates(params) {
        lastGeometry = merge({}, params || {})
        logQmlEvent("function_called", "applyGeometryUpdates")
    }

    function applyAnimationUpdates(params) {
        lastAnimation = merge({}, params || {})
        if (params && params.animationTime !== undefined) {
            animationTime = normaliseNumber(params.animationTime, animationTime)
        }
        if (params && params.isRunning !== undefined) {
            isRunning = Boolean(params.isRunning)
        }
        logQmlEvent("function_called", "applyAnimationUpdates")
    }

    function applyLightingUpdates(params) {
        lastLighting = merge({}, params || {})
        logQmlEvent("function_called", "applyLightingUpdates")
    }

    function applyMaterialUpdates(params) {
        lastMaterials = merge({}, params || {})
        logQmlEvent("function_called", "applyMaterialUpdates")
    }

    function applyEnvironmentUpdates(params) {
        lastEnvironment = merge({}, params || {})
        logQmlEvent("function_called", "applyEnvironmentUpdates")
    }

    function applyQualityUpdates(params) {
        lastQuality = merge({}, params || {})
        logQmlEvent("function_called", "applyQualityUpdates")
    }

    function applyCameraUpdates(params) {
        lastCamera = merge({}, params || {})
        logQmlEvent("function_called", "applyCameraUpdates")
    }

    function applyEffectsUpdates(params) {
        lastEffects = merge({}, params || {})
        logQmlEvent("function_called", "applyEffectsUpdates")
    }

    function applySimulationUpdates(params) {
        lastSimulation = merge({}, params || {})
        if (params && params.animation) {
            applyAnimationUpdates(params.animation)
        }
        if (params && params.threeD) {
            applyThreeDUpdates(params.threeD)
        }
        logQmlEvent("function_called", "applySimulationUpdates")
    }

    function applyThreeDUpdates(params) {
        lastThreeD = merge({}, params || {})
        logQmlEvent("function_called", "applyThreeDUpdates")
    }

    // Legacy function names expected by Python diagnostics
    function updateGeometry(params) { applyGeometryUpdates(params) }
    function updateAnimation(params) { applyAnimationUpdates(params) }
    function updateLighting(params) { applyLightingUpdates(params) }
    function updateMaterials(params) { applyMaterialUpdates(params) }
    function updateEnvironment(params) { applyEnvironmentUpdates(params) }
    function updateQuality(params) { applyQualityUpdates(params) }
    function updateCamera(params) { applyCameraUpdates(params) }
    function updateEffects(params) { applyEffectsUpdates(params) }

    function updatePistonPositions(positions) {
        if (!positions) {
            return
        }
        if (!lastSimulation.pistons) {
            lastSimulation.pistons = {}
        }
        lastSimulation.pistons.fl = normaliseNumber(positions.fl, 0)
        lastSimulation.pistons.fr = normaliseNumber(positions.fr, 0)
        lastSimulation.pistons.rl = normaliseNumber(positions.rl, 0)
        lastSimulation.pistons.rr = normaliseNumber(positions.rr, 0)
    }

    // ------------------------------------------------------------------
    // Minimal 2D visualisation to confirm updates arrive
    // ------------------------------------------------------------------
    Rectangle {
        anchors.fill: parent
        color: "#1b1d2a"

        Column {
            anchors.centerIn: parent
            spacing: 16
            width: 420

            Label {
                text: "PneumoStabSim Fallback Scene"
                font.pixelSize: 22
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
            }

            Label {
                text: isRunning ? "Simulation: RUNNING" : "Simulation: STOPPED"
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
            }

            Label {
                text: "Animation time: " + animationTime.toFixed(3) + " s"
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
            }

            Repeater {
                model: [
                    { key: "Geometry", payload: lastGeometry },
                    { key: "Lighting", payload: lastLighting },
                    { key: "Environment", payload: lastEnvironment },
                    { key: "Camera", payload: lastCamera },
                    { key: "Effects", payload: lastEffects }
                ]

                delegate: Rectangle {
                    width: parent.width
                    height: 48
                    radius: 8
                    color: "#22263a"
                    border.color: "#303552"
                    border.width: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 4

                        Label {
                            text: modelData.key + ": " + Object.keys(modelData.payload).length + " params"
                            font.pixelSize: 14
                        }
                        Label {
                            text: JSON.stringify(modelData.payload).slice(0, 120)
                            font.pixelSize: 12
                            color: "#9aa1bc"
                            wrapMode: Text.WrapAnywhere
                        }
                    }
                }
            }
        }
    }
}
