import QtQuick
import QtQuick3D

/*
 * CameraRig.qml - 3D Camera Rig Structure
 * PneumoStabSim Professional - Phase 2
 * Version: 1.0.0
 *
 * 3D Node hierarchy для orbital camera:
 * cameraRig (pivot + rotation) → panNode (local offset) → camera
 */
Node {
    id: cameraRig

    // ===============================================================
    // VERSION INFO
    // ===============================================================
    readonly property string version: "1.0.0"
    readonly property string module: "CameraRig"

    // ===============================================================
    // REQUIRED PROPERTIES (must be set by parent)
    // ===============================================================

    /**
     * Reference to CameraState
     */
    required property var cameraState

    // ===============================================================
    // PUBLIC API
    // ===============================================================

    /**
     * Access to camera object
     */
    readonly property alias camera: perspectiveCamera

    /**
     * Access to pan node
     */
    readonly property alias panNode: localPanNode

    // ===============================================================
    // POSITION & ROTATION (bind to CameraState)
    // ===============================================================

    position: cameraState.pivot
    eulerRotation: Qt.vector3d(cameraState.pitchDeg, cameraState.yawDeg, 0)

    // ===============================================================
    // PAN NODE (local camera offset)
    // ===============================================================

    Node {
        id: localPanNode

        position: Qt.vector3d(cameraState.panX, cameraState.panY, 0)

        // ===============================================================
        // PERSPECTIVE CAMERA
        // ===============================================================

        PerspectiveCamera {
            id: perspectiveCamera

            // Камера находится на distance от pivot вдоль локальной оси Z
            position: Qt.vector3d(0, 0, cameraState.distance)

            // Camera properties (bind to CameraState)
            fieldOfView: cameraState.fov
            clipNear: cameraState.nearPlane
            clipFar: cameraState.farPlane

            // ===============================================================
            // CAMERA INFO (for debugging)
            // ===============================================================

            Component.onCompleted: {
                console.log("✅ PerspectiveCamera initialized")
                console.log("   📷 Position:", position)
                console.log("   📷 FOV:", fieldOfView, "°")
                console.log("   📷 Near:", clipNear, "mm | Far:", clipFar, "mm")
            }
        }

        Component.onCompleted: {
            console.log("✅ PanNode initialized")
            console.log("   📷 Local offset:", position)
        }
    }

    // ===============================================================
    // INITIALIZATION
    // ===============================================================

    Component.onCompleted: {
        console.log("✅ CameraRig initialized (v" + version + ")")
        console.log("   📷 Pivot:", position)
        console.log("   📷 Rotation: Yaw", eulerRotation.y, "° | Pitch", eulerRotation.x, "°")
    }

    // ===============================================================
    // DEBUG: Log rotation changes
    // ===============================================================

    onEulerRotationChanged: {
        // Можно раскомментировать для отладки
        // console.log("📷 Camera rotation changed: Yaw", eulerRotation.y, "° | Pitch", eulerRotation.x, "°")
    }
}
