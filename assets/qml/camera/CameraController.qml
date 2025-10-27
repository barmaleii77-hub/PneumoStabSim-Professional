import QtQuick
import QtQuick3D

/*
 * CameraController.qml - Main Camera System Controller
 * PneumoStabSim Professional - Phase 2
 * Version: 1.0.0
 *
 * Главный контроллер системы камеры.
 * Объединяет CameraState, CameraRig, MouseControls в единый API.
 * Предоставляет упрощенный интерфейс для main.qml.
 */
Item {
    id: controller

    // ===============================================================
    // VERSION INFO
    // ===============================================================
    readonly property string version: "1.0.0"
    readonly property string module: "CameraController"

    // ===============================================================
    // REQUIRED PROPERTIES (set by main.qml)
    // ===============================================================

    /**
     * Reference to worldRoot Node (parent for CameraRig)
     */
    required property Node worldRoot

    /**
     * Reference to View3D (for viewHeight in MouseControls)
     */
    property var view3d: null

    /**
     * SceneBridge instance injected from Python.
     */
    property var sceneBridge: null

    // ===============================================================
    // GEOMETRY PROPERTIES (for auto-fit/reset)
    // ===============================================================

    property real frameLength: 3200
    property real trackWidth: 1600
    property real frameHeight: 650
    property real beamSize: 120
    property real frameToPivot: frameLength / 2

    // ===============================================================
    // OPTIONAL PROPERTIES
    // ===============================================================

    /**
     * TAA motion adaptive
     */
    property bool taaMotionAdaptive: false

    /**
     * Controls visibility of the HUD overlay
     */
    property bool hudVisible: false

    /**
     * Arbitrary HUD configuration payload
     */
    property var hudSettings: ({})

    /**
     * Scene scale factor used for unit conversion (mm → m)
     */
    property real sceneScaleFactor: 1000.0

    /**
     * External callbacks
     */
    property var onToggleAnimation: null

    // ===============================================================
    // PUBLIC API - STATE ACCESS
    // ===============================================================

    /**
     * Direct access to camera state
     */
    readonly property alias state: cameraState

    /**
     * Direct access to camera rig
     */
    readonly property alias rig: cameraRig

    /**
     * Direct access to camera object
     */
    readonly property alias camera: cameraRig.camera

    /**
     * Direct access to mouse controls
     */
    readonly property alias mouseControls: mouseInput

    readonly property alias motionSettlingMs: mouseInput.motionSettlingMs

    // ===============================================================
    // PUBLIC API - CONVENIENCE PROPERTIES
    // ===============================================================

    // Position
    readonly property alias pivot: cameraState.pivot
    readonly property alias distance: cameraState.distance
    readonly property alias yawDeg: cameraState.yawDeg
    readonly property alias pitchDeg: cameraState.pitchDeg
    readonly property alias panX: cameraState.panX
    readonly property alias panY: cameraState.panY

    // Camera settings
    readonly property alias fov: cameraState.fov
    readonly property alias nearPlane: cameraState.nearPlane
    readonly property alias farPlane: cameraState.farPlane
    readonly property alias speed: cameraState.speed

    // Auto-rotation
    readonly property alias autoRotate: cameraState.autoRotate
    readonly property alias autoRotateSpeed: cameraState.autoRotateSpeed

    // Motion tracking
    readonly property alias isMoving: cameraState.isMoving

    signal hudToggleRequested()

    // ===============================================================
    // SIGNALS (forwarded from CameraState)
    // ===============================================================

    // ✅ Используем сигналы из CameraState напрямую через Connections
    // Не создаем дублирующие сигналы, чтобы избежать конфликта

    // ===============================================================
    // COMPONENTS
    // ===============================================================

    // 1. Camera State Management
    CameraState {
        id: cameraState
    }

    // 2. Camera 3D Rig
    CameraRig {
        id: cameraRig
        parent: controller.worldRoot
        cameraState: cameraState
        sceneScaleFactor: controller.sceneScaleFactor
    }

    // 3. Mouse & Keyboard Controls
    MouseControls {
        id: mouseInput
        anchors.fill: parent

        cameraState: cameraState
        camera: cameraRig.camera
        viewHeight: controller.view3d ? controller.view3d.height : 600
        taaMotionAdaptive: controller.taaMotionAdaptive

        onAutoFit: function() { controller.autoFitFrame() }
        onResetView: function() { controller.resetView() }
        onToggleAnimation: function() {
            if (controller.onToggleAnimation) {
                controller.onToggleAnimation()
            }
        }
        onToggleCameraHud: function() {
            controller.hudToggleRequested()
        }
    }

    CameraStateHud {
        id: cameraHud
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 12
        anchors.rightMargin: 12
        width: implicitWidth
        height: implicitHeight
        cameraController: controller
        settings: controller.hudSettings
        visible: controller.hudVisible
        opacity: controller.hudVisible ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: 120
                easing.type: Easing.InOutQuad
            }
        }
    }

    // 4. Auto-Rotation Timer
    Timer {
        id: autoRotationTimer
        running: cameraState.autoRotate
        interval: 16  // 60 FPS
        repeat: true

        onTriggered: {
            // Qt интерполирует правильно через SLERP - NO normalization!
            cameraState.yawDeg = cameraState.yawDeg + cameraState.autoRotateSpeed * 0.016 * 10

            if (taaMotionAdaptive) {
                cameraState.flagMotion()
            }
        }
    }

    // ===============================================================
    // PUBLIC FUNCTIONS
    // ===============================================================

    /**
     * Auto-fit camera to current frame geometry
     */
    function autoFitFrame(marginFactor) {
        console.log("📷 CameraController: auto-fit to frame...")

        cameraState.autoFitFrame(
            frameLength,
            trackWidth,
            frameHeight,
            beamSize,
            marginFactor,
            _effectiveFrameToPivot()
        )
    }

    /**
     * Soft reset view (preserves camera if in bounds)
     */
    function resetView() {
        console.log("📷 CameraController: reset view...")

        cameraState.resetView(beamSize, frameHeight, frameLength, _effectiveFrameToPivot())
    }

    /**
     * Full reset view to defaults
     */
    function fullResetView() {
        console.log("📷 CameraController: FULL reset view...")

        cameraState.fullResetView(
            beamSize,
            frameHeight,
            frameLength,
            trackWidth,
            1600,  // default trackWidth
            _effectiveFrameToPivot()
        )
    }

    /**
     * Update camera settings from Python
     *
     * @param params - camera parameters object
     */
    function applyCameraUpdates(params) {
        if (!params)
            return

        console.log("📷 CameraController: applying camera updates...")

        var numeric = Number(controller.sceneScaleFactor)
        var sceneScale = isFinite(numeric) && numeric > 0 ? numeric : 1000.0

        function toMillimeters(value) {
            if (value === undefined || value === null)
                return null
            var num = Number(value)
            if (!isFinite(num))
                return null
            return num * sceneScale
        }

        function coerceNumber(value) {
            var num = Number(value)
            return isFinite(num) ? num : null
        }

        var changed = false

        var fovValue = params.fov !== undefined ? params.fov : params.fieldOfView
        var fovNumeric = coerceNumber(fovValue)
        if (fovNumeric !== null) {
            cameraState.fov = fovNumeric
            changed = true
        }

        var nearSource = params.near !== undefined ? params.near : params.clipNear
        var nearMillimeters = toMillimeters(nearSource)
        if (nearMillimeters !== null) {
            cameraState.nearPlane = Math.max(0.1, nearMillimeters)
            changed = true
        }

        var farSource = params.far !== undefined ? params.far : params.clipFar
        var farMillimeters = toMillimeters(farSource)
        if (farMillimeters !== null) {
            cameraState.farPlane = Math.max(cameraState.nearPlane + 0.1, farMillimeters)
            changed = true
        }

        var speedNumeric = coerceNumber(params.speed)
        if (speedNumeric !== null) {
            cameraState.speed = Math.max(0.0, speedNumeric)
            changed = true
        }

        if (params.auto_rotate !== undefined) {
            cameraState.autoRotate = !!params.auto_rotate
            changed = true
        }

        var autoRotateSpeed = coerceNumber(params.auto_rotate_speed)
        if (autoRotateSpeed !== null) {
            cameraState.autoRotateSpeed = autoRotateSpeed
            changed = true
        }

        var yawSource = params.orbit_yaw !== undefined ? params.orbit_yaw : params.yaw
        var yawNumeric = coerceNumber(yawSource)
        if (yawNumeric !== null) {
            cameraState.yawDeg = yawNumeric
            changed = true
        }

        var pitchSource = params.orbit_pitch !== undefined ? params.orbit_pitch : params.pitch
        var pitchNumeric = coerceNumber(pitchSource)
        if (pitchNumeric !== null) {
            cameraState.pitchDeg = cameraState.clampPitch(pitchNumeric)
            changed = true
        }

        var distanceSource = params.orbit_distance !== undefined ? params.orbit_distance : params.distance
        var distanceMillimeters = toMillimeters(distanceSource)
        if (distanceMillimeters !== null) {
            cameraState.distance = cameraState.clampDistance(distanceMillimeters)
            changed = true
        }

        var pivotVector = params.orbit_target
        var pivotX = params.orbit_target_x
        var pivotY = params.orbit_target_y
        var pivotZ = params.orbit_target_z
        if (pivotVector && pivotX === undefined && pivotY === undefined && pivotZ === undefined) {
            pivotX = pivotVector.x !== undefined ? pivotVector.x : pivotVector[0]
            pivotY = pivotVector.y !== undefined ? pivotVector.y : pivotVector[1]
            pivotZ = pivotVector.z !== undefined ? pivotVector.z : pivotVector[2]
        }
        if (pivotX !== undefined || pivotY !== undefined || pivotZ !== undefined) {
            var currentPivot = cameraState.pivot
            var px = toMillimeters(pivotX)
            var py = toMillimeters(pivotY)
            var pz = toMillimeters(pivotZ)
            cameraState.pivot = Qt.vector3d(
                px !== null ? px : currentPivot.x,
                py !== null ? py : currentPivot.y,
                pz !== null ? pz : currentPivot.z
            )
            changed = true
        }

        var autoFitTriggered = false
        if (params.center_camera === true) {
            cameraState.autoFitFrame(
                frameLength,
                trackWidth,
                frameHeight,
                beamSize,
                1.15,
                _effectiveFrameToPivot()
            )
            autoFitTriggered = true
            changed = true
        }

        if (changed && !autoFitTriggered) {
            cameraState.cameraChanged()
        }

        console.log("   ✅ Camera updated successfully")
    }

    function _effectiveFrameToPivot() {
        var numeric = Number(frameToPivot)
        if (!isFinite(numeric)) {
            numeric = frameLength / 2
        }
        return numeric
    }

    /**
     * Update geometry parameters (for auto-fit/reset)
     *
     * @param params - geometry parameters object
     */
    function updateGeometry(params) {
        if (params.frameLength !== undefined) {
            var lengthValue = Number(params.frameLength)
            if (isFinite(lengthValue)) {
                frameLength = lengthValue
            }
        }

        if (params.frameHeight !== undefined) {
            var heightValue = Number(params.frameHeight)
            if (isFinite(heightValue)) {
                frameHeight = heightValue
            }
        }

        if (params.trackWidth !== undefined) {
            var trackValue = Number(params.trackWidth)
            if (isFinite(trackValue)) {
                trackWidth = trackValue
            }
        }

        if (params.beamSize !== undefined) {
            var beamValue = Number(params.beamSize)
            if (isFinite(beamValue)) {
                beamSize = beamValue
            }
        }

        if (params.frameToPivot !== undefined) {
            var pivotValue = Number(params.frameToPivot)
            if (isFinite(pivotValue)) {
                frameToPivot = pivotValue
            }
        }
    }

    // ===============================================================
    // BRIDGE INTEGRATION
    // ===============================================================
    function _applySceneBridgeState() {
        if (!sceneBridge)
            return

        if (sceneBridge.geometry && Object.keys(sceneBridge.geometry).length)
            updateGeometry(sceneBridge.geometry)

        if (sceneBridge.camera && Object.keys(sceneBridge.camera).length)
            applyCameraUpdates(sceneBridge.camera)
    }

    onSceneBridgeChanged: _applySceneBridgeState()

    Connections {
        target: sceneBridge
        enabled: !!sceneBridge

        function onGeometryChanged(payload) {
            if (payload)
                updateGeometry(payload)
        }

        function onCameraChanged(payload) {
            if (payload)
                applyCameraUpdates(payload)
        }
    }

    // ===============================================================
    // INITIALIZATION
    // ===============================================================

    Component.onCompleted: {
        if (!isFinite(frameToPivot)) {
            frameToPivot = frameLength / 2
        }

        console.log("═══════════════════════════════════════════")
        console.log("✅ CameraController initialized (v" + version + ")")
        console.log("═══════════════════════════════════════════")
        console.log("📷 Camera System Status:")
        console.log("   State:        " + cameraState.module + " v" + cameraState.version)
        console.log("   Rig:          " + cameraRig.module + " v" + cameraRig.version)
        console.log("   Controls:     " + mouseInput.module + " v" + mouseInput.version)
        console.log("   Auto-rotate:  " + (cameraState.autoRotate ? "ON" : "OFF"))
        console.log("   TAA adaptive: " + (taaMotionAdaptive ? "ON" : "OFF"))
        console.log("═══════════════════════════════════════════")
        console.log("🎯 Camera Controller ready!")
        console.log("═══════════════════════════════════════════")

        // Initial auto-fit
        autoFitFrame()

        _applySceneBridgeState()
    }
}
