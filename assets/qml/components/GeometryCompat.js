// GeometryCompat.js — попытка повысить качество геометрии при наличии QtQuick3D.Helpers
// Позволяет апгрейдить встроенные примитивы (#Cone/#Cylinder/#Sphere) до Mesh-типов

function _createIn(target, qml) {
    if (!target) return null
    try {
        // Импортируем Helpers, где объявлены *Mesh типы
        var header = 'import QtQuick 6.10\nimport QtQuick3D 6.10\nimport QtQuick3D.Helpers 6.10\n'
        return Qt.createQmlObject(header + qml, target, 'GeometryCompat')
    } catch (e) {
        return null
    }
}

function _safeSet(target, name, value) {
    if (!target) return false
    try {
        if (target.setProperty !== undefined) {
            var r = target.setProperty(name, value)
            return r === undefined ? true : Boolean(r)
        }
        target[name] = value
        return true
    } catch (e) {
        return false
    }
}

function applyCylinderMesh(model, slices, rings) {
    var s = Math.max(3, Number(slices) || 24)
    var r = Math.max(1, Number(rings) || 1)
    var obj = _createIn(model, 'CylinderMesh { slices: ' + s + '; rings: ' + r + ' }')
    if (obj) {
        // Современное API — свойство 'mesh'
        if (!_safeSet(model, 'mesh', obj)) {
            _safeSet(model, 'geometry', obj)
        }
        return true
    }
    return false
}

function applyConeMesh(model, slices, rings) {
    var s = Math.max(3, Number(slices) || 24)
    var r = Math.max(1, Number(rings) || 1)
    var obj = _createIn(model, 'ConeMesh { slices: ' + s + '; rings: ' + r + ' }')
    if (obj) {
        if (!_safeSet(model, 'mesh', obj)) {
            _safeSet(model, 'geometry', obj)
        }
        return true
    }
    return false
}

function applySphereMesh(model, rings, slices) {
    var s = Math.max(6, Number(slices) || 24)
    var r = Math.max(6, Number(rings) || 16)
    var obj = _createIn(model, 'SphereMesh { slices: ' + s + '; rings: ' + r + ' }')
    if (obj) {
        if (!_safeSet(model, 'mesh', obj)) {
            _safeSet(model, 'geometry', obj)
        }
        return true
    }
    return false
}

var GeometryCompat = {
    applyCylinderMesh: applyCylinderMesh,
    applyConeMesh: applyConeMesh,
    applySphereMesh: applySphereMesh
}

function __dummy() {}
