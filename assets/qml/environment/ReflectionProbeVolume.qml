import QtQuick
import QtQuick3D

ReflectionProbe {
    id: probe

    property vector3d pivot: Qt.vector3d(0, 0, 0)
    property real trackWidth: 1600.0
    property real frameHeight: 650.0
    property real frameLength: 3200.0
    property real padding: 0.0
    property string qualitySetting: "veryhigh"
    property string refreshModeSetting: "everyframe"
    property string timeSlicingSetting: "individualfaces"
    property bool probeEnabled: true

    readonly property real _clampedTrackWidth: Math.max(1.0, trackWidth)
    readonly property real _clampedFrameHeight: Math.max(1.0, frameHeight)
    readonly property real _clampedFrameLength: Math.max(1.0, frameLength)
    readonly property real _clampedPadding: Math.max(0.0, padding)

    position: probe.pivot
    boxSize: Qt.vector3d(
                 _clampedTrackWidth + 2.0 * _clampedPadding,
                 _clampedFrameHeight + 2.0 * _clampedPadding,
                 _clampedFrameLength + 2.0 * _clampedPadding)
    parallaxCorrection: true
    quality: resolveQuality(qualitySetting)
    refreshMode: resolveRefreshMode(refreshModeSetting)
    timeSlicing: resolveTimeSlicing(timeSlicingSetting)

    function syncEnabledState() {
        try {
            // qmllint disable missing-property
            if (probe.setProperty !== undefined) {
                if (probe.setProperty("enabled", probe.probeEnabled)) {
            // qmllint enable missing-property
                    return
                }
            }
        } catch (error) {
            console.warn("ReflectionProbeVolume: unable to toggle enabled state", error)
            return
        }

        // Fallback for runtimes without an enabled property
        console.warn("ReflectionProbeVolume: 'enabled' property is unavailable; probeEnabled will be ignored")
    }

    Component.onCompleted: syncEnabledState()
    onProbeEnabledChanged: syncEnabledState()

    function resolveQuality(setting) {
        const normalized = String(setting || "").toLowerCase()
        switch (normalized) {
        case "low":
            return ReflectionProbe.Low
        case "medium":
            return ReflectionProbe.Medium
        case "high":
            return ReflectionProbe.High
        case "veryhigh":
        case "very_high":
            return ReflectionProbe.VeryHigh
        default:
            return ReflectionProbe.VeryHigh
        }
    }

    function resolveRefreshMode(setting) {
        const normalized = String(setting || "").toLowerCase()
        switch (normalized) {
        case "firstframe":
        case "first_frame":
        case "first":
            return ReflectionProbe.FirstFrame
        case "never":
        case "disabled":
        case "off":
            return ReflectionProbe.FirstFrame
        case "everyframe":
        case "always":
        default:
            return ReflectionProbe.EveryFrame
        }
    }

    function resolveTimeSlicing(setting) {
        const normalized = String(setting || "").toLowerCase()
        switch (normalized) {
        case "allfacesatonce":
        case "all_faces_at_once":
        case "allfaces":
            return ReflectionProbe.AllFacesAtOnce
        case "notimeslicing":
        case "no_time_slicing":
        case "none":
            return ReflectionProbe.None
        case "individualfaces":
        case "perface":
        default:
            return ReflectionProbe.IndividualFaces
        }
    }
}
