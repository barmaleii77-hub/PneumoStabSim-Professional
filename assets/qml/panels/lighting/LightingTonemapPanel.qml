import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQml 2.15
import Panels.Common 1.0

ColumnLayout {
    id: root

    property var settingsBridge: (typeof lightingSettings !== "undefined" ? lightingSettings : null)
    property var tonemapPresets: []
    property string activePresetId: ""

    signal presetActivated(string presetId)

    spacing: 12
    Layout.fillWidth: true

    Binding {
        target: root
        property: "tonemapPresets"
        value: root.settingsBridge ? root.settingsBridge.tonemapPresets : []
    }

    Binding {
        target: root
        property: "activePresetId"
        value: root.settingsBridge ? root.settingsBridge.activeTonemapPreset : ""
    }

    PresetButtons {
        Layout.fillWidth: true
        title: qsTr("Tonemapping presets")
        emptyText: qsTr("No tonemapping presets configured")
        model: root.tonemapPresets
        activePresetId: root.activePresetId
        onPresetActivated: function(presetId) {
            root.presetActivated(presetId)
            if (root.settingsBridge) {
                root.settingsBridge.applyTonemapPreset(presetId)
            }
        }
    }
}
