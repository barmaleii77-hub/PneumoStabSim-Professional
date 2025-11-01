import QtQuick 2.15
import QtQuick.Controls 2.15

pragma ComponentBehavior: Bound

Rectangle {
    id: root
    width: 280
    radius: 8
    color: "#B0202020"
    border.width: 1
    border.color: "#30ffffff"
    visible: root.profileService !== null

    property var profileService: null
    property var profiles: []
    property string statusText: ""
    property bool _refreshingProfiles: false

    function refreshProfiles() {
        if (root._refreshingProfiles)
            return

        root._refreshingProfiles = true
        try {
            if (
                !root.profileService
                || typeof root.profileService.listProfiles !== "function"
            ) {
                root.profiles = []
                profileCombo.currentIndex = -1
                nameField.text = ""
                return
            }

            const names = root.profileService.listProfiles()
            root.profiles = names ? names : []

            if (root.profiles.length === 0) {
                profileCombo.currentIndex = -1
            } else if (profileCombo.currentIndex < 0) {
                profileCombo.currentIndex = 0
            }
        } finally {
            root._refreshingProfiles = false
        }
    }

    Component.onCompleted: refreshProfiles()
    onProfileServiceChanged: refreshProfiles()

    Column {
        id: layout
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        Label {
            text: qsTr("Settings profiles")
            color: "#ffffff"
            font.pixelSize: 14
            font.bold: true
        }

        ComboBox {
            id: profileCombo
            model: root.profiles
            enabled: root.profiles.length > 0
            onActivated: {
                if (currentIndex >= 0) {
                    nameField.text = currentText
                }
            }
        }

        TextField {
            id: nameField
            placeholderText: qsTr("Profile name")
            text: profileCombo.currentIndex >= 0 ? profileCombo.currentText : ""
        }

        Row {
            spacing: 8

            Button {
                text: qsTr("Load")
                enabled: root.profileService && profileCombo.currentIndex >= 0
                onClicked: {
                    if (root.profileService) {
                        root.profileService.loadProfile(profileCombo.currentText)
                    }
                }
            }

            Button {
                text: qsTr("Save")
                enabled: root.profileService && nameField.text.length > 0
                onClicked: {
                    if (root.profileService) {
                        root.profileService.saveProfile(nameField.text)
                    }
                }
            }
        }

        Button {
            text: qsTr("Delete")
            enabled: root.profileService && profileCombo.currentIndex >= 0
            onClicked: {
                if (root.profileService) {
                    root.profileService.deleteProfile(profileCombo.currentText)
                }
            }
        }

        Text {
            id: statusLabel
            text: root.statusText
            visible: root.statusText.length > 0
            color: "#dddddd"
            wrapMode: Text.Wrap
            font.pixelSize: 11
        }
    }

    Connections {
        target: root.profileService

        function onProfilesChanged(names) {
            if (root._refreshingProfiles)
                return
            root.profiles = names || []
            if (root.profiles.length === 0) {
                profileCombo.currentIndex = -1
                nameField.text = ""
            }
        }

        function onProfileSaved(name) {
            root.statusText = qsTr("Profile '%1' saved").arg(name)
            root.refreshProfiles()
        }

        function onProfileLoaded(name) {
            root.statusText = qsTr("Profile '%1' loaded").arg(name)
            root.refreshProfiles()
        }

        function onProfileDeleted(name) {
            root.statusText = qsTr("Profile '%1' deleted").arg(name)
            root.refreshProfiles()
        }

        function onProfileError(operation, message) {
            root.statusText = qsTr("%1: %2").arg(operation).arg(message)
        }
    }
}
