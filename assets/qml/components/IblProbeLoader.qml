import QtQuick
import QtQuick3D

// qmllint disable missing-property

pragma ComponentBehavior: Bound

Item {
    id: controller

    // Основной HDR для IBL/skybox
    property url primarySource: ""   // ✅ Без дефолтов — задаётся из UI/настроек
    // Резервный HDR (на случай ошибки загрузки основного) — приводим к той же папке assets/hdr
    property url fallbackSource: ""   // ✅ Без дефолтов — задаётся из UI/настроек

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
        const timestamp = new Date().toISOString()
        const logEntry = `${timestamp} | ${level} | IblProbeLoader | ${message}`
        const handler = (typeof window !== "undefined" && window)
            ? window
            : (Qt.application ? Qt.application.activeWindow : null)
        if (handler && typeof handler.logIblEvent === "function") {
            handler.logIblEvent(logEntry)
        }
        if (level === "ERROR" || level === "WARN") {
            console.warn(logEntry)
        } else {
            console.log(logEntry)
        }
    }

    // Отслеживание статуса с помощью Connections (Qt 6.10 сообщает statusChanged)
    property int _lastStatus: -1

    onProbeChanged: {
        if (probe && typeof probe.status !== "undefined") {
            controller._lastStatus = probe.status
            controller._checkStatus()
        }
    }

    Connections {
        target: hdrProbe

        function onStatusChanged() {
            if (typeof hdrProbe.status === "undefined") {
                return
            }
            if (hdrProbe.status !== controller._lastStatus) {
                controller._lastStatus = hdrProbe.status
            }
            controller._checkStatus()
        }

        function onSourceChanged() {
            controller._lastStatus = -1
        }
    }

    function statusToString(s) {
        if (s === Texture.Null) {
            return "Null"
        }
        if (s === Texture.Ready) {
            return "Ready"
        }
        if (s === Texture.Loading) {
            return "Loading"
        }
        if (s === Texture.Error) {
            return "Error"
        }
        return `Unknown(${s})`
    }

    function _checkStatus() {
        if (typeof hdrProbe.status === "undefined")
            return

        var statusStr = statusToString(hdrProbe.status)
        writeLog("INFO", "Texture status: " + statusStr + " | source: " + hdrProbe.source)

        if (hdrProbe.status === Texture.Error && !controller._fallbackTried) {
            // ✅ Переключаемся на fallback ТОЛЬКО если указан primarySource (т.е. пользователь выбирал HDR)
            controller._fallbackTried = true
            var hasPrimary = (controller.primarySource && String(controller.primarySource) !== "")
            if (hasPrimary && controller.fallbackSource && String(controller.fallbackSource) !== "") {
                controller._useFallback = true
                writeLog("WARN", "Primary FAILED → switch to fallback: " + controller.fallbackSource)
            } else if (!hasPrimary) {
                // Нет выбранного primary — не активируем fallback автоматически
                writeLog("INFO", "No primarySource selected, skip fallback auto-switch")
            } else {
                writeLog("ERROR", "Primary FAILED and no valid fallback specified")
            }
        } else if (hdrProbe.status === Texture.Ready) {
            // ✅ Сообщение совместимо с обработчиком в Python
            writeLog("SUCCESS", "HDR probe LOADED successfully: " + hdrProbe.source)
            // Если primary загрузился успешно, сбрасываем флаги возврата к норме
            if (!controller._useFallback) {
                controller._fallbackTried = false
            }
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
        controller._lastStatus = -1
    }

    onFallbackSourceChanged: {
        writeLog("INFO", "Fallback source changed: " + fallbackSource)
        // Если сейчас используем fallback — перезагрузим его
        controller._lastStatus = -1
    }

    // Готовность проба: считаем готовым только когда source валиден и статус Ready
    readonly property bool ready: (
        hdrProbe
        && hdrProbe.source
        && String(hdrProbe.source) !== ""
        && hdrProbe.status === Texture.Ready
    )

    Component.onCompleted: {
        writeLog("INFO", "IblProbeLoader initialized | Primary: " + (primarySource || "<empty>") + " | Fallback: " + (fallbackSource || "<empty>"))
        if (!primarySource || String(primarySource) === "") {
            writeLog("WARN", "No primarySource provided at init")
        }
        _checkStatus()
    }

    Component.onDestruction: {
        writeLog("INFO", "IblProbeLoader destroyed")
    }
}
