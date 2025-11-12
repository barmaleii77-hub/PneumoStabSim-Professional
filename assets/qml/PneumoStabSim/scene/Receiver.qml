import QtQuick 6.10
import QtQuick3D 6.10
import "../../components/MaterialCompat.js" as MaterialCompat
import "../../components/GeometryCompat.js" as GeometryCompat // добавлен для апгрейда примитивов

pragma ComponentBehavior: Bound

Node {
    id: root

    // --- ДАННЫЕ ---
    property var flowData: ({})
    property var receiverState: ({})
    property var geometryHelper: null
    property real sceneScale: 1.0

    // --- КЛЮЧИ ЛИНИЙ ---
    property var lineKeys: ["a1", "b1", "a2", "b2"]
    property var sideMap: ({ a1: "fl", b1: "fr", a2: "rl", b2: "rr" })

    // --- ГЕОМЕТРИЯ ПОЗИЦИЙ ---
    property real anchorElevationM: 0.18
    property real baseElevationM: 0.28
    property real elevationSpanM: 0.22
    property real sphereBaseRadiusM: 0.09
    property real sphereMaxRadiusM: 0.16
    property real lateralOffsetM: 0.06

    // --- ЦВЕТА ДАВЛЕНИЯ ---
    property color lowPressureColor: "#3b4252"
    property color highPressureColor: "#ff6b6b"
    property color midPressureColor: "#3fc1ff"

    // --- ДИАПАЗОН ДАВЛЕНИЯ ---
    property real pressureMin: 0.0
    property real pressureMax: 0.0

    // --- ПАРАМЕТРЫ МАТЕРИАЛОВ (Доступны для UI) ---
    property real sphereRoughness: 0.25        // базовая шероховатость
    property real sphereMetalness: 0.05        // металл
    property real sphereBaseOpacity: 0.85      // базовая прозрачность
    property real sphereEmissiveBase: 0.6      // минимальное эмиссивное значение
    property real sphereEmissiveSpan: 2.2      // множитель диапазона эмиссии
    property bool sphereAlphaBlend: true       // вкл. смешивание альфа

    // --- СТАТУС ---
    readonly property bool hasPressureRange: pressureMax > 0 && pressureMax >= pressureMin
    readonly property bool hasFlowData: flowData && typeof flowData === "object"
    readonly property bool hasReceiverState: receiverState && typeof receiverState === "object"

    visible: hasPressureRange && hasFlowData

    onFlowDataChanged: _updatePressureStats()
    onReceiverStateChanged: _updatePressureStats()

    Component.onCompleted: _updatePressureStats()

    function asObject(value) { return value && typeof value === "object" ? value : null }

    function _updatePressureStats() {
        var pressures = {}
        var receiver = asObject(receiverState)
        if (receiver && receiver.pressures && typeof receiver.pressures === "object") {
            pressures = receiver.pressures
        } else {
            var flowObject = asObject(flowData)
            if (flowObject && flowObject.lines && typeof flowObject.lines === "object") {
                pressures = {}
                for (var i = 0; i < lineKeys.length; ++i) {
                    var key = lineKeys[i]
                    var entry = flowObject.lines[key]
                    if (entry && typeof entry === "object" && entry.pressure !== undefined)
                        pressures[key] = Number(entry.pressure)
                }
            }
        }
        var minValue = Infinity
        var maxValue = -Infinity
        for (var key in pressures) {
            if (!Object.prototype.hasOwnProperty.call(pressures, key))
                continue
            var value = Number(pressures[key])
            if (!isFinite(value))
                continue
            if (value < minValue) minValue = value
            if (value > maxValue) maxValue = value
        }
        pressureMin = (isFinite(minValue) ? minValue : 0.0)
        pressureMax = (isFinite(maxValue) ? maxValue : 0.0)
    }

    function _lineEntry(key) {
        var flowObject = asObject(flowData)
        if (!flowObject) return null
        var lines = flowObject.lines && typeof flowObject.lines === "object" ? flowObject.lines : null
        if (!lines) return null
        var entry = lines[key]
        return entry && typeof entry === "object" ? entry : null
    }

    function _linePressure(key) {
        var receiver = asObject(receiverState)
        if (receiver && receiver.pressures && receiver.pressures[key] !== undefined) {
            var direct = Number(receiver.pressures[key]); if (isFinite(direct)) return direct
        }
        var entry = _lineEntry(key)
        if (entry && entry.pressure !== undefined) {
            var fallback = Number(entry.pressure); if (isFinite(fallback)) return fallback
        }
        return 0.0
    }

    function _pressureRatio(key) {
        var value = _linePressure(key)
        if (!isFinite(value)) return 0.0
        var minValue = pressureMin
        var maxValue = pressureMax
        if (!(maxValue > minValue)) return maxValue > 0 ? Math.min(Math.max(value / maxValue, 0.0), 1.0) : 0.0
        return Math.min(Math.max((value - minValue) / (maxValue - minValue), 0.0), 1.0)
    }

    function _lineAnchor(key) {
        var side = sideMap[key]
        var helper = geometryHelper
        if (!side || !helper) return Qt.vector3d(0, 0, 0)
        var base = null
        if (typeof helper.armPosition === "function") base = helper.armPosition(side)
        else if (typeof helper.cornerArmPosition === "function") base = helper.cornerArmPosition(side)
        if (!base) return Qt.vector3d(0, 0, 0)
        var x = Number(base.x) * sceneScale
        var y = (Number(base.y) + anchorElevationM) * sceneScale
        var z = Number(base.z) * sceneScale
        return Qt.vector3d(x, y, z)
    }

    function _lateralOffset(key) {
        var side = sideMap[key]; if (!side) return 0.0
        return side.charAt(1) === "l" ? -lateralOffsetM : lateralOffsetM
    }

    function _spherePosition(key) {
        var anchor = _lineAnchor(key)
        var ratio = _pressureRatio(key)
        var elevation = (baseElevationM + elevationSpanM * ratio) * sceneScale
        var lateral = _lateralOffset(key) * sceneScale
        return Qt.vector3d(anchor.x + lateral, anchor.y + elevation, anchor.z)
    }

    function _sphereScale(key) {
        var ratio = _pressureRatio(key)
        var radius = sphereBaseRadiusM + (sphereMaxRadiusM - sphereBaseRadiusM) * ratio
        var uniform = Math.max(0.01, radius * sceneScale)
        return Qt.vector3d(uniform, uniform, uniform)
    }

    function _blendColors(baseColor, overlayColor, factor) {
        factor = Math.max(0.0, Math.min(1.0, Number(factor)))
        var base = Qt.rgba(baseColor.r, baseColor.g, baseColor.b, 1)
        var overlay = Qt.rgba(overlayColor.r, overlayColor.g, overlayColor.b, 1)
        return Qt.rgba(base.r + (overlay.r - base.r) * factor, base.g + (overlay.g - base.g) * factor, base.b + (overlay.b - base.b) * factor, 1)
    }

    function _sphereColor(key) {
        var ratio = _pressureRatio(key)
        if (ratio <= 0.5) return _blendColors(lowPressureColor, midPressureColor, ratio * 2)
        return _blendColors(midPressureColor, highPressureColor, (ratio - 0.5) * 2)
    }

    function _sphereEmissive(key) {
        var ratio = _pressureRatio(key)
        return sphereEmissiveBase + ratio * sphereEmissiveSpan
    }

    function _applyMaterial(mat, key) {
        if (!mat) return
        try { mat.baseColor = _sphereColor(key) } catch (e) {}
        try { mat.roughness = sphereRoughness } catch (e) {}
        try { mat.metalness = sphereMetalness } catch (e) {}
        try { mat.opacity = sphereBaseOpacity } catch (e) {}
        if (sphereAlphaBlend) {
            try { mat.alphaMode = PrincipledMaterial.Blend } catch (e) {}
        }
        MaterialCompat.applyEmissive(mat, _sphereColor(key), _sphereEmissive(key))
    }

    // Обновление материалов при изменениях
    onSphereRoughnessChanged: _refreshMaterials()
    onSphereMetalnessChanged: _refreshMaterials()
    onSphereBaseOpacityChanged: _refreshMaterials()
    onSphereEmissiveBaseChanged: _refreshMaterials()
    onSphereEmissiveSpanChanged: _refreshMaterials()
    onLowPressureColorChanged: _refreshMaterials()
    onMidPressureColorChanged: _refreshMaterials()
    onHighPressureColorChanged: _refreshMaterials()

    function _refreshMaterials() {
        _applyMaterial(matA1, "a1")
        _applyMaterial(matB1, "b1")
        _applyMaterial(matA2, "a2")
        _applyMaterial(matB2, "b2")
    }

    Model {
        id: sphereA1
        source: "#Sphere"
        position: root._spherePosition("a1")
        scale: root._sphereScale("a1")
        visible: root.hasPressureRange
        Component.onCompleted: GeometryCompat.applySphereMesh(sphereA1, 24, 36)
        materials: PrincipledMaterial {
            id: matA1
            Component.onCompleted: root._applyMaterial(matA1, "a1")
        }
    }

    Model {
        id: sphereB1
        source: "#Sphere"
        position: root._spherePosition("b1")
        scale: root._sphereScale("b1")
        visible: root.hasPressureRange
        Component.onCompleted: GeometryCompat.applySphereMesh(sphereB1, 24, 36)
        materials: PrincipledMaterial {
            id: matB1
            Component.onCompleted: root._applyMaterial(matB1, "b1")
        }
    }

    Model {
        id: sphereA2
        source: "#Sphere"
        position: root._spherePosition("a2")
        scale: root._sphereScale("a2")
        visible: root.hasPressureRange
        Component.onCompleted: GeometryCompat.applySphereMesh(sphereA2, 24, 36)
        materials: PrincipledMaterial {
            id: matA2
            Component.onCompleted: root._applyMaterial(matA2, "a2")
        }
    }

    Model {
        id: sphereB2
        source: "#Sphere"
        position: root._spherePosition("b2")
        scale: root._sphereScale("b2")
        visible: root.hasPressureRange
        Component.onCompleted: GeometryCompat.applySphereMesh(sphereB2, 24, 36)
        materials: PrincipledMaterial {
            id: matB2
            Component.onCompleted: root._applyMaterial(matB2, "b2")
        }
    }
}
