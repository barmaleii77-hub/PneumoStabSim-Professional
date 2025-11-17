from __future__ import annotations

from pathlib import Path

import pytest

from src.core import settings_validation as validation


def _clear_split_cache() -> None:
    validation._split_path.cache_clear()


def test_split_path_caches_segments() -> None:
    _clear_split_cache()

    before = validation._split_path.cache_info()
    validation._split_path("current.graphics.materials")
    after_first = validation._split_path.cache_info()
    validation._split_path("current.graphics.materials")
    after_second = validation._split_path.cache_info()

    assert after_first.misses == before.misses + 1
    assert after_second.hits == after_first.hits + 1


def test_get_path_reports_non_mapping_section() -> None:
    payload = {"current": "invalid"}

    with pytest.raises(validation.SettingsValidationError) as exc:
        validation._get_path(payload, "current.graphics")

    message = str(exc.value)
    assert "current" in message
    assert "должна быть объектом" in message


def test_load_settings_payload_handles_invalid_json(tmp_path: Path) -> None:
    broken = tmp_path / "settings.json"
    broken.write_text("{ invalid", encoding="utf-8")

    with pytest.raises(validation.SettingsValidationError) as exc:
        validation._load_settings_payload(broken)

    assert "Некорректный JSON" in str(exc.value)


def test_load_settings_payload_handles_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "absent.json"

    with pytest.raises(validation.SettingsValidationError) as exc:
        validation._load_settings_payload(missing)

    assert "Файл настроек не найден" in str(exc.value)
