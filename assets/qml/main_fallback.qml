import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    anchors.fill: parent
    color: "#2a2a2a"
    
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