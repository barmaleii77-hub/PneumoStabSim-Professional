import QtQuick

/*
 * MouseControls.qml - Mouse & Keyboard Input Handler
 * PneumoStabSim Professional - Phase 2
 * Version: 1.0.0
 *
 * Обработка пользовательского ввода:
 * - ЛКМ: вращение камеры (orbital)
 * - ПКМ: panning (локальное перемещение)
 * - Колесо: zoom (изменение distance)
 * - Двойной клик: reset view
 * - Клавиши: R (reset), F (auto-fit), Space (toggle animation)
 */
MouseArea {
    id: mouseControls

    // ===============================================================
    // VERSION INFO
    // ===============================================================
    readonly property string version: "1.0.0"
    readonly property string module: "MouseControls"

    // ===============================================================
    // REQUIRED PROPERTIES
    // ===============================================================

    /**
     * Reference to CameraState
     */
    required property var cameraState

    /**
     * Reference to camera object (for pan calculation)
     */
    required property var camera

    /**
     * View height (for pan world-space calculation)
     */
    required property real viewHeight

    // ===============================================================
    // OPTIONAL PROPERTIES
    // ===============================================================

    /**
     * TAA motion adaptive enabled
     */
    property bool taaMotionAdaptive: false

    /**
     * Callback for auto-fit (external)
     */
    property var onAutoFit: null

    /**
     * Callback for reset view (external)
     */
    property var onResetView: null

    /**
     * Callback for toggle animation (external)
     */
    property var onToggleAnimation: null

    /**
     * Callback for toggling the camera HUD (Ctrl+H)
     */
    property var onToggleCameraHud: null

    /**
     * Duration (ms) after which motion is considered settled
     */
    readonly property int motionSettlingMs: cameraMotionSettler.interval

    // ===============================================================
    // MOUSE STATE
    // ===============================================================

    property bool mouseDown: false
    property int mouseButton: 0
    property real lastX: 0
    property real lastY: 0

    // ===============================================================
    // CONFIGURATION
    // ===============================================================

    anchors.fill: parent
    hoverEnabled: true
    acceptedButtons: Qt.LeftButton | Qt.RightButton
    focus: true  // Для keyboard events

    // ===============================================================
    // MOUSE HANDLERS
    // ===============================================================

    onPressed: (mouse) => {
        // ✅ Правильная инициализация для избежания рывка
        mouseDown = true
        mouseButton = mouse.button
        lastX = mouse.x
        lastY = mouse.y

        if (taaMotionAdaptive) {
            cameraState.flagMotion()
        }

        console.log("🖱️ Mouse pressed: button =", mouse.button, "at", mouse.x, mouse.y)
    }

    onReleased: (mouse) => {
        mouseDown = false
        mouseButton = 0

        if (taaMotionAdaptive) {
            cameraMotionSettler.restart()
        }

        console.log("🖱️ Mouse released")
    }

    onPositionChanged: (mouse) => {
        if (!mouseDown) return

        var dx = mouse.x - lastX
        var dy = mouse.y - lastY

        // ✅ Проверяем на разумные значения delta для избежания рывков
        if (Math.abs(dx) > 100 || Math.abs(dy) > 100) {
            console.log("⚠️ Ignoring large mouse delta:", dx, dy)
            lastX = mouse.x
            lastY = mouse.y
            return
        }

        if (mouseButton === Qt.LeftButton) {
            // ✅ ROTATION (orbital)
            // Qt сам знает как интерполировать через SLERP - NO manual normalization!
            cameraState.yawDeg = cameraState.yawDeg - dx * cameraState.rotateSpeed
            cameraState.pitchDeg = cameraState.clampPitch(
                cameraState.pitchDeg - dy * cameraState.rotateSpeed
            )

        } else if (mouseButton === Qt.RightButton) {
            // ✅ PANNING (local camera movement)
            // Рассчитываем world-space movement из pixel delta

            var fovRad = camera.fieldOfView * Math.PI / 180.0
            var worldPerPixel = (2 * cameraState.distance * Math.tan(fovRad / 2)) / viewHeight
            var speed = worldPerPixel * cameraState.speed

            cameraState.panX -= dx * speed
            cameraState.panY += dy * speed
        }

        lastX = mouse.x
        lastY = mouse.y

        if (taaMotionAdaptive) {
            cameraState.flagMotion()
        }
    }

    onWheel: (wheel) => {
        // ✅ ZOOM (изменение distance)
        var zoomFactor = 1.0 + (wheel.angleDelta.y / 1200.0)

        cameraState.distance = cameraState.clampDistance(
            cameraState.distance * zoomFactor
        )

        if (taaMotionAdaptive) {
            cameraState.flagMotion()
        }
    }

    onDoubleClicked: () => {
        console.log("🖱️ Double-click: resetting view")

        if (onResetView) {
            onResetView()
        }
    }

    // ===============================================================
    // KEYBOARD HANDLERS
    // ===============================================================

    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_R) {
            // Reset view
            console.log("⌨️ Key R: reset view")

            if (onResetView) {
                onResetView()
            }

            event.accepted = true

        } else if (event.key === Qt.Key_F) {
            // Auto-fit frame
            console.log("⌨️ Key F: auto-fit frame")

            if (onAutoFit) {
                onAutoFit()
            }

            event.accepted = true

        } else if (event.key === Qt.Key_Space) {
            // Toggle animation
            console.log("⌨️ Key Space: toggle animation")

            if (onToggleAnimation) {
                onToggleAnimation()
            }

            event.accepted = true
        } else if (event.key === Qt.Key_H && (event.modifiers & Qt.ControlModifier)) {
            console.log("⌨️ Ctrl+H: toggle camera HUD")

            if (onToggleCameraHud) {
                onToggleCameraHud()
            }

            event.accepted = true
        }
    }

    // ===============================================================
    // CAMERA MOTION SETTLER (for TAA)
    // ===============================================================

    Timer {
        id: cameraMotionSettler
        interval: 240
        repeat: false
        onTriggered: {
            mouseControls.cameraState.clearMotion()
        }
    }

    // ===============================================================
    // INITIALIZATION
    // ===============================================================

    Component.onCompleted: {
        console.log("✅ MouseControls initialized (v" + version + ")")
        console.log("   🖱️ Left button: rotation")
        console.log("   🖱️ Right button: panning")
        console.log("   🖱️ Wheel: zoom")
        console.log("   🖱️ Double-click: reset view")
        console.log("   ⌨️ Keys: R (reset), F (auto-fit), Space (animation), Ctrl+H (camera HUD)")
    }
}
