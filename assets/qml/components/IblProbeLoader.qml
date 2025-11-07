import QtQuick 6.10
import QtQuick3D 6.10

// qmllint disable missing-property

pragma ComponentBehavior: Bound

Item {
    id: controller

    // Основной HDR для IBL/skybox
    property url primarySource: ""   // ✅ Без дефолтов — задаётся из UI/настроек

    // Резервный HDR: используем процедурно сгенерированный прямоугольник,
    // чтобы не полагаться на бинарные ассеты. Текстовое описание пригодится
    // для логов и биндингов.
    readonly property string fallbackDescriptor: "generated://ibl-placeholder"
    readonly property string fallbackSource: fallbackDescriptor

    // Флаг активного использования резервного HDR
    property bool fallbackActive: false

    // Итоговый источник, который подаётся в Texture (строка для удобства UI)
    readonly property string effectiveSource: fallbackActive
        ? fallbackDescriptor
        : primarySource

    // Экспортируемый probe
    property Texture probe: hdrProbe

    // Текущий активный источник (удобно для отладки/синхронизации UI)
    readonly property string activeSource: effectiveSource

    // Текстура HDR. Источник определяется напрямую primarySource
    Texture {
        id: hdrProbe
        source: controller.fallbackActive ? "" : controller.primarySource
        sourceItem: controller.fallbackActive ? fallbackCanvas : null
        minFilter: Texture.Linear
        magFilter: Texture.Linear
        generateMipmaps: true
    }

    Item {
        id: fallbackCanvas
        width: 512
        height: 256
        visible: false

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#2a2f3a" }
                GradientStop { position: 0.5; color: "#1b1f29" }
                GradientStop { position: 1.0; color: "#0b0e15" }
            }
            border.color: "#404750"
            border.width: 2
            radius: 24
        }

        Text {
            anchors.centerIn: parent
            text: qsTr("HDR Fallback")
            color: "#c0c7d4"
            font.pixelSize: 48
            font.family: "Source Sans Pro"
            font.bold: true
            opacity: 0.9
        }
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

        if (hdrProbe.status === Texture.Null) {
            if (!controller.primarySource || String(controller.primarySource) === "")
                controller._activateFallback("No primary HDR source provided")
        } else if (hdrProbe.status === Texture.Error) {
            if (controller.fallbackActive) {
                writeLog(
                    "ERROR",
                    "Fallback HDR failed to load: " + controller.fallbackDescriptor
                )
                controller.fallbackActive = false
                controller._lastStatus = -1
                return
            }
            if (controller.primarySource && String(controller.primarySource) !== "") {
                var fallbackUsed = controller._activateFallback(
                    "HDR probe failed to load"
                )
                if (!fallbackUsed)
                    writeLog(
                        "WARN",
                        "HDR probe failed to load and no fallback is available: " +
                            hdrProbe.source
                    )
            } else {
                var emptyFallback = controller._activateFallback(
                    "No primary HDR source provided"
                )
                if (!emptyFallback)
                    writeLog("INFO", "No HDR source specified; skybox remains empty")
            }
        } else if (hdrProbe.status === Texture.Ready) {
            if (controller.fallbackActive && hdrProbe.sourceItem === fallbackCanvas) {
                writeLog(
                    "WARN",
                    "Fallback HDR probe LOADED successfully: " + controller.fallbackDescriptor
                )
            } else {
                writeLog("SUCCESS", "HDR probe LOADED successfully: " + hdrProbe.source)
            }
        }
    }

    function _activateFallback(reason) {
        if (controller.fallbackActive)
            return true
        writeLog(
            "WARN",
            reason + "; switching to fallback HDR source: " + controller.fallbackDescriptor
        )
        controller.fallbackActive = true
        controller._lastStatus = -1
        return true
    }

    // Логирование изменения source'ов
    onPrimarySourceChanged: {
        writeLog("INFO", "Primary source changed: " + primarySource)
        controller._lastStatus = -1
        if (controller.fallbackActive) {
            writeLog("INFO", "Primary HDR updated; fallback disabled")
        }
        controller.fallbackActive = false
    }

    // Готовность проба: считаем готовым только когда source валиден и статус Ready
    readonly property bool ready: (
        hdrProbe
        && hdrProbe.status === Texture.Ready
        && (
            (
                !controller.fallbackActive
                && hdrProbe.source
                && String(hdrProbe.source) !== ""
            )
            || (
                controller.fallbackActive
                && hdrProbe.sourceItem === fallbackCanvas
            )
        )
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
