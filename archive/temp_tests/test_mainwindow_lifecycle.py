"""
Test MainWindow creation with error handling
"""
import sys
import traceback
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

print("=== TESTING MAINWINDOW ===\n")

# Setup Qt
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

app = QApplication(sys.argv)
print("? QApplication created\n")

try:
    print("Importing MainWindow...")
    from src.ui.main_window import MainWindow
    print("? MainWindow imported\n")
    
    print("Creating MainWindow...")
    window = MainWindow()
    print(f"? MainWindow created: {window.windowTitle()}\n")
    
    print(f"Window size: {window.size().width()}x{window.size().height()}")
    print(f"Window visible before show(): {window.isVisible()}\n")
    
    print("Calling window.show()...")
    window.show()
    print(f"? Window shown: visible={window.isVisible()}")
    print(f"   Position: {window.pos().x()}, {window.pos().y()}\n")
    
    print("="*60)
    print("Starting Qt event loop...")
    print("CLOSE THE WINDOW to exit")
    print("="*60)
    
    result = app.exec()
    
    print(f"\n? Event loop finished (code: {result})")
    
except Exception as e:
    print(f"\n? ERROR: {e}\n")
    traceback.print_exc()
    sys.exit(1)
