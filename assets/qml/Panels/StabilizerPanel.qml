import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10

Pane {
    id: root
    property real couplingDiameter: 0.0
    property alias value: couplingSlider.value
    signal couplingChanged(real diameter)

    padding: 12
    width: 320

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        Label {
            text: qsTr("Пневматический стабилизатор")
            font.bold: true
            font.pointSize: 12
        }

        Text {
            text: qsTr("Настройка дросселя между диагоналями позволяет управлять скоростью выравнивания давления. Значение 0 мм означает полное перекрытие.")
            wrapMode: Text.WordWrap
            color: Qt.rgba(0.85, 0.88, 0.92, 0.9)
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: qsTr("Диаметр (мм)")
                Layout.alignment: Qt.AlignVCenter
            }

            Slider {
                id: couplingSlider
                Layout.fillWidth: true
                from: 0.0
                to: 20.0
                stepSize: 0.1
                value: root.couplingDiameter * 1000.0
                onMoved: {
                    if (root.couplingDiameter !== value / 1000.0) {
                        root.couplingDiameter = value / 1000.0
                        root.couplingChanged(root.couplingDiameter)
                    }
                }
            }

            SpinBox {
                id: couplingSpin
                from: 0.0
                to: 20.0
                stepSize: 0.1
                value: couplingSlider.value
                editable: true
                Layout.preferredWidth: 80
                onValueModified: {
                    couplingSlider.value = value
                    root.couplingDiameter = value / 1000.0
                    root.couplingChanged(root.couplingDiameter)
                }
            }
        }
    }
}
