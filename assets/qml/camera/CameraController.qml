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
            marginFactor
        )
    }

    /**
     * Soft reset view (preserves camera if in bounds)
     */
    function resetView() {
        console.log("📷 CameraController: reset view...")

        cameraState.resetView(beamSize, frameHeight, frameLength)
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
            1600  // default trackWidth
        )
    }

    /**
     * Update camera settings from Python
     *
     * @param params - camera parameters object
     */
    function applyCameraUpdates(params) {
        console.log("📷 CameraController: applying camera updates...")

        if (params.fov !== undefined) {
            cameraState.fov = Number(params.fov)
        }

        if (params.near !== undefined) {
            cameraState.nearPlane = Number(params.near)
        }

        if (params.far !== undefined) {
            cameraState.farPlane = Number(params.far)
        }

        if (params.speed !== undefined) {
            cameraState.speed = Number(params.speed)
        }

        if (params.auto_rotate !== undefined) {
            cameraState.autoRotate = !!params.auto_rotate
        }

        if (params.auto_rotate_speed !== undefined) {
            cameraState.autoRotateSpeed = Number(params.auto_rotate_speed)
        }

        console.log("   ✅ Camera updated successfully")
        // ✅ Вызываем сигнал из cameraState
        cameraState.cameraChanged()
    }

    /**
     * Update geometry parameters (for auto-fit/reset)
     *
     * @param params - geometry parameters object
     */
    function updateGeometry(params) {
        if (params.frameLength !== undefined) {
            frameLength = params.frameLength
        }

        if (params.frameHeight !== undefined) {
            frameHeight = params.frameHeight
        }

        if (params.trackWidth !== undefined) {
            trackWidth = params.trackWidth
        }

        if (params.beamSize !== undefined) {
            beamSize = params.beamSize
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
