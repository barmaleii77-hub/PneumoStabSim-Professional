import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Layouts 6.10
import "../Panels/Common" as Common

Pane {
    id: root

    property var bridge: (typeof trainingBridge !== "undefined" ? trainingBridge : null)
    property string activePresetId: ""
    property var presetModel: []
    property var selectedDetails: ({})
    property var metadataDetails: ({})
    property var objectivesList: []
    property var modulesList: []
    property var metricsList: []
    property var simulationEntries: []
    property var pneumaticEntries: []
    property var tagList: []

    signal presetActivated(string presetId)

    width: 360
    implicitHeight: columnContent.implicitHeight + topPadding + bottomPadding
    padding: 16

    background: Rectangle {
        radius: 12
        color: Qt.rgba(0.09, 0.1, 0.14, 0.92)
        border.color: Qt.rgba(0.25, 0.3, 0.38, 0.9)
        border.width: 1
    }

    function formatValue(value) {
        if (typeof value === "number")
            return Number(value).toLocaleString(Qt.locale(), { maximumFractionDigits: 4 })
        if (typeof value === "boolean")
            return value ? qsTr("Да") : qsTr("Нет")
        if (value === undefined || value === null)
            return ""
        return String(value)
    }

    function setSelected(details) {
        const next = details || {}
        selectedDetails = next
        metadataDetails = next.metadata || {}
        tagList = next.tags || []

        const objectives = metadataDetails.learningObjectives || []
        objectivesList = objectives.slice()
        const modules = metadataDetails.recommendedModules || []
        modulesList = modules.slice()
        const metrics = metadataDetails.evaluationMetrics || []
        metricsList = metrics.slice()

        simulationEntries = []
        pneumaticEntries = []

        if (next.simulation) {
            const keys = Object.keys(next.simulation).sort()
            simulationEntries = keys.map(function(key) {
                return { key: key, value: next.simulation[key] }
            })
        }
        if (next.pneumatic) {
            const pneKeys = Object.keys(next.pneumatic).sort()
            pneumaticEntries = pneKeys.map(function(key) {
                return { key: key, value: next.pneumatic[key] }
            })
        }
    }

    function loadFromBridge() {
        if (!bridge)
            return
        presetModel = bridge.listPresets()
        activePresetId = bridge.activePresetId
        setSelected(bridge.selectedPreset())
    }

    ColumnLayout {
        id: columnContent
        anchors.fill: parent
        anchors.margins: 0
        spacing: 12

        Label {
            text: qsTr("Учебные пресеты")
            font.bold: true
            font.pointSize: 14
            Layout.fillWidth: true
        }

        Label {
            text: selectedDetails.description || qsTr("Выберите пресет, чтобы увидеть описание и параметры.")
            wrapMode: Text.WordWrap
            color: Qt.rgba(0.8, 0.83, 0.92, 0.9)
            Layout.fillWidth: true
        }

        Common.PresetButtons {
            id: presetButtons
            Layout.fillWidth: true
            title: qsTr("Предустановки симуляции")
            model: root.presetModel
            activePresetId: root.activePresetId
            onPresetActivated: function(presetId) {
                root.presetActivated(presetId)
                if (!root.bridge)
                    return
                const details = root.bridge.describePreset(presetId)
                if (details)
                    root.setSelected(details)
                if (root.bridge.applyPreset(presetId))
                    root.activePresetId = root.bridge.activePresetId
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: root.tagList && root.tagList.length > 0
            spacing: 6

            Repeater {
                model: root.tagList || []
                delegate: Rectangle {
                    radius: 6
                    color: Qt.rgba(0.21, 0.25, 0.33, 0.9)
                    border.color: Qt.rgba(0.33, 0.39, 0.49, 0.9)
                    border.width: 1
                    implicitHeight: 24
                    implicitWidth: tagLabel.implicitWidth + 16

                    Text {
                        id: tagLabel
                        anchors.centerIn: parent
                        text: String(modelData)
                        color: Qt.rgba(0.9, 0.92, 0.97, 1.0)
                        font.pointSize: 9
                    }
                }
            }
        }

        GroupBox {
            title: qsTr("Метаданные обучения")
            Layout.fillWidth: true
            visible: Object.keys(root.metadataDetails).length > 0

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                Label {
                    text: qsTr("Сложность: %1").arg(root.metadataDetails.difficulty || qsTr("не указано"))
                    Layout.fillWidth: true
                }
                Label {
                    text: qsTr("Длительность: %1 мин").arg(root.metadataDetails.durationMinutes || 0)
                    Layout.fillWidth: true
                }
                Label {
                    text: qsTr("Сценарий: %1").arg(root.metadataDetails.scenarioId || qsTr("нет"))
                    visible: !!root.metadataDetails.scenarioId
                    Layout.fillWidth: true
                }
                Label {
                    text: root.metadataDetails.notes || ""
                    visible: !!root.metadataDetails.notes
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Label {
                    text: qsTr("Цели обучения")
                    visible: root.objectivesList.length > 0
                    font.bold: true
                    Layout.topMargin: 6
                    Layout.fillWidth: true
                }
                Repeater {
                    model: root.objectivesList
                    delegate: Label {
                        text: "• " + String(modelData)
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }

                Label {
                    text: qsTr("Рекомендуемые модули")
                    visible: root.modulesList.length > 0
                    font.bold: true
                    Layout.topMargin: 6
                    Layout.fillWidth: true
                }
                Flow {
                    width: parent.width
                    visible: root.modulesList.length > 0
                    spacing: 6
                    Repeater {
                        model: root.modulesList
                        delegate: Rectangle {
                            radius: 4
                            color: Qt.rgba(0.18, 0.21, 0.28, 0.9)
                            border.color: Qt.rgba(0.3, 0.35, 0.44, 0.9)
                            border.width: 1
                            implicitHeight: 22
                            implicitWidth: moduleLabel.implicitWidth + 14

                            Text {
                                id: moduleLabel
                                anchors.centerIn: parent
                                text: String(modelData)
                                color: Qt.rgba(0.85, 0.88, 0.95, 1.0)
                                font.pointSize: 8
                            }
                        }
                    }
                }

                Label {
                    text: qsTr("Метрики оценки")
                    visible: root.metricsList.length > 0
                    font.bold: true
                    Layout.topMargin: 6
                    Layout.fillWidth: true
                }
                Repeater {
                    model: root.metricsList
                    delegate: Label {
                        text: "• " + String(modelData)
                        Layout.fillWidth: true
                    }
                }
            }
        }

        GroupBox {
            title: qsTr("Параметры симуляции")
            Layout.fillWidth: true
            visible: root.simulationEntries.length > 0

            GridLayout {
                columns: 2
                columnSpacing: 12
                rowSpacing: 4
                Layout.fillWidth: true

                Repeater {
                    model: root.simulationEntries
                    delegate: RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: String(modelData.key)
                            color: Qt.rgba(0.75, 0.79, 0.88, 1.0)
                            Layout.fillWidth: true
                        }
                        Label {
                            text: root.formatValue(modelData.value)
                            horizontalAlignment: Text.AlignRight
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }

        GroupBox {
            title: qsTr("Пневматика")
            Layout.fillWidth: true
            visible: root.pneumaticEntries.length > 0

            GridLayout {
                columns: 2
                columnSpacing: 12
                rowSpacing: 4
                Layout.fillWidth: true

                Repeater {
                    model: root.pneumaticEntries
                    delegate: RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: String(modelData.key)
                            color: Qt.rgba(0.75, 0.79, 0.88, 1.0)
                            Layout.fillWidth: true
                        }
                        Label {
                            text: root.formatValue(modelData.value)
                            horizontalAlignment: Text.AlignRight
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }

    onBridgeChanged: loadFromBridge()

    Component.onCompleted: loadFromBridge()

    Connections {
        target: bridge
        function onPresetsChanged() {
            presetModel = bridge.presets
        }
        function onActivePresetChanged() {
            activePresetId = bridge.activePresetId
        }
        function onSelectedPresetChanged() {
            setSelected(bridge.selectedPreset())
        }
    }
}
