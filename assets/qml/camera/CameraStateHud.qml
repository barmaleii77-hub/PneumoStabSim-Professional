import QtQuick
import QtQuick.Layouts

/*
 * CameraStateHud.qml - Debug overlay for camera metrics
 * Displays camera position, distance, angles, motion flags and damping data.
 */
Item {
    id: hud

    property var cameraController: null
    property var settings: ({})

    readonly property var cameraState: cameraController ? cameraController.state : null
    readonly property real sceneScaleFactor: cameraController ? cameraController.sceneScaleFactor : 1000.0

    readonly property int precision: settings && settings.precision !== undefined
        ? Math.max(0, Number(settings.precision)) : 2
    readonly property bool showPivot: settings && settings.showPivot !== undefined
        ? !!settings.showPivot : true
    readonly property bool showPan: settings && settings.showPan !== undefined
        ? !!settings.showPan : true
    readonly property bool showAngles: settings && settings.showAngles !== undefined
        ? !!settings.showAngles : true
    readonly property bool showMotion: settings && settings.showMotion !== undefined
        ? !!settings.showMotion : true

    implicitWidth: panel.implicitWidth
    implicitHeight: panel.implicitHeight

    width: panel.implicitWidth
    height: panel.implicitHeight

    Rectangle {
        id: panel
        anchors.fill: parent
        color: Qt.rgba(0.07, 0.09, 0.14, 0.88)
        border.color: Qt.rgba(0.25, 0.47, 0.87, 0.95)
        border.width: 1
        radius: 8

        ColumnLayout {
            id: layout
            anchors.fill: parent
            anchors.margins: 12
            spacing: 6

            Text {
                id: header
                text: qsTr("Camera HUD")
                font.pixelSize: 15
                font.bold: true
                color: "#dce7ff"
            }

            Repeater {
                model: metricsModel()

                delegate: RowLayout {
                    spacing: 6
                    Layout.fillWidth: true

                    Text {
                        text: model.label + ":"
                        font.pixelSize: 13
                        color: "#8fa6d3"
                        horizontalAlignment: Text.AlignLeft
                        Layout.fillWidth: false
                        Layout.preferredWidth: 110
                    }

                    Text {
                        text: model.value
                        font.pixelSize: 13
                        color: "#e9f0ff"
                        horizontalAlignment: Text.AlignRight
                        Layout.fillWidth: true
                        wrapMode: Text.NoWrap
                        font.family: "monospace"
                    }
                }
            }
        }
    }

    function metricsModel() {
        if (!cameraState) {
            return []
        }

        var values = []
        values.push({
            label: qsTr("Distance [m]"),
            value: formatMeters(cameraState.distance)
        })

        if (showAngles) {
            values.push({
                label: qsTr("Yaw/Pitch [°]"),
                value: formatAngles(cameraState.yawDeg, cameraState.pitchDeg)
            })
        }

        if (showPan) {
            values.push({
                label: qsTr("Pan [m]"),
                value: formatVector(Qt.vector3d(cameraState.panX, cameraState.panY, 0))
            })
        }

        if (showPivot) {
            values.push({
                label: qsTr("Pivot [m]"),
                value: formatVector(cameraState.pivot)
            })
        }

        values.push({
            label: qsTr("FOV / Speed"),
            value: formatScalar(cameraState.fov) + "° / " + formatScalar(cameraState.speed)
        })

        values.push({
            label: qsTr("Clip [m]"),
            value: formatMeters(cameraState.nearPlane) + " – " + formatMeters(cameraState.farPlane)
        })

        if (showMotion) {
            values.push({
                label: qsTr("Auto-rotate"),
                value: cameraState.autoRotate ? qsTr("ON (%1°/s)").arg(formatScalar(cameraState.autoRotateSpeed)) : qsTr("OFF")
            })
            values.push({
                label: qsTr("Motion state"),
                value: cameraController && cameraController.isMoving ? qsTr("Moving") : qsTr("Idle")
            })
        }

        values.push({
            label: qsTr("Damping [ms]"),
            value: formatDamping()
        })

        if (cameraController && cameraController.motionSettlingMs !== undefined) {
            values.push({
                label: qsTr("Settle [ms]"),
                value: String(cameraController.motionSettlingMs)
            })
        }

        return values
    }

    function formatScalar(value) {
        var numeric = Number(value)
        if (!isFinite(numeric)) {
            return "—"
        }
        return numeric.toFixed(precision)
    }

    function formatMeters(value) {
        var numeric = Number(value)
        if (!isFinite(numeric)) {
            return "—"
        }
        if (sceneScaleFactor === 0) {
            return formatScalar(numeric)
        }
        return Number(numeric / sceneScaleFactor).toFixed(Math.min(3, Math.max(0, precision + 1)))
    }

    function formatAngles(yaw, pitch) {
        var yawVal = Number(yaw)
        var pitchVal = Number(pitch)
        if (!isFinite(yawVal) || !isFinite(pitchVal)) {
            return "—"
        }
        return yawVal.toFixed(precision) + " / " + pitchVal.toFixed(precision)
    }

    function formatVector(vector) {
        if (!vector) {
            return "—"
        }
        return [vector.x, vector.y, vector.z]
            .map(function (component) { return formatMeters(component) })
            .join(", ")
    }

    function formatDamping() {
        if (!cameraState) {
            return "—"
        }
        var parts = [
            cameraState.rotationDampingMs,
            cameraState.distanceDampingMs,
            cameraState.panDampingMs
        ].map(function (value) { return String(value) })
        return parts.join(" / ")
    }
}
