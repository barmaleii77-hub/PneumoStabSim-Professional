import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    width: 280
    radius: 8
    color: "#B0202020"
    border.width: 1
    border.color: "#30ffffff"
    visible: profileService !== null

    property var profileService: null
    property var profiles: []
    property string statusText: ""

    function refreshProfiles() {
        if (!profileService || typeof profileService.listProfiles !== "function") {
            profiles = []
            profileCombo.currentIndex = -1
            nameField.text = ""
            return
        }

        const names = profileService.listProfiles()
        profiles = names ? names : []

        if (profiles.length === 0) {
            profileCombo.currentIndex = -1
        } else if (profileCombo.currentIndex < 0) {
            profileCombo.currentIndex = 0
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
            model: profiles
            enabled: profiles.length > 0
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
                enabled: profileService && profileCombo.currentIndex >= 0
                onClicked: {
                    if (profileService) {
                        profileService.loadProfile(profileCombo.currentText)
                    }
                }
            }

            Button {
                text: qsTr("Save")
                enabled: profileService && nameField.text.length > 0
                onClicked: {
                    if (profileService) {
                        profileService.saveProfile(nameField.text)
                    }
                }
            }
        }

        Button {
            text: qsTr("Delete")
            enabled: profileService && profileCombo.currentIndex >= 0
            onClicked: {
                if (profileService) {
                    profileService.deleteProfile(profileCombo.currentText)
                }
            }
        }

        Text {
            id: statusLabel
            text: statusText
            visible: statusText.length > 0
            color: "#dddddd"
            wrapMode: Text.Wrap
            font.pixelSize: 11
        }
    }

    Connections {
        target: profileService

        function onProfilesChanged(names) {
            profiles = names || []
            if (profiles.length === 0) {
                profileCombo.currentIndex = -1
                nameField.text = ""
            }
        }

        function onProfileSaved(name) {
            statusText = qsTr("Profile '%1' saved").arg(name)
            refreshProfiles()
        }

        function onProfileLoaded(name) {
            statusText = qsTr("Profile '%1' loaded").arg(name)
            refreshProfiles()
        }

        function onProfileDeleted(name) {
            statusText = qsTr("Profile '%1' deleted").arg(name)
            refreshProfiles()
        }

        function onProfileError(operation, message) {
            statusText = qsTr("%1: %2").arg(operation).arg(message)
        }
    }
}
