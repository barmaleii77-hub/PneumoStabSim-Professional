import QtQuick 6.10
import QtQuick3D 6.10
import "./MaterialCompat.js" as MaterialCompat

PrincipledMaterial {
    id: root

    // ===========================================================
    // CONFIGURATION (доступно из UI/внешних биндингов)
    // ===========================================================
    required property var materialsDefaults

    property color okColor: (materialsDefaults && materialsDefaults.rod_ok_color !== undefined
                             ? materialsDefaults.rod_ok_color : "#00ff55")
    property color warningColor: (materialsDefaults && materialsDefaults.rod_warning_color !== undefined
                                  ? materialsDefaults.rod_warning_color : "#ff3333")
    property bool warning: false

    // Базовые физические параметры (UI-доступные)
    property real pbrMetalness: 1.0
    property real pbrRoughness: 0.22
    property real pbrClearcoat: 0.15
    property real pbrClearcoatRoughness: 0.08
    property real pbrOpacity: 1.0
    property string pbrAlphaMode: "default"   // opaque|mask|blend|default
    property real pbrAlphaCutoff: 0.5

    // Цвет/эмиссия (на будущее)
    property color pbrEmissiveColor: "#000000"
    property real pbrEmissiveIntensity: 0.0

    // Minimal гарантированные свойства (не вызывают parse-ошибок)
    baseColor: warning ? warningColor : okColor
    metalness: pbrMetalness
    roughness: pbrRoughness

    // Clearcoat и прочее безопасно задаём через совместимость (setProperty)
    function _applyCompat() {
        MaterialCompat.applyPbr(root, {
            clearcoatAmount: pbrClearcoat,
            clearcoatRoughnessAmount: pbrClearcoatRoughness,
            opacity: pbrOpacity,
            alphaMode: pbrAlphaMode,
            alphaCutoff: pbrAlphaCutoff,
            emissiveColor: pbrEmissiveColor,
            emissiveIntensity: pbrEmissiveIntensity
        })
    }

    Component.onCompleted: _applyCompat()

    onPbrClearcoatChanged: _applyCompat()
    onPbrClearcoatRoughnessChanged: _applyCompat()
    onPbrOpacityChanged: _applyCompat()
    onPbrAlphaModeChanged: _applyCompat()
    onPbrAlphaCutoffChanged: _applyCompat()
    onPbrEmissiveColorChanged: _applyCompat()
    onPbrEmissiveIntensityChanged: _applyCompat()

    Behavior on baseColor {
        ColorAnimation { duration: 220; easing.type: Easing.InOutQuad }
    }
}
