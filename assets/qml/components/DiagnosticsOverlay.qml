import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import "."

Item {
    id: root

    // ===========================================================
    // PUBLIC STATE
    // ===========================================================

    property bool traceOverlayVisible: false
    property bool recordingEnabled: false
    property bool panelExpanded: false
    property int historyLimit: 200
    property var historyEntries: []
    property bool clearEnabled: false
    property var profileService: null
    property string overlayLabel: qsTr("Сигналы")

    signal overlayToggled(bool enabled)
    signal recordingToggled(bool enabled)
    signal panelVisibilityToggled(bool expanded)
    signal clearHistoryRequested()

    readonly property bool hasProfiles: profileService !== null

    visible: traceOverlayVisible || hasProfiles
    anchors.fill: parent

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        hoverEnabled: true
    }

    ProfileManagerControls {
        id: profileControls
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: 12
        profileService: root.profileService
        visible: root.hasProfiles
    }

    Rectangle {
        id: signalTraceContainer
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 12
        width: 360
        visible: root.traceOverlayVisible || opacity > 0.01
        opacity: root.traceOverlayVisible ? 1 : 0
        radius: 10
        color: Qt.rgba(0.08, 0.1, 0.14, 0.92)
        border.width: 1
        border.color: Qt.rgba(0.25, 0.65, 0.95, 0.4)

        Behavior on opacity {
            NumberAnimation {
                duration: 160
                easing.type: Easing.InOutQuad
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            SignalTraceIndicator {
                id: traceIndicator
                Layout.fillWidth: true
                label: root.overlayLabel
                count: root.historyEntries ? root.historyEntries.length : 0
                pulseOnChange: root.recordingEnabled
                backgroundColor: Qt.rgba(0.05, 0.07, 0.11, 0.95)
                accentColor: root.recordingEnabled
                    ? Qt.rgba(0.2, 0.75, 0.5, 1)
                    : Qt.rgba(0.5, 0.5, 0.5, 1)
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Switch {
                    id: overlaySwitch
                    text: qsTr("Оверлей")
                    checked: root.traceOverlayVisible
                    Layout.alignment: Qt.AlignLeft
                    onToggled: root.overlayToggled(checked)
                }

                Switch {
                    id: recordingSwitch
                    text: qsTr("Запись")
                    checked: root.recordingEnabled
                    Layout.alignment: Qt.AlignLeft
                    onToggled: root.recordingToggled(checked)
                }

                ToolButton {
                    text: root.panelExpanded ? qsTr("Скрыть") : qsTr("Показать")
                    enabled: root.traceOverlayVisible
                    Layout.alignment: Qt.AlignRight
                    onClicked: root.panelVisibilityToggled(!root.panelExpanded)
                }

                ToolButton {
                    text: qsTr("Очистить")
                    enabled: root.clearEnabled
                    Layout.alignment: Qt.AlignRight
                    onClicked: root.clearHistoryRequested()
                }
            }

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: root.recordingEnabled ? "#a5e6c8" : "#c0c0c0"
                text: root.recordingEnabled
                    ? qsTr("Запись сигналов активна")
                    : qsTr("Запись сигналов отключена")
            }

            SignalTracePanel {
                id: tracePanel
                Layout.fillWidth: true
                Layout.preferredHeight: root.panelExpanded ? 240 : 0
                visible: root.panelExpanded
                maxEntries: root.historyLimit
                onClearRequested: root.clearHistoryRequested()
            }
        }
    }

    onHistoryEntriesChanged: tracePanel.reset(historyEntries)
    onHistoryLimitChanged: {
        tracePanel.maxEntries = historyLimit
        tracePanel.reset(historyEntries)
    }

    Component.onCompleted: {
        tracePanel.maxEntries = historyLimit
        tracePanel.reset(historyEntries)
    }
}
