"""
Test MainWindow creation and display
"""
import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Setup basic logging to console
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    print("=== TESTING MAIN WINDOW ===\n")

    # Enable high DPI
    print("Setting High DPI policy...")
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    print("Creating QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("PneumoStabSim")
    print("? QApplication created\n")

    try:
        # Import MainWindow
        print("Importing MainWindow...")
        from src.ui.main_window import MainWindow

        print("? MainWindow imported\n")

        # Create window
        print("Creating MainWindow...")
        window = MainWindow()
        print("? MainWindow created\n")

        # Check window properties
        print(f"Window title: {window.windowTitle()}")
        print(f"Window size: {window.size().width()}x{window.size().height()}")
        print(f"Window visible: {window.isVisible()}")
        print()

        # Show window
        print("Showing window...")
        window.show()
        print(f"? Window shown - Visible: {window.isVisible()}")
        print(f"   Position: {window.pos().x()}, {window.pos().y()}")
        print()

        print("Starting event loop (close window to exit)...")
        print("=" * 50)

        result = app.exec()

        print("\n" + "=" * 50)
        print(f"Event loop finished (code: {result})")
        return result

    except Exception as e:
        print(f"\n? ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
