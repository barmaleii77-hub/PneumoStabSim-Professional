import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10

Item {
    id: root

    implicitWidth: layout.implicitWidth
    implicitHeight: layout.implicitHeight

    property string title: qsTr("Резервуар давления")
    property real pressure: 0.0
    property real minPressure: 0.0
    property real maxPressure: 250000.0
    property real userMinPressure: minPressure
    property real userMaxPressure: maxPressure
    property real atmosphericPressure: 101325.0
    property real reservoirPressure: pressure

    readonly property real effectiveMinimum: _minValue(_rangeCandidates(), 0.0)
    readonly property real effectiveMaximum: _maxValue(_rangeCandidates(), 1.0)
    readonly property bool hasValidRange: effectiveMaximum > effectiveMinimum
    readonly property real normalizedPressure: hasValidRange ? _normalize(pressure) : 0.0

    signal pressureChangedExternally(real value)

    function _rangeCandidates() {
        var values = []
        function push(value) {
            var numeric = Number(value)
            if (Number.isFinite(numeric))
                values.push(numeric)
        }
        push(minPressure)
        push(maxPressure)
        push(userMinPressure)
        push(userMaxPressure)
        push(atmosphericPressure)
        push(reservoirPressure)
        if (values.length === 0) {
            values.push(0.0)
            values.push(1.0)
        } else if (values.length === 1) {
            values.push(values[0] + 1.0)
        }
        return values
    }

    function _minValue(values, fallback) {
        if (!values.length)
            return fallback
        var min = values[0]
        for (var i = 1; i < values.length; ++i) {
            if (values[i] < min)
                min = values[i]
        }
        return min
    }

    function _maxValue(values, fallback) {
        if (!values.length)
            return fallback
        var max = values[0]
        for (var i = 1; i < values.length; ++i) {
            if (values[i] > max)
                max = values[i]
        }
        return max
    }

    function _normalize(value) {
        var min = effectiveMinimum
        var max = effectiveMaximum
        if (!hasValidRange)
            return 0.0
        var numeric = Number(value)
        if (!Number.isFinite(numeric))
            numeric = min
        var ratio = (numeric - min) / (max - min)
        if (!Number.isFinite(ratio))
            ratio = 0.0
        if (ratio < 0.0)
            ratio = 0.0
        else if (ratio > 1.0)
            ratio = 1.0
        return ratio
    }

    ColumnLayout {
        id: layout
        anchors.fill: parent
        spacing: 12

        Label {
            id: titleLabel
            text: root.title
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 18
            color: "#f1f3f7"
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            PressureScale {
                id: scale
                Layout.preferredWidth: 120
                Layout.fillHeight: true
                minPressure: root.minPressure
                maxPressure: root.maxPressure
                userMinPressure: root.userMinPressure
                userMaxPressure: root.userMaxPressure
                atmosphericPressure: root.atmosphericPressure
                pressure: root.pressure
                tickCount: 6
            }

            Reservoir {
                id: reservoirView
                Layout.fillWidth: true
                Layout.fillHeight: true
                minPressure: root.minPressure
                maxPressure: root.maxPressure
                userMinPressure: root.userMinPressure
                userMaxPressure: root.userMaxPressure
                atmosphericPressure: root.atmosphericPressure
                pressure: root.reservoirPressure
            }
        }

        Label {
            id: rangeLabel
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            color: "#cdd6e5"
            text: {
                if (!root.hasValidRange)
                    return qsTr("Недостаточно данных для нормализации")
                var locale = Qt.locale()
                var minText = Number(root.effectiveMinimum).toLocaleString(locale, { maximumFractionDigits: 0, minimumFractionDigits: 0 })
                var maxText = Number(root.effectiveMaximum).toLocaleString(locale, { maximumFractionDigits: 0, minimumFractionDigits: 0 })
                return qsTr("Диапазон: %1 – %2 Па").arg(minText).arg(maxText)
            }
        }
    }

    onPressureChanged: pressureChangedExternally(pressure)
}
