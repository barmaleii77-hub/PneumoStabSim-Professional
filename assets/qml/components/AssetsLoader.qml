import QtQuick 6.10
import QtQuick3D 6.10

pragma ComponentBehavior: Bound

Texture {
    id: root

    /**
     * Primary resource URL resolved by the consumer. When ``fallbackActive`` is
     * ``false`` the texture will attempt to load this source.
     */
    property url primarySource: ""

    /**
     * Optional fallback URL. When provided the loader switches to this source
     * after a failure. If empty, ``fallbackItem`` will be used instead.
     */
    property url fallbackSource: ""

    /**
     * Name used in diagnostic output.
     */
    property string assetName: ""

    /**
     * Describes the fallback resource for diagnostics.
     */
    property string fallbackDescriptor: fallbackSource && fallbackSource !== ""
        ? String(fallbackSource)
        : "generated://texture-placeholder"

    /**
     * Placeholder item rendered into the texture when ``fallbackSource`` is
     * empty. Consumers may override its appearance by setting ``fallbackItem``.
     */
    property Item fallbackItem: defaultFallback

    /**
     * When ``true`` the loader currently serves the fallback resource.
     */
    property bool fallbackActive: false

    /**
     * ``true`` if the fallback was activated because of a load error.
     */
    property bool fallbackDueToError: false

    /**
     * Human readable reason for the last fallback activation.
     */
    property string fallbackReason: ""

    /**
     * Allows callers to silence logging during tests.
     */
    property bool loggingEnabled: true

    /**
     * Colour gradient used by the default fallback item.
     */
    property color fallbackStartColor: Qt.rgba(0.29, 0.33, 0.42, 1.0)
    property color fallbackEndColor: Qt.rgba(0.13, 0.16, 0.22, 1.0)
    property string fallbackLabel: assetName.length ? assetName : qsTr("Fallback")

    readonly property bool usingFallbackItem: fallbackActive
        && (!fallbackSource || fallbackSource === "")

    property int _lastStatus: -1

    source: fallbackActive
        ? (fallbackSource && fallbackSource !== "" ? fallbackSource : "")
        : primarySource
    sourceItem: fallbackActive && (!fallbackSource || fallbackSource === "")
        ? fallbackItem
        : null

    function _logWarn(message) {
        if (!loggingEnabled)
            return
        const prefix = assetName && assetName.length
            ? `[AssetsLoader:${assetName}]`
            : "[AssetsLoader]"
        console.warn(`${prefix} ${message}`)
    }

    function _activateFallback(reason, dueToError) {
        if (fallbackActive)
            return
        fallbackReason = reason || ""
        fallbackDueToError = Boolean(dueToError)
        fallbackActive = true
        _logWarn(
            `${reason || "Switching to fallback"}; using ${fallbackDescriptor}; fallback activated`
        )
    }

    function _handleFallbackError() {
        _logWarn(
            `Fallback resource ${fallbackDescriptor} failed to load; texture will remain empty; fallback still active`
        )
    }

    onPrimarySourceChanged: {
        fallbackReason = ""
        fallbackDueToError = false
        _lastStatus = -1
        if (fallbackActive) {
            fallbackActive = false
        }
    }

    // qmllint disable missing-property
    function _handleStatusChanged() {
        const currentStatus = root.status
        if (currentStatus === root._lastStatus)
            return
        root._lastStatus = currentStatus

        if (currentStatus === Texture.Error) {
            if (!fallbackActive) {
                const reason = primarySource && String(primarySource).length
                    ? `Failed to load ${primarySource}`
                    : "Primary source not specified"
                _activateFallback(reason, true)
            } else {
                _handleFallbackError()
            }
        } else if (currentStatus === Texture.Null) {
            if (!primarySource || String(primarySource).length === 0) {
                _activateFallback("Primary source not provided", false)
            }
        }
    }
    // qmllint enable missing-property

    Component.onCompleted: {
        if (!primarySource || String(primarySource).length === 0) {
            _activateFallback("Primary source not provided", false)
        }
        _handleStatusChanged()
    }

    Connections {
        target: root

        function onStatusChanged() {
            root._handleStatusChanged()
        }
    }

    Item {
        id: defaultFallback
        width: 256
        height: 256
        visible: false

        Rectangle {
            anchors.fill: parent
            radius: 24
            gradient: Gradient {
                GradientStop { position: 0.0; color: root.fallbackStartColor }
                GradientStop { position: 1.0; color: root.fallbackEndColor }
            }
            border.width: 2
            border.color: Qt.rgba(0.9, 0.9, 0.9, 0.35)
        }

        Text {
            anchors.centerIn: parent
            text: root.fallbackLabel
            color: "#f0f4f8"
            font.pixelSize: 28
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: parent.width * 0.8
        }
    }
}
