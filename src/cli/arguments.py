"""Модуль обработки аргументов командной строки.

Определяет CLI интерфейс приложения с поддержкой
test-mode, verbose logging и диагностики.
"""

import argparse
import sys
from collections.abc import Iterable


def _add_mode_arguments(parser: argparse.ArgumentParser) -> None:
    """Add launch-mode flags shared between bootstrap and main parsing."""

    parser.add_argument(
        "--safe-mode",
        action="store_true",
        help="Allow Qt to auto-select the graphics backend (no forced OpenGL)",
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Launch the legacy Qt Widgets interface without loading QML",
    )


def _add_test_mode_argument(parser: argparse.ArgumentParser) -> None:
    """Register the shared test-mode flag used by bootstrap and main parsing."""

    parser.add_argument(
        "--test-mode",
        "--safe",
        action="store_true",
        help="Test mode (auto-close 5s; safe bootstrap alias: --safe)",
    )


def _add_bootstrap_arguments(parser: argparse.ArgumentParser) -> None:
    """Register arguments that must be parsed before Qt is imported."""

    parser.add_argument(
        "--env-check",
        action="store_true",
        help="Run environment diagnostics and exit before Qt starts",
    )
    parser.add_argument(
        "--env-report",
        nargs="?",
        const="ENVIRONMENT_SETUP_REPORT.md",
        metavar="PATH",
        help="Write environment diagnostics to PATH and exit before Qt starts",
    )
    parser.add_argument(
        "--no-qml",
        action="store_true",
        help="Disable Qt Quick 3D scene (skip QML loading, use diagnostics/placeholder view)",
    )
    _add_test_mode_argument(parser)
    _add_mode_arguments(parser)


def _add_main_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_mode_flags: bool,
    include_test_mode: bool,
) -> None:
    """Register the main CLI arguments for the application."""

    if include_test_mode:
        _add_test_mode_argument(parser)
    parser.add_argument("--verbose", action="store_true", help="Enable console logging")
    parser.add_argument(
        "--diag", action="store_true", help="Run post-run diagnostics to console"
    )
    if include_mode_flags:
        _add_mode_arguments(parser)


def create_bootstrap_parser() -> argparse.ArgumentParser:
    """Return a lightweight parser used to handle bootstrap arguments."""

    parser = argparse.ArgumentParser(add_help=False)
    _add_bootstrap_arguments(parser)
    return parser


def _create_argument_parser(*, include_bootstrap: bool) -> argparse.ArgumentParser:
    """Create the main argument parser optionally including bootstrap arguments."""

    parser = argparse.ArgumentParser(
        description="PneumoStabSim - Pneumatic Stabilizer Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py app.py                    # Main Qt Quick 3D version
  py app.py --test-mode        # Test mode (auto-close 5s)
  py app.py --verbose          # Verbose console output
  py app.py --diag             # Run post-run diagnostics to console
  py app.py --safe-mode        # Allow Qt to choose the graphics backend
  py app.py --legacy           # Launch legacy Qt Widgets UI (no QML)
  py app.py --safe             # Headless-safe mode (no Qt Quick 3D scene)
  py app.py --no-qml           # Disable QML/Qt Quick 3D (UI placeholder only)
        """,
    )

    if include_bootstrap:
        _add_bootstrap_arguments(parser)
        include_mode_flags = False
        include_test_mode = False
    else:
        include_mode_flags = True
        include_test_mode = True

    _add_main_arguments(
        parser,
        include_mode_flags=include_mode_flags,
        include_test_mode=include_test_mode,
    )
    return parser


def parse_arguments(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments passed to the application."""

    parser = _create_argument_parser(include_bootstrap=True)
    if argv is None:
        argv_list = list(sys.argv[1:])
    else:
        argv_list = list(argv)

    namespace = parser.parse_args(argv_list)

    safe_alias_used = "--safe" in argv_list
    setattr(namespace, "safe", safe_alias_used)
    if safe_alias_used:
        setattr(namespace, "test_mode", True)

    setattr(namespace, "safe_cli_mode", bool(getattr(namespace, "test_mode", False)))

    return namespace


__all__ = ["create_bootstrap_parser", "parse_arguments"]
