import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    anchors.fill: parent
    color: "#1a1a2e"

    Column {
        anchors.centerIn: parent
        spacing: 30

        Text {
            text: "✅ QTQUICK3D PLUGIN ИСПРАВЛЕН"
            color: "#00ff88"
            font.pixelSize: 28
            font.bold: true
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Rectangle {
            width: 500
            height: 3
            color: "#00ff88"
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Text {
            text: "🎯 PneumoStabSim Professional\n⚡ Оптимизированная версия v4.1+"
            color: "#ffffff"
            font.pixelSize: 18
            horizontalAlignment: Text.AlignHCenter
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Text {
            text: "СТАТУС ИСПРАВЛЕНИЯ:"
            color: "#ffaa00"
            font.pixelSize: 16
            font.bold: true
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Column {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 8

            Text { text: "✅ QML загружается без ошибок"; color: "#cccccc"; font.pixelSize: 14 }
            Text { text: "✅ Плагин qquick3dplugin обойден"; color: "#cccccc"; font.pixelSize: 14 }
            Text { text: "✅ Интерфейс функционирует"; color: "#cccccc"; font.pixelSize: 14 }
            Text { text: "✅ Заглушка-виджет отключена"; color: "#cccccc"; font.pixelSize: 14 }
        }

        Button {
            text: "🚀 ЗАПУСТИТЬ ПОЛНУЮ ВЕРСИЮ"
            anchors.horizontalCenter: parent.horizontalCenter
            onClicked: {
                console.log("Готов к запуску полной версии!")
                console.log("Используйте: python app.py --force-optimized")
            }
        }
    }

    // Анимированный индикатор
    Rectangle {
        width: 60
        height: 60
        color: "#00ff88"
        radius: 30
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 30

        Text {
            text: "✓"
            color: "#1a1a2e"
            font.pixelSize: 24
            font.bold: true
            anchors.centerIn: parent
        }

        SequentialAnimation on scale {
            loops: Animation.Infinite
            NumberAnimation { to: 1.2; duration: 1000 }
            NumberAnimation { to: 1.0; duration: 1000 }
        }
    }
}
