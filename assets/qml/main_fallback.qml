import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    anchors.fill: parent
    color: "#2a2a2a"

    signal batchUpdatesApplied(var summary)

    property var pendingPythonUpdates: ({})
    onPendingPythonUpdatesChanged: {
        if (!pendingPythonUpdates || typeof pendingPythonUpdates !== "object") {
            return
        }
        _processUpdates(pendingPythonUpdates)
    }

    readonly property var _updateHandlers: ({
        "geometry": applyGeometryUpdates,
        "animation": applyAnimationUpdates,
        "lighting": applyLightingUpdates,
        "materials": applyMaterialUpdates,
        "environment": applyEnvironmentUpdates,
        "quality": applyQualityUpdates,
        "camera": applyCameraUpdates,
        "effects": applyEffectsUpdates,
        "simulation": applySimulationUpdates,
        "threeD": applyThreeDUpdates,
        "render": applyRenderSettings
    })

    function _processUpdates(updates) {
        var categories = []
        for (var key in updates) {
            if (!updates.hasOwnProperty(key))
                continue
            var handler = _updateHandlers[key]
            var payload = updates[key]
            if (typeof handler === "function") {
                try {
                    handler(payload)
                } catch (err) {
                    console.warn("Fallback scene failed to process", key, err)
                }
            } else {
                console.warn("Fallback scene does not support", key, payload)
            }
            categories.push(key)
        }
        batchUpdatesApplied({
            timestamp: Date.now(),
            categories: categories
        })
    }

    function applyGeometryUpdates(params) {
        console.warn("Fallback scene ignoring geometry updates", params)
    }

    function applyAnimationUpdates(params) {
        console.warn("Fallback scene ignoring animation updates", params)
    }

    function applyLightingUpdates(params) {
        console.warn("Fallback scene ignoring lighting updates", params)
    }

    function applyMaterialUpdates(params) {
        console.warn("Fallback scene ignoring material updates", params)
    }

    function applyEnvironmentUpdates(params) {
        console.warn("Fallback scene ignoring environment updates", params)
    }

    function applyQualityUpdates(params) {
        console.warn("Fallback scene ignoring quality updates", params)
    }

    function applyCameraUpdates(params) {
        console.warn("Fallback scene ignoring camera updates", params)
    }

    function applyEffectsUpdates(params) {
        console.warn("Fallback scene ignoring effects updates", params)
    }

    function applySimulationUpdates(params) {
        console.warn("Fallback scene ignoring simulation updates", params)
    }

    function applyThreeDUpdates(params) {
        console.warn("Fallback scene ignoring 3D updates", params)
    }

    function applyRenderSettings(params) {
        console.warn("Fallback scene ignoring render updates", params)
    }

    Column {
        anchors.centerIn: parent
        spacing: 20

        Text {
            text: "⚠️ QtQuick3D Недоступен"
            color: "#ffffff"
            font.pixelSize: 24
            font.bold: true
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Text {
            text: "3D визуализация временно отключена"
            color: "#cccccc"
            font.pixelSize: 16
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Button {
            text: "Запустить диагностику"
            anchors.horizontalCenter: parent.horizontalCenter
            onClicked: {
                console.log("Запустите: python qtquick3d_diagnostic.py")
            }
        }

        Text {
            text: "Для решения проблемы:\n1. Переустановите PySide6\n2. Обновите драйверы видеокарты\n3. Используйте --legacy режим"
            color: "#aaaaaa"
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }
}
