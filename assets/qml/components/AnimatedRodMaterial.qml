import QtQuick 6.10
import QtQuick3D 6.10

PrincipledMaterial {
    id: root

    // ===========================================================
    // CONFIGURATION
    // ===========================================================
    property color okColor: "#00ff55"
    property color warningColor: "#ff3333"
    property bool warning: false

    baseColor: warning ? warningColor : okColor
    metalness: 1.0
    roughness: 0.22
    specularAmount: 1.0
    specularTint: 0.0
    clearcoatAmount: 0.15
    clearcoatRoughnessAmount: 0.08

    Behavior on baseColor {
        ColorAnimation {
            duration: 220
            easing.type: Easing.InOutQuad
        }
    }
}
