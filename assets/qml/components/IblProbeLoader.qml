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
    property url fallbackSource: Qt.resolvedUrl("../../assets/studio_small_09_2k.hdr")

    /** Internal flag preventing infinite fallback recursion. */
    property bool _fallbackTried: false

    /** Expose the probe for consumers. */
    property Texture probe: hdrProbe

    Texture {
        id: hdrProbe
        source: controller.primarySource
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
    property int _lastStatus: -1  // Начинаем с -1 вместо Texture.Null
    
    onProbeChanged: {
        if (probe && typeof probe.status !== "undefined") {
            _lastStatus = probe.status
            _checkStatus()
        }
    }
    
    // Polling-based status check (since Texture doesn't emit statusChanged signal)
    Timer {
        interval: 100  // Check every 100ms
        running: true
        repeat: true
        onTriggered: {
            // Безопасная проверка на undefined
            if (typeof hdrProbe.status !== "undefined" && hdrProbe.status !== controller._lastStatus) {
                controller._lastStatus = hdrProbe.status
                controller._checkStatus()
            }
        }
    }
    
    function _checkStatus() {
        // Безопасная проверка статуса
        if (typeof hdrProbe.status === "undefined") {
            return
        }
        
        var statusStr = hdrProbe.status === Texture.Null ? "Null" :
                      hdrProbe.status === Texture.Ready ? "Ready" :
                      hdrProbe.status === Texture.Loading ? "Loading" :
                      hdrProbe.status === Texture.Error ? "Error" : "Unknown(" + hdrProbe.status + ")"
        
        writeLog("INFO", "Texture status: " + statusStr + " | source: " + hdrProbe.source)
        
        if (hdrProbe.status === Texture.Error && !controller._fallbackTried) {
            controller._fallbackTried = true
            writeLog("WARN", "HDR probe FAILED at " + hdrProbe.source + " — switching to fallback: " + controller.fallbackSource)
            hdrProbe.source = controller.fallbackSource
        } else if (hdrProbe.status === Texture.Ready) {
            writeLog("SUCCESS", "HDR probe LOADED successfully: " + hdrProbe.source)
        } else if (hdrProbe.status === Texture.Error && controller._fallbackTried) {
            writeLog("ERROR", "CRITICAL: Both HDR probes failed to load - IBL will be disabled")
        }
    }

    // Логирование изменения source
    onPrimarySourceChanged: {
        writeLog("INFO", "Primary source changed: " + primarySource)
    }

    onFallbackSourceChanged: {
        writeLog("INFO", "Fallback source changed: " + fallbackSource)
    }

    /** Simple ready flag to avoid binding against an invalid texture. */
    readonly property bool ready: probe.status === Texture.Ready

    Component.onCompleted: {
        writeLog("INFO", "IblProbeLoader initialized | Primary: " + primarySource + " | Fallback: " + fallbackSource)
        _checkStatus()  // Первоначальная проверка
    }

    Component.onDestruction: {
        writeLog("INFO", "IblProbeLoader destroyed")
    }
}
