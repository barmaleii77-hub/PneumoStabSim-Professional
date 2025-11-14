pragma ComponentBehavior: Bound

import QtQuick
import QtQuick3D
import "../../assets/qml/environment" as Environment

QtObject {
    id: root

    // Python DiagnosticsRecorder (QObject со slot recordObservation)
    property var recorder: null
    // QtObject‑обёртка для передачи в RealismEnvironment как sceneBridge
    property QtObject bridgeProxy: QtObject {
        property var signalTrace: root.recorder
        property var environment: ({})
        property var effects: ({})
        property var quality: ({})
    }

    property var env: Environment.RealismEnvironment {
        id: environmentComponent
        sceneBridge: root.bridgeProxy
        diagnosticsTrace: root.recorder
    }

    function setSceneBridge(value) {
        // value может быть {signalTrace: recorder} или сам recorder
        if (value && value.signalTrace) {
            recorder = value.signalTrace
        } else {
            recorder = value
        }
        bridgeProxy.signalTrace = recorder
        environmentComponent.diagnosticsTrace = recorder
        // После подключения overlay воспроизводим кешированные предупреждения
        if (environmentComponent._replayCachedWarnings)
            environmentComponent._replayCachedWarnings()
    }

    function callNumber(section, keys, fallback) { return environmentComponent._number(section, keys, fallback) }
    function callWarn(section, keys, reason, fallback) { environmentComponent._warn(section, keys, reason, fallback) }
    function callWarnWithoutFallback(section, keys, reason) { environmentComponent._warn(section, keys, reason) }
}
