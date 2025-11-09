pragma ComponentBehavior: Bound

import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Controls.Basic 6.10
import QtQuick.Layouts 6.10

Item {
    id: root
    implicitWidth: 560
    implicitHeight: 680

    property color accentColor: "#4FC3F7"
    property color backgroundColor: "#101821"
    property color surfaceColor: "#182434"
    property color borderColor: "#293542"
    property color textColor: "#E6EEF5"
    property color mutedTextColor: "#A9B7C6"

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

    Rectangle {
        anchors.fill: parent
        radius: 10
        color: root.backgroundColor
        border.color: root.borderColor
        border.width: 1
        z: -1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        TabBar {
            id: tabBar
            objectName: "tabBar"
            Layout.fillWidth: true
            currentIndex: Math.min(currentIndex, count - 1)
            focusPolicy: Qt.StrongFocus
            Accessible.role: Accessible.PageTabList
            Accessible.name: qsTr("Graphics configuration categories")

            background: Rectangle {
                implicitHeight: 42
                radius: 8
                color: root.surfaceColor
                border.width: tabBar.activeFocus ? 2 : 1
                border.color: tabBar.activeFocus ? root.accentColor : root.borderColor
            }

            Repeater {
                model: root.tabs
                TabButton {
                    id: tabButton
                    required property var modelData
                    readonly property var tab: modelData
                    objectName: "tabButton_" + tab.key
                    text: qsTr(tab.title)
                    focusPolicy: Qt.StrongFocus
                    Accessible.role: Accessible.PageTab
                    Accessible.name: text
                    Accessible.description: tab.sections
                        .map(function(section) { return qsTr(section.title); })
                        .join(", ")

                    contentItem: Label {
                        text: tabButton.text
                        font.bold: tabButton.checked
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                        color: tabButton.checked || tabButton.activeFocus ? root.accentColor : root.textColor
                    }

                    background: Rectangle {
                        implicitHeight: 34
                        radius: 6
                        color: tabButton.checked ? Qt.lighter(root.surfaceColor, 1.2) : "transparent"
                        border.width: tabButton.activeFocus ? 2 : 1
                        border.color: tabButton.activeFocus ? root.accentColor : root.borderColor
                    }
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
                    focusPolicy: Qt.StrongFocus
                    Accessible.role: Accessible.Pane
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical: ScrollBar {
                        id: verticalBar
                        policy: ScrollBar.AsNeeded
                        active: tabPage.activeFocus
                        background: Rectangle {
                            color: "transparent"
                        }
                        contentItem: Rectangle {
                            radius: 4
                            implicitWidth: 6
                            color: verticalBar.pressed || verticalBar.hovered
                                ? root.accentColor
                                : Qt.lighter(root.surfaceColor, 1.6)
                        }
                    }

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
                                focusPolicy: Qt.StrongFocus
                                Accessible.role: Accessible.Grouping
                                Accessible.name: qsTr("%1 section").arg(sectionGroup.section.title)
                                Accessible.description: qsTr(sectionGroup.section.hint)

                                background: Rectangle {
                                    radius: 8
                                    color: root.surfaceColor
                                    border.width: sectionGroup.activeFocus ? 2 : 1
                                    border.color: sectionGroup.activeFocus ? root.accentColor : root.borderColor
                                }

                                ColumnLayout {
                                    width: parent.width
                                    spacing: 6

                                    Label {
                                        objectName: "hint_" + sectionGroup.section.key
                                        Layout.fillWidth: true
                                        text: qsTr(sectionGroup.section.hint)
                                        color: root.mutedTextColor
                                        wrapMode: Text.WordWrap
                                        Accessible.role: Accessible.StaticText
                                        Accessible.name: qsTr(sectionGroup.section.hint)
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
                focusPolicy: Qt.StrongFocus
                Accessible.name: text
                Accessible.description: qsTr("Revert all tabs to their default values")
                background: Rectangle {
                    radius: 6
                    color: resetButton.down ? Qt.darker(root.surfaceColor, 1.4) : root.surfaceColor
                    border.width: resetButton.activeFocus ? 2 : 1
                    border.color: resetButton.activeFocus ? root.accentColor : root.borderColor
                }
                contentItem: Label {
                    text: resetButton.text
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: resetButton.activeFocus || resetButton.hovered ? root.accentColor : root.textColor
                }
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Revert all tabs to the active profile defaults.")
            }

            Button {
                id: saveDefaultsButton
                objectName: "saveDefaultsButton"
                text: qsTr("Save as defaults")
                focusPolicy: Qt.StrongFocus
                Accessible.name: text
                Accessible.description: qsTr("Store the active configuration as the default profile")
                background: Rectangle {
                    radius: 6
                    color: saveDefaultsButton.down ? Qt.darker(root.surfaceColor, 1.4) : root.surfaceColor
                    border.width: saveDefaultsButton.activeFocus ? 2 : 1
                    border.color: saveDefaultsButton.activeFocus ? root.accentColor : root.borderColor
                }
                contentItem: Label {
                    text: saveDefaultsButton.text
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: saveDefaultsButton.activeFocus || saveDefaultsButton.hovered ? root.accentColor : root.textColor
                }
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
                focusPolicy: Qt.StrongFocus
                Accessible.name: text
                Accessible.description: qsTr("Export the current graphics configuration for diagnostics")
                background: Rectangle {
                    radius: 6
                    color: exportButton.down ? Qt.darker(root.surfaceColor, 1.4) : root.surfaceColor
                    border.width: exportButton.activeFocus ? 2 : 1
                    border.color: exportButton.activeFocus ? root.accentColor : root.borderColor
                }
                contentItem: Label {
                    text: exportButton.text
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: exportButton.activeFocus || exportButton.hovered ? root.accentColor : root.textColor
                }
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Export the active graphics configuration for diagnostics.")
            }
        }
    }
}
