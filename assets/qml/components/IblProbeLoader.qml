import QtQuick 6.10
import QtQuick3D 6.10

// qmllint disable missing-property

pragma ComponentBehavior: Bound

Item {
    id: controller

    // Основной HDR для IBL/skybox
    property url primarySource: ""   // ✅ Без дефолтов — задаётся из UI/настроек

    // Экспортируемый probe
    property Texture probe: hdrProbe

    // Текущий активный источник (удобно для отладки/синхронизации UI)
    readonly property url activeSource: primarySource

    // Текстура HDR. Источник определяется напрямую primarySource
    Texture {
        id: hdrProbe
        source: controller.primarySource
        minFilter: Texture.Linear
        magFilter: Texture.Linear
        generateMipmaps: true
    }

    // ✅ FILE LOGGING SYSTEM для анализа сигналов
    function writeLog(level, message) {
        const timestamp = new Date().toISOString()
        const logEntry = `${timestamp} | ${level} | IblProbeLoader | ${message}`
        const appWindow = Qt.application ? Qt.application.activeWindow : null
        if (appWindow && typeof appWindow.logIblEvent === "function") {
            appWindow.logIblEvent(logEntry)
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

        if (hdrProbe.status === Texture.Error) {
            if (controller.primarySource && String(controller.primarySource) !== "") {
                writeLog(
                    "WARN",
                    "HDR probe failed to load (no fallback will be applied): " +
                        hdrProbe.source
                )
            } else {
                writeLog("INFO", "No HDR source specified; skybox remains empty")
            }
        } else if (hdrProbe.status === Texture.Ready) {
            writeLog("SUCCESS", "HDR probe LOADED successfully: " + hdrProbe.source)
        }
    }

    // Логирование изменения source'ов
    onPrimarySourceChanged: {
        writeLog("INFO", "Primary source changed: " + primarySource)
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
        writeLog(
            "INFO",
            "IblProbeLoader initialized | Primary: " + (primarySource || "<empty>")
        )
        if (!primarySource || String(primarySource) === "") {
            writeLog("WARN", "No primarySource provided at init")
        }
        _checkStatus()
    }

    Component.onDestruction: {
        writeLog("INFO", "IblProbeLoader destroyed")
    }
}
