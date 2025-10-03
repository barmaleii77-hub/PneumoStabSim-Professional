"""
Test with QSurfaceFormat set BEFORE QApplication
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat

print("=== TEST: QSurfaceFormat BEFORE QApplication ===\n")

# Set default surface format BEFORE creating QApplication
print("Setting default QSurfaceFormat...")
format = QSurfaceFormat()
format.setVersion(2, 1)  # Use older OpenGL 2.1 for maximum compatibility
format.setProfile(QSurfaceFormat.OpenGLContextProfile.NoProfile)
format.setDepthBufferSize(24)
format.setStencilBufferSize(8)
QSurfaceFormat.setDefaultFormat(format)
print("? Default format set (OpenGL 2.1 NoProfile)\n")

# High DPI
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

# Create app
app = QApplication(sys.argv)
print("? QApplication created\n")

try:
    from src.ui.main_window import MainWindow
    print("? MainWindow imported\n")
    
    window = MainWindow()
    print(f"? MainWindow created\n")
    
    print("Calling window.show()...")
    window.show()
    print(f"? Window shown: visible={window.isVisible()}\n")
    
    print("="*60)
    print("Starting event loop - CLOSE WINDOW to exit")
    print("="*60)
    
    result = app.exec()
    print(f"\n? Closed normally (code: {result})")
    
except Exception as e:
    print(f"\n? ERROR: {e}")
    import traceback
    traceback.print_exc()
