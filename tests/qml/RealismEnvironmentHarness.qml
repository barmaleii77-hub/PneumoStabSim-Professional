pragma ComponentBehavior: Bound

import QtQuick
import "../../assets/qml/environment" as Environment

QtObject {
    id: root

    property var sceneBridgePayload: null

    property var env: Environment.RealismEnvironment {
        id: environmentComponent
        sceneBridge: root.sceneBridgePayload
    }

    onSceneBridgePayloadChanged: {
        environmentComponent.sceneBridge = sceneBridgePayload
    }

    function setSceneBridge(value) {
        sceneBridgePayload = value
    }

    function callNumber(section, keys, fallback) {
        return environmentComponent._number(section, keys, fallback)
    }

    function callWarn(section, keys, reason, fallback) {
        environmentComponent._warn(section, keys, reason, fallback)
    }

    function callWarnWithoutFallback(section, keys, reason) {
        environmentComponent._warn(section, keys, reason)
    }
}
