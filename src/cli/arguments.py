# -*- coding: utf-8 -*-
"""
Модуль обработки аргументов командной строки.

Определяет CLI интерфейс приложения с поддержкой
test-mode, verbose logging и диагностики.
"""

import argparse
from typing import Iterable


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
    _add_mode_arguments(parser)


def _add_main_arguments(
    parser: argparse.ArgumentParser, *, include_mode_flags: bool
) -> None:
    """Register the main CLI arguments for the application."""

    parser.add_argument(
        "--test-mode", action="store_true", help="Test mode (auto-close 5s)"
    )
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
        """,
    )

    if include_bootstrap:
        _add_bootstrap_arguments(parser)
        include_mode_flags = False
    else:
        include_mode_flags = True

    _add_main_arguments(parser, include_mode_flags=include_mode_flags)
    return parser


def parse_arguments(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments passed to the application."""

    parser = _create_argument_parser(include_bootstrap=True)
    return parser.parse_args(None if argv is None else list(argv))


__all__ = ["create_bootstrap_parser", "parse_arguments"]
