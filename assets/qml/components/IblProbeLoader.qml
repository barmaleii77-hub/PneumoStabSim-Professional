import QtQuick
import QtQuick3D

Item {
    id: controller

    // Основной HDR для IBL/skybox
    property url primarySource: Qt.resolvedUrl("../../hdr/studio.hdr")
    // Резервный HDR (на случай ошибки загрузки основного) — приводим к той же папке assets/hdr
    property url fallbackSource: Qt.resolvedUrl("../../hdr/studio_small_09_2k.hdr")

    // Внутренние флаги
    property bool _fallbackTried: false
    property bool _useFallback: false   // ✅ НЕ ломаем биндинг, управляем источником через флаг

    // Экспортируемый probe
    property Texture probe: hdrProbe

    // Текущий активный источник (удобно для отладки/синхронизации UI)
    readonly property url activeSource: _useFallback ? fallbackSource : primarySource

    // Текстура HDR. Источник определяется логикой выбора (primary/fallback)
    Texture {
        id: hdrProbe
        source: controller._useFallback ? controller.fallbackSource : controller.primarySource
        minFilter: Texture.Linear
        magFilter: Texture.Linear
        generateMipmaps: true
    }

    // ✅ FILE LOGGING SYSTEM для анализа сигналов
    function writeLog(level, message) {
        var timestamp = new Date().toISOString()
        var logEntry = timestamp + " | " + level + " | IblProbeLoader | " + message
        if (typeof window !== "undefined" && window !== null && window.logIblEvent) {
            window.logIblEvent(logEntry)
        }
        if (level === "ERROR" || level === "WARN") {
            console.warn(logEntry)
        } else {
            console.log(logEntry)
        }
    }

    // Отслеживание статуса через polling (Texture не шлет statusChanged)
    property int _lastStatus: -1

    onProbeChanged: {
        if (probe && typeof probe.status !== "undefined") {
            _lastStatus = probe.status
            _checkStatus()
        }
    }

    Timer {
        interval: 100
        running: true
        repeat: true
        onTriggered: {
            if (typeof hdrProbe.status !== "undefined" && hdrProbe.status !== controller._lastStatus) {
                controller._lastStatus = hdrProbe.status
                controller._checkStatus()
            }
        }
    }

    function statusToString(s) {
        return s === Texture.Null ? "Null" :
               s === Texture.Ready ? "Ready" :
               s === Texture.Loading ? "Loading" :
               s === Texture.Error ? "Error" : ("Unknown(" + s + ")")
    }

    function _checkStatus() {
        if (typeof hdrProbe.status === "undefined")
            return

        var statusStr = statusToString(hdrProbe.status)
        writeLog("INFO", "Texture status: " + statusStr + " | source: " + hdrProbe.source)

        if (hdrProbe.status === Texture.Error && !controller._fallbackTried) {
            // ✅ Переключаемся на fallback НЕ трогая биндинг source
            controller._fallbackTried = true
            controller._useFallback = true
            writeLog("WARN", "Primary FAILED → switch to fallback: " + controller.fallbackSource)
        } else if (hdrProbe.status === Texture.Ready) {
            // ✅ Сообщение совместимо с обработчиком в Python
            writeLog("SUCCESS", "HDR probe LOADED successfully: " + hdrProbe.source)
        } else if (hdrProbe.status === Texture.Error && controller._fallbackTried) {
            writeLog("ERROR", "CRITICAL: Both HDR probes failed to load")
        }
    }

    // Логирование изменения source'ов
    onPrimarySourceChanged: {
        writeLog("INFO", "Primary source changed: " + primarySource)
        // ✅ При выборе нового файла: заново пробуем primary
        controller._fallbackTried = false
        controller._useFallback = false
    }

    onFallbackSourceChanged: {
        writeLog("INFO", "Fallback source changed: " + fallbackSource)
        // Если сейчас используем fallback — перезагрузим его
        if (controller._useFallback)
            controller._lastStatus = -1
    }

    // Готовность проба
    readonly property bool ready: probe.status === Texture.Ready

    Component.onCompleted: {
        writeLog("INFO", "IblProbeLoader initialized | Primary: " + primarySource + " | Fallback: " + fallbackSource)
        _checkStatus()
    }

    Component.onDestruction: {
        writeLog("INFO", "IblProbeLoader destroyed")
    }
}
