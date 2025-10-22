// MouseEventLogger.qml
// Компонент для логирования всех действий мыши на 3D канве
import QtQuick

MouseArea {
    id: mouseLogger

    // Properties
    property bool enableLogging: true
    property string componentName: "main.qml"

    // Tracking state
    property real lastX: 0
    property real lastY: 0
    property bool isDragging: false

    anchors.fill: parent
    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

    // Mouse Press
    onPressed: (mouse) => {
        if (!enableLogging) return;

        lastX = mouse.x;
        lastY = mouse.y;
        isDragging = false;

        let buttonName = "unknown";
        if (mouse.button === Qt.LeftButton) buttonName = "left";
        else if (mouse.button === Qt.RightButton) buttonName = "right";
        else if (mouse.button === Qt.MiddleButton) buttonName = "middle";

        console.log(
            "[EVENT] MOUSE_PRESS:",
            JSON.stringify({
                component: componentName,
                action: "mouse_press",
                x: mouse.x,
                y: mouse.y,
                button: buttonName,
                modifiers: {
                    ctrl: mouse.modifiers & Qt.ControlModifier,
                    shift: mouse.modifiers & Qt.ShiftModifier,
                    alt: mouse.modifiers & Qt.AltModifier
                }
            })
        );
    }

    // Mouse Move (Drag)
    onPositionChanged: (mouse) => {
        if (!enableLogging) return;
        if (!pressed) return; // Игнорируем движение без нажатия

        let deltaX = mouse.x - lastX;
        let deltaY = mouse.y - lastY;

        // Логируем только если реальное движение (не шум)
        if (Math.abs(deltaX) > 1 || Math.abs(deltaY) > 1) {
            if (!isDragging) {
                isDragging = true;
                console.log("[EVENT] MOUSE_DRAG: started");
            }

            console.log(
                "[EVENT] MOUSE_DRAG:",
                JSON.stringify({
                    component: componentName,
                    action: "mouse_drag",
                    delta_x: deltaX,
                    delta_y: deltaY,
                    abs_x: mouse.x,
                    abs_y: mouse.y
                })
            );

            lastX = mouse.x;
            lastY = mouse.y;
        }
    }

    // Mouse Release
    onReleased: (mouse) => {
        if (!enableLogging) return;

        console.log(
            "[EVENT] MOUSE_RELEASE:",
            JSON.stringify({
                component: componentName,
                action: "mouse_release",
                was_dragging: isDragging,
                x: mouse.x,
                y: mouse.y
            })
        );

        isDragging = false;
    }

    // Mouse Wheel (Zoom)
    onWheel: (wheel) => {
        if (!enableLogging) return;

        console.log(
            "[EVENT] MOUSE_WHEEL:",
            JSON.stringify({
                component: componentName,
                action: "mouse_wheel",
                delta: wheel.angleDelta.y,
                x: wheel.x,
                y: wheel.y,
                modifiers: {
                    ctrl: wheel.modifiers & Qt.ControlModifier,
                    shift: wheel.modifiers & Qt.ShiftModifier,
                    alt: wheel.modifiers & Qt.AltModifier
                }
            })
        );
    }
}
