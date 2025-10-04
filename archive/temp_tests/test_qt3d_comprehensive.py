#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE Qt Quick 3D TEST APPLICATION
Tests multiple scenarios to identify the exact issue
"""
import sys
import os
from pathlib import Path

# Set RHI backend BEFORE importing PySide6
os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.scenegraph*=true;qt.rhi*=true;qt.quick3d*=true"

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTabWidget
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, QTimer, Qt

print("="*80)
print("COMPREHENSIVE Qt Quick 3D DIAGNOSTIC TEST")
print("="*80)
print()
print("This application tests 5 different QML scenarios:")
print("  Tab 1: Minimal (View3D + Sphere only)")
print("  Tab 2: With Item wrapper")
print("  Tab 3: With 2D overlay")
print("  Tab 4: Complex (current main.qml)")
print("  Tab 5: Alternative backends test")
print()
print("="*80)
print()

# TEST SCENARIO 1: Absolute minimal - just View3D and Sphere
QML_TEST_1_MINIMAL = """
import QtQuick
import QtQuick3D

View3D {
    anchors.fill: parent
    
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#ff0000"
    }
    
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 5)
    }
    
    DirectionalLight {
        brightness: 2.0
    }
    
    Model {
        source: "#Sphere"
        scale: Qt.vector3d(2, 2, 2)
        materials: PrincipledMaterial {
            baseColor: "#00ff00"
        }
        NumberAnimation on eulerRotation.y {
            from: 0; to: 360; duration: 3000
            loops: Animation.Infinite; running: true
        }
    }
}
"""

# TEST SCENARIO 2: Item wrapper (recommended structure)
QML_TEST_2_ITEM_WRAPPER = """
import QtQuick
import QtQuick3D

Item {
    anchors.fill: parent
    
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
            brightness: 2.0
        }
        
        Model {
            source: "#Sphere"
            scale: Qt.vector3d(2, 2, 2)
            materials: PrincipledMaterial {
                baseColor: "#ffff00"
            }
            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }
        }
    }
}
"""

# TEST SCENARIO 3: With 2D overlay
QML_TEST_3_WITH_OVERLAY = """
import QtQuick
import QtQuick3D

Item {
    anchors.fill: parent
    
    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#ff00ff"
        }
        
        PerspectiveCamera {
            position: Qt.vector3d(0, 0, 5)
        }
        
        DirectionalLight {
            brightness: 2.0
        }
        
        Model {
            source: "#Sphere"
            scale: Qt.vector3d(2, 2, 2)
            materials: PrincipledMaterial {
                baseColor: "#00ffff"
            }
            NumberAnimation on eulerRotation.y {
                from: 0; to: 360; duration: 3000
                loops: Animation.Infinite; running: true
            }
        }
    }
    
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 10
        width: 200
        height: 60
        color: "#80000000"
        border.color: "#ffffff"
        
        Text {
            anchors.centerIn: parent
            text: "2D OVERLAY\\nON TOP OF 3D"
            color: "#ffffff"
            font.pixelSize: 14
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
"""

# TEST SCENARIO 4: Current main.qml structure
QML_TEST_4_CURRENT = """
import QtQuick
import QtQuick3D

Item {
    id: root
    anchors.fill: parent
    
    View3D {
        id: view3d
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#1a1a2e"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }
        
        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 5)
            eulerRotation: Qt.vector3d(0, 0, 0)
        }
        
        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: 30
            brightness: 1.0
        }
        
        Model {
            id: sphere
            source: "#Sphere"
            position: Qt.vector3d(0, 0, 0)
            scale: Qt.vector3d(1, 1, 1)
            
            materials: PrincipledMaterial {
                baseColor: "#ff4444"
                metalness: 0.0
                roughness: 0.5
            }
            
            NumberAnimation on eulerRotation.y {
                from: 0
                to: 360
                duration: 3000
                loops: Animation.Infinite
                running: true
            }
        }
    }
    
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 20
        width: 250
        height: 60
        color: "#20000000"
        border.color: "#40ffffff"
        border.width: 1
        radius: 5
        
        Column {
            anchors.centerIn: parent
            spacing: 3
            
            Text {
                text: "Test 4: Current Structure"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true
            }
            
            Text {
                text: "Red sphere with dark background"
                color: "#aaaaaa"
                font.pixelSize: 10
            }
        }
    }
}
"""

# TEST SCENARIO 5: Multiple primitives test
QML_TEST_5_MULTIPLE = """
import QtQuick
import QtQuick3D

View3D {
    anchors.fill: parent
    
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#2a2a2a"
    }
    
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 8)
    }
    
    DirectionalLight {
        eulerRotation.x: -30
        brightness: 1.5
    }
    
    // Sphere
    Model {
        source: "#Sphere"
        position: Qt.vector3d(-2, 0, 0)
        materials: PrincipledMaterial { baseColor: "#ff0000" }
        NumberAnimation on eulerRotation.y {
            from: 0; to: 360; duration: 3000
            loops: Animation.Infinite; running: true
        }
    }
    
    // Cube
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, 0, 0)
        materials: PrincipledMaterial { baseColor: "#00ff00" }
        NumberAnimation on eulerRotation.x {
            from: 0; to: 360; duration: 4000
            loops: Animation.Infinite; running: true
        }
    }
    
    // Cylinder
    Model {
        source: "#Cylinder"
        position: Qt.vector3d(2, 0, 0)
        materials: PrincipledMaterial { baseColor: "#0000ff" }
        NumberAnimation on eulerRotation.z {
            from: 0; to: 360; duration: 5000
            loops: Animation.Infinite; running: true
        }
    }
}
"""


class TestTab(QWidget):
    """Single test tab with QML widget"""
    
    def __init__(self, test_name, qml_code, expected_bg, expected_obj, parent=None):
        super().__init__(parent)
        
        self.test_name = test_name
        self.qml_code = qml_code
        self.expected_bg = expected_bg
        self.expected_obj = expected_obj
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Info label
        info = QLabel(f"<b>{test_name}</b><br>"
                     f"Expected BG: {expected_bg}<br>"
                     f"Expected OBJ: {expected_obj}")
        info.setStyleSheet("background: #333; color: #fff; padding: 5px; font-size: 11pt;")
        layout.addWidget(info)
        
        # QML widget
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        
        # Save QML to temp file
        qml_path = Path(f"test_qml_{test_name.replace(' ', '_').lower()}.qml")
        qml_path.write_text(qml_code, encoding='utf-8')
        
        # Load QML
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)
        
        layout.addWidget(self.qml_widget, 1)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("background: #000; color: #0f0; padding: 5px; font-family: monospace;")
        layout.addWidget(self.status_label)
        
        # Check status
        self.update_status()
        
        # Update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)
    
    def update_status(self):
        status = self.qml_widget.status()
        
        if status == QQuickWidget.Status.Error:
            errors = "\n".join([e.toString() for e in self.qml_widget.errors()])
            self.status_label.setText(f"ERROR: {errors}")
            self.status_label.setStyleSheet("background: #000; color: #f00; padding: 5px; font-family: monospace;")
        elif status == QQuickWidget.Status.Ready:
            root = self.qml_widget.rootObject()
            size = self.qml_widget.size()
            self.status_label.setText(
                f"Ready | Root: {'OK' if root else 'NULL'} | Size: {size.width()}x{size.height()}"
            )
            self.status_label.setStyleSheet("background: #000; color: #0f0; padding: 5px; font-family: monospace;")
        else:
            self.status_label.setText(f"Status: {status}")


class ComprehensiveTestWindow(QMainWindow):
    """Main test window with multiple tabs"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Qt Quick 3D - Comprehensive Diagnostic Test")
        self.resize(1000, 700)
        
        # Central widget
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Instructions
        instructions = QLabel(
            "<b>INSTRUCTIONS:</b> Switch between tabs to test different QML scenarios.<br>"
            "For EACH tab, note what you SEE:<br>"
            "- Background color (should match 'Expected BG')<br>"
            "- 3D object(s) (should match 'Expected OBJ')<br>"
            "- Any errors in status bar at bottom of each tab"
        )
        instructions.setStyleSheet("background: #1a1a2e; color: #fff; padding: 10px; font-size: 11pt;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Tab widget
        tabs = QTabWidget(self)
        
        # Add test tabs
        tabs.addTab(
            TestTab("Test 1: Minimal", QML_TEST_1_MINIMAL, 
                   "RED (#ff0000)", "GREEN sphere"),
            "1: Minimal"
        )
        
        tabs.addTab(
            TestTab("Test 2: Item Wrapper", QML_TEST_2_ITEM_WRAPPER,
                   "BLUE (#0000ff)", "YELLOW sphere"),
            "2: Item Wrapper"
        )
        
        tabs.addTab(
            TestTab("Test 3: With Overlay", QML_TEST_3_WITH_OVERLAY,
                   "MAGENTA (#ff00ff)", "CYAN sphere + overlay"),
            "3: Overlay"
        )
        
        tabs.addTab(
            TestTab("Test 4: Current", QML_TEST_4_CURRENT,
                   "DARK BLUE (#1a1a2e)", "RED sphere + overlay"),
            "4: Current"
        )
        
        tabs.addTab(
            TestTab("Test 5: Multiple", QML_TEST_5_MULTIPLE,
                   "DARK GRAY (#2a2a2a)", "RED sphere + GREEN cube + BLUE cylinder"),
            "5: Multiple"
        )
        
        layout.addWidget(tabs)
        
        # Result recording area
        result_label = QLabel(
            "<b>RECORD YOUR RESULTS:</b><br>"
            "For each tab, write down:<br>"
            "1 = See correct background + 3D objects<br>"
            "2 = See correct background but NO 3D objects<br>"
            "3 = Wrong background or blank screen"
        )
        result_label.setStyleSheet("background: #2a2a3e; color: #fff; padding: 10px; font-size: 10pt;")
        layout.addWidget(result_label)
        
        self.setCentralWidget(central)
        
        print("\n" + "="*80)
        print("TEST WINDOW OPENED")
        print("="*80)
        print()
        print("Check EACH of the 5 tabs and record what you see:")
        print()
        print("Tab 1 (Minimal): Expected RED background + GREEN rotating sphere")
        print("Tab 2 (Item Wrapper): Expected BLUE background + YELLOW rotating sphere")
        print("Tab 3 (Overlay): Expected MAGENTA background + CYAN sphere + 2D overlay")
        print("Tab 4 (Current): Expected DARK BLUE background + RED sphere + overlay")
        print("Tab 5 (Multiple): Expected 3 objects (red sphere, green cube, blue cylinder)")
        print()
        print("For EACH tab, answer: 1, 2, or 3")
        print("  1 = Correct (background + 3D visible)")
        print("  2 = Background only (no 3D)")
        print("  3 = Broken (wrong colors or blank)")
        print()
        print("="*80)


def main():
    app = QApplication(sys.argv)
    
    window = ComprehensiveTestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
