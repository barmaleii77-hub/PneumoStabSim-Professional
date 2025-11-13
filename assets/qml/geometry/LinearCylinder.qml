import QtQuick 6.10
import QtQuick3D 6.10
import "../components/GeometryCompat.js" as GeometryCompat

/*
 * LinearCylinder - упрощённая связка двух точек цилиндром.
 * Основная стратегия:
 * 1) Пытаемся динамически создать procedural геометрию (CustomGeometry 1.0)
 * 2) Если модуль недоступен или отключён, используем Helpers (CylinderMesh)
 * 3) В крайнем случае остаётся встроенный примитив #Cylinder с масштабом
 */
Node {
    id: root

    // --- Required endpoints ---
    required property vector3d startPoint
    required property vector3d endPoint

    // --- Appearance ---
    property real radius: 0.05
    property var material: null
    property list<Material> materialOverrides

    // --- Quality ---
    property int segments: 24
    property int rings: 1

    // --- Behaviour ---
    property real minimumLength: 1e-6
    property bool warnOnTinyLength: true
    property bool planar: false
    // Включает/выключает попытку использования процедурной геометрии
    property bool allowProcedural: true

    property var _procGeom: null

    function _vlen(v) { return Math.sqrt(v.x*v.x + v.y*v.y + v.z*v.z) }
    function _vdot(a, b) { return a.x*b.x + a.y*b.y + a.z*b.z }
    function _vcross(a, b) {
        return Qt.vector3d(
            a.y*b.z - a.z*b.y,
            a.z*b.x - a.x*b.z,
            a.x*b.y - a.y*b.x
        )
    }
    function _clamp(x, lo, hi) { return Math.max(lo, Math.min(hi, x)) }
    function _vnormalize(v, fallback) {
        var len = _vlen(v)
        if (len > 1e-9)
            return Qt.vector3d(v.x/len, v.y/len, v.z/len)
        return fallback
    }

    readonly property vector3d _delta: Qt.vector3d(
        endPoint.x - startPoint.x,
        endPoint.y - startPoint.y,
        endPoint.z - startPoint.z
    )
    readonly property vector3d _deltaPlanar: Qt.vector3d(_delta.x, _delta.y, 0)
    readonly property real _rawLength: Math.sqrt(_delta.x * _delta.x + _delta.y * _delta.y + _delta.z * _delta.z)
    readonly property real length: Math.max(_rawLength, minimumLength)
    readonly property vector3d midpoint: Qt.vector3d(
        (startPoint.x + endPoint.x) / 2,
        (startPoint.y + endPoint.y) / 2,
        (startPoint.z + endPoint.z) / 2
    )
    readonly property real safeRadius: Math.max(radius, 1e-5)

    readonly property vector3d _dir: _vnormalize(planar ? _deltaPlanar : _delta, Qt.vector3d(0, 1, 0))
    readonly property quaternion orientationQuat: _orientationFromDir(_dir)

    readonly property real rotationDeg: Math.atan2((planar ? _deltaPlanar.y : _delta.y), (planar ? _deltaPlanar.x : _delta.x)) * 180 / Math.PI + 90

    function _orientationFromDir(dir) {
        var yAxis = Qt.vector3d(0, 1, 0)
        var eps = 1e-6
        var dot = _vdot(yAxis, dir)
        if (Math.abs(dot - 1.0) < eps)
            return Qt.quaternion(1, 0, 0, 0)
        if (Math.abs(dot + 1.0) < eps)
            return Qt.quaternion(0, 1, 0, 0)
        var axis = _vcross(yAxis, dir)
        var axisLen = _vlen(axis)
        if (axisLen < eps)
            return Qt.quaternion(1, 0, 0, 0)
        axis = Qt.vector3d(axis.x/axisLen, axis.y/axisLen, axis.z/axisLen)
        var angle = Math.acos(_clamp(dot, -1.0, 1.0))
        var half = angle / 2.0
        var s = Math.sin(half)
        var c = Math.cos(half)
        return Qt.quaternion(c, axis.x * s, axis.y * s, axis.z * s)
    }

    function _applyScale() {
        cylinderModel.scale = Qt.vector3d(root.safeRadius, root.length / 2, root.safeRadius)
    }

    function _syncProcGeom() {
        if (!_procGeom)
            return
        try { _procGeom.segments = segments } catch (e) {}
        try { _procGeom.rings = rings } catch (e) {}
        try { _procGeom.radius = safeRadius } catch (e) {}
        try { _procGeom.length = length } catch (e) {}
    }

    function _destroyProcGeom() {
        if (_procGeom) {
            // Отвязываем геометрию и переходим на mesh
            try { cylinderModel.geometry = null } catch (e) {}
            _procGeom = null
            GeometryCompat.applyCylinderMesh(cylinderModel, segments, rings)
        }
    }

    function _tryCreateProcedural() {
        if (!allowProcedural)
            return false
        var qml = "import QtQuick 6.10\n"
                + "import QtQuick3D 6.10\n"
                + "import CustomGeometry 1.0\n"
                + "ProceduralCylinderGeometry {}\n"
        try {
            var obj = Qt.createQmlObject(qml, cylinderModel, "LinearCylinderProcGeom")
            if (obj) {
                try { cylinderModel.geometry = obj } catch (e) { obj = null }
            }
            _procGeom = obj || null
            if (_procGeom)
                _syncProcGeom()
            return !!_procGeom
        } catch (e) {
            _procGeom = null
            return false
        }
    }

    function refreshGeometry() {
        if (_procGeom) {
            // Уже процедурная: просто синхронизируем
            _syncProcGeom()
            return
        }
        if (!_tryCreateProcedural()) {
            GeometryCompat.applyCylinderMesh(cylinderModel, segments, rings)
        }
    }

    Component.onCompleted: {
        if (warnOnTinyLength && _rawLength < minimumLength * 2)
            console.warn("LinearCylinder: endpoints nearly overlapping", startPoint, endPoint)
        _applyScale()
        refreshGeometry()
    }

    onSegmentsChanged: {
        _syncProcGeom()
        if (!_procGeom)
            GeometryCompat.applyCylinderMesh(cylinderModel, segments, rings)
    }
    onRingsChanged: {
        _syncProcGeom()
        if (!_procGeom)
            GeometryCompat.applyCylinderMesh(cylinderModel, segments, rings)
    }
    onRadiusChanged: {
        _applyScale(); _syncProcGeom()
    }
    onLengthChanged: {
        _applyScale(); _syncProcGeom()
    }
    onAllowProceduralChanged: {
        if (!allowProcedural)
            _destroyProcGeom()
        else
            refreshGeometry()
    }
    onStartPointChanged: {}
    onEndPointChanged: {}
    onPlanarChanged: {}

    Model {
        id: cylinderModel
        objectName: "cylinderModel"
        position: root.midpoint
        rotation: root.orientationQuat
        source: "#Cylinder"
        materials: root.material ? [root.material] : root.materialOverrides
    }
}
