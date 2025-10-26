# -*- coding: utf-8 -*-
"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point - MODULAR VERSION v4.9.5
"""

import argparse
import sys
from pathlib import Path


# Ensure the project sources are importable before any local modules execute.
_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"
_PATH_CANDIDATES = [str(_PROJECT_ROOT), str(_SRC_PATH)]
for candidate in _PATH_CANDIDATES:
    if candidate and candidate not in sys.path:
        sys.path.insert(0, candidate)


def _parse_bootstrap_arguments(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    """Parse lightweight CLI arguments required before Qt import."""

    bootstrap_parser = argparse.ArgumentParser(add_help=False)
    bootstrap_parser.add_argument(
        "--env-check",
        action="store_true",
        help="Run environment diagnostics without starting the Qt application.",
    )
    bootstrap_parser.add_argument(
        "--env-report",
        nargs="?",
        const="ENVIRONMENT_SETUP_REPORT.md",
        metavar="PATH",
        help="Write environment diagnostics report to PATH and exit (default: ENVIRONMENT_SETUP_REPORT.md).",
    )

    parsed, remaining = bootstrap_parser.parse_known_args(argv[1:])
    return parsed, remaining


bootstrap_args, remaining_argv = _parse_bootstrap_arguments(sys.argv)

if bootstrap_args.env_check or bootstrap_args.env_report:
    from src.bootstrap.environment_check import (
        generate_environment_report,
        render_console_report,
    )

    report = generate_environment_report()

    print(render_console_report(report))

    if bootstrap_args.env_report:
        report_path = Path(bootstrap_args.env_report)
        report_path.write_text(report.to_markdown() + "\n", encoding="utf-8")
        print(f"\n📝 Environment report written to {report_path.resolve()}")

    sys.exit(0 if report.is_successful else 1)

sys.argv = [sys.argv[0], *remaining_argv]

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
