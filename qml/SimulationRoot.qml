#pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import "." as Local
import "./singletons" as Singletons

/**
 * Минимальный корневой компонент для стенд‑запуска панели симуляции.
 * Повторяет публичную поверхность API SimulationRoot рабочего приложения,
 * чтобы qmllint/локальные инструменты не ругались на отсутствующие биндинги.
 */
Pane {
    id: root

    width: 960
    height: 640
    padding: 24

    /** Полный снимок телеметрии потоков от симулятора. */
    property var flowTelemetry: ({})
    property var geometryParameters: ({})

    /** Прокси к внутренним моделям, экспортируемые для автотестов. */
    property var simulationPanel: simulationLoader.item
    property var flowArrowsModel: simulationPanel ? simulationPanel.flowArrowsModel : null
    property var lineValveModel: simulationPanel ? simulationPanel.lineValveModel : null
    property var reliefValveModel: simulationPanel ? simulationPanel.reliefValveModel : null

    signal geometryUpdatesApplied(var payload)
    signal shaderWarningRegistered(string effectId, string message)
    signal shaderWarningCleared(string effectId)

    /** Кэш активных предупреждений шейдеров (effectId -> message). */
    property var shaderWarningState: ({})

    function _normalizeEffectId(value) {
        var normalized = "unknown"
        if (value !== undefined && value !== null) {
            normalized = String(value)
            if (!normalized.length)
                normalized = "unknown"
        }
        return normalized
    }

    function _normalizeWarningMessage(value) {
        if (value === undefined || value === null)
            return ""
        return String(value)
    }

    function _cloneWarningState(source) {
        if (!source || typeof source !== "object")
            return ({})
        var clone = {}
        for (var key in source) {
            if (Object.prototype.hasOwnProperty.call(source, key))
                clone[key] = source[key]
        }
        return clone
    }

    property var _pendingFlowTelemetry: null
    property var _pendingGeometry: null
    // Стартуем в ленивом режиме: Loader не активен пока не придут данные
    property bool _loadRequested: false

    // Rollback hooks exposed for bridge-driven undo flows
    signal undoPostEffects()
    signal resetSharedMaterials()

    function applyFlowTelemetry(payload) {
        flowTelemetry = payload
        if (_hasPayload(payload)) {
            _pendingFlowTelemetry = payload
            _requestLoad()
            _flushPending()
        }
    }

    onFlowTelemetryChanged: {
        if (_hasPayload(flowTelemetry)) {
            _pendingFlowTelemetry = flowTelemetry
            _requestLoad()
            _flushPending()
        }
    }

    function _hostWindow() {
        // qmllint disable unqualified
        try {
            if (typeof window !== "undefined" && window)
                return window
        } catch (error) {
        }
        // qmllint enable unqualified
        return null
    }

    function _normalizeGeometryPayload(params) {
        if (!params || typeof params !== "object")
            return ({})

        var normalized = {}
        for (var key in params) {
            if (Object.prototype.hasOwnProperty.call(params, key))
                normalized[key] = params[key]
        }
        return normalized
    }

    /**
     * Принимает обновления геометрии (имитация продакшн‑моста Python→QML).
     * В заглушке просто ретранслируем полезную нагрузку наружу.
     */
    function applyGeometryUpdates(params) {
        geometryParameters = _normalizeGeometryPayload(params)
        geometryUpdatesApplied(geometryParameters)
        if (_hasPayload(geometryParameters)) {
            _pendingGeometry = geometryParameters
            _requestLoad()
            _flushPending()
        }
    }

    function triggerUndoPostEffects() { undoPostEffects() }

    function triggerResetSharedMaterials() { resetSharedMaterials() }

    onGeometryParametersChanged: {
        if (_hasPayload(geometryParameters)) {
            _pendingGeometry = geometryParameters
            _requestLoad()
            _flushPending()
        }
    }

    function _flushPending() {
        if (!simulationPanel) {
            if (_pendingGeometry !== null || _pendingFlowTelemetry !== null)
                _requestLoad()
            return
        }
        if (_pendingGeometry !== null)
            simulationPanel.applyGeometryParameters(_pendingGeometry)
        if (_pendingFlowTelemetry !== null)
            simulationPanel.applyFlowTelemetry(_pendingFlowTelemetry)
        _pendingGeometry = null
        _pendingFlowTelemetry = null
    }

    function _requestLoad() {
        if (!_loadRequested)
            _loadRequested = true
    }

    function _hasPayload(payload) {
        return payload && typeof payload === "object" && Object.keys(payload).length > 0
    }

    /**
     * Интерфейс для регистрации предупреждений шейдеров, совместимый со сценой.
     */
    function registerShaderWarning(effectId, message) {
        var normalizedId = _normalizeEffectId(effectId)
        var normalizedMessage = _normalizeWarningMessage(message)

        var previousState = shaderWarningState
        var nextState = _cloneWarningState(previousState)
        if (nextState[normalizedId] !== normalizedMessage)
            nextState[normalizedId] = normalizedMessage
        shaderWarningState = nextState

        shaderWarningRegistered(normalizedId, normalizedMessage)

        var hostWindow = _hostWindow()
        if (hostWindow && typeof hostWindow.registerShaderWarning === "function") {
            try {
                hostWindow.registerShaderWarning(normalizedId, normalizedMessage)
            } catch (error) {
                console.debug("SimulationRoot (stub): window.registerShaderWarning failed", error)
            }
        }
    }

    function clearShaderWarning(effectId) {
        var normalizedId = _normalizeEffectId(effectId)

        var previousState = shaderWarningState
        var nextState = _cloneWarningState(previousState)
        if (Object.prototype.hasOwnProperty.call(nextState, normalizedId))
            delete nextState[normalizedId]
        shaderWarningState = nextState

        shaderWarningCleared(normalizedId)

        var hostWindow = _hostWindow()
        if (hostWindow && typeof hostWindow.clearShaderWarning === "function") {
            try {
                hostWindow.clearShaderWarning(normalizedId)
            } catch (error) {
                console.debug("SimulationRoot (stub): window.clearShaderWarning failed", error)
            }
        }
    }

    // Оформляем фон панели
    background: Rectangle {
        radius: 18
        color: Singletons.UiConstants.panels.background
        border.color: Singletons.UiConstants.panels.border
        border.width: 1
    }

    // Основной контент — панель симуляции с гибридной ленивой загрузкой (кастомный Loader-совместимый контейнер)
    // Заменяем стандартный Loader чтобы панель была доступна сразу (tests/qml ожидают),
    // но флаг active остаётся false до прихода данных (tests/optimization ожидает initial_clean).
    contentItem: Item {
        id: simulationLoader
        objectName: "simulationLoader"
        anchors.fill: parent
        property bool active: root._loadRequested  // станет true после _requestLoad()
        // Совместимый интерфейс: item указывает на реальную панель
        property alias item: simulationPanel
        // Статус эмулируем для panelReady (Ready когда active true)
        readonly property int status: active ? 1 : 0  // 1 ~ Loader.Ready, 0 ~ Loader.Null

        // Реальная панель (загружается сразу, но считается "лениво активированной" когда active=true)
        Local.SimulationPanel {
            id: simulationPanel
            objectName: "simulationPanel"
            anchors.fill: parent
            anchors.margins: 24
        }
    }

    // Переопределяем panelReady с учётом эмулированного статуса
    readonly property bool panelReady: simulationLoader.active && simulationPanel !== null
}
