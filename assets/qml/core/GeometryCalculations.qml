pragma Singleton
import QtQuick

/*
 * GeometryCalculations.qml - Geometry Utilities (Singleton)
 * PneumoStabSim Professional - Phase 1
 * Version: 1.0.0
 *
 * Геометрические расчеты для подвески и 3D моделей.
 * Использует MathUtils для базовых операций.
 */
QtObject {
    id: geomCalc

    // ===============================================================
    // VERSION INFO
    // ===============================================================
    readonly property string version: "1.0.0"
    readonly property string module: "GeometryCalculations"

    // ===============================================================
    // SUSPENSION GEOMETRY CALCULATIONS
    // ===============================================================

    /**
     * Расчет позиции точки крепления штока (j_rod) на рычаге
     *
     * @param j_arm - точка крепления рычага к раме
     * @param leverLength - длина рычага (мм)
     * @param rodPosition - позиция крепления штока на рычаге (0.0-1.0)
     * @param baseAngle - базовый угол рычага (180° слева, 0° справа)
     * @param leverAngle - текущий угол отклонения рычага
     * @returns Qt.vector3d - позиция j_rod
     */
    function calculateJRodPosition(j_arm, leverLength, rodPosition, baseAngle, leverAngle) {
        // Эффективная длина до точки крепления штока
        var effectiveLength = leverLength * rodPosition

        // Полный угол (базовый + отклонение)
        var totalAngleDeg = baseAngle + leverAngle
        var totalAngleRad = totalAngleDeg * Math.PI / 180.0

        return Qt.vector3d(
            j_arm.x + effectiveLength * Math.cos(totalAngleRad),
            j_arm.y + effectiveLength * Math.sin(totalAngleRad),
            j_arm.z
        )
    }

    /**
     * Расчет оси цилиндра и её параметров
     *
     * @param j_rod - точка крепления штока
     * @param j_tail - точка крепления цилиндра к раме
     * @returns Object {direction, length, normalized, angle}
     */
    function calculateCylinderAxis(j_rod, j_tail) {
        var dx = j_rod.x - j_tail.x
        var dy = j_rod.y - j_tail.y
        var dz = j_rod.z - j_tail.z

        var length = Math.sqrt(dx * dx + dy * dy + dz * dz)

        // Защита от деления на ноль
        if (length < 0.001) {
            return {
                direction: Qt.vector3d(0, 1, 0),
                length: 0,
                normalized: Qt.vector3d(0, 1, 0),
                angle: 90.0
            }
        }

        var normalized = Qt.vector3d(dx / length, dy / length, dz / length)

        // Угол для ориентации цилиндра в 2D (XY plane)
        // +90° т.к. Qt Cylinder по умолчанию направлен вдоль Y
        var angle = Math.atan2(dy, dx) * 180.0 / Math.PI + 90.0

        return {
            direction: Qt.vector3d(dx, dy, dz),
            length: length,
            normalized: normalized,
            angle: angle
        }
    }

    /**
     * Расчет позиции поршня внутри цилиндра
     *
     * @param cylStart - начало цилиндра (конец хвостовика)
     * @param cylDirection - направление цилиндра
     * @param cylLength - длина цилиндра
     * @param pistonRatio - позиция поршня (0.0 = начало, 1.0 = конец)
     * @returns Qt.vector3d - позиция поршня
     */
    function calculatePistonPosition(cylStart, cylDirection, cylLength, pistonRatio) {
        // Нормализуем направление
        var dirLength = Math.sqrt(
            cylDirection.x * cylDirection.x +
            cylDirection.y * cylDirection.y +
            cylDirection.z * cylDirection.z
        )

        if (dirLength < 0.001) {
            return cylStart
        }

        var normalizedDir = Qt.vector3d(
            cylDirection.x / dirLength,
            cylDirection.y / dirLength,
            cylDirection.z / dirLength
        )

        // Позиция поршня вдоль оси
        var position = pistonRatio * cylLength

        return Qt.vector3d(
            cylStart.x + normalizedDir.x * position,
            cylStart.y + normalizedDir.y * position,
            cylStart.z + normalizedDir.z * position
        )
    }

    /**
     * Расчет конца хвостовика (начала цилиндра)
     *
     * @param j_tail - точка крепления к раме
     * @param cylDirection - направление цилиндра (normalized)
     * @param tailRodLength - длина хвостовика
     * @returns Qt.vector3d - конец хвостовика
     */
    function calculateTailRodEnd(j_tail, cylDirection, tailRodLength) {
        return Qt.vector3d(
            j_tail.x + cylDirection.x * tailRodLength,
            j_tail.y + cylDirection.y * tailRodLength,
            j_tail.z + cylDirection.z * tailRodLength
        )
    }

    // ===============================================================
    // LEVER CALCULATIONS
    // ===============================================================

    /**
     * Расчет базового угла рычага в зависимости от стороны
     *
     * @param side - "left" или "right"
     * @returns Number - базовый угол (180° для левой, 0° для правой)
     */
    function calculateLeverBaseAngle(side) {
        return (side === "left") ? 180.0 : 0.0
    }

    /**
     * Расчет полного угла рычага
     *
     * @param baseAngle - базовый угол
     * @param leverAngle - угол отклонения
     * @returns Number - полный угол
     */
    function calculateLeverTotalAngle(baseAngle, leverAngle) {
        return baseAngle + leverAngle
    }

    /**
     * Расчет центра рычага (для позиционирования Model)
     *
     * @param j_arm - точка крепления
     * @param leverLength - длина рычага
     * @param totalAngle - полный угол рычага
     * @returns Qt.vector3d - центр рычага
     */
    function calculateLeverCenter(j_arm, leverLength, totalAngle) {
        var totalAngleRad = totalAngle * Math.PI / 180.0

        return Qt.vector3d(
            j_arm.x + (leverLength / 2.0) * Math.cos(totalAngleRad),
            j_arm.y + (leverLength / 2.0) * Math.sin(totalAngleRad),
            j_arm.z
        )
    }

    // ===============================================================
    // CAMERA CALCULATIONS
    // ===============================================================

    /**
     * Расчет оптимального расстояния камеры для фрейма в кадре
     *
     * @param frameLength - длина рамы
     * @param frameHeight - высота рамы
     * @param trackWidth - колея
     * @param fov - field of view камеры (градусы)
     * @param margin - запас (1.0 = без запаса, 1.5 = +50% запас)
     * @returns Number - оптимальное расстояние
     */
    function calculateOptimalCameraDistance(frameLength, frameHeight, trackWidth, fov, margin) {
        if (margin === undefined) {
            margin = 1.5
        }

        // Радиус bounding sphere вокруг рамы
        var radius = 0.5 * Math.sqrt(
            frameLength * frameLength +
            trackWidth * trackWidth +
            frameHeight * frameHeight
        )

        // FOV в радианах
        var fovRad = fov * Math.PI / 180.0

        // Расстояние для покрытия radius с учетом margin
        var distance = (radius * margin) / Math.tan(fovRad * 0.5)

        return distance
    }

    /**
     * Расчет pivot point для камеры (центр рамы)
     *
     * @param beamSize - размер балки
     * @param frameHeight - высота рамы
     * @param frameLength - длина рамы
     * @returns Qt.vector3d - pivot point
     */
    function calculateCameraPivot(beamSize, frameHeight, frameLength) {
        return Qt.vector3d(
            0,                          // X - центр
            beamSize + frameHeight / 2, // Y - середина высоты
            frameLength / 2             // Z - середина длины
        )
    }

    // ===============================================================
    // BOUNDING BOX CALCULATIONS
    // ===============================================================

    /**
     * Расчет bounding box для набора точек
     *
     * @param points - Array of Qt.vector3d
     * @returns Object {min, max, center, size}
     */
    function calculateBoundingBox(points) {
        if (!points || points.length === 0) {
            return {
                min: Qt.vector3d(0, 0, 0),
                max: Qt.vector3d(0, 0, 0),
                center: Qt.vector3d(0, 0, 0),
                size: Qt.vector3d(0, 0, 0)
            }
        }

        var minX = points[0].x, maxX = points[0].x
        var minY = points[0].y, maxY = points[0].y
        var minZ = points[0].z, maxZ = points[0].z

        for (var i = 1; i < points.length; i++) {
            var p = points[i]

            minX = Math.min(minX, p.x)
            maxX = Math.max(maxX, p.x)

            minY = Math.min(minY, p.y)
            maxY = Math.max(maxY, p.y)

            minZ = Math.min(minZ, p.z)
            maxZ = Math.max(maxZ, p.z)
        }

        var min = Qt.vector3d(minX, minY, minZ)
        var max = Qt.vector3d(maxX, maxY, maxZ)
        var center = Qt.vector3d(
            (minX + maxX) / 2,
            (minY + maxY) / 2,
            (minZ + maxZ) / 2
        )
        var size = Qt.vector3d(
            maxX - minX,
            maxY - minY,
            maxZ - minZ
        )

        return {
            min: min,
            max: max,
            center: center,
            size: size
        }
    }

    // ===============================================================
    // SCALE CALCULATIONS
    // ===============================================================

    /**
     * Преобразование миллиметров в единицы Qt (mm / 100)
     *
     * Qt Quick 3D использует метры, но мы работаем в мм,
     * поэтому scale = mm / 100
     *
     * @param mm - размер в миллиметрах
     * @returns Number - scale для Qt
     */
    function mmToScale(mm) {
        return mm / 100.0
    }

    /**
     * Преобразование единиц Qt обратно в миллиметры
     *
     * @param scale - Qt scale
     * @returns Number - размер в мм
     */
    function scaleToMm(scale) {
        return scale * 100.0
    }

    // ===============================================================
    // VALIDATION
    // ===============================================================

    /**
     * Проверка валидности позиции
     *
     * @param position - Qt.vector3d
     * @returns Boolean - true если валидна
     */
    function isValidPosition(position) {
        if (!position) return false

        return isFiniteNumber(position.x) &&
               isFiniteNumber(position.y) &&
               isFiniteNumber(position.z)
    }

    /**
     * Проверка что число конечное (не NaN, не Infinity)
     */
    function isFiniteNumber(value) {
        return !isNaN(value) && isFinite(value)
    }

    // ===============================================================
    // INITIALIZATION
    // ===============================================================

    Component.onCompleted: {
        console.log("✅ GeometryCalculations Singleton initialized (v" + version + ")")
        console.log("   📐 Suspension geometry calculations ready")
        console.log("   📷 Camera calculations available")
        console.log("   📦 Bounding box utilities loaded")
    }
}
