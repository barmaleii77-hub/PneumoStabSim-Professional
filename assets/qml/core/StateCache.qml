pragma Singleton
import QtQuick

/*
 * StateCache.qml - State Caching Utilities (Singleton)
 * PneumoStabSim Professional - Phase 1
 * Version: 1.0.0
 *
 * Кэширование вычислений для оптимизации производительности.
 * Аналог animationCache и geometryCache из main.qml
 */
QtObject {
    id: stateCache

    // ===============================================================
    // VERSION INFO
    // ===============================================================
    readonly property string version: "1.0.0"
    readonly property string module: "StateCache"

    // ===============================================================
    // EXTERNAL PROPERTIES (устанавливаются из main.qml)
    // ===============================================================

    // Animation parameters
    property real animationTime: 0.0
    property real userFrequency: 0.0
    property real userPhaseGlobal: 0.0
    property real userPhaseFL: 0.0
    property real userPhaseFR: 0.0
    property real userPhaseRL: 0.0
    property real userPhaseRR: 0.0
    property real userAmplitude: 0.0

    // Geometry parameters
    property real userLeverLength: 0.0
    property real userRodPosition: 0.0
    property real userCylinderLength: 0.0
    property real userTrackWidth: 0.0
    property real userFrameLength: 0.0

    // Camera parameters
    property real cameraFov: 60.0

    // ===============================================================
    // ANIMATION CACHE
    // ===============================================================

    // Базовая фаза анимации (вычисляется 1 раз за фрейм вместо 4х)
    readonly property real basePhase: animationTime * userFrequency * 2.0 * Math.PI

    // Глобальная фаза в радианах
    readonly property real globalPhaseRad: userPhaseGlobal * Math.PI / 180.0

    // Предварительно вычисленные фазы для каждого колеса
    readonly property real flPhaseRad: globalPhaseRad + userPhaseFL * Math.PI / 180.0
    readonly property real frPhaseRad: globalPhaseRad + userPhaseFR * Math.PI / 180.0
    readonly property real rlPhaseRad: globalPhaseRad + userPhaseRL * Math.PI / 180.0
    readonly property real rrPhaseRad: globalPhaseRad + userPhaseRR * Math.PI / 180.0

    // Кэшированные синусы (4 Math.sin() вызова → 4 кэшированных значения)
    readonly property real flSin: Math.sin(basePhase + flPhaseRad)
    readonly property real frSin: Math.sin(basePhase + frPhaseRad)
    readonly property real rlSin: Math.sin(basePhase + rlPhaseRad)
    readonly property real rrSin: Math.sin(basePhase + rrPhaseRad)

    // Кэшированные углы отклонения рычагов
    readonly property real flAngle: userAmplitude * flSin
    readonly property real frAngle: userAmplitude * frSin
    readonly property real rlAngle: userAmplitude * rlSin
    readonly property real rrAngle: userAmplitude * rrSin

    // ===============================================================
    // GEOMETRY CACHE
    // ===============================================================

    // Эффективная длина рычага до точки крепления штока
    readonly property real leverLengthRodPos: userLeverLength * userRodPosition

    // Математические константы (кэшированные)
    readonly property real piOver180: Math.PI / 180.0
    readonly property real deg180OverPi: 180.0 / Math.PI

    // Кэшированные вычисления камеры
    readonly property real cachedFovRad: cameraFov * piOver180
    readonly property real cachedTanHalfFov: Math.tan(cachedFovRad / 2.0)

    // Половинные размеры (часто используемые)
    readonly property real halfTrackWidth: userTrackWidth / 2.0
    readonly property real halfFrameLength: userFrameLength / 2.0

    // ===============================================================
    // SUSPENSION POSITION CACHE
    // ===============================================================

    /**
     * Кэш позиций для левых/правых углов
     * Вычисляется один раз, используется многократно
     */
    readonly property real leftBaseAngle: 180.0
    readonly property real rightBaseAngle: 0.0

    /**
     * Полные углы рычагов (базовый + отклонение)
     */
    readonly property real flTotalAngle: leftBaseAngle + flAngle
    readonly property real frTotalAngle: rightBaseAngle + frAngle
    readonly property real rlTotalAngle: leftBaseAngle + rlAngle
    readonly property real rrTotalAngle: rightBaseAngle + rrAngle

    // ===============================================================
    // PERFORMANCE MONITORING
    // ===============================================================

    // Счетчик обновлений кэша
    property int updateCount: 0

    // Таймер для мониторинга производительности
    property real lastUpdateTime: 0.0
    property real updateDelta: 0.0

    onAnimationTimeChanged: {
        var now = Date.now()
        updateDelta = now - lastUpdateTime
        lastUpdateTime = now
        updateCount++
    }

    /**
     * Получить статистику производительности
     */
    function getPerformanceStats() {
        return {
            updateCount: updateCount,
            lastDelta: updateDelta,
            fps: updateDelta > 0 ? 1000.0 / updateDelta : 0,
            cachedValues: 15  // Количество кэшированных значений
        }
    }

    /**
     * Сбросить счетчики
     */
    function resetStats() {
        updateCount = 0
        lastUpdateTime = Date.now()
        updateDelta = 0.0
    }

    // ===============================================================
    // UTILITY FUNCTIONS
    // ===============================================================

    /**
     * Получить кэшированный угол для указанного колеса
     *
     * @param wheelId - "fl", "fr", "rl", или "rr"
     * @returns Number - кэшированный угол
     */
    function getCachedAngle(wheelId) {
        switch (wheelId) {
            case "fl": return flAngle
            case "fr": return frAngle
            case "rl": return rlAngle
            case "rr": return rrAngle
            default: return 0.0
        }
    }

    /**
     * Получить кэшированный полный угол для указанного колеса
     *
     * @param wheelId - "fl", "fr", "rl", или "rr"
     * @returns Number - кэшированный полный угол
     */
    function getCachedTotalAngle(wheelId) {
        switch (wheelId) {
            case "fl": return flTotalAngle
            case "fr": return frTotalAngle
            case "rl": return rlTotalAngle
            case "rr": return rrTotalAngle
            default: return 0.0
        }
    }

    /**
     * Проверка готовности кэша
     *
     * @returns Boolean - true если все параметры валидны
     */
    function isReady() {
        return userFrequency > 0 &&
               userLeverLength > 0 &&
               userRodPosition > 0 &&
               userCylinderLength > 0 &&
               userTrackWidth > 0 &&
               userFrameLength > 0
    }

    // ===============================================================
    // DEBUGGING
    // ===============================================================

    /**
     * Получить полное состояние кэша для отладки
     */
    function debugState() {
        return {
            // Animation
            animationTime: animationTime,
            basePhase: basePhase,
            angles: {
                fl: flAngle,
                fr: frAngle,
                rl: rlAngle,
                rr: rrAngle
            },
            totalAngles: {
                fl: flTotalAngle,
                fr: frTotalAngle,
                rl: rlTotalAngle,
                rr: rrTotalAngle
            },
            // Geometry
            leverLengthRodPos: leverLengthRodPos,
            halfTrackWidth: halfTrackWidth,
            halfFrameLength: halfFrameLength,
            // Performance
            updateCount: updateCount,
            updateDelta: updateDelta
        }
    }

    // ===============================================================
    // INITIALIZATION
    // ===============================================================

    Component.onCompleted: {
        console.log("✅ StateCache Singleton initialized (v" + version + ")")
        console.log("   ⚡ Animation cache: 8 pre-computed values")
        console.log("   📐 Geometry cache: 7 pre-computed values")
        console.log("   📊 Performance monitoring enabled")

        lastUpdateTime = Date.now()
    }
}
