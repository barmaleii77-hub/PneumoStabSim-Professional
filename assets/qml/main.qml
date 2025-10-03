import QtQuick
import QtQuick3D

/*
 * MAIN PNEUMATIC SUSPENSION VISUALIZATION
 * Interactive 3D frame with unlimited mouse controls
 */
Item {
    id: root
    anchors.fill: parent
    
    // Load the interactive frame
    Loader {
        id: frameLoader
        anchors.fill: parent
        source: "main_interactive_frame.qml"
        
        onLoaded: {
            console.log("?? Interactive 3D frame loaded successfully")
        }
        
        onStatusChanged: {
            if (status === Loader.Error) {
                console.log("? Error loading interactive frame:", sourceComponent.errorString())
                // Fallback to simple 3D scene
                frameLoader.source = "main_working_builtin.qml"
            }
        }
    }
}
