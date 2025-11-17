from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.cli.arguments import parse_arguments


def test_parse_arguments_no_qml_sets_flag_true() -> None:
    ns = parse_arguments(["--no-qml"])  # bootstrap-флаг
    assert getattr(ns, "no_qml", False) is True
    # Не должен мутировать test_mode/safe сам по себе
    assert getattr(ns, "test_mode", False) is False
    assert getattr(ns, "safe", False) is False


def test_parse_arguments_safe_alias_sets_test_mode() -> None:
    ns = parse_arguments(["--safe"])  # alias для test-mode в bootstrap парсере
    assert getattr(ns, "safe", False) is True
    assert getattr(ns, "test_mode", False) is True


@pytest.mark.parametrize(
    "argv,expect_no_qml",
    [
        ([], False),
        (["--legacy"], False),  # флаг присутствует, но не активирован
        (["--no-qml"], True),
    ],
)
def test_parse_arguments_matrix(argv: list[str], expect_no_qml: bool) -> None:
    ns = parse_arguments(argv)
    assert bool(getattr(ns, "no_qml", False)) is expect_no_qml
