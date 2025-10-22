"""
Test MainWindow WITHOUT GLView (to isolate the problem)
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

print("=== TEST: MAINWINDOW WITHOUT GLVIEW ===\n")

QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

app = QApplication(sys.argv)

# Create simple window instead of MainWindow
window = QMainWindow()
window.setWindowTitle("PneumoStabSim - TEST (No OpenGL)")
window.resize(1500, 950)

# Simple central widget
central = QWidget()
layout = QVBoxLayout()
label = QLabel("Test Window\n\nIf you see this, the problem is in GLView/OpenGL")
label.setAlignment(Qt.AlignmentFlag.AlignCenter)
label.setStyleSheet("font-size: 16px; padding: 20px;")
layout.addWidget(label)
central.setLayout(layout)
window.setCentralWidget(central)

print("Showing window...")
window.show()
print(f"? Window shown: visible={window.isVisible()}\n")

print("=" * 60)
print("If window appears and stays open - problem is in GLView!")
print("Close window to exit")
print("=" * 60 + "\n")

result = app.exec()
print(f"\n? Closed normally (code: {result})")
