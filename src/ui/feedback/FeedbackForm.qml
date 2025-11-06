import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10

Item {
    id: root
    width: 420
    implicitWidth: 420
    implicitHeight: 520

    property alias titleText: titleField.text
    property alias descriptionText: descriptionField.text
    property alias categoryText: categoryField.currentText
    property alias severityText: severityField.currentText
    property alias contactText: contactField.text

    // Контроллер прокидывается из Python через свойство root.controller
    property var controller: null

    property bool busy: false
    property string statusMessage: ""

    function resetForm() {
        titleField.text = ""
        descriptionField.text = ""
        categoryField.currentIndex = 0
        severityField.currentIndex = 1
        contactField.text = ""
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            text: qsTr("Отправка отчёта")
            font.pixelSize: 20
            Layout.alignment: Qt.AlignHCenter
        }

        TextField {
            id: titleField
            placeholderText: qsTr("Краткий заголовок")
            Layout.fillWidth: true
        }

        ComboBox {
            id: categoryField
            Layout.fillWidth: true
            model: [qsTr("Стабильность"), qsTr("Графика"), qsTr("Управление"), qsTr("Другое")]
        }

        ComboBox {
            id: severityField
            Layout.fillWidth: true
            model: [qsTr("Низкая"), qsTr("Средняя"), qsTr("Высокая"), qsTr("Блокер")]
            currentIndex: 1
        }

        TextArea {
            id: descriptionField
            placeholderText: qsTr("Подробное описание, шаги воспроизведения, ожидаемый результат")
            Layout.fillWidth: true
            Layout.preferredHeight: 200
            wrapMode: Text.Wrap
        }

        TextField {
            id: contactField
            placeholderText: qsTr("Контакт для обратной связи (опционально)")
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true

            Button {
                text: root.busy ? qsTr("Отправка...") : qsTr("Отправить")
                enabled: !root.busy && titleField.text.length > 0 && descriptionField.text.length > 10
                Layout.fillWidth: true
                onClicked: {
                    root.busy = true
                    root.statusMessage = ""
                    const metadata = {
                        platform: Qt.platform.os,
                        qtVersion: Qt.platform.pluginName,
                        locale: Qt.locale().name
                    }
                    const response = root.controller ? root.controller.submitFeedback(
                        titleField.text,
                        descriptionField.text,
                        categoryField.currentText,
                        severityField.currentText,
                        contactField.text,
                        metadata
                    ) : { ok: false, error: "controller unavailable" }
                    if (response.ok) {
                        root.statusMessage = qsTr("✅ Отчёт сохранён: %1").arg(response.submission_id)
                        root.resetForm()
                    } else {
                        root.statusMessage = qsTr("❌ Ошибка: %1").arg(response.error)
                    }
                    root.busy = false
                }
            }

            Button {
                text: qsTr("Очистить")
                Layout.preferredWidth: 110
                enabled: !root.busy
                onClicked: {
                    root.resetForm()
                    root.statusMessage = ""
                }
            }
        }

        Label {
            text: root.statusMessage
            color: root.statusMessage.startsWith("✅") ? "#1b5e20" : "#b71c1c"
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            visible: root.statusMessage.length > 0
        }

        Item { Layout.fillHeight: true }
    }
}

