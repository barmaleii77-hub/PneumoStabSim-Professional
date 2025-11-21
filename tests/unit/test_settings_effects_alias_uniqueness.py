from __future__ import annotations

import inspect
import re

from src.common import settings_manager as sm


def test_effects_alias_uniqueness() -> None:
    aliases = getattr(sm, "_EFFECTS_KEY_ALIASES", {})
    assert isinstance(aliases, dict)
    values = list(aliases.values())
    # Уникальность значений
    assert len(values) == len(set(values)), "Duplicate canonical effect alias targets detected"
    # Отсутствие self‑mapping коллизий: ключ не должен совпадать с другим canonical значением если он тоже присутствует как ключ
    collisions = [k for k in aliases if k in aliases.values() and aliases[k] != k]
    assert not collisions, f"Effect alias key collides with canonical value: {collisions}"
