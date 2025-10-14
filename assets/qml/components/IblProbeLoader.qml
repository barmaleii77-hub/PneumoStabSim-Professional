import QtQuick
import QtQuick3D

Item {
    id: controller

    /**
      * Primary HDR environment map used for IBL/skybox lighting.
      * Defaults to the studio lighting provided with the project.
      */
    property url primarySource: Qt.resolvedUrl("../../hdr/studio.hdr")

    /**
      * Optional fallback map that is tried automatically when the primary
      * asset is missing (useful for developer setups without HDR packages).
      */
    // Path from components/ → assets/qml/assets/studio_small_09_2k.hdr
    property url fallbackSource: Qt.resolvedUrl("../assets/studio_small_09_2k.hdr")

    /** Internal flag preventing infinite fallback recursion. */
    property bool _fallbackTried: false

    /**
      * Double-buffered textures to prevent flicker when switching HDRs.
      * We keep the last ready texture active while the new one loads.
      */
    property int activeIndex: 0         // 0 → texA active, 1 → texB active
    property int loadingIndex: -1       // index currently loading, -1 if none
    readonly property Texture _activeTex: activeIndex === 0 ? texA : texB
    readonly property Texture _inactiveTex: activeIndex === 0 ? texB : texA

    /** Expose the currently active probe for consumers (always Ready if available). */
    property Texture probe: _activeTex

    Texture {
        id: texA
        source: ""
        minFilter: Texture.Linear
        magFilter: Texture.Linear
        generateMipmaps: true
    }
    Texture {
        id: texB
        source: ""
        minFilter: Texture.Linear
        magFilter: Texture.Linear
        generateMipmaps: true
    }

    // ✅ FILE LOGGING SYSTEM для анализа сигналов
    function writeLog(level, message) {
        var timestamp = new Date().toISOString()
        var logEntry = timestamp + " | " + level + " | IblProbeLoader | " + message
        
        // Отправляем в Python для записи в файл
        if (typeof window !== "undefined" && window !== null && window.logIblEvent) {
            window.logIblEvent(logEntry)
        }
        
        // Также выводим в консоль для отладки
        if (level === "ERROR" || level === "WARN") {
            console.warn(logEntry)
        } else {
            console.log(logEntry)
        }
    }

    // Monitor texture status using Timer polling (Texture has no statusChanged signal!)
    property int _lastStatusA: -1
    property int _lastStatusB: -1

    // Polling-based status check for both textures
    Timer {
        interval: 100  // Check every 100ms
        running: true
        repeat: true
        onTriggered: {
            controller._checkStatusFor(texA, 0)
            controller._checkStatusFor(texB, 1)
        }
    }
    function _statusToString(s) {
        return s === Texture.Null ? "Null" :
               s === Texture.Ready ? "Ready" :
               s === Texture.Loading ? "Loading" :
               s === Texture.Error ? "Error" : ("Unknown(" + s + ")")
    }

    function _checkStatusFor(tex, index) {
        if (typeof tex.status === "undefined")
            return
        var prev = index === 0 ? _lastStatusA : _lastStatusB
        if (tex.status === prev)
            return

        var statusStr = _statusToString(tex.status)
        writeLog("INFO", "Texture[" + index + "] status: " + statusStr + " | source: " + tex.source)

        if (index === 0) _lastStatusA = tex.status; else _lastStatusB = tex.status

        // React only for the currently loading slot
        if (index === loadingIndex) {
            if (tex.status === Texture.Error) {
                if (!controller._fallbackTried) {
                    controller._fallbackTried = true
                    writeLog("WARN", "HDR probe FAILED at " + tex.source + " — switching to fallback: " + controller.fallbackSource)
                    tex.source = controller.fallbackSource
                } else {
                    writeLog("ERROR", "CRITICAL: Both HDR probes failed to load - keeping previous probe active")
                    loadingIndex = -1
                }
            } else if (tex.status === Texture.Ready) {
                activeIndex = index
                loadingIndex = -1
                writeLog("SUCCESS", "HDR probe LOADED successfully: " + tex.source + " (active slot=" + activeIndex + ")")
            }
        }
    }

    // Логирование изменения source
    onPrimarySourceChanged: {
        writeLog("INFO", "Primary source changed: " + primarySource)
        _startLoading(primarySource)
    }

    onFallbackSourceChanged: {
        writeLog("INFO", "Fallback source changed: " + fallbackSource)
        // no immediate reload; used only when current load fails
    }

    /** Simple ready flag: active probe is ready. */
    readonly property bool ready: _activeTex.status === Texture.Ready

    function _startLoading(url) {
        // choose inactive slot to load into
        var idx = (activeIndex === 0) ? 1 : 0
        loadingIndex = idx
        _fallbackTried = false
        var tex = (idx === 0) ? texA : texB
        writeLog("INFO", "Start loading HDR into slot " + idx + ": " + url)
        tex.source = url
    }

    Component.onCompleted: {
        writeLog("INFO", "IblProbeLoader initialized | Primary: " + primarySource + " | Fallback: " + fallbackSource)
        // Initial load into slot 0
        activeIndex = 0
        loadingIndex = 0
        _fallbackTried = false
        texA.source = primarySource
    }

    Component.onDestruction: {
        writeLog("INFO", "IblProbeLoader destroyed")
    }
}
