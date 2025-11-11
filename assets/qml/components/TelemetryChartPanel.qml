import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import QtCharts 6.10

pragma ComponentBehavior: Bound

Item {
    id: root

    required property var telemetryBridge

    property bool panelExpanded: true
    property var metricCatalog: telemetryBridge ? telemetryBridge.metricCatalog : []
    property var metricInfoById: ({})
    property var selectedMetrics: []
    property var seriesMap: ({})
    property var seriesBuffers: ({})
    property real timeWindow: 10
    property bool autoScroll: true
    property real manualScrollPosition: 1.0
    property bool autoScale: true
    property real manualMin: -1.0
    property real manualMax: 1.0
    property bool streamPaused: telemetryBridge ? telemetryBridge.paused : false
    property int updateInterval: telemetryBridge ? telemetryBridge.updateInterval : 1
    property real oldestTimestamp: 0
    property real latestTimestamp: 0
    property int maxSamples: telemetryBridge ? telemetryBridge.maxSamples : 2048

    implicitWidth: 420
    implicitHeight: panelExpanded ? 520 : headerRow.implicitHeight + 24
    visible: telemetryBridge !== null

    Rectangle {
        anchors.fill: parent
        radius: 12
        color: Qt.rgba(0.05, 0.07, 0.12, 0.94)
        border.width: 1
        border.color: Qt.rgba(0.25, 0.65, 0.95, 0.4)
    }

    ListModel {
        id: metricsModel
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10

        RowLayout {
            id: headerRow
            Layout.fillWidth: true

            Label {
                text: qsTr("Телеметрия")
                font.bold: true
                Layout.fillWidth: true
                color: "#e8f0ff"
            }

            ToolButton {
                id: collapseButton
                text: root.panelExpanded ? qsTr("Скрыть") : qsTr("Показать")
                onClicked: root.panelExpanded = !root.panelExpanded
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.panelExpanded
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Switch {
                    id: streamSwitch
                    text: checked ? qsTr("Стрим") : qsTr("Пауза")
                    checked: !root.streamPaused
                    onToggled: {
                        if (root.telemetryBridge)
                            root.telemetryBridge.setPaused(!checked)
                    }
                }

                Button {
                    text: qsTr("Сброс")
                    icon.name: "refresh"
                    onClicked: {
                        if (root.telemetryBridge) {
                            root.telemetryBridge.resetStream()
                            root.refreshSeriesFromBridge()
                        }
                    }
                }

                ComboBox {
                    id: intervalCombo
                    Layout.fillWidth: true
                    textRole: "label"
                    valueRole: "value"
                    model: ListModel {
                        ListElement { label: qsTr("Каждый шаг"); value: 1 }
                        ListElement { label: qsTr("Каждый 2-й"); value: 2 }
                        ListElement { label: qsTr("Каждый 5-й"); value: 5 }
                        ListElement { label: qsTr("Каждый 10-й"); value: 10 }
                        ListElement { label: qsTr("Каждый 20-й"); value: 20 }
                    }
                    onActivated: function(index) {
                        if (!root.telemetryBridge)
                            return
                        const entry = intervalCombo.model.get(index)
                        if (!entry || entry.value === undefined)
                            return
                        root.telemetryBridge.setUpdateInterval(entry.value)
                    }

                    function syncToInterval(current) {
                        var bestIndex = 0
                        for (var i = 0; i < model.count; ++i) {
                            if (model.get(i).value === current) {
                                bestIndex = i
                                break
                            }
                        }
                        currentIndex = bestIndex
                    }

                    Component.onCompleted: syncToInterval(root.updateInterval)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: qsTr("Окно, с")
                    color: "#d0d9ef"
                }

                SpinBox {
                    id: windowSpin
                    from: 1
                    to: 120
                    value: root.timeWindow
                    stepSize: 1
                    onValueChanged: {
                        root.timeWindow = Math.max(1, value)
                        root.updateAxes()
                    }
                }

                CheckBox {
                    id: autoScrollCheck
                    text: qsTr("Автопрокрутка")
                    checked: root.autoScroll
                    onToggled: {
                        root.autoScroll = checked
                        if (checked)
                            root.manualScrollPosition = 1.0
                        root.updateAxes()
                    }
                }

                Slider {
                    id: scrollSlider
                    Layout.fillWidth: true
                    visible: !root.autoScroll
                    enabled: visible
                    from: 0
                    to: 1
                    value: root.manualScrollPosition
                    onValueChanged: {
                        root.manualScrollPosition = value
                        root.updateAxes()
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                CheckBox {
                    id: autoScaleCheck
                    text: qsTr("Автомасштаб Y")
                    checked: root.autoScale
                    onToggled: {
                        root.autoScale = checked
                        root.updateValueAxis()
                    }
                }

                Label {
                    text: qsTr("Мин")
                    enabled: !root.autoScale
                    color: enabled ? "#d0d9ef" : "#808080"
                }

                SpinBox {
                    id: minSpin
                    readonly property int valueScale: 20
                    enabled: !root.autoScale
                    from: Math.round(-1000000 * valueScale)
                    to: Math.round((root.manualMax - 0.0001) * valueScale)
                    stepSize: Math.max(1, Math.round(0.05 * valueScale))
                    value: Math.round(root.manualMin * valueScale)
                    textFromValue: function(value, locale) {
                        return Number(value / valueScale).toLocaleString(Qt.locale(), { maximumFractionDigits: 2, minimumFractionDigits: 2 })
                    }
                    valueFromText: function(text, locale) {
                        var numeric = Number(text)
                        return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                    }
                    onValueChanged: {
                        root.manualMin = value / valueScale
                        root.updateValueAxis()
                    }
                }

                Label {
                    text: qsTr("Макс")
                    enabled: !root.autoScale
                    color: enabled ? "#d0d9ef" : "#808080"
                }

                SpinBox {
                    id: maxSpin
                    readonly property int valueScale: 20
                    enabled: !root.autoScale
                    from: Math.round((root.manualMin + 0.0001) * valueScale)
                    to: Math.round(1000000 * valueScale)
                    stepSize: Math.max(1, Math.round(0.05 * valueScale))
                    value: Math.round(root.manualMax * valueScale)
                    textFromValue: function(value, locale) {
                        return Number(value / valueScale).toLocaleString(Qt.locale(), { maximumFractionDigits: 2, minimumFractionDigits: 2 })
                    }
                    valueFromText: function(text, locale) {
                        var numeric = Number(text)
                        return Number.isFinite(numeric) ? Math.round(numeric * valueScale) : value
                    }
                    onValueChanged: {
                        root.manualMax = value / valueScale
                        root.updateValueAxis()
                    }
                }
            }

            GroupBox {
                title: qsTr("Показатели")
                Layout.fillWidth: true
                Layout.preferredHeight: 150

                ScrollView {
                    anchors.fill: parent
                    clip: true

                    ListView {
                        id: metricsView
                        anchors.fill: parent
                        model: metricsModel
                        delegate: CheckDelegate {
                            id: metricDelegate
                            required property string metricId
                            required property string label
                            required property string unit
                            required property color metricColor
                            implicitWidth: {
                                const view = ListView.view
                                const fallbackParent = parent && parent.width !== undefined ? parent.width : 0
                                const baseWidth = view && view.width !== undefined ? view.width : fallbackParent
                                const numericWidth = Number(baseWidth)
                                return isNaN(numericWidth) ? 0 : Math.round(numericWidth)
                            }
                            text: label + " (" + unit + ")"
                            checked: root.selectedMetrics.indexOf(metricId) !== -1
                            indicator: Rectangle {
                                implicitWidth: 12
                                implicitHeight: 12
                                radius: 6
                                color: metricDelegate.metricColor
                                border.width: 1
                                border.color: Qt.darker(metricDelegate.metricColor, 1.6)
                            }
                            onToggled: {
                                if (checked)
                                    root.addMetric(metricId)
                                else
                                    root.removeMetric(metricId)
                            }
                        }
                    }
                }
            }

            Frame {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                ChartView {
                    id: chartView
                    anchors.fill: parent
                    antialiasing: true
                    legend.visible: true
                    legend.alignment: Qt.AlignBottom
                    backgroundRoundness: 8
                    backgroundColor: Qt.rgba(0.08, 0.1, 0.15, 0.9)
                    theme: ChartView.ChartThemeDark
                    animationOptions: ChartView.NoAnimation

                    ValueAxis {
                        id: timeAxis
                        min: 0
                        max: root.timeWindow
                        titleText: qsTr("Время, с")
                        labelFormat: "%.1f"
                    }

                    ValueAxis {
                        id: valueAxis
                        min: -1
                        max: 1
                        titleText: qsTr("Значение")
                        labelFormat: "%.3f"
                    }
                }
            }
        }
    }

    Connections {
        target: root.telemetryBridge
        enabled: root.telemetryBridge !== null

        function onMetricsChanged() {
            root.rebuildMetricCatalog()
        }

        function onActiveMetricsChanged() {
            root.syncSelectionFromBridge()
        }

        function onPausedChanged() {
            root.streamPaused = root.telemetryBridge.paused
            streamSwitch.checked = !root.streamPaused
        }

        function onUpdateIntervalChanged() {
            root.updateInterval = root.telemetryBridge.updateInterval
            intervalCombo.syncToInterval(root.updateInterval)
        }

        function onSampleAppended(sample) {
            root.handleSample(sample)
        }

        function onStreamReset() {
            root.resetPanel()
        }
    }

    onTelemetryBridgeChanged: {
        root.rebuildMetricCatalog()
        root.syncSelectionFromBridge()
        if (intervalCombo)
            intervalCombo.syncToInterval(root.updateInterval)
    }

    onAutoScaleChanged: root.updateValueAxis()
    onTimeWindowChanged: root.updateAxes()

    function rebuildMetricCatalog() {
        metricsModel.clear()
        metricInfoById = ({})
        seriesBuffers = ({})
        if (!root.metricCatalog)
            return
        for (var i = 0; i < root.metricCatalog.length; ++i) {
            var entry = root.metricCatalog[i]
            metricInfoById[entry.id] = entry
            metricsModel.append({
                metricId: entry.id,
                label: entry.label,
                unit: entry.unit,
                category: entry.category,
                metricColor: entry.color,
            })
        }
    }

    function syncSelectionFromBridge() {
        if (!root.telemetryBridge)
            return
        var active = root.telemetryBridge.activeMetrics || []
        var changed = false
        if (active.length !== root.selectedMetrics.length)
            changed = true
        else {
            for (var i = 0; i < active.length; ++i) {
                if (root.selectedMetrics[i] !== active[i]) {
                    changed = true
                    break
                }
            }
        }
        if (changed)
            root.selectedMetrics = active.slice(0)
        root.streamPaused = root.telemetryBridge.paused
        root.updateInterval = root.telemetryBridge.updateInterval
        intervalCombo.syncToInterval(root.updateInterval)
        streamSwitch.checked = !root.streamPaused
        root.refreshSeriesFromBridge()
    }

    function addMetric(metricId) {
        if (!metricId)
            return
        if (root.selectedMetrics.indexOf(metricId) !== -1)
            return
        var updated = root.selectedMetrics.slice(0)
        updated.push(metricId)
        root.selectedMetrics = updated
        if (root.telemetryBridge)
            root.telemetryBridge.setActiveMetrics(root.selectedMetrics)
        root.refreshSeriesFromBridge()
    }

    function removeMetric(metricId) {
        var index = root.selectedMetrics.indexOf(metricId)
        if (index === -1)
            return
        var updated = root.selectedMetrics.slice(0)
        updated.splice(index, 1)
        root.selectedMetrics = updated
        if (root.telemetryBridge)
            root.telemetryBridge.setActiveMetrics(root.selectedMetrics)
        root.refreshSeriesFromBridge()
    }

    function refreshSeriesFromBridge() {
        if (!root.telemetryBridge) {
            root.resetPanel()
            return
        }
        var response = root.telemetryBridge.exportSeries(root.selectedMetrics)
        root.oldestTimestamp = Number(response.oldestTimestamp || 0)
        root.latestTimestamp = Number(response.latestTimestamp || 0)
        var payload = response.series || {}
        root.seriesBuffers = ({})

        for (var metric in payload) {
            var entries = payload[metric]
            var buffer = []
            for (var i = 0; i < entries.length; ++i) {
                var point = entries[i]
                buffer.push([Number(point.timestamp), Number(point.value)])
            }
            root.seriesBuffers[metric] = buffer
        }
        for (var j = 0; j < root.selectedMetrics.length; ++j) {
            var selectedId = root.selectedMetrics[j]
            if (!root.seriesBuffers[selectedId])
                root.seriesBuffers[selectedId] = []
        }
        root.dropUnusedSeries()
        for (var i = 0; i < root.selectedMetrics.length; ++i)
            root.updateSeries(root.selectedMetrics[i])
        if (root.selectedMetrics.length === 1) {
            var descriptor = root.metricInfoById[root.selectedMetrics[0]]
            if (descriptor && descriptor.rangeHint && descriptor.rangeHint.length === 2) {
                root.manualMin = Number(descriptor.rangeHint[0])
                root.manualMax = Number(descriptor.rangeHint[1])
                if (minSpin)
                    minSpin.value = root.manualMin
                if (maxSpin)
                    maxSpin.value = root.manualMax
            }
        }
        root.updateAxes()
        root.updateValueAxis()
    }

    function dropUnusedSeries() {
        for (var metricId in root.seriesMap) {
            if (root.selectedMetrics.indexOf(metricId) === -1) {
                var obsolete = root.seriesMap[metricId]
                chartView.removeSeries(obsolete)
                delete root.seriesMap[metricId]
            }
        }
    }

    function ensureSeries(metricId) {
        var descriptor = root.metricInfoById[metricId]
        if (!descriptor)
            return null
        var existing = root.seriesMap[metricId]
        if (existing)
            return existing
        var label = descriptor.label + " (" + descriptor.unit + ")"
        var created = chartView.createSeries(
            ChartView.SeriesTypeLine,
            label,
            timeAxis,
            valueAxis,
        )
        created.color = descriptor.color
        created.useOpenGL = true
        created.width = 2
        root.seriesMap[metricId] = created
        return created
    }

    function updateSeries(metricId) {
        var buffer = root.seriesBuffers[metricId]
        if (!buffer || buffer.length === 0) {
            var emptySeries = root.seriesMap[metricId]
            if (emptySeries)
                emptySeries.clear()
            return
        }
        var series = root.ensureSeries(metricId)
        if (!series)
            return
        var points = []
        for (var i = 0; i < buffer.length; ++i) {
            points.push(Qt.point(buffer[i][0], buffer[i][1]))
        }
        series.replace(points)
    }

    function handleSample(sample) {
        if (!sample)
            return
        if (sample.latestTimestamp !== undefined)
            root.latestTimestamp = Number(sample.latestTimestamp)
        else
            root.latestTimestamp = Number(sample.timestamp || root.latestTimestamp)
        if (sample.oldestTimestamp !== undefined)
            root.oldestTimestamp = Number(sample.oldestTimestamp)
        var timestamp = Number(sample.timestamp || root.latestTimestamp)
        var values = sample.values || {}
        var updatedMetrics = []
        for (var metricId in values) {
            if (root.selectedMetrics.indexOf(metricId) === -1)
                continue
            var buffer = root.seriesBuffers[metricId]
            if (!buffer)
                buffer = []
            buffer.push([timestamp, Number(values[metricId])])
            if (buffer.length > root.maxSamples)
                buffer.splice(0, buffer.length - root.maxSamples)
            root.seriesBuffers[metricId] = buffer
            updatedMetrics.push(metricId)
        }
        if (!root.panelExpanded)
            return
        for (var i = 0; i < updatedMetrics.length; ++i)
            root.updateSeries(updatedMetrics[i])
        root.updateAxes()
        root.updateValueAxis()
    }

    function updateAxes() {
        var windowSize = Math.max(1, root.timeWindow)
        if (root.latestTimestamp <= 0 && root.oldestTimestamp <= 0) {
            timeAxis.min = 0
            timeAxis.max = windowSize
            return
        }
        if (root.autoScroll) {
            var end = Math.max(windowSize, root.latestTimestamp)
            timeAxis.max = end
            timeAxis.min = Math.max(0, end - windowSize)
            root.manualScrollPosition = 1.0
        } else {
            var span = Math.max(0, root.latestTimestamp - root.oldestTimestamp)
            if (span <= windowSize) {
                var start = Math.max(0, root.oldestTimestamp)
                timeAxis.min = start
                timeAxis.max = start + windowSize
            } else {
                var offset = span - windowSize
                var position = Math.min(1.0, Math.max(0.0, root.manualScrollPosition))
                var startValue = root.oldestTimestamp + offset * position
                timeAxis.min = startValue
                timeAxis.max = startValue + windowSize
            }
        }
    }

    function updateValueAxis() {
        if (root.autoScale)
            root.autoScaleAxis()
        else
            root.applyManualScale()
    }

    function autoScaleAxis() {
        var minValue = Number.POSITIVE_INFINITY
        var maxValue = Number.NEGATIVE_INFINITY
        for (var i = 0; i < root.selectedMetrics.length; ++i) {
            var metricId = root.selectedMetrics[i]
            var buffer = root.seriesBuffers[metricId]
            if (!buffer || buffer.length === 0)
                continue
            for (var j = 0; j < buffer.length; ++j) {
                var value = buffer[j][1]
                if (value < minValue)
                    minValue = value
                if (value > maxValue)
                    maxValue = value
            }
        }
        if (minValue === Number.POSITIVE_INFINITY) {
            minValue = -1
            maxValue = 1
        }
        if (minValue === maxValue) {
            var delta = Math.abs(minValue) * 0.1 + 1e-6
            minValue -= delta
            maxValue += delta
        }
        var margin = (maxValue - minValue) * 0.1
        valueAxis.min = minValue - margin
        valueAxis.max = maxValue + margin
    }

    function applyManualScale() {
        if (root.manualMax <= root.manualMin) {
            root.manualMax = root.manualMin + 0.001
        }
        valueAxis.min = root.manualMin
        valueAxis.max = root.manualMax
    }

    function resetPanel() {
        root.oldestTimestamp = 0
        root.latestTimestamp = 0
        root.seriesBuffers = ({})
        for (var metricId in root.seriesMap) {
            var series = root.seriesMap[metricId]
            series.clear()
        }
        root.updateAxes()
        root.updateValueAxis()
    }

    Component.onCompleted: {
        root.rebuildMetricCatalog()
        root.syncSelectionFromBridge()
        root.updateAxes()
        root.updateValueAxis()
    }

    onPanelExpandedChanged: {
        if (root.panelExpanded)
            root.refreshSeriesFromBridge()
    }
}
