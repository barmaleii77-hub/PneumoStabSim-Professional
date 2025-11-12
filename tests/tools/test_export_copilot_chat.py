"""Tests for the Copilot chat export filtering helpers."""

from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "export_copilot_chat.py"
_SPEC = importlib.util.spec_from_file_location("export_copilot_chat", MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - defensive guard
    raise RuntimeError("Не удалось загрузить модуль export_copilot_chat")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

filter_conversation_blocks = _MODULE.filter_conversation_blocks
ConversationBlock = _MODULE.ConversationBlock


def _block(messages: list[dict[str, object]]) -> ConversationBlock:
    return ("source.json", dt.datetime(2024, 1, 1, 12, 0, 0), messages, 1700000000.0)


def test_filter_by_substring_keeps_matching_messages():
    original = [
        {"role": "User", "content": "Please review src/app/main.py"},
        {"role": "Copilot", "content": "Summary for src/ui/panel.qml"},
    ]
    blocks = [_block(list(original))]

    filtered = filter_conversation_blocks(blocks, substrings=["main.py"])

    assert len(filtered) == 1
    assert len(filtered[0][2]) == 1
    assert "main.py" in filtered[0][2][0]["content"]
    # ensure the original payload is untouched
    assert len(blocks[0][2]) == 2
    assert filtered[0][2][0] is not blocks[0][2][0]


def test_filter_respects_case_sensitivity_flag():
    blocks = [_block([{"role": "User", "content": "Discuss README.md"}])]

    insensitive = filter_conversation_blocks(
        blocks, substrings=["readme"], case_sensitive=False
    )
    assert insensitive and insensitive[0][2]

    sensitive = filter_conversation_blocks(
        blocks, substrings=["readme"], case_sensitive=True
    )
    assert sensitive == []


def test_filter_by_regex_and_keep_empty():
    blocks = [
        _block(
            [
                {"role": "Copilot", "content": "File: src/core/settings_service.py"},
                {"role": "User", "content": "Another line"},
            ]
        )
    ]

    filtered = filter_conversation_blocks(
        blocks, regex_patterns=[r"settings_service\.py$"]
    )
    assert len(filtered) == 1
    assert filtered[0][2][0]["content"].endswith("settings_service.py")

    kept = filter_conversation_blocks(
        blocks, regex_patterns=["missing"], keep_empty=True
    )
    assert len(kept) == 1
    assert kept[0][2] == []


def test_filter_invalid_regex_raises_value_error():
    blocks = [_block([{"role": "Copilot", "content": "example"}])]

    with pytest.raises(ValueError):
        filter_conversation_blocks(blocks, regex_patterns=["["])
