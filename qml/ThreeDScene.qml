#pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick3D 6.10
import QtQuick3D.Helpers 6.10

/**
 * Minimalistic 3D playground used by Phase 3 rendering diagnostics.
 *
 * The component intentionally mirrors a subset of the production scene so that
 * python-side tests can verify 3D payload contracts (primitives, lights,
 * camera controls) without requiring the full application shell. The scene
 * supports batched updates via `pendingPythonUpdates` and manual overrides
 * through `applyThreeDUpdates`.
 */
Item {
    id: root

    width: 960
    height: 640

    // ---------------------------------------------------------------------
    // Public API and observability
    // ---------------------------------------------------------------------
    property var pendingPythonUpdates: ({})
    property var lastAppliedBatch: ({})
    property alias interactionTelemetry: telemetry.state

    // Scene state snapshots (exposed for tests/bridges)
    property real orbitAzimuthDeg: 35.0
    property real orbitElevationDeg: 25.0
    property real orbitDistance: 8.0
    property vector3d orbitTarget: Qt.vector3d(0, 0.5, 0)
    property vector3d panOffset: Qt.vector3d(0, 0, 0)

    property color boxColor: Qt.rgba(0.38, 0.55, 0.78, 1)
    property color sphereColor: Qt.rgba(0.78, 0.44, 0.33, 1)
    property color cylinderColor: Qt.rgba(0.35, 0.74, 0.53, 1)

    property real boxScale: 1.2
    property real sphereScale: 0.9
    property real cylinderScale: 1.0

    property vector3d boxPosition: Qt.vector3d(-1.25, 0.5, 0)
    property vector3d spherePosition: Qt.vector3d(1.25, 0.65, 0)
    property vector3d cylinderPosition: Qt.vector3d(0, 0.9, -1.25)

    property real keyLightIntensity: 600.0
    property real fillLightIntensity: 280.0
    property real rimLightIntensity: 220.0

    property real cameraDamping: 0.2
    property real orbitRotationSpeed: 0.35
    property real panSpeed: 0.015
    property real zoomSpeed: 0.015

    signal frameRendered(var metrics)

    // ---------------------------------------------------------------------
    // Batch entrypoint
    // ---------------------------------------------------------------------
    function applyBatchedUpdates(updates) {
        var payload = updates || ({})
        var applied = ({})
        if (payload.threeD) {
            applyThreeDUpdates(payload.threeD)
            applied.threeD = true
        }
        if (payload.lighting) {
            applyLightingOverrides(payload.lighting)
            applied.lighting = true
        }
        if (payload.camera) {
            applyCameraOverrides(payload.camera)
            applied.camera = true
        }
        lastAppliedBatch = applied
        return applied
    }

    onPendingPythonUpdatesChanged: applyBatchedUpdates(pendingPythonUpdates)

    // ---------------------------------------------------------------------
    // Update helpers
    // ---------------------------------------------------------------------
    function applyThreeDUpdates(params) {
        var normalized = _normalizeMap(params)
        if (normalized.camera)
            applyCameraOverrides(normalized.camera)
        if (normalized.primitives)
            applyPrimitiveOverrides(normalized.primitives)
        if (normalized.lighting)
            applyLightingOverrides(normalized.lighting)
        if (normalized.interaction)
            telemetry.registerInteraction(normalized.interaction)
        if (normalized.zoom !== undefined)
            _applyZoom(normalized.zoom)
    }

    function applyCameraOverrides(payload) {
        var cam = _normalizeMap(payload)
        if (cam.azimuth !== undefined)
            orbitAzimuthDeg = Number(cam.azimuth)
        if (cam.elevation !== undefined)
            orbitElevationDeg = Number(cam.elevation)
        if (cam.distance !== undefined && cam.distance > 0)
            orbitDistance = Number(cam.distance)
        if (cam.target)
            orbitTarget = _toVector3d(cam.target)
        if (cam.pan)
            panOffset = _toVector3d(cam.pan)
        if (cam.damping !== undefined)
            cameraDamping = Math.max(0.0, Number(cam.damping))
        _syncCamera()
    }

    function applyPrimitiveOverrides(payload) {
        var data = _normalizeMap(payload)
        if (data.box) {
            var box = _normalizeMap(data.box)
            if (box.color) boxColor = _toColor(box.color, boxColor)
            if (box.scale !== undefined) boxScale = _positive(box.scale, boxScale)
            if (box.position) boxPosition = _toVector3d(box.position)
        }
        if (data.sphere) {
            var sphere = _normalizeMap(data.sphere)
            if (sphere.color) sphereColor = _toColor(sphere.color, sphereColor)
            if (sphere.scale !== undefined) sphereScale = _positive(sphere.scale, sphereScale)
            if (sphere.position) spherePosition = _toVector3d(sphere.position)
        }
        if (data.cylinder) {
            var cyl = _normalizeMap(data.cylinder)
            if (cyl.color) cylinderColor = _toColor(cyl.color, cylinderColor)
            if (cyl.scale !== undefined) cylinderScale = _positive(cyl.scale, cylinderScale)
            if (cyl.position) cylinderPosition = _toVector3d(cyl.position)
        }
    }

    function applyLightingOverrides(payload) {
        var lighting = _normalizeMap(payload)
        if (lighting.keyIntensity !== undefined)
            keyLightIntensity = _positive(lighting.keyIntensity, keyLightIntensity)
        if (lighting.fillIntensity !== undefined)
            fillLightIntensity = _positive(lighting.fillIntensity, fillLightIntensity)
        if (lighting.rimIntensity !== undefined)
            rimLightIntensity = _positive(lighting.rimIntensity, rimLightIntensity)
        if (lighting.ambient) {
            var ambient = _normalizeMap(lighting.ambient)
            if (ambient.color)
                sceneEnvironment.clearColor = _toColor(ambient.color, sceneEnvironment.clearColor)
        }
    }

    // ---------------------------------------------------------------------
    // Input handlers (rotate / pan / zoom)
    // ---------------------------------------------------------------------
    function _applyOrbitDrag(dx, dy) {
        orbitAzimuthDeg -= dx * orbitRotationSpeed
        orbitElevationDeg = Math.max(-80, Math.min(80, orbitElevationDeg - dy * orbitRotationSpeed))
        telemetry.registerInteraction({ kind: "rotate", dx: dx, dy: dy })
        _syncCamera()
    }

    function _applyPan(dx, dy) {
        var delta = Qt.vector3d(dx * panSpeed, 0, dy * panSpeed)
        panOffset = Qt.vector3d(panOffset.x + delta.x, panOffset.y, panOffset.z + delta.z)
        telemetry.registerInteraction({ kind: "pan", dx: dx, dy: dy })
        _syncCamera()
    }

    function _applyZoom(step) {
        var factor = 1.0 + step * zoomSpeed
        orbitDistance = Math.max(2.0, Math.min(60.0, orbitDistance * factor))
        telemetry.registerInteraction({ kind: "zoom", delta: step })
        _syncCamera()
    }

    // ---------------------------------------------------------------------
    // Internal helpers
    // ---------------------------------------------------------------------
    function _normalizeMap(value) {
        if (!value || typeof value !== "object")
            return ({})
        return value
    }

    function _toVector3d(value) {
        if (value === undefined || value === null)
            return Qt.vector3d(0, 0, 0)
        if (value.x !== undefined && value.y !== undefined && value.z !== undefined)
            return Qt.vector3d(Number(value.x), Number(value.y), Number(value.z))
        if (Array.isArray(value) && value.length >= 3)
            return Qt.vector3d(Number(value[0]), Number(value[1]), Number(value[2]))
        return Qt.vector3d(0, 0, 0)
    }

    function _toColor(value, fallback) {
        if (value === undefined || value === null)
            return fallback
        try {
            return Qt.color(value)
        } catch (error) {
            return fallback
        }
    }

    function _positive(value, fallback) {
        var n = Number(value)
        return isFinite(n) && n > 0 ? n : fallback
    }

    function _orbitPosition() {
        var azimuthRad = orbitAzimuthDeg * Math.PI / 180.0
        var elevationRad = orbitElevationDeg * Math.PI / 180.0
        var x = Math.cos(elevationRad) * Math.sin(azimuthRad) * orbitDistance
        var y = Math.sin(elevationRad) * orbitDistance
        var z = Math.cos(elevationRad) * Math.cos(azimuthRad) * orbitDistance
        return Qt.vector3d(x + orbitTarget.x + panOffset.x, y + orbitTarget.y + panOffset.y, z + orbitTarget.z + panOffset.z)
    }

    function _syncCamera() {
        cameraTransform.translation = _orbitPosition()
        sceneCamera.lookAt(Qt.vector3d(orbitTarget.x + panOffset.x, orbitTarget.y + panOffset.y, orbitTarget.z + panOffset.z), Qt.vector3d(0, 1, 0))
    }

    Component.onCompleted: _syncCamera()

    Rectangle {
        anchors.fill: parent
        color: "transparent"
    }

    View3D {
        id: sceneView
        anchors.fill: parent
        renderMode: View3D.Underlay
        environment: SceneEnvironment {
            id: sceneEnvironment
            clearColor: Qt.rgba(0.06, 0.09, 0.13, 1.0)
            backgroundMode: SceneEnvironment.Color
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        PerspectiveCamera {
            id: sceneCamera
            clipFar: 2000
            clipNear: 0.1
            fieldOfView: 55
            position: _orbitPosition()
            lookAt: Qt.vector3d(orbitTarget.x, orbitTarget.y, orbitTarget.z)
        }

        Node {
            id: cameraTransform
            position: sceneCamera.position
        }

        DirectionalLight {
            id: keyLight
            eulerRotation.x: -45
            eulerRotation.y: -35
            brightness: keyLightIntensity
            castsShadow: true
        }

        PointLight {
            id: fillLight
            position: Qt.vector3d(-3, 4, 3)
            brightness: fillLightIntensity
            castsShadow: false
        }

        PointLight {
            id: rimLight
            position: Qt.vector3d(3, 2.5, -4)
            brightness: rimLightIntensity
            castsShadow: false
        }

        Model {
            id: groundPlane
            source: "#Plane"
            scale: Qt.vector3d(10, 1, 10)
            position: Qt.vector3d(0, 0, 0)
            materials: PrincipledMaterial {
                baseColor: Qt.rgba(0.12, 0.16, 0.2, 1)
                roughness: 0.8
                metalness: 0.0
            }
        }

        Model {
            id: boxPrimitive
            objectName: "boxPrimitive"
            source: "#Cube"
            scale: Qt.vector3d(boxScale, boxScale, boxScale)
            position: boxPosition
            materials: PrincipledMaterial {
                baseColor: boxColor
                roughness: 0.35
                metalness: 0.18
            }
        }

        Model {
            id: spherePrimitive
            objectName: "spherePrimitive"
            source: "#Sphere"
            scale: Qt.vector3d(sphereScale, sphereScale, sphereScale)
            position: spherePosition
            materials: PrincipledMaterial {
                baseColor: sphereColor
                roughness: 0.15
                metalness: 0.35
            }
        }

        Model {
            id: cylinderPrimitive
            objectName: "cylinderPrimitive"
            source: "#Cylinder"
            scale: Qt.vector3d(cylinderScale, cylinderScale, cylinderScale)
            position: cylinderPosition
            materials: PrincipledMaterial {
                baseColor: cylinderColor
                roughness: 0.42
                metalness: 0.12
            }
        }

        Timer {
            interval: 16
            running: true
            repeat: true
            onTriggered: frameRendered({
                timestamp: Date.now(),
                cameraPosition: sceneCamera.position,
                target: Qt.vector3d(orbitTarget.x + panOffset.x, orbitTarget.y + panOffset.y, orbitTarget.z + panOffset.z),
                distance: orbitDistance
            })
        }

        // Input: orbit (LMB/primary), pan (MMB), zoom (wheel/pinch)
        DragHandler {
            id: orbitDrag
            acceptedButtons: Qt.LeftButton
            target: null
            onActiveChanged: telemetry.registerInteraction({ kind: "drag", active: active })
            onTranslationChanged: _applyOrbitDrag(translation.x, translation.y)
        }

        DragHandler {
            id: panDrag
            acceptedButtons: Qt.MiddleButton
            target: null
            onTranslationChanged: _applyPan(translation.x, translation.y)
        }

        WheelHandler {
            id: zoomWheel
            rotationScale: 1.0
            onWheel: _applyZoom(wheel.angleDelta.y / 120.0)
        }

        PinchHandler {
            id: pinchZoom
            onScaleChanged: _applyZoom(scale - 1.0)
        }
    }

    QtObject {
        id: telemetry
        property var state: ({
            lastKind: "",
            lastDelta: 0,
            lastDx: 0,
            lastDy: 0,
            interactions: []
        })

        function registerInteraction(payload) {
            var normalized = payload || ({})
            var next = ({
                lastKind: normalized.kind || state.lastKind,
                lastDelta: normalized.delta !== undefined ? normalized.delta : state.lastDelta,
                lastDx: normalized.dx !== undefined ? normalized.dx : state.lastDx,
                lastDy: normalized.dy !== undefined ? normalized.dy : state.lastDy,
                interactions: state.interactions.slice(-4)
            })
            next.interactions.push({
                at: Date.now(),
                kind: normalized.kind || "unknown",
                delta: normalized.delta || 0,
                dx: normalized.dx || 0,
                dy: normalized.dy || 0
            })
            state = next
        }
    }
}
