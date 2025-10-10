import QtQuick
import QtQuick3D

SceneEnvironment {
    id: root

    property int tonemapSelection: SceneEnvironment.TonemapModeFilmic
    property bool tonemapToggle: true

    function resolvedTonemapMode(selection, enabled) {
        if (!enabled)
            return SceneEnvironment.TonemapModeNone

        switch (selection) {
        case SceneEnvironment.TonemapModeFilmic:
        case 3:
            return SceneEnvironment.TonemapModeFilmic
        case SceneEnvironment.TonemapModeReinhard:
        case 2:
            return SceneEnvironment.TonemapModeReinhard
        case SceneEnvironment.TonemapModeLinear:
        case 1:
            return SceneEnvironment.TonemapModeLinear
        default:
            return SceneEnvironment.TonemapModeNone
        }
    }

    onTonemapSelectionChanged: tonemapMode = resolvedTonemapMode(tonemapSelection, tonemapToggle)
    onTonemapToggleChanged: tonemapMode = resolvedTonemapMode(tonemapSelection, tonemapToggle)

    Component.onCompleted: tonemapMode = resolvedTonemapMode(tonemapSelection, tonemapToggle)
}
