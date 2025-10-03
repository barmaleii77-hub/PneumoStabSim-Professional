# -*- coding: utf-8 -*-
"""
Comprehensive Qt Quick 3D diagnostic test
Tests multiple scenarios to find why 3D is not working
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QSurfaceFormat

# Test 1: Minimal 3D scene
TEST_1_QML = """
import QtQuick
import QtQuick3D

View3D {
    anchors.fill: parent
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#ff0000"
    }
}
"""

# Test 2: 3D with camera only
TEST_2_QML = """
import QtQuick
import QtQuick3D

View3D {
    anchors.fill: parent
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#00ff00"
    }
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 5)
    }
}
"""

# Test 3: 3D with light
TEST_3_QML = """
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
"""

# Test 4: 3D with simple cube (not sphere)
TEST_4_QML = """
import QtQuick
import QtQuick3D

View3D {
    anchors.fill: parent
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#1a1a2e"
    }
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 5)
    }
    DirectionalLight {
        brightness: 1.0
        eulerRotation.x: -30
    }
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, 0, 0)
        materials: DefaultMaterial {
            diffuseColor: "#ffff00"
        }
    }
}
"""

# Test 5: 3D with sphere and DefaultMaterial
TEST_5_QML = """
import QtQuick
import QtQuick3D

View3D {
    anchors.fill: parent
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#1a1a2e"
    }
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 5)
    }
    DirectionalLight {
        brightness: 1.0
        eulerRotation.x: -30
    }
    Model {
        source: "#Sphere"
        position: Qt.vector3d(0, 0, 0)
        materials: DefaultMaterial {
            diffuseColor: "#ff4444"
        }
    }
}
"""

# Test 6: 3D with sphere and PrincipledMaterial
TEST_6_QML = """
import QtQuick
import QtQuick3D

View3D {
    anchors.fill: parent
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#1a1a2e"
    }
    PerspectiveCamera {
        position: Qt.vector3d(0, 0, 5)
    }
    DirectionalLight {
        brightness: 1.0
        eulerRotation.x: -30
    }
    Model {
        source: "#Sphere"
        position: Qt.vector3d(0, 0, 0)
        scale: Qt.vector3d(1.5, 1.5, 1.5)
        materials: PrincipledMaterial {
            baseColor: "#ff4444"
            metalness: 0.0
            roughness: 0.5
        }
    }
}
"""


class DiagnosticWindow(QWidget):
    """Diagnostic window with multiple test buttons"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Qt Quick 3D Diagnostic Tool")
        self.resize(900, 700)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Info label
        self.info_label = QLabel("Click buttons to test different 3D scenarios")
        self.info_label.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px;")
        layout.addWidget(self.info_label)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 10px; color: #666;")
        layout.addWidget(self.status_label)
        
        # Test buttons
        tests = [
            ("Test 1: Empty View3D (Red BG)", TEST_1_QML, "Should show RED background"),
            ("Test 2: + Camera (Green BG)", TEST_2_QML, "Should show GREEN background"),
            ("Test 3: + Light (Blue BG)", TEST_3_QML, "Should show BLUE background"),
            ("Test 4: + Cube (Yellow)", TEST_4_QML, "Should show YELLOW cube"),
            ("Test 5: + Sphere DefaultMaterial (Red)", TEST_5_QML, "Should show RED sphere"),
            ("Test 6: + Sphere PrincipledMaterial (Red)", TEST_6_QML, "Should show RED sphere (PBR)"),
        ]
        
        for i, (title, qml, expected) in enumerate(tests):
            btn = QPushButton(f"{title}\n  Expected: {expected}")
            btn.setStyleSheet("QPushButton { text-align: left; padding: 10px; font-size: 10pt; }")
            btn.clicked.connect(lambda checked, q=qml, t=title: self.run_test(q, t))
            layout.addWidget(btn)
        
        # QML widget
        self.qml_widget = QQuickWidget(self)
        self.qml_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self.qml_widget.setMinimumHeight(400)
        layout.addWidget(self.qml_widget)
        
        # System info
        self.print_system_info()
    
    def print_system_info(self):
        """Print Qt Quick 3D system information"""
        print("\n" + "="*70)
        print("QT QUICK 3D DIAGNOSTIC TOOL")
        print("="*70)
        
        # Qt version
        from PySide6 import QtCore
        print(f"\nQt Version: {QtCore.qVersion()}")
        
        # OpenGL info
        try:
            from PySide6.QtGui import QOpenGLContext
            context = QOpenGLContext.currentContext()
            if context:
                print(f"OpenGL Context: {context}")
                print(f"  Valid: {context.isValid()}")
            else:
                print("OpenGL Context: None (not created yet)")
        except Exception as e:
            print(f"OpenGL Context: Error - {e}")
        
        # Surface format
        try:
            fmt = QSurfaceFormat.defaultFormat()
            print(f"\nDefault Surface Format:")
            print(f"  Version: {fmt.majorVersion()}.{fmt.minorVersion()}")
            print(f"  Profile: {fmt.profile()}")
            print(f"  Samples: {fmt.samples()}")
            print(f"  Depth buffer: {fmt.depthBufferSize()}")
            print(f"  Stencil buffer: {fmt.stencilBufferSize()}")
        except Exception as e:
            print(f"Surface Format: Error - {e}")
        
        # Environment variables
        import os
        print(f"\nEnvironment Variables:")
        print(f"  QSG_RHI_BACKEND: {os.environ.get('QSG_RHI_BACKEND', 'not set')}")
        print(f"  QSG_INFO: {os.environ.get('QSG_INFO', 'not set')}")
        print(f"  QT_QUICK_BACKEND: {os.environ.get('QT_QUICK_BACKEND', 'not set')}")
        
        print("\n" + "="*70)
        print("Click test buttons to check each scenario")
        print("="*70 + "\n")
    
    def run_test(self, qml_code, test_name):
        """Run a specific test"""
        self.status_label.setText(f"Running: {test_name}...")
        
        # Save QML to temp file
        qml_path = Path("temp_diagnostic_test.qml")
        qml_path.write_text(qml_code, encoding='utf-8')
        
        # Load QML
        qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
        self.qml_widget.setSource(qml_url)
        
        # Check status
        status = self.qml_widget.status()
        
        if status == QQuickWidget.Status.Error:
            print(f"\n{'='*70}")
            print(f"TEST FAILED: {test_name}")
            print(f"{'='*70}")
            errors = self.qml_widget.errors()
            for error in errors:
                print(f"  ERROR: {error.toString()}")
            print(f"{'='*70}\n")
            self.status_label.setText(f"FAILED: {test_name} - Check console for errors")
            self.status_label.setStyleSheet("padding: 10px; color: #ff0000; font-weight: bold;")
        
        elif status == QQuickWidget.Status.Ready:
            print(f"\n{'='*70}")
            print(f"TEST SUCCESS: {test_name}")
            print(f"{'='*70}")
            print(f"  Status: Ready")
            print(f"  Root object: {self.qml_widget.rootObject()}")
            print(f"  Size: {self.qml_widget.size().width()}x{self.qml_widget.size().height()}")
            print(f"{'='*70}\n")
            self.status_label.setText(f"SUCCESS: {test_name} - Check if visual output is correct")
            self.status_label.setStyleSheet("padding: 10px; color: #00aa00; font-weight: bold;")
        
        else:
            print(f"\n{'='*70}")
            print(f"TEST UNKNOWN: {test_name}")
            print(f"{'='*70}")
            print(f"  Status: {status}")
            print(f"{'='*70}\n")
            self.status_label.setText(f"UNKNOWN: {test_name} - Status: {status}")
            self.status_label.setStyleSheet("padding: 10px; color: #ffaa00; font-weight: bold;")


def main():
    # Set RHI backend
    import os
    os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
    os.environ.setdefault("QSG_INFO", "1")
    
    # Set OpenGL format (try to request hardware acceleration)
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setSamples(4)  # MSAA
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)
    
    app = QApplication(sys.argv)
    
    print("\nStarting Qt Quick 3D Diagnostic Tool...")
    
    window = DiagnosticWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
