import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10

ColumnLayout {
    id: root

    property string labelText: ""
    property string settingsKey: ""
    property real value: 0
    property real from: 0
    property real to: 1
    property real stepSize: 0.1
    property int decimals: 2
    property string unit: ""
    property string helperText: ""

    readonly property bool hasError: errorLabel.visible

    signal valueCommitted(string settingsKey, real value)
    signal validationFailed(string settingsKey, string reason)

    spacing: 4
    Layout.fillWidth: true

    function _clampValue(rawValue) {
        var numeric = Number(rawValue)
        if (!Number.isFinite(numeric))
            return null
        var clamped = Math.min(Math.max(numeric, root.from), root.to)
        var rounded = Number(clamped.toFixed(Math.max(0, root.decimals)))
        return rounded
    }

    Label {
        text: root.unit.length > 0 ? `${root.labelText} (${root.unit})` : root.labelText
        font.bold: true
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8

        SpinBox {
            id: input
            Layout.fillWidth: true
            from: root.from
            to: root.to
            stepSize: root.stepSize
            value: root.value
            editable: true
            validator: DoubleValidator { bottom: root.from; top: root.to; decimals: root.decimals }
            textFromValue: function(value, locale) {
                return Number(value).toLocaleString(Qt.locale(), {
                    maximumFractionDigits: root.decimals,
                    minimumFractionDigits: root.decimals
                })
            }
            valueFromText: function(text, locale) {
                var numeric = Number(text)
                return Number.isFinite(numeric) ? numeric : value
            }
            onValueModified: {
                var nextValue = root._clampValue(value)
                if (nextValue === null) {
                    errorLabel.text = qsTr("Введите числовое значение")
                    errorLabel.visible = true
                    root.validationFailed(root.settingsKey, errorLabel.text)
                    return
                }
                errorLabel.visible = false
                root.value = nextValue
                if (root.settingsKey && root.settingsKey.length > 0) {
                    root.valueCommitted(root.settingsKey, nextValue)
                }
            }
        }

        Label {
            text: root.unit
            visible: root.unit.length > 0
            Layout.alignment: Qt.AlignVCenter
            color: Qt.rgba(0.82, 0.86, 0.93, 0.9)
        }
    }

    Label {
        id: helperLabel
        text: root.helperText
        visible: helperText.length > 0 && !errorLabel.visible
        color: Qt.rgba(0.78, 0.83, 0.91, 0.8)
        font.pointSize: 9
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }

    Label {
        id: errorLabel
        text: ""
        visible: false
        color: "#ff6b6b"
        font.pointSize: 9
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }
}
