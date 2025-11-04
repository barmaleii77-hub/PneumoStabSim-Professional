import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

RowLayout {
    id: root

    property var controller: null

    spacing: 8
    Layout.alignment: Qt.AlignLeft

    Button {
        id: undoButton
        text: qsTr("Undo")
        enabled: controller && controller.canUndo
        onClicked: if (controller) controller.undo()
        Layout.preferredWidth: 96
        ToolTip.visible: hovered && enabled
        ToolTip.text: qsTr("Revert the most recent panel change")
    }

    Button {
        id: redoButton
        text: qsTr("Redo")
        enabled: controller && controller.canRedo
        onClicked: if (controller) controller.redo()
        Layout.preferredWidth: 96
        ToolTip.visible: hovered && enabled
        ToolTip.text: qsTr("Re-apply the last reverted change")
    }

    Shortcut {
        sequences: [ StandardKey.Undo ]
        enabled: controller && controller.canUndo
        onActivated: controller.undo()
    }

    Shortcut {
        sequences: [ StandardKey.Redo ]
        enabled: controller && controller.canRedo
        onActivated: controller.redo()
    }
}
