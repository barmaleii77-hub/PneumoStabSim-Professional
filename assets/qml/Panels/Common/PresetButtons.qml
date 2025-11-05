import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Panels.Common 1.0 as PanelsCommon

ColumnLayout {
    id: root

    property string title: qsTr("Presets")
    property string emptyText: qsTr("No presets available")
    property var model: []
    property string activePresetId: ""
    property var undoController: null

    signal presetActivated(string presetId)

    spacing: 12
    Layout.fillWidth: true

    PanelsCommon.UndoRedoControls {
        id: undoControls
        visible: !!root.undoController
        controller: root.undoController
        Layout.alignment: Qt.AlignLeft
    }

    Label {
        id: headerLabel
        text: root.title
        font.bold: true
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }

    Repeater {
        model: root.model

        delegate: Button {
            id: presetButton

            readonly property string presetId: modelData.id || ""
            readonly property string tooltipText: modelData.descriptionKey ? qsTrId(modelData.descriptionKey) : (modelData.description || "")

            text: modelData.labelKey ? qsTrId(modelData.labelKey) : (modelData.label || presetId)
            checkable: true
            checked: presetId.length > 0 && presetId === root.activePresetId
            Layout.fillWidth: true

            onClicked: {
                if (!presetId.length)
                    return
                root.presetActivated(presetId)
            }

            ToolTip.visible: hovered && tooltipText.length > 0
            ToolTip.delay: 200
            ToolTip.text: tooltipText
        }
    }

    Label {
        text: root.emptyText
        visible: !root.model || root.model.length === 0
        color: palette.mid
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }
}
