import QtQuick 6.10
import QtQuick.Layouts 6.10
import "."

pragma ComponentBehavior: Bound

Item {
    id: root

    property var geometryState: ({})
    property var simulationState: ({})
    property bool sceneBridgeConnected: false
    property bool sceneBridgeHasUpdates: false

    readonly property bool geometryReady: _hasKeys(geometryState)
    readonly property bool simulationReady: _hasKeys(simulationState && simulationState.levers)
            || _hasKeys(simulationState && simulationState.pistons)
    readonly property int geometryKeyCount: _keyCount(geometryState)
    readonly property int leverKeyCount: _keyCount(simulationState && simulationState.levers)
    readonly property int pistonKeyCount: _keyCount(simulationState && simulationState.pistons)
    readonly property var aggregatesState: _asObject(simulationState && simulationState.aggregates)
    readonly property bool geometryWarning: !sceneBridgeConnected || (!geometryReady && sceneBridgeHasUpdates)
    readonly property bool simulationWarning: !sceneBridgeConnected || (!simulationReady && sceneBridgeHasUpdates)

    implicitWidth: background.implicitWidth
    implicitHeight: background.implicitHeight

    function _asObject(value) {
        return value && typeof value === "object" ? value : null
    }

    function _keyCount(value) {
        if (!value || typeof value !== "object")
            return 0
        var count = 0
        for (var key in value) {
            if (Object.prototype.hasOwnProperty.call(value, key))
                ++count
        }
        return count
    }

    function _hasKeys(value) {
        return _keyCount(value) > 0
    }

    Rectangle {
        id: background
        implicitWidth: layout.implicitWidth + (layout.anchors.margins * 2)
        implicitHeight: layout.implicitHeight + (layout.anchors.margins * 2)
        radius: 16
        color: Qt.rgba(0.07, 0.09, 0.12, 0.88)
        border.width: 1
        border.color: Qt.rgba(0.24, 0.36, 0.52, 0.55)

        ColumnLayout {
            id: layout
            anchors.fill: parent
            anchors.margins: 14
            spacing: 10

            BridgeStateIndicator {
                id: geometryIndicator
                objectName: "geometryIndicator"
                label: qsTr("Геометрия")
                active: root.geometryReady
                warning: root.geometryWarning
                detailText: root.geometryReady
                    ? qsTr("%1 параметров").arg(root.geometryKeyCount)
                    : qsTr("Ожидание данных от SceneBridge")
                secondaryText: root.geometryReady
                    ? qsTr("Последнее обновление: %1 ключей").arg(root.geometryKeyCount)
                    : (root.sceneBridgeConnected ? qsTr("Сигналы ещё не получены") : qsTr("Bridge недоступен"))
                pulse: root.geometryReady && root.sceneBridgeHasUpdates
            }

            BridgeStateIndicator {
                id: simulationIndicator
                objectName: "simulationIndicator"
                label: qsTr("Симуляция")
                active: root.simulationReady
                warning: root.simulationWarning
                detailText: root.simulationReady
                    ? qsTr("Рычаги: %1 • Поршни: %2").arg(root.leverKeyCount).arg(root.pistonKeyCount)
                    : qsTr("Нет активного снапшота")
                secondaryText: {
                    if (!root.simulationReady)
                        return root.sceneBridgeConnected ? qsTr("Ожидание шага") : qsTr("Bridge недоступен")
                    const aggregates = root.aggregatesState
                    if (aggregates && aggregates.stepNumber !== undefined) {
                        const timeValue = aggregates.simulationTime !== undefined ? Number(aggregates.simulationTime) : NaN
                        const formattedTime = isFinite(timeValue) ? timeValue.toFixed(3) : "—"
                        return qsTr("Шаг %1 • Время %2 с").arg(aggregates.stepNumber).arg(formattedTime)
                    }
                    return ""
                }
                pulse: root.simulationReady && root.sceneBridgeHasUpdates
            }
        }
    }

    property alias geometryIndicatorItem: geometryIndicator
    property alias simulationIndicatorItem: simulationIndicator
}
