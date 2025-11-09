"""Политики определения отсутствия файла для FileCyclerWidget.

Стратегии:
- test_mode: пути из items всегда валидны, кастомный путь помечается missing.
- strict: все пути проверяются физически; кастомный считается missing до подтверждения.

Использование:
    from .file_cycler_policy import get_missing_strategy
    strategy = get_missing_strategy(test_mode=True)
    missing = strategy(entry_is_custom, entry_in_items, physical_exists)
"""

from __future__ import annotations

from typing import Callable

MissingStrategy = Callable[[bool, bool, bool], bool]


def strategy_test_mode(
    entry_is_custom: bool, entry_in_items: bool, physical_exists: bool
) -> bool:
    if entry_in_items:
        return False
    if entry_is_custom:
        return True
    return not physical_exists


def strategy_strict(
    entry_is_custom: bool, entry_in_items: bool, physical_exists: bool
) -> bool:
    if entry_is_custom:
        return True
    if entry_in_items:
        return not physical_exists
    return not physical_exists


def get_missing_strategy(*, test_mode: bool) -> MissingStrategy:
    return strategy_test_mode if test_mode else strategy_strict


__all__ = ["MissingStrategy", "get_missing_strategy"]
