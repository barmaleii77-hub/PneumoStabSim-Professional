import QtQuick 6.10
import QtQuick.Controls 6.10

Pane {
    id: root
    objectName: "simulationPanel"

    property var controller: null
    property bool isReady: false
    property bool simulationRunning: false
    property string statusText: simulationRunning ? qsTr("▶ Запущено") : qsTr("⏹ Остановлено")

    signal simulationControlRequested(string command)
    signal modesPresetSelected(string presetId)
    signal modesModeChanged(string modeType, string newMode)
    signal modesPhysicsChanged(var payload)
    signal modesAnimationChanged(var payload)
    signal pneumaticSettingsChanged(var payload)
    signal simulationSettingsChanged(var payload)
    signal cylinderSettingsChanged(var payload)

    padding: 24
    width: 420
    height: 320

    background: Rectangle {
        radius: 16
        color: Qt.rgba(0.07, 0.09, 0.13, 0.92)
        border.color: Qt.rgba(0.24, 0.29, 0.37, 0.92)
        border.width: 1
    }

    Component.onCompleted: {
        isReady = true
        if (controller && typeof controller._onSimulationPanelReady === "function") {
            controller._onSimulationPanelReady()
        }
    }

    function applyModesSettings(payload) {
        return true
    }

    function applyAnimationSettings(payload) {
        if (!payload)
            payload = {}
        if (payload.is_running !== undefined)
            simulationRunning = Boolean(payload.is_running)
        else if (payload.running !== undefined)
            simulationRunning = Boolean(payload.running)
        statusText = simulationRunning ? qsTr("▶ Запущено") : qsTr("⏹ Остановлено")
        return true
    }

    function applyPneumaticSettings(payload) { return true }
    function applySimulationSettings(payload) {
        if (payload && payload.animation)
            applyAnimationSettings(payload.animation)
        return true
    }
    function applyCylinderSettings(payload) { return true }

    contentItem: Column {
        spacing: 12
        anchors.fill: parent
        anchors.margins: 12
        Label {
            text: qsTr("Состояние симуляции")
            font.pointSize: 14
            font.bold: true
            color: "#f0f6ff"
        }
        Rectangle {
            radius: 12
            color: simulationRunning ? "#1d7c36" : "#5d2020"
            border.color: Qt.rgba(1, 1, 1, 0.1)
            height: 64
            width: parent.width
            Column {
                anchors.centerIn: parent
                spacing: 4
                Label {
                    text: qsTr("Статус:")
                    color: "#e0e9ff"
                    font.bold: true
                }
                Label {
                    text: statusText
                    color: "#f4f9ff"
                    font.pointSize: 16
                }
            }
        }
        Label {
            wrapMode: Text.WordWrap
            text: simulationRunning
                ? qsTr("Анимация активна. Скриншот должен показать зелёную панель.")
                : qsTr("Анимация остановлена. Скриншот должен показать красную панель.")
            color: "#c6d4f2"
        }
    }
}
