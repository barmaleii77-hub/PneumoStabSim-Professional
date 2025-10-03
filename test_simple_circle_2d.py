# -*- coding: utf-8 -*-
"""
Test 2D circle in QML - no 3D, just basic QML
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl

# Simple 2D QML with circle
SIMPLE_2D_QML = """
import QtQuick

Rectangle {
    anchors.fill: parent
    color: "#1a1a2e"
    
    // Red circle
    Rectangle {
        id: circle
        width: 200
        height: 200
        radius: 100
        color: "#ff4444"
        anchors.centerIn: parent
        
        // Rotation animation
        RotationAnimation on rotation {
            from: 0
            to: 360
            duration: 3000
            loops: Animation.Infinite
        }
        
        // White dot in center to show rotation
        Rectangle {
            width: 20
            height: 20
            radius: 10
            color: "#ffffff"
            x: parent.width / 2 - 10
            y: 20
        }
    }
    
    // Title text
    Text {
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 50
        text: "2D ROTATING CIRCLE (RED)"
        color: "#ffffff"
        font.pixelSize: 24
        font.bold: true
    }
    
    // Info text
    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 50
        text: "White dot shows rotation"
        color: "#aaaaaa"
        font.pixelSize: 16
    }
}
"""


class Simple2DWindow(QWidget):
    """Simple 2D test window"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("QML 2D Test - Circle")
        self.resize(800, 600)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # QQuickWidget
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        
        # Save QML
        qml_path = Path("test_circle_2d_temp.qml")
        qml_path.write_text(SIMPLE_2D_QML, encoding='utf-8')
        
        # Load QML
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)
        
        # Check status
        if self.qml_widget.status() == QQuickWidget.Status.Error:
            print("ERROR: QML ERRORS:")
            for error in self.qml_widget.errors():
                print(f"   {error.toString()}")
        else:
            print("SUCCESS: 2D QML loaded")
            print(f"   Status: {self.qml_widget.status()}")
        
        layout.addWidget(self.qml_widget)
        
        print("\n" + "="*60)
        print("2D QML TEST (NO 3D)")
        print("="*60)
        print("Expected:")
        print("  - Dark blue background")
        print("  - Red circle in center (200x200)")
        print("  - White dot rotating to show animation")
        print("  - Text on top and bottom")
        print("="*60 + "\n")


def main():
    app = QApplication(sys.argv)
    
    print("Creating 2D test window...")
    window = Simple2DWindow()
    
    print("Showing window...")
    window.show()
    
    print("Starting event loop...\n")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
