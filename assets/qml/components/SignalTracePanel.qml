import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Control {
    id: root
    property alias model: traceList.model
    property bool autoScroll: true
    property int maxEntries: 200
    property color backgroundColor: Qt.rgba(0.1, 0.1, 0.12, 0.9)
    property color textColor: "#f0f0f0"
    property string title: qsTr("Signal trace")
    signal clearRequested()

    contentItem: ColumnLayout {
     spacing: 8
    anchors.fill: parent

        ToolBar {
          Layout.fillWidth: true
     background: Rectangle {
       color: Qt.rgba(0.18, 0.18, 0.2, 0.95)
            }

            RowLayout {
       anchors.fill: parent
                Label {
Layout.fillWidth: true
          text: root.title
         color: root.textColor
  font.bold: true
            }

  ToolButton {
    text: qsTr("Clear")
  onClicked: {
           root.clear()
        root.clearRequested()
   }
  }
  }
        }

   ListView {
            id: traceList
            Layout.fillWidth: true
            Layout.fillHeight: true
      clip: true
      spacing: 4
            model: ListModel {}

            delegate: Rectangle {
        width: ListView.view.width
      color: index % 2 === 0 ? Qt.rgba(0.14, 0.14, 0.18, 0.9)
          : Qt.rgba(0.16, 0.16, 0.2, 0.9)
     radius: 4
          border.width: 0
      implicitHeight: Math.max(32, entryColumn.implicitHeight + 8)

                Column {
        id: entryColumn
         anchors.fill: parent
            anchors.margins: 8
   spacing: 2

  Text {
   text: `${timestamp} — <b>${signal}</b> (${sender})`
     color: root.textColor
       font.bold: true
      textFormat: Text.RichText
        wrapMode: Text.WrapAnywhere
          }

         Text {
              text: args.join(", ")
  visible: args && args.length > 0
       color: Qt.rgba(0.7, 0.7, 0.75, 1)
            font.family: "Monospace"
      wrapMode: Text.WrapAnywhere
          }
      }
            }

            onCountChanged: {
        if (count > root.maxEntries) {
       const diff = count - root.maxEntries
    for (let i = 0; i < diff; i++) {
             model.remove(0)
   }
         }
if (root.autoScroll && count > 0) {
       positionViewAtEnd()
      }
     }
        }
    }

    background: Rectangle {
      color: root.backgroundColor
      radius: 8
    }

    function appendTrace(trace) {
        if (!trace) {
  return
        }
     model.append({
      timestamp: trace.timestamp || "",
       sender: trace.sender || "",
            signal: trace.signal || "",
  args: trace.args || []
        })
    }

    function clear() {
        model.clear()
    }

    function reset(traces) {
        clear()
     if (!traces) {
return
        }
        for (let i = 0; i < traces.length; ++i) {
    appendTrace(traces[i])
        }
    }
}
