"""
MINIMAL APP - No OpenGL, just simple window
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import Qt

from src.common import init_logging, log_ui_event

def main():
    # Logging
    logger = init_logging("PneumoStabSim_Minimal", Path("logs"))
    logger.info("Minimal app starting...")
    
    print("=== MINIMAL APP (NO OPENGL) ===\n")
    
    # High DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create app
    app = QApplication(sys.argv)
    app.setApplicationName("PneumoStabSim Minimal")
    
    print("? QApplication created\n")
    
    # Simple window
    window = QMainWindow()
    window.setWindowTitle("PneumoStabSim - Minimal Version (Working!)")
    window.resize(800, 600)
    
    # Simple label
    label = QLabel(
        "? ПРИЛОЖЕНИЕ РАБОТАЕТ!\n\n"
        "Это минимальная версия без OpenGL.\n\n"
        "Если вы видите это окно - Qt работает корректно.\n\n"
        "Проблема в OpenGL инициализации.\n\n"
        "Закройте окно для выхода."
    )
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("font-size: 16px; padding: 40px; background: #2a2a3e; color: white;")
    
    window.setCentralWidget(label)
    
    print("? Window created\n")
    
    # Show
    window.show()
    window.raise_()
    window.activateWindow()
    
    print("? Window shown\n")
    print("="*60)
    print("ОКНО ДОЛЖНО БЫТЬ ВИДНО!")
    print("Проверьте Alt+Tab или панель задач")
    print("="*60)
    print("\nЗапуск event loop...\n")
    
    # Event loop
    result = app.exec()
    
    logger.info(f"App closed with code: {result}")
    print(f"\n? Приложение закрыто (code: {result})")
    
    return result

if __name__ == "__main__":
    sys.exit(main())
