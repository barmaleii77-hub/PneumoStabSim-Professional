"""
Minimal diagnostic app to test window display
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt


def main():
    print("=== DIAGNOSTIC APP START ===")

    app = QApplication(sys.argv)
    print("? QApplication created")

    window = QMainWindow()
    window.setWindowTitle("PneumoStabSim - Diagnostic Window")
    window.resize(800, 600)

    # Add simple content
    central = QWidget()
    layout = QVBoxLayout()
    label = QLabel(
        "If you see this window, Qt is working!\n\nClose this window to continue."
    )
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("font-size: 16px; padding: 20px;")
    layout.addWidget(label)
    central.setLayout(layout)
    window.setCentralWidget(central)

    print("? Window created")

    window.show()
    print(f"? Window shown - Visible: {window.isVisible()}")
    print(f"   Size: {window.size().width()}x{window.size().height()}")
    print(f"   Position: {window.pos().x()}, {window.pos().y()}")
    print("")
    print("Starting event loop (close window to exit)...")

    result = app.exec()

    print(f"\n=== APP FINISHED (code: {result}) ===")
    return result


if __name__ == "__main__":
    sys.exit(main())
