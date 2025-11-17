import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
// PySide 6.7 reports mismatched revision metadata for QtCharts' qmllint types.
// See https://bugreports.qt.io/browse/PYSIDE-2268 — suppress the noisy warning.
// qmllint disable import
import QtCharts 6.10
// qmllint enable import

pragma ComponentBehavior: Bound

Item {
    id: root

    property var telemetryBridge: null

    property bool panelExpanded: true
    property var metricCatalog: telemetryBridge ? telemetryBridge.metricCatalog : []
    property var metricDescriptorById: ({})
    property var metricInfoById: ({})
    property var selectedMetrics: telemetryBridge ? telemetryBridge.activeMetrics : []
    property var seriesMap: ({})
    property var seriesBuffers: ({})
    property var buffersJs: ({})
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

    readonly property alias metricsModelItem: metricsModel
    readonly property alias intervalComboControl: intervalCombo
    readonly property alias streamSwitchControl: streamSwitch
    readonly property alias minSpinControl: minSpin
    readonly property alias maxSpinControl: maxSpin
    readonly property alias chartViewItem: chartView
    readonly property alias timeAxisItem: timeAxis
    readonly property alias valueAxisItem: valueAxis

    implicitWidth: 420
    implicitHeight: panelExpanded ? 520 : headerRow.implicitHeight + 24
    visible: true

    // Хелпер для безопасной работы с QVariantList/QJSValue как с JS-массивом
    function asArray(value) {
        var result = []
        var n = value && value.length !== undefined ? Number(value.length) : 0
        for (var i = 0; i < n; ++i)
            result.push(value[i])
        return result
    }

    Rectangle {
        anchors.fill: parent
        radius: 12
        color: Qt.rgba(0.05, 0.07, 0.12, 0.94)
        border.width: 1
        border.color: Qt.rgba(0.25, 0.65, 0.95, 0.4)
    }

    ListModel { id: metricsModel }

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
                        var listModel = intervalCombo.model
                        var modelCount = listModel ? listModel.count : 0
                        for (var i = 0; i < modelCount; ++i) {
                            var candidate = listModel.get(i)
                            if (candidate && candidate.value === current) {
                                bestIndex = i
                                break
                            }
                        }
                        intervalCombo.currentIndex = bestIndex
                    }

                    Component.onCompleted: intervalCombo.syncToInterval(root.updateInterval)
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
                                const viewWidth = metricsView && metricsView.width !== undefined ? Number(metricsView.width) : NaN
                                const fallbackWidth = metricDelegate.parent && metricDelegate.parent.width !== undefined
                                    ? Number(metricDelegate.parent.width)
                                    : NaN
                                const baseWidth = Number.isFinite(viewWidth) ? viewWidth : fallbackWidth
                                return Number.isFinite(baseWidth) ? Math.round(baseWidth) : 0
                            }
                            text: label + " (" + unit + ")"
                            checked: (function(){ var arr = root.asArray(root.selectedMetrics); return arr.indexOf(metricId) !== -1; })()
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

        function onMetricsChanged() { root.rebuildMetricCatalog() }
        function onActiveMetricsChanged() { root.syncSelectionFromBridge() }
        function onPausedChanged() { root.streamPaused = root.telemetryBridge.paused; root.streamSwitchControl.checked = !root.streamPaused }
        function onUpdateIntervalChanged() { root.updateInterval = root.telemetryBridge.updateInterval; root.intervalComboControl.syncToInterval(root.updateInterval) }
        function onSampleAppended(sample) { root.handleSample(sample) }
        function onStreamReset() { root.resetPanel() }
    }

    onTelemetryBridgeChanged: {
        root.rebuildMetricCatalog()
        root.syncSelectionFromBridge()
        if (root.intervalComboControl)
            root.intervalComboControl.syncToInterval(root.updateInterval)
    }

    onAutoScaleChanged: root.updateValueAxis()
    onTimeWindowChanged: root.updateAxes()

    function rebuildMetricCatalog() {
        root.metricsModelItem.clear()
        root.metricDescriptorById = ({})
        if (!root.metricCatalog)
            return
        for (var i = 0; i < root.metricCatalog.length; ++i) {
            var entry = root.metricCatalog[i]
            root.metricDescriptorById[entry.id] = entry
            root.metricsModelItem.append({ metricId: entry.id, label: entry.label, unit: entry.unit, category: entry.category, metricColor: entry.color })
        }
        // вместо локальной JS-копии — сразу подтянуть series из моста, чтобы metricInfoById стал Python dict
        if (root.telemetryBridge) root.refreshSeriesFromBridge()
    }

    function syncSelectionFromBridge() {
        if (!root.telemetryBridge)
            return
        root.streamPaused = root.telemetryBridge.paused
        root.updateInterval = root.telemetryBridge.updateInterval
        if (root.intervalComboControl) root.intervalComboControl.syncToInterval(root.updateInterval)
        if (root.streamSwitchControl) root.streamSwitchControl.checked = !root.streamPaused
        root.refreshSeriesFromBridge()
    }

    function addMetric(metricId) {
        if (!metricId || !root.telemetryBridge)
            return
        var active = root.telemetryBridge ? root.telemetryBridge.activeMetrics : []
        var arr = root.asArray(active)
        if (arr.indexOf(metricId) === -1) arr.push(metricId)
        root.telemetryBridge.setActiveMetrics(arr)
    }

    function removeMetric(metricId) {
        if (!root.telemetryBridge)
            return
        var active = root.telemetryBridge ? root.telemetryBridge.activeMetrics : []
        var curr = root.asArray(active)
        var arr = []
        for (var i = 0; i < curr.length; ++i) if (curr[i] !== metricId) arr.push(curr[i])
        root.telemetryBridge.setActiveMetrics(arr)
    }

    function refreshSeriesFromBridge() {
        if (!root.telemetryBridge) { root.resetPanel(); return }
        var ids = root.asArray(root.telemetryBridge.activeMetrics || [])
        var response = root.telemetryBridge.exportSeries(ids)
        root.oldestTimestamp = Number(response.oldestTimestamp || 0)
        root.latestTimestamp = Number(response.latestTimestamp || 0)
        var src = response.series || {}

        // Публикуем исходный QVariantMap (dict на Python-стороне)
        root.metricInfoById = src

        // Конвертируем значения src[key] на месте в массивы пар [t, v]
        for (var key in src) {
            var entries = src[key] || []
            var pairs = []
            var n = entries.length || 0
            for (var i = 0; i < n; ++i) {
                var p = entries[i]
                if (p && p.timestamp !== undefined) pairs.push([Number(p.timestamp), Number(p.value)])
                else if (p && p.length === 2) pairs.push([Number(p[0]), Number(p[1])])
            }
            if (entries.splice) entries.splice(0, entries.length)
            for (var j = 0; j < pairs.length; ++j) entries.push(pairs[j])
            src[key] = entries
        }
        for (var k = 0; k < ids.length; ++k) if (!src[ids[k]]) src[ids[k]] = []

        // seriesBuffers — тот же map, уже с массивами пар
        root.seriesBuffers = src

        // buffersJs синхронизируем
        root.buffersJs = ({})
        for (var m in src) root.buffersJs[m] = src[m]

        root.dropUnusedSeries(); for (var q = 0; q < ids.length; ++q) root.updateSeries(ids[q])
        if (ids.length === 1) {
            var descriptor = root.metricDescriptorById[ids[0]]
            if (descriptor && descriptor.rangeHint && descriptor.rangeHint.length === 2) {
                root.manualMin = Number(descriptor.rangeHint[0])
                root.manualMax = Number(descriptor.rangeHint[1])
                if (root.minSpinControl) root.minSpinControl.value = Math.round(root.manualMin * root.minSpinControl.valueScale)
                if (root.maxSpinControl) root.maxSpinControl.value = Math.round(root.manualMax * root.maxSpinControl.valueScale)
            }
        }
        root.updateAxes(); root.updateValueAxis()
    }

    function dropUnusedSeries() {
        var active = root.telemetryBridge ? root.telemetryBridge.activeMetrics : []
        var idsArr = root.asArray(active)
        for (var metricId in root.seriesMap) {
            if (idsArr.indexOf(metricId) === -1) {
                var obsolete = root.seriesMap[metricId]
                root.chartViewItem.removeSeries(obsolete)
                delete root.seriesMap[metricId]
            }
        }
    }

    function ensureSeries(metricId) {
        var descriptor = root.metricDescriptorById[metricId]
        if (!descriptor) return null
        var existing = root.seriesMap[metricId]
        if (existing) return existing
        var label = descriptor.label + " (" + descriptor.unit + ")"
        var created = root.chartViewItem.createSeries(ChartView.SeriesTypeLine, label, root.timeAxisItem, root.valueAxisItem)
        created.color = descriptor.color
        created.useOpenGL = true
        created.width = 2
        root.seriesMap[metricId] = created
        return created
    }

    function updateSeries(metricId) {
        var buffer = root.buffersJs[metricId]
        var series = root.ensureSeries(metricId)
        if (!series) return
        if (!buffer || buffer.length === 0) { if (series.clear) series.clear(); return }
        var points = []
        for (var i = 0; i < buffer.length; ++i) points.push(Qt.point(buffer[i][0], buffer[i][1]))
        if (series.clear) series.clear()
        if (series.append) {
            try { series.append(points) } catch (e) { for (var j = 0; j < points.length; ++j) series.append(points[j].x, points[j].y) }
        }
    }

    function handleSample(sample) {
        if (!sample) return
        if (sample.latestTimestamp !== undefined) root.latestTimestamp = Number(sample.latestTimestamp)
        else if (sample.timestamp !== undefined) root.latestTimestamp = Number(sample.timestamp)
        if (sample.oldestTimestamp !== undefined) root.oldestTimestamp = Number(sample.oldestTimestamp)
        var timestamp = Number(sample.timestamp !== undefined ? sample.timestamp : root.latestTimestamp)
        var values = sample.values || {}

        var updated = []
        for (var metricId in values) {
            var v = Number(values[metricId])
            var buf = root.seriesBuffers[metricId]
            if (!buf) { buf = []; root.seriesBuffers[metricId] = buf }
            buf.push([timestamp, v])
            if (buf.length > root.maxSamples) buf.splice(0, buf.length - root.maxSamples)

            var rbuf = root.buffersJs[metricId] || []
            rbuf.push([timestamp, v])
            if (rbuf.length > root.maxSamples) rbuf.splice(0, rbuf.length - root.maxSamples)
            root.buffersJs[metricId] = rbuf
            updated.push(metricId)
        }
        if (!root.panelExpanded) return
        for (var i = 0; i < updated.length; ++i) root.updateSeries(updated[i])
        root.updateAxes(); root.updateValueAxis()
    }

    function updateAxes() {
        var windowSize = Math.max(1, root.timeWindow)
        if (root.latestTimestamp <= 0 && root.oldestTimestamp <= 0) { root.timeAxisItem.min = 0; root.timeAxisItem.max = windowSize; return }
        if (root.autoScroll) { var end = Math.max(windowSize, root.latestTimestamp); root.timeAxisItem.max = end; root.timeAxisItem.min = Math.max(0, end - windowSize); root.manualScrollPosition = 1.0 }
        else { var span = Math.max(0, root.latestTimestamp - root.oldestTimestamp); if (span <= windowSize) { var start = Math.max(0, root.oldestTimestamp); root.timeAxisItem.min = start; root.timeAxisItem.max = start + windowSize } else { var offset = span - windowSize; var position = Math.min(1.0, Math.max(0.0, root.manualScrollPosition)); var startValue = root.oldestTimestamp + offset * position; root.timeAxisItem.min = startValue; root.timeAxisItem.max = startValue + windowSize } }
    }

    function updateValueAxis() { if (root.autoScale) root.autoScaleAxis(); else root.applyManualScale() }

    function autoScaleAxis() {
        var minValue = Number.POSITIVE_INFINITY
        var maxValue = Number.NEGATIVE_INFINITY
        var active = root.telemetryBridge ? root.telemetryBridge.activeMetrics : []
        var idsArr = root.asArray(active)
        for (var i = 0; i < idsArr.length; ++i) {
            var metricId = idsArr[i]
            var buffer = root.buffersJs[metricId]
            if (!buffer || buffer.length === 0) continue
            for (var j = 0; j < buffer.length; ++j) { var value = buffer[j][1]; if (value < minValue) minValue = value; if (value > maxValue) maxValue = value }
        }
        if (minValue === Number.POSITIVE_INFINITY) { minValue = -1; maxValue = 1 }
        if (minValue === maxValue) { var delta = Math.abs(minValue) * 0.1 + 1e-6; minValue -= delta; maxValue += delta }
        var margin = (maxValue - minValue) * 0.1
        root.valueAxisItem.min = minValue - margin
        root.valueAxisItem.max = maxValue + margin
    }

    function applyManualScale() { if (root.manualMax <= root.manualMin) { root.manualMax = root.manualMin + 0.001 } root.valueAxisItem.min = root.manualMin; root.valueAxisItem.max = root.manualMax }

    function resetPanel() {
        root.oldestTimestamp = 0
        root.latestTimestamp = 0
        // Очищаем существующие массивы на месте, сохраняя map-объект
        for (var k in root.seriesBuffers) {
            var arr = root.seriesBuffers[k]
            if (arr && arr.splice) arr.splice(0, arr.length)
            else root.seriesBuffers[k] = []
        }
        for (var b in root.buffersJs) {
            var arr2 = root.buffersJs[b]
            if (arr2 && arr2.splice) arr2.splice(0, arr2.length)
            else root.buffersJs[b] = []
        }
        for (var metricId in root.seriesMap) { var series = root.seriesMap[metricId]; if (series && series.clear) series.clear() }
        root.updateAxes(); root.updateValueAxis()
    }

    Component.onCompleted: { root.rebuildMetricCatalog(); root.syncSelectionFromBridge(); root.updateAxes(); root.updateValueAxis() }
    onPanelExpandedChanged: { if (root.panelExpanded) root.refreshSeriesFromBridge() }
}
