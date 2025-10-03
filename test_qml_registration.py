import sys
import os

os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QT_LOGGING_RULES"] = "qt.qml.import*=true;qt.quick3d*=true"

from PySide6.QtWidgets import QApplication
from PySide6.QtQml import qmlRegisterType
from src.ui.custom_geometry import SphereGeometry, CubeGeometry

print("=== QML TYPE REGISTRATION TEST ===")
print()

app = QApplication(sys.argv)

print("1. Checking @QmlElement registration...")
# Types should be auto-registered via @QmlElement decorator

print("2. Verifying registration worked...")
# Try to create QML engine and check if types are available
from PySide6.QtQml import QQmlEngine

engine = QQmlEngine()

# Test QML that uses CustomGeometry
test_qml = '''
import QtQuick
import QtQuick3D
import CustomGeometry 1.0

Item {
    SphereGeometry {
        id: testSphere
        Component.onCompleted: {
            console.log("SphereGeometry instantiated in QML")
        }
    }
}
'''

print("3. Testing QML compilation...")
from PySide6.QtQml import QQmlComponent
from PySide6.QtCore import QUrl

component = QQmlComponent(engine)
component.setData(test_qml.encode('utf-8'), QUrl())

if component.isError():
    print("   ? QML compilation errors:")
    for error in component.errors():
        print(f"      {error.toString()}")
else:
    print("   ? QML compiles successfully")
    
    # Try to create object
    obj = component.create()
    if obj:
        print("   ? QML object created successfully")
    else:
        print("   ? Failed to create QML object")

print()
print("=== QML REGISTRATION TEST COMPLETE ===")