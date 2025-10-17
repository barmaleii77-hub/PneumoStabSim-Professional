import QtQuick
import "../core" as Core

/*
 * CameraState.qml - Camera State Management
 * PneumoStabSim Professional - Phase 2
 * Version: 1.0.0
 * 
 * Управление состоянием камеры: позиция, вращение, параметры.
 * Включает smooth behaviors и auto-rotation logic.
 */
QtObject {
    id: cameraState
    
    // ===============================================================
    // VERSION INFO
    // ===============================================================
    readonly property string version: "1.0.0"
    readonly property string module: "CameraState"
    
    // ===============================================================
    // PIVOT & POSITION
    // ===============================================================
    
    /**
     * Pivot point (центр вращения камеры)
     * По умолчанию - центр рамы подвески
     */
    property vector3d pivot: Qt.vector3d(0, 0, 0)
    
    /**
     * Расстояние камеры от pivot point (в мм)
     */
    property real distance: 3500
    
    /**
     * Минимальное/максимальное расстояние
     */
    readonly property real minDistance: 150
    readonly property real maxDistance: 30000
    
    // ===============================================================
    // ROTATION (Orbital Camera)
    // ===============================================================
    
    /**
     * Yaw (горизонтальное вращение) в градусах
     * 0° = вид с востока, 90° = вид с севера, 180° = вид с запада
     */
    property real yawDeg: 225
    
    /**
     * Pitch (вертикальное вращение) в градусах
     * 0° = горизонт, -90° = вид сверху, +90° = вид снизу
     */
    property real pitchDeg: -25
    
    /**
     * Ограничения pitch (избежание gimbal lock)
     */
    readonly property real minPitchDeg: -89
    readonly property real maxPitchDeg: 89
    
    // ===============================================================
    // PANNING (Local Camera Movement)
    // ===============================================================
    
    /**
     * Pan offset по локальным осям камеры (в мм)
     */
    property real panX: 0
    property real panY: 0
    
    // ===============================================================
    // CAMERA PROPERTIES
    // ===============================================================
    
    /**
     * Field of View (в градусах)
     */
    property real fov: 60.0
    
    /**
     * Near/Far clipping planes (в мм)
     */
    property real nearPlane: 10.0
    property real farPlane: 50000.0
    
    /**
     * Camera movement speed multiplier
     */
    property real speed: 1.0
    
    // ===============================================================
    // MOUSE CONTROL SETTINGS
    // ===============================================================
    
    /**
     * Mouse rotation sensitivity
     */
    property real rotateSpeed: 0.35
    
    // ===============================================================
    // AUTO-ROTATION
    // ===============================================================
    
    /**
     * Auto-rotation enabled/disabled
     */
    property bool autoRotate: false
    
    /**
     * Auto-rotation speed (degrees per second)
     */
    property real autoRotateSpeed: 0.5
    
    // ===============================================================
    // MOTION TRACKING (for TAA)
    // ===============================================================
    
    /**
     * Camera is currently moving (for TAA motion adaptive)
     */
    property bool isMoving: false
    
    // ===============================================================
    // SMOOTH BEHAVIORS
    // ===============================================================
    
    Behavior on yawDeg {
        NumberAnimation {
            duration: 90
            easing.type: Easing.OutCubic
        }
    }
    
    Behavior on pitchDeg {
        NumberAnimation {
            duration: 90
            easing.type: Easing.OutCubic
        }
    }
    
    Behavior on distance {
        NumberAnimation {
            duration: 90
            easing.type: Easing.OutCubic
        }
    }
    
    Behavior on panX {
        NumberAnimation {
            duration: 60
            easing.type: Easing.OutQuad
        }
    }
    
    Behavior on panY {
        NumberAnimation {
            duration: 60
            easing.type: Easing.OutQuad
        }
    }
    
    // ===============================================================
    // SIGNALS
    // ===============================================================
    
    signal viewReset()
    signal cameraChanged()
    
    // ===============================================================
    // FUNCTIONS
    // ===============================================================
    
    /**
     * Рассчитать оптимальное расстояние камеры для фрейма
     * 
     * @param frameLength - длина рамы (мм)
     * @param trackWidth - колея (мм)
     * @param frameHeight - высота рамы (мм)
     * @param margin - запас (1.0 = без запаса, 1.5 = +50%)
     */
    function calculateOptimalDistance(frameLength, trackWidth, frameHeight, margin) {
        if (margin === undefined) {
            margin = 1.15
        }
        
        // Используем GeometryCalculations для расчета
        var optimalDist = Core.GeometryCalculations.calculateOptimalCameraDistance(
            frameLength, frameHeight, trackWidth, fov, margin
        )
        
        // Применяем с ограничениями
        return Core.MathUtils.clamp(optimalDist, minDistance, maxDistance)
    }
    
    /**
     * Рассчитать pivot point для текущей геометрии
     * 
     * @param beamSize - размер балки (мм)
     * @param frameHeight - высота рамы (мм)
     * @param frameLength - длина рамы (мм)
     */
    function calculatePivot(beamSize, frameHeight, frameLength) {
        return Core.GeometryCalculations.calculateCameraPivot(
            beamSize, frameHeight, frameLength
        )
    }
    
    /**
     * Auto-fit camera to frame
     * 
     * @param frameLength - длина рамы (мм)
     * @param trackWidth - колея (мм)
     * @param frameHeight - высота рамы (мм)
     * @param beamSize - размер балки (мм)
     * @param marginFactor - коэффициент запаса (default: 1.15)
     */
    function autoFitFrame(frameLength, trackWidth, frameHeight, beamSize, marginFactor) {
        console.log("📷 CameraState: auto-fitting to frame...")
        
        // Обновляем pivot
        pivot = calculatePivot(beamSize, frameHeight, frameLength)
        
        // Обновляем distance
        distance = calculateOptimalDistance(frameLength, trackWidth, frameHeight, marginFactor)
        
        console.log("   Pivot:", pivot)
        console.log("   Distance:", distance.toFixed(0), "mm")
        
        cameraChanged()
    }
    
    /**
     * Soft reset - сохраняет камеру если она в разумных пределах
     * 
     * @param beamSize - размер балки (мм)
     * @param frameHeight - высота рамы (мм)
     * @param frameLength - длина рамы (мм)
     */
    function resetView(beamSize, frameHeight, frameLength) {
        console.log("🔄 CameraState: soft reset view...")
        
        // Проверяем что камера в разумных пределах
        var preserveCamera = (
            Math.abs(yawDeg) < 720 && 
            Math.abs(pitchDeg) < maxPitchDeg && 
            distance > minDistance && 
            distance < maxDistance
        )
        
        if (preserveCamera) {
            console.log("   Preserving camera position, updating only pivot")
            pivot = calculatePivot(beamSize, frameHeight, frameLength)
        } else {
            console.log("   Full reset: camera out of bounds")
            fullResetView(beamSize, frameHeight, frameLength, frameLength, 1600)
        }
        
        viewReset()
        cameraChanged()
    }
    
    /**
     * Full reset - сброс камеры к defaults
     * 
     * @param beamSize - размер балки (мм)
     * @param frameHeight - высота рамы (мм)
     * @param frameLength - длина рамы (мм)
     * @param trackWidth - колея (мм) для расчета distance
     * @param defaultTrackWidth - default значение колеи
     */
    function fullResetView(beamSize, frameHeight, frameLength, trackWidth, defaultTrackWidth) {
        console.log("🔄 CameraState: FULL reset view to defaults...")
        
        // Reset pivot
        pivot = calculatePivot(beamSize, frameHeight, frameLength)
        
        // Reset rotation to defaults
        yawDeg = 225
        pitchDeg = -25
        
        // Reset pan
        panX = 0
        panY = 0
        
        // Calculate optimal distance
        var tw = trackWidth !== undefined ? trackWidth : defaultTrackWidth
        distance = calculateOptimalDistance(frameLength, tw, frameHeight, 1.15)
        
        console.log("   Reset to defaults:")
        console.log("     Pivot:", pivot)
        console.log("     Yaw:", yawDeg, "Pitch:", pitchDeg)
        console.log("     Distance:", distance.toFixed(0), "mm")
        
        viewReset()
        cameraChanged()
    }
    
    /**
     * Flag camera motion (для TAA motion adaptive)
     */
    function flagMotion() {
        if (!isMoving) {
            isMoving = true
        }
    }
    
    /**
     * Clear motion flag (вызывается из MouseControls через Timer)
     */
    function clearMotion() {
        isMoving = false
    }
    
    /**
     * Clamp pitch to limits
     * 
     * @param pitch - pitch angle to clamp
     * @returns clamped pitch
     */
    function clampPitch(pitch) {
        return Core.MathUtils.clamp(pitch, minPitchDeg, maxPitchDeg)
    }
    
    /**
     * Clamp distance to limits
     * 
     * @param dist - distance to clamp
     * @returns clamped distance
     */
    function clampDistance(dist) {
        return Core.MathUtils.clamp(dist, minDistance, maxDistance)
    }
    
    // ===============================================================
    // INITIALIZATION
    // ===============================================================
    
    Component.onCompleted: {
        console.log("✅ CameraState initialized (v" + version + ")")
        console.log("   📷 Pivot:", pivot)
        console.log("   📷 Distance:", distance, "mm")
        console.log("   📷 Yaw:", yawDeg, "° | Pitch:", pitchDeg, "°")
        console.log("   📷 FOV:", fov, "°")
    }
}
