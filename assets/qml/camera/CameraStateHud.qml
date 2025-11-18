import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

pragma ComponentBehavior: Bound

/*
 * CameraStateHud.qml - Debug overlay for camera metrics
 * Displays camera position, distance, angles, motion flags and damping data.
 */
Item {
    id: hud

    property var safeApplyConfigChange: null

    property var cameraController: null
    property var settings: ({})
    property var telemetry: null

    function setSetting(key, value) {
        var current = settings || {}
        if (current[key] === value)
            return

        var next = {}
        for (var entry in current) {
            if (current.hasOwnProperty(entry))
                next[entry] = current[entry]
        }
        next[key] = value
        settings = next
    }

    function persistSetting(key, value) {
        hud.setSetting(key, value)
        if (typeof hud.safeApplyConfigChange === "function") {
            var patch = {}
            patch[key] = value
            hud.safeApplyConfigChange("diagnostics.camera_hud", patch)
        }
    }

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
    readonly property bool showDamping: settings && settings.showDamping !== undefined
        ? !!settings.showDamping : true
    readonly property bool showInertia: settings && settings.showInertia !== undefined
        ? !!settings.showInertia : true
    readonly property bool showSmoothing: settings && settings.showSmoothing !== undefined
        ? !!settings.showSmoothing : true
    readonly property bool showPreset: settings && settings.showPreset !== undefined
        ? !!settings.showPreset : true
    readonly property bool showTimestamp: settings && settings.showTimestamp !== undefined
        ? !!settings.showTimestamp : true

    readonly property string labelOn: qsTrId("camera.hud.state.on") || qsTr("ON")
    readonly property string labelOff: qsTrId("camera.hud.state.off") || qsTr("OFF")
    readonly property string labelMoving: qsTrId("camera.hud.state.moving") || qsTr("Moving")
    readonly property string labelIdle: qsTrId("camera.hud.state.idle") || qsTr("Idle")

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
                text: qsTrId("camera.hud.header") || qsTr("Camera HUD")
                font.pixelSize: 15
                font.bold: true
                color: "#dce7ff"
            }

            Flow {
                id: toggleFlow
                Layout.fillWidth: true
                spacing: 6
                flow: Flow.LeftToRight

                Repeater {
                    model: [
                        {
                            binding: "showPivot",
                            settingKey: "showPivot",
                            text: qsTrId("camera.hud.toggle.pivot") || qsTr("Pivot")
                        },
                        {
                            binding: "showPan",
                            settingKey: "showPan",
                            text: qsTrId("camera.hud.toggle.pan") || qsTr("Pan")
                        },
                        {
                            binding: "showAngles",
                            settingKey: "showAngles",
                            text: qsTrId("camera.hud.toggle.angles") || qsTr("Angles")
                        },
                        {
                            binding: "showMotion",
                            settingKey: "showMotion",
                            text: qsTrId("camera.hud.toggle.motion") || qsTr("Motion")
                        },
                        {
                            binding: "showDamping",
                            settingKey: "showDamping",
                            text: qsTrId("camera.hud.toggle.damping") || qsTr("Damping")
                        },
                        {
                            binding: "showInertia",
                            settingKey: "showInertia",
                            text: qsTrId("camera.hud.toggle.inertia") || qsTr("Inertia")
                        },
                        {
                            binding: "showSmoothing",
                            settingKey: "showSmoothing",
                            text: qsTrId("camera.hud.toggle.smoothing") || qsTr("Smoothing")
                        },
                        {
                            binding: "showPreset",
                            settingKey: "showPreset",
                            text: qsTrId("camera.hud.toggle.preset") || qsTr("Preset")
                        },
                        {
                            binding: "showTimestamp",
                            settingKey: "showTimestamp",
                            text: qsTrId("camera.hud.toggle.timestamp") || qsTr("Timestamp")
                        }
                    ]

                    delegate: CheckDelegate {
                        required property var modelData

                        text: modelData.text
                        checked: hud[modelData.binding]
                        onToggled: hud.persistSetting(modelData.settingKey, checked)
                    }
                }
            }

            Repeater {
                model: metricsModel()

                delegate: RowLayout {
                    id: metricsRow
                    required property var modelData

                    spacing: 6
                    Layout.fillWidth: true

                    readonly property string metricLabel: modelData && modelData.label !== undefined
                        ? String(modelData.label)
                        : ""
                    readonly property string metricValue: modelData && modelData.value !== undefined && modelData.value !== null
                        ? String(modelData.value)
                        : "—"

                    Text {
                        text: metricsRow.metricLabel.length ? metricsRow.metricLabel + ":" : "—"
                        font.pixelSize: 13
                        color: "#8fa6d3"
                        horizontalAlignment: Text.AlignLeft
                        Layout.fillWidth: false
                        Layout.preferredWidth: 160
                    }

                    Text {
                        text: metricsRow.metricValue
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
        var metrics = []
        var state = hud.cameraState
        var data = hud.telemetry

        function telemetryToMillimetres(value) {
            var numeric = Number(value)
            if (!isFinite(numeric))
                return null
            if (!isFinite(hud.sceneScaleFactor) || hud.sceneScaleFactor === 0)
                return numeric
            return numeric * hud.sceneScaleFactor
        }

        function resolveNumber(telemetryKey, stateValue) {
            if (data && data[telemetryKey] !== undefined) {
                var candidate = Number(data[telemetryKey])
                if (isFinite(candidate))
                    return candidate
            }
            var fallback = Number(stateValue)
            return isFinite(fallback) ? fallback : null
        }

        var distanceMm = null
        if (data && data.distance !== undefined)
            distanceMm = telemetryToMillimetres(data.distance)
        if (distanceMm === null && state && state.distance !== undefined) {
            var stateDistance = Number(state.distance)
            if (isFinite(stateDistance))
                distanceMm = stateDistance
        }
        metrics.push({
            label: qsTrId("camera.hud.metric.distance") || qsTr("Distance [m]"),
            value: distanceMm !== null ? formatMeters(distanceMm) : "—"
        })

        if (hud.showAngles) {
            var yaw = resolveNumber("yawDeg", state ? state.yawDeg : undefined)
            var pitch = resolveNumber("pitchDeg", state ? state.pitchDeg : undefined)
            metrics.push({
                label: qsTrId("camera.hud.metric.angles") || qsTr("Yaw/Pitch [°]"),
                value: formatAngles(yaw, pitch)
            })
        }

        if (hud.showPan) {
            var panVector = null
            if (data && (data.panX !== undefined || data.panY !== undefined || data.panZ !== undefined)) {
                var px = telemetryToMillimetres(data.panX)
                var py = telemetryToMillimetres(data.panY)
                var pz = telemetryToMillimetres(data.panZ)
                if (px !== null || py !== null || pz !== null) {
                    panVector = Qt.vector3d(px !== null ? px : 0, py !== null ? py : 0, pz !== null ? pz : 0)
                }
            }
            if (!panVector && state)
                panVector = Qt.vector3d(state.panX, state.panY, 0)
            metrics.push({
                label: qsTrId("camera.hud.metric.pan") || qsTr("Pan [m]"),
                value: panVector ? formatVector(panVector) : "—"
            })
        }

        if (hud.showPivot) {
            var pivotVector = null
            if (data && data.pivot) {
                var pivot = data.pivot
                var pvx = telemetryToMillimetres(pivot.x !== undefined ? pivot.x : pivot[0])
                var pvy = telemetryToMillimetres(pivot.y !== undefined ? pivot.y : pivot[1])
                var pvz = telemetryToMillimetres(pivot.z !== undefined ? pivot.z : pivot[2])
                if (pvx !== null || pvy !== null || pvz !== null)
                    pivotVector = Qt.vector3d(pvx !== null ? pvx : 0, pvy !== null ? pvy : 0, pvz !== null ? pvz : 0)
            }
            if (!pivotVector && state)
                pivotVector = state.pivot
            metrics.push({
                label: qsTrId("camera.hud.metric.pivot") || qsTr("Pivot [m]"),
                value: pivotVector ? formatVector(pivotVector) : "—"
            })
        }

        var fovValue = resolveNumber("fov", state ? state.fov : undefined)
        var speedValue = resolveNumber("speed", state ? state.speed : undefined)
        var fovText = fovValue !== null ? formatScalar(fovValue) + "°" : "—"
        var speedText = speedValue !== null ? formatScalar(speedValue) : "—"
        metrics.push({
            label: qsTrId("camera.hud.metric.fov") || qsTr("FOV / Speed"),
            value: fovText + " / " + speedText
        })

        var nearMm = data && data.nearPlane !== undefined
            ? telemetryToMillimetres(data.nearPlane)
            : (state ? Number(state.nearPlane) : null)
        var farMm = data && data.farPlane !== undefined
            ? telemetryToMillimetres(data.farPlane)
            : (state ? Number(state.farPlane) : null)
        var nearText = nearMm !== null && isFinite(nearMm) ? formatMeters(nearMm) : "—"
        var farText = farMm !== null && isFinite(farMm) ? formatMeters(farMm) : "—"
        metrics.push({
            label: qsTrId("camera.hud.metric.clip") || qsTr("Clip [m]"),
            value: nearText + " – " + farText
        })

        if (hud.showMotion) {
            var autoRotate = data && data.autoRotate !== undefined ? !!data.autoRotate : (state ? !!state.autoRotate : false)
            var autoSpeed = resolveNumber("autoRotateSpeed", state ? state.autoRotateSpeed : undefined)
            var autoText = autoRotate
                ? hud.labelOn + (autoSpeed !== null ? " (" + formatScalar(autoSpeed) + "°/s)" : "")
                : hud.labelOff
            metrics.push({
                label: qsTrId("camera.hud.metric.autorotate") || qsTr("Auto-rotate"),
                value: autoText
            })

            var moving = cameraController && cameraController.isMoving
            metrics.push({
                label: qsTrId("camera.hud.metric.motionstate") || qsTr("Motion state"),
                value: moving ? hud.labelMoving : hud.labelIdle
            })
        }

        if (hud.showDamping) {
            metrics.push({
                label: qsTrId("camera.hud.metric.damping") || qsTr("Damping [ms]"),
                value: formatDamping()
            })
        }

        var settleValue = data && data.motionSettlingMs !== undefined
            ? Number(data.motionSettlingMs)
            : (cameraController && cameraController.motionSettlingMs !== undefined
                ? Number(cameraController.motionSettlingMs)
                : null)
        if (isFinite(settleValue)) {
            metrics.push({
                label: qsTrId("camera.hud.metric.settle") || qsTr("Settle [ms]"),
                value: formatScalar(settleValue)
            })
        }

        var inertiaInfo = formatInertiaTelemetry()
        if (hud.showInertia && inertiaInfo) {
            metrics.push({
                label: qsTrId("camera.hud.metric.inertia") || qsTr("Inertia / Friction"),
                value: inertiaInfo
            })
        }

        var smoothingInfo = formatSmoothingTelemetry()
        if (hud.showSmoothing && smoothingInfo) {
            metrics.push({
                label: qsTrId("camera.hud.metric.smoothing") || qsTr("Smoothing [rotate/pan/zoom]"),
                value: smoothingInfo
            })
        }

        var presetInfo = formatPresetTelemetry()
        if (hud.showPreset && presetInfo) {
            metrics.push({
                label: qsTrId("camera.hud.metric.preset") || qsTr("Preset"),
                value: presetInfo
            })
        }

        var timestampInfo = formatTimestamp()
        if (hud.showTimestamp && timestampInfo) {
            metrics.push({
                label: qsTrId("camera.hud.metric.timestamp") || qsTr("Snapshot"),
                value: timestampInfo
            })
        }

        for (var i = 0; i < metrics.length; ++i) {
            var entry = metrics[i]
            if (!entry || typeof entry !== "object")
                continue
            if (!("value" in entry) || entry.value === undefined || entry.value === null) {
                entry.value = "—"
            } else if (typeof entry.value !== "string") {
                entry.value = String(entry.value)
            }
        }

        return metrics
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
        var components = []
        if (vector.x !== undefined && vector.y !== undefined && vector.z !== undefined) {
            components = [vector.x, vector.y, vector.z]
        } else if (vector.length === 3) {
            components = [vector[0], vector[1], vector[2]]
        } else {
            return "—"
        }
        return components
            .map(function (component) { return formatMeters(component) })
            .join(", ")
    }

    function formatDamping() {
        if (telemetry) {
            var rotation = Number(telemetry.rotationDampingMs)
            var distance = Number(telemetry.distanceDampingMs)
            var pan = Number(telemetry.panDampingMs)
            var parts = []
            if (isFinite(rotation) && rotation > 0)
                parts.push(formatScalar(rotation))
            if (isFinite(distance) && distance > 0)
                parts.push(formatScalar(distance))
            if (isFinite(pan) && pan > 0)
                parts.push(formatScalar(pan))
            if (parts.length)
                return parts.join(" / ")
        }

        if (!cameraState) {
            return "—"
        }
        var rawParts = [
            cameraState.rotationDampingMs,
            cameraState.distanceDampingMs,
            cameraState.panDampingMs
        ].map(function (value) { return String(value) })
        return rawParts.join(" / ")
    }

    function formatInertiaTelemetry() {
        if (!telemetry)
            return ""
        var enabled = telemetry.inertiaEnabled
        var inertia = Number(telemetry.inertia)
        var friction = Number(telemetry.friction)
        var parts = []
        if (enabled !== undefined)
            parts.push(enabled ? labelOn : labelOff)
        if (isFinite(inertia))
            parts.push("μ=" + formatScalar(inertia))
        if (isFinite(friction))
            parts.push("ƒ=" + formatScalar(friction))
        return parts.join(" • ")
    }

    function formatSmoothingTelemetry() {
        if (!telemetry)
            return ""
        var rotate = Number(telemetry.rotateSmoothing)
        var pan = Number(telemetry.panSmoothing)
        var zoom = Number(telemetry.zoomSmoothing)
        var entries = []
        if (isFinite(rotate))
            entries.push((qsTrId("camera.hud.metric.rotate") || qsTr("Rotate")) + "=" + formatScalar(rotate))
        if (isFinite(pan))
            entries.push((qsTrId("camera.hud.metric.pan.short") || qsTr("Pan")) + "=" + formatScalar(pan))
        if (isFinite(zoom))
            entries.push((qsTrId("camera.hud.metric.zoom") || qsTr("Zoom")) + "=" + formatScalar(zoom))
        return entries.join(" / ")
    }

    function formatPresetTelemetry() {
        if (!telemetry)
            return ""
        var label = telemetry.presetLabel
        if (label && typeof label === "object") {
            if (label.en)
                label = label.en
            else {
                for (var key in label) {
                    if (label.hasOwnProperty(key) && typeof label[key] === "string" && label[key].length) {
                        label = label[key]
                        break
                    }
                }
            }
        }
        var presetId = telemetry.presetId || telemetry.orbitPresetDefault
        var version = telemetry.orbitPresetVersion
        var labelText = typeof label === "string" && label.length ? label : ""

        var parts = []
        if (labelText.length)
            parts.push(labelText)
        if (typeof presetId === "string" && presetId.length) {
            if (!labelText.length || labelText.toLowerCase() !== presetId.toLowerCase())
                parts.push("#" + presetId)
        }
        if (version !== undefined && version !== null && version !== "") {
            parts.push("v" + version)
        }
        if (parts.length)
            return parts.join(" • ")
        return ""
    }

    function formatTimestamp() {
        if (!telemetry || !telemetry.timestamp)
            return ""
        return String(telemetry.timestamp)
    }
}
