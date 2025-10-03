
import QtQuick
import QtQuick3D

View3D {
    anchors.fill: parent
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#0000ff"
    }
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 5)
    }
    DirectionalLight {
        brightness: 1.0
    }
}
