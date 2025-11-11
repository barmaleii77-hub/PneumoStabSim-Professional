pragma ComponentBehavior: Bound

import QtQuick 6.10

ShaderEffect {
    id: root

    // Public API -----------------------------------------------------------
    /** Identifier propagated to logs and fallback controllers. */
    property string effectId: objectName && objectName.length ? objectName : "shaderEffect"

    /** Optional controller object with request/clear methods for fallbacks. */
    property var fallbackController: null

    /** When true, JSON diagnostics are forwarded to window.logQmlEvent. */
    property bool diagnosticsLoggingEnabled: false

    /** True when the effect requested a simplified fallback mode. */
    property bool fallbackActive: false

    /** Description of the most recent compilation failure. */
    property string fallbackReason: ""

    /** Cached warning message to prevent duplicate registrations. */
    property string lastWarningMessage: ""

    /** Cached shader status to avoid repeated log spam. */
    property int _lastKnownStatus: ShaderEffect.Uncompiled

    signal simplifiedFallbackRequested(string effectId, string reason)
    signal simplifiedFallbackRecovered(string effectId)
    signal shaderWarningRaised(string effectId, string message)
    signal shaderWarningCleared(string effectId)

    /**
     * Manual hook for unit tests – feeds the same code path as statusChanged.
     */
    function __applyStatusForTesting(value) { handleStatus(value) }

    /**
     * Manual hook for unit tests – clears cached state without touching GPU.
     */
    function __resetFallbackForTesting() {
        fallbackActive = false
        fallbackReason = ""
        lastWarningMessage = ""
        _lastKnownStatus = ShaderEffect.Uncompiled
    }

    function logDiagnostics(eventName, payload) {
        if (!diagnosticsLoggingEnabled)
            return

        var snapshot = {
            level: "info",
            logger: "qml.shader_effect",
            event: eventName,
            effectId: effectId,
            payload: payload || ({})
        }
        var json = JSON.stringify(snapshot)
        if (json && json.length)
            console.log(json)

        // qmllint disable unqualified
        var windowRef = typeof window !== "undefined" ? window : null
        // qmllint enable unqualified
        if (!windowRef || typeof windowRef.logQmlEvent !== "function")
            return
        try {
            windowRef.logQmlEvent(eventName, effectId)
        } catch (error) {
            console.debug("ShaderEffect diagnostics forwarding failed", effectId, error)
        }
    }

    function handleStatus(nextStatus) {
        if (_lastKnownStatus === nextStatus)
            return
        _lastKnownStatus = nextStatus

        if (nextStatus === ShaderEffect.Error) {
            var reason = _buildFailureReason()
            console.error("❌ ShaderEffect:", reason)
            _registerWarning(reason)
            _activateFallback(reason)
            return
        }

        if (nextStatus === ShaderEffect.Compiled) {
            if (fallbackActive)
                console.log("✅ ShaderEffect:", effectId, "recovered from compilation error")
            _deactivateFallback()
            return
        }

        if (nextStatus === ShaderEffect.Uncompiled) {
            // Transitional state (e.g. effect just created); clear stale warnings.
            if (!fallbackActive)
                _clearWarning()
        }
    }

    function _buildFailureReason() {
        var base = effectId + ": shader effect compilation failed"
        var logText = _firstLogLine()
        if (logText.length)
            return base + " – " + logText
        return base
    }

    function _firstLogLine() {
        try {
            var logText = root.log
            if (!logText)
                return ""
            var trimmed = String(logText).trim()
            if (!trimmed.length)
                return ""
            var newlineIndex = trimmed.indexOf("\n")
            if (newlineIndex !== -1)
                trimmed = trimmed.substring(0, newlineIndex)
            return trimmed
        } catch (error) {
            console.debug("ShaderEffect: unable to read compilation log", effectId, error)
            return ""
        }
    }

    function _activateFallback(message) {
        var reasonChanged = fallbackReason !== message
        if (!fallbackActive || reasonChanged) {
            fallbackActive = true
            fallbackReason = message
            simplifiedFallbackRequested(effectId, message)
            logDiagnostics("shader_fallback_requested", { message: message })
            _withController(function(controller) {
                if (typeof controller.requestSimplifiedFallback === "function")
                    controller.requestSimplifiedFallback(effectId, message)
                else if (typeof controller.requestSimplifiedRendering === "function")
                    controller.requestSimplifiedRendering(effectId, message)
            })
        }
    }

    function _deactivateFallback() {
        if (!fallbackActive && !fallbackReason.length) {
            _clearWarning()
            return
        }
        var previousReason = fallbackReason
        fallbackActive = false
        fallbackReason = ""
        simplifiedFallbackRecovered(effectId)
        logDiagnostics("shader_fallback_recovered", { previousReason: previousReason })
        _withController(function(controller) {
            if (typeof controller.clearSimplifiedFallback === "function")
                controller.clearSimplifiedFallback(effectId)
            if (typeof controller.clearSimplifiedRendering === "function")
                controller.clearSimplifiedRendering(effectId)
        })
        _clearWarning()
    }

    function _registerWarning(message) {
        if (lastWarningMessage === message)
            return
        lastWarningMessage = message
        shaderWarningRaised(effectId, message)
        _withController(function(controller) {
            if (typeof controller.registerShaderWarning === "function")
                controller.registerShaderWarning(effectId, message)
        })
    }

    function _clearWarning() {
        if (!lastWarningMessage.length)
            return
        var clearedMessage = lastWarningMessage
        lastWarningMessage = ""
        shaderWarningCleared(effectId)
        _withController(function(controller) {
            if (typeof controller.clearShaderWarning === "function")
                controller.clearShaderWarning(effectId)
        })
        logDiagnostics("shader_warning_cleared", { message: clearedMessage })
    }

    function _withController(callback) {
        if (typeof callback !== "function")
            return
        var controller = fallbackController
        // qmllint disable unqualified
        if (!controller && typeof window !== "undefined" && window)
            controller = window
        // qmllint enable unqualified
        if (!controller)
            return
        try {
            callback(controller)
        } catch (error) {
            console.debug("ShaderEffect: fallback controller callback failed", effectId, error)
        }
    }

    onStatusChanged: handleStatus(root.status)
}
