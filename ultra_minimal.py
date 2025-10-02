"""
Ultra-minimal test - absolutely basic Qt window
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

print("1. Importing...")
app = QApplication(sys.argv)
print("2. QApplication created")

window = QMainWindow()
print("3. MainWindow created")

window.setWindowTitle("Test")
window.resize(400, 300)
print("4. Window configured")

label = QLabel("TEST WINDOW")
window.setCentralWidget(label)
print("5. Central widget set")

print("6. Calling show()...")
window.show()
print("7. Show() returned")

print("8. Window visible:", window.isVisible())
print("9. Starting exec()...")

sys.exit(app.exec())
