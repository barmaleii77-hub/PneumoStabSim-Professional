import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Controls.Basic 6.10
import QtQuick.Layouts 6.10

Item {
    id: root
    implicitWidth: 560
    implicitHeight: 680

    property alias currentTab: tabBar.currentIndex
    readonly property var tabs: [
        {
            key: "lighting",
            title: "Lighting",
            sections: [
                {
                    key: "keyLighting",
                    title: "Key light",
                    hint: "Control the key light's intensity, direction, and color."
                },
                {
                    key: "fillLighting",
                    title: "Fill light",
                    hint: "Soften contrast by adjusting the contribution from fill lights."
                }
            ]
        },
        {
            key: "environment",
            title: "Environment",
            sections: [
                {
                    key: "skyEnvironment",
                    title: "Sky and HDRI",
                    hint: "Select environment maps and balance sky illumination."
                },
                {
                    key: "fogEnvironment",
                    title: "Fog and atmosphere",
                    hint: "Shape volumetric fog density, falloff, and horizon height."
                }
            ]
        },
        {
            key: "quality",
            title: "Quality",
            sections: [
                {
                    key: "renderQuality",
                    title: "Render pipeline quality",
                    hint: "Configure anti-aliasing, shadow resolution, and texture filtering."
                },
                {
                    key: "optimization",
                    title: "Performance safeguards",
                    hint: "Limit frame rate and render scale to safeguard performance."
                }
            ]
        },
        {
            key: "scene",
            title: "Scene",
            sections: [
                {
                    key: "sceneDefaults",
                    title: "Scene defaults",
                    hint: "Manage default animation states and global scene toggles."
                },
                {
                    key: "motionBlur",
                    title: "Motion blur",
                    hint: "Balance motion blur with shutter duration and vector strength."
                }
            ]
        },
        {
            key: "camera",
            title: "Camera",
            sections: [
                {
                    key: "cameraRig",
                    title: "Camera rig",
                    hint: "Configure orbit rig sensitivity, pivot behaviour, and damping."
                },
                {
                    key: "dofControls",
                    title: "Depth of field",
                    hint: "Focus the camera with distance, aperture, and bokeh controls."
                }
            ]
        },
        {
            key: "materials",
            title: "Materials",
            sections: [
                {
                    key: "surfaceMaterials",
                    title: "Surface response",
                    hint: "Tune base color, roughness, and metallic response."
                },
                {
                    key: "clearcoat",
                    title: "Clear coat",
                    hint: "Layer clear coat strength, tint, and Fresnel behaviour."
                }
            ]
        },
        {
            key: "effects",
            title: "Effects",
            sections: [
                {
                    key: "postEffects",
                    title: "Post-processing",
                    hint: "Enable bloom, vignette, and exposure adaptation."
                },
                {
                    key: "postToneMapping",
                    title: "Tone mapping",
                    hint: "Select tone mapping curves and white point to balance highlights."
                }
            ]
        }
    ]

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        TabBar {
            id: tabBar
            objectName: "tabBar"
            Layout.fillWidth: true
            currentIndex: Math.min(currentIndex, count - 1)

            Repeater {
                model: root.tabs
                TabButton {
                    required property var modelData
                    readonly property var tab: modelData
                    objectName: "tabButton_" + tab.key
                    text: qsTr(tab.title)
                }
            }
        }

        StackLayout {
            id: tabStack
            objectName: "tabStack"
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            Repeater {
                model: root.tabs
                ScrollView {
                    id: tabPage
                    required property var modelData
                    readonly property var tab: modelData

                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: availableWidth
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                    ColumnLayout {
                        width: parent.width
                        spacing: 12

                        Repeater {
                            model: tabPage.tab.sections
                            GroupBox {
                                id: sectionGroup
                                required property var modelData
                                readonly property var section: modelData

                                Layout.fillWidth: true
                                objectName: "section_" + sectionGroup.section.key
                                title: qsTr(sectionGroup.section.title)

                                ColumnLayout {
                                    width: parent.width
                                    spacing: 6

                                    Label {
                                        objectName: "hint_" + sectionGroup.section.key
                                        Layout.fillWidth: true
                                        text: qsTr(sectionGroup.section.hint)
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Button {
                id: resetButton
                objectName: "resetButton"
                text: qsTr("Reset to defaults")
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Revert all tabs to the active profile defaults.")
            }

            Button {
                id: saveDefaultsButton
                objectName: "saveDefaultsButton"
                text: qsTr("Save as defaults")
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Store the current configuration as the new default profile.")
            }

            Item {
                Layout.fillWidth: true
            }

            Button {
                id: exportButton
                objectName: "exportButton"
                text: qsTr("Export snapshot")
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Export the active graphics configuration for diagnostics.")
            }
        }
    }
}
