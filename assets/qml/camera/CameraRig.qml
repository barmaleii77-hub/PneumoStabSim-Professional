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
     * Scene scale factor (mm ↔ scene units).
     * Значение передаётся из контроллера камеры и соответствует
     * `sceneScaleFactor` в SimulationRoot. Для совместимости
     * используем 1000 (мм в метры) по умолчанию.
     */
    property real sceneScaleFactor: 1000.0

    /**
     * Access to camera object
     */
    readonly property alias camera: perspectiveCamera

    /**
     * Access to pan node
     */
    readonly property alias panNode: localPanNode

    readonly property real _effectiveScale: {
        var numeric = Number(sceneScaleFactor)
        return numeric > 0 && isFinite(numeric) ? numeric : 1.0
    }

    function toSceneLength(mmValue) {
        var numeric = Number(mmValue)
        if (!isFinite(numeric)) {
            return 0.0
        }
        return numeric / _effectiveScale
    }

    function toSceneVector(vector) {
        if (!vector) {
            return Qt.vector3d(0, 0, 0)
        }
        var vx = vector.x !== undefined ? vector.x : vector[0]
        var vy = vector.y !== undefined ? vector.y : vector[1]
        var vz = vector.z !== undefined ? vector.z : vector[2]
        return Qt.vector3d(
            toSceneLength(vx),
            toSceneLength(vy),
            toSceneLength(vz)
        )
    }

    // ===============================================================
    // POSITION & ROTATION (bind to CameraState)
    // ===============================================================

    position: toSceneVector(cameraState.pivot)
    eulerRotation: Qt.vector3d(cameraState.pitchDeg, cameraState.yawDeg, 0)

    // ===============================================================
    // PAN NODE (local camera offset)
    // ===============================================================

    Node {
        id: localPanNode

        position: Qt.vector3d(
            toSceneLength(cameraState.panX),
            toSceneLength(cameraState.panY),
            0
        )

        // ===============================================================
        // PERSPECTIVE CAMERA
        // ===============================================================

        PerspectiveCamera {
            id: perspectiveCamera

            // Камера находится на distance от pivot вдоль локальной оси Z
            position: Qt.vector3d(
                0,
                0,
                Math.max(0.0001, toSceneLength(cameraState.distance))
            )

            // Camera properties (bind to CameraState)
            fieldOfView: cameraState.fov
            clipNear: Math.max(0.0001, toSceneLength(cameraState.nearPlane))
            clipFar: Math.max(0.1, toSceneLength(cameraState.farPlane))

            // ===============================================================
            // CAMERA INFO (for debugging)
            // ===============================================================

            Component.onCompleted: {
                console.log("✅ PerspectiveCamera initialized")
                console.log("   📷 Position:", position)
                console.log("   📷 FOV:", fieldOfView, "°")
                console.log("   📷 Near:", clipNear, "scene units | Far:", clipFar, "scene units")
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
