# -*- coding: utf-8 -*-
"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point - MODULAR VERSION v4.9.5
"""
import sys

# =============================================================================
# Bootstrap Phase0: .env
# =============================================================================
# Загружаем переменные окружения из .env до настройки Qt
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# =============================================================================
# Bootstrap Phase1: Environment & Terminal
# =============================================================================

from src.diagnostics.warnings import log_warning, log_error
from src.bootstrap.environment import (
    setup_qtquick3d_environment,
    configure_qt_environment,
)
from src.bootstrap.terminal import configure_terminal_encoding
from src.bootstrap.version_check import check_python_compatibility

# Настройка окружения перед импортом Qt
qtquick3d_setup_ok, qtquick3d_error = setup_qtquick3d_environment(log_error)
if not qtquick3d_setup_ok:
    failure_reason = (
        qtquick3d_error or "Unknown error while configuring QtQuick3D environment"
    )
    critical_message = (
        "❌ Critical startup failure: QtQuick3D environment setup failed."
        f" Reason: {failure_reason}"
    )
    log_error(critical_message)
    sys.stderr.write(critical_message + "\n")
    sys.exit(1)

configure_terminal_encoding(log_warning)
check_python_compatibility(log_warning, log_error)
configure_qt_environment()

# =============================================================================
# Bootstrap Phase2: Qt Import
# =============================================================================

from src.bootstrap.qt_imports import safe_import_qt  # noqa: E402

QApplication, qInstallMessageHandler, Qt, QTimer = safe_import_qt(  # noqa: E402
    log_warning, log_error
)

# =============================================================================
# Application Entry Point
# =============================================================================

from src.cli.arguments import parse_arguments  # noqa: E402
from src.app_runner import ApplicationRunner  # noqa: E402


def main() -> int:
    """Main application entry point - MODULAR VERSION"""
    args = parse_arguments()

    runner = ApplicationRunner(QApplication, qInstallMessageHandler, Qt, QTimer)
    return runner.run(args)


if __name__ == "__main__":
    sys.exit(main())
