pragma Singleton
import QtQuick

/*
 * MathUtils.qml - Mathematical Utilities (Singleton)
 * PneumoStabSim Professional - Phase 1
 * Version: 1.0.0
 * 
 * Централизованные математические функции для всех QML компонентов.
 * Аналог Python утилит из src.common
 */
QtObject {
    id: mathUtils
    
    // ===============================================================
    // VERSION INFO
    // ===============================================================
    readonly property string version: "1.0.0"
    readonly property string module: "MathUtils"
    
    // ===============================================================
    // MATHEMATICAL CONSTANTS
    // ===============================================================
    readonly property real pi: Math.PI
    readonly property real twoPi: 2.0 * Math.PI
    readonly property real halfPi: Math.PI / 2.0
    readonly property real piOver180: Math.PI / 180.0
    readonly property real deg180OverPi: 180.0 / Math.PI
    
    // ===============================================================
    // ANGLE OPERATIONS
    // ===============================================================
    
    /**
     * ✅ КРИТИЧНО: НЕ нормализуем углы вручную!
     * Qt использует SLERP (Spherical Linear Interpolation) и сам знает,
     * как правильно интерполировать углы.
     * 
     * Эта функция оставлена для совместимости, но просто возвращает угол как есть.
     */
    function normalizeAngleDeg(angle) {
        // ❌ НИКОГДА не делайте: angle % 360
        // Qt сам обрабатывает углы правильно через SLERP
        return angle
    }
    
    /**
     * Конвертация градусов в радианы
     */
    function degToRad(degrees) {
        return degrees * piOver180
    }
    
    /**
     * Конвертация радиан в градусы
     */
    function radToDeg(radians) {
        return radians * deg180OverPi
    }
    
    // ===============================================================
    // BASIC MATH OPERATIONS
    // ===============================================================
    
    /**
     * Ограничить значение в диапазоне [min, max]
     */
    function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value))
    }
    
    /**
     * Ограничить значение в диапазоне [0, 1]
     */
    function clamp01(value) {
        return Math.max(0.0, Math.min(1.0, value))
    }
    
    /**
     * Линейная интерполяция между a и b
     */
    function lerp(a, b, t) {
        return a + (b - a) * clamp01(t)
    }
    
    /**
     * Инверсная линейная интерполяция (возвращает t для заданного value)
     */
    function inverseLerp(a, b, value) {
        if (Math.abs(b - a) < 0.0001) {
            return 0.0
        }
        return clamp01((value - a) / (b - a))
    }
    
    /**
     * Remap значения из одного диапазона в другой
     */
    function remap(value, fromMin, fromMax, toMin, toMax) {
        var t = inverseLerp(fromMin, fromMax, value)
        return lerp(toMin, toMax, t)
    }
    
    /**
     * Проверка на приблизительное равенство
     */
    function approximately(a, b, epsilon) {
        if (epsilon === undefined) {
            epsilon = 0.0001
        }
        return Math.abs(a - b) < epsilon
    }
    
    // ===============================================================
    // VECTOR3D OPERATIONS
    // ===============================================================
    
    /**
     * Длина вектора
     */
    function vector3dLength(v) {
        return Math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
    }
    
    /**
     * Квадрат длины вектора (быстрее, чем length)
     */
    function vector3dLengthSquared(v) {
        return v.x * v.x + v.y * v.y + v.z * v.z
    }
    
    /**
     * Нормализация вектора
     */
    function vector3dNormalize(v) {
        var len = vector3dLength(v)
        if (len > 0.0001) {
            return Qt.vector3d(v.x / len, v.y / len, v.z / len)
        }
        return Qt.vector3d(0, 0, 0)
    }
    
    /**
     * Скалярное произведение векторов
     */
    function vector3dDot(a, b) {
        return a.x * b.x + a.y * b.y + a.z * b.z
    }
    
    /**
     * Векторное произведение (cross product)
     */
    function vector3dCross(a, b) {
        return Qt.vector3d(
            a.y * b.z - a.z * b.y,
            a.z * b.x - a.x * b.z,
            a.x * b.y - a.y * b.x
        )
    }
    
    /**
     * Расстояние между двумя точками
     */
    function vector3dDistance(a, b) {
        var dx = b.x - a.x
        var dy = b.y - a.y
        var dz = b.z - a.z
        return Math.sqrt(dx * dx + dy * dy + dz * dz)
    }
    
    /**
     * Линейная интерполяция между двумя векторами
     */
    function vector3dLerp(a, b, t) {
        t = clamp01(t)
        return Qt.vector3d(
            a.x + (b.x - a.x) * t,
            a.y + (b.y - a.y) * t,
            a.z + (b.z - a.z) * t
        )
    }
    
    // ===============================================================
    // SPHERICAL COORDINATES (для камеры)
    // ===============================================================
    
    /**
     * Конвертация сферических координат в декартовы
     * 
     * @param distance - расстояние от центра
     * @param pitch - угол наклона (градусы)
     * @param yaw - угол поворота (градусы)
     * @returns Qt.vector3d(x, y, z)
     */
    function sphericalToCartesian(distance, pitch, yaw) {
        var pitchRad = degToRad(pitch)
        var yawRad = degToRad(yaw)
        
        return Qt.vector3d(
            distance * Math.cos(pitchRad) * Math.sin(yawRad),
            distance * Math.sin(pitchRad),
            distance * Math.cos(pitchRad) * Math.cos(yawRad)
        )
    }
    
    /**
     * Конвертация декартовых координат в сферические
     * 
     * @param position - Qt.vector3d(x, y, z)
     * @returns Object {distance, pitch, yaw}
     */
    function cartesianToSpherical(position) {
        var distance = vector3dLength(position)
        var pitch = radToDeg(Math.asin(position.y / distance))
        var yaw = radToDeg(Math.atan2(position.x, position.z))
        
        return {
            distance: distance,
            pitch: pitch,
            yaw: yaw
        }
    }
    
    // ===============================================================
    // 2D OPERATIONS (для расчетов в плоскости)
    // ===============================================================
    
    /**
     * Длина 2D вектора (игнорирует z)
     */
    function vector2dLength(v) {
        return Math.sqrt(v.x * v.x + v.y * v.y)
    }
    
    /**
     * Угол 2D вектора (в градусах)
     */
    function vector2dAngle(v) {
        return radToDeg(Math.atan2(v.y, v.x))
    }
    
    /**
     * Создать 2D вектор из угла и длины
     */
    function vector2dFromAngle(angleDeg, length) {
        var rad = degToRad(angleDeg)
        return Qt.vector3d(
            length * Math.cos(rad),
            length * Math.sin(rad),
            0
        )
    }
    
    // ===============================================================
    // SMOOTHING & EASING
    // ===============================================================
    
    /**
     * Smooth step (hermite interpolation)
     */
    function smoothStep(edge0, edge1, x) {
        var t = clamp01((x - edge0) / (edge1 - edge0))
        return t * t * (3.0 - 2.0 * t)
    }
    
    /**
     * Smoother step (Ken Perlin's improved version)
     */
    function smootherStep(edge0, edge1, x) {
        var t = clamp01((x - edge0) / (edge1 - edge0))
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
    }
    
    /**
     * Exponential ease out
     */
    function easeOutExpo(t) {
        return t === 1.0 ? 1.0 : 1.0 - Math.pow(2.0, -10.0 * t)
    }
    
    /**
     * Exponential ease in
     */
    function easeInExpo(t) {
        return t === 0.0 ? 0.0 : Math.pow(2.0, 10.0 * (t - 1.0))
    }
    
    // ===============================================================
    // UTILITY FUNCTIONS
    // ===============================================================
    
    /**
     * Безопасное деление (возвращает fallback при делении на 0)
     */
    function safeDivide(numerator, denominator, fallback) {
        if (fallback === undefined) {
            fallback = 0.0
        }
        
        if (Math.abs(denominator) < 0.0001) {
            return fallback
        }
        
        return numerator / denominator
    }
    
    /**
     * Знак числа (-1, 0, или 1)
     */
    function sign(value) {
        if (value > 0) return 1
        if (value < 0) return -1
        return 0
    }
    
    /**
     * Плавное приближение к цели (damping)
     */
    function smoothDamp(current, target, velocity, smoothTime, deltaTime, maxSpeed) {
        if (smoothTime === undefined) smoothTime = 0.3
        if (maxSpeed === undefined) maxSpeed = Infinity
        
        smoothTime = Math.max(0.0001, smoothTime)
        var omega = 2.0 / smoothTime
        var x = omega * deltaTime
        var exp = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)
        
        var change = current - target
        var originalTo = target
        var maxChange = maxSpeed * smoothTime
        
        change = clamp(change, -maxChange, maxChange)
        target = current - change
        
        var temp = (velocity + omega * change) * deltaTime
        velocity = (velocity - omega * temp) * exp
        
        var output = target + (change + temp) * exp
        
        if ((originalTo - current > 0.0) === (output > originalTo)) {
            output = originalTo
            velocity = (output - originalTo) / deltaTime
        }
        
        return {
            value: output,
            velocity: velocity
        }
    }
    
    // ===============================================================
    // INITIALIZATION
    // ===============================================================
    
    Component.onCompleted: {
        console.log("✅ MathUtils Singleton initialized (v" + version + ")")
        console.log("   📐 Mathematical constants loaded")
        console.log("   🧮 Vector operations available")
        console.log("   📊 26 utility functions ready")
    }
}
