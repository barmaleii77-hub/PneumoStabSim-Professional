import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ColumnLayout {
    id: root

    property var tonemapPresets: []
    property string activePresetId: ""

    signal presetActivated(string presetId)

    spacing: 12
    Layout.fillWidth: true

    Label {
        text: qsTr("Tonemapping presets")
        font.bold: true
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }

    Repeater {
        model: tonemapPresets

        delegate: Button {
            id: presetButton

            readonly property string tooltipText: modelData.descriptionKey ? qsTrId(modelData.descriptionKey) : ""

            text: modelData.labelKey ? qsTrId(modelData.labelKey) : modelData.id
            checkable: true
            checked: modelData.id === root.activePresetId
            Layout.fillWidth: true

            onClicked: root.presetActivated(modelData.id)

            ToolTip.visible: hovered && tooltipText.length > 0
            ToolTip.delay: 200
            ToolTip.text: tooltipText
        }
    }

    Label {
        text: qsTr("No tonemapping presets configured")
        visible: tonemapPresets.length === 0
        color: palette.mid
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }
}
