# -*- coding: utf-8 -*-
"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point - MODULAR VERSION v4.9.5
"""
import sys

# =============================================================================
# Bootstrap Phase 1: Environment & Terminal
# =============================================================================

from src.diagnostics.warnings import log_warning, log_error
from src.bootstrap.environment import setup_qtquick3d_environment, configure_qt_environment
from src.bootstrap.terminal import configure_terminal_encoding
from src.bootstrap.version_check import check_python_compatibility

# Настройка окружения перед импортом Qt
qtquick3d_setup_ok: bool = setup_qtquick3d_environment(log_error)
configure_terminal_encoding(log_warning)
check_python_compatibility(log_warning, log_error)
configure_qt_environment()

# =============================================================================
# Bootstrap Phase 2: Qt Import
# =============================================================================

from src.bootstrap.qt_imports import safe_import_qt

QApplication, qInstallMessageHandler, Qt, QTimer = safe_import_qt(log_warning, log_error)

# =============================================================================
# Application Entry Point
# =============================================================================

from src.cli.arguments import parse_arguments
from src.app_runner import ApplicationRunner


def main() -> int:
    """Main application entry point - MODULAR VERSION"""
    args = parse_arguments()
    
    runner = ApplicationRunner(QApplication, qInstallMessageHandler, Qt, QTimer)
    return runner.run(args)


if __name__ == "__main__":
    sys.exit(main())
