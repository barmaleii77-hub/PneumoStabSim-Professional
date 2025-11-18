pragma Singleton
pragma ComponentBehavior: Bound

import QtQml 6.10
import QtQuick 6.10

QtObject {
    id: root

    readonly property url _source: Qt.resolvedUrl("../../config/ui_constants.json")
    readonly property var values: _loadConstants()

    readonly property var pressure: values.pressure || ({})
    readonly property var temperature: values.temperature || ({})
    readonly property var layout: values.layout || ({})

    readonly property real defaultPadding: Number(layout.panelPadding || 24)
    readonly property real defaultContentMargin: Number(layout.contentMargin || 24)

    function _loadConstants() {
        var request = new XMLHttpRequest()
        request.open("GET", _source, false)
        request.send()
        if (request.status === 0 || request.status === 200) {
            try {
                return JSON.parse(request.responseText)
            } catch (error) {
                console.warn("UiConstants: failed to parse config", error)
            }
        }
        return ({})
    }
}
