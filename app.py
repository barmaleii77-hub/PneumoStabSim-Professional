"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point
"""
import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    """Main application function"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("PneumoStabSim")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PneumoStabSim")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())