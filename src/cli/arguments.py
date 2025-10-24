# -*- coding: utf-8 -*-
"""
Модуль обработки аргументов командной строки.

Определяет CLI интерфейс приложения с поддержкой
test-mode, verbose logging и диагностики.
"""

import argparse


def parse_arguments() -> argparse.Namespace:
    """
    Парсинг аргументов командной строки.

    Returns:
        Namespace с распарсенными аргументами
    """
    parser = argparse.ArgumentParser(
        description="PneumoStabSim - Pneumatic Stabilizer Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py app.py                    # Main Qt Quick 3D version
  py app.py --test-mode        # Test mode (auto-close 5s)
  py app.py --verbose          # Verbose console output
  py app.py --diag             # Run post-run diagnostics to console
        """,
    )

    parser.add_argument(
        "--test-mode", action="store_true", help="Test mode (auto-close 5s)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable console logging")
    parser.add_argument(
        "--diag", action="store_true", help="Run post-run diagnostics to console"
    )

    return parser.parse_args()
