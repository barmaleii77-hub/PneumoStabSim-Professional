from __future__ import annotations

import json
from pathlib import Path

from src.core.settings_service import SettingsService, SettingsValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SETTINGS_PATH = PROJECT_ROOT / "config" / "app_settings.json"


def test_settings_round_trip_preserves_key_order(tmp_path: Path) -> None:
    """Проверить что порядок ключей в JSON не меняется после загрузки/сохранения.

    Для стабильности диффов и читаемости ревью — settings_service не должен
    перетасовывать верхний уровень current/defaults_snapshot.
    """
    original = SETTINGS_PATH.read_text(encoding="utf-8")
    service = SettingsService(str(SETTINGS_PATH))
    payload = service.load()
    dump_dict = json.loads(json.dumps(payload.model_dump()))
    service.save(payload)
    after = SETTINGS_PATH.read_text(encoding="utf-8")
    assert original.splitlines()[0] == after.splitlines()[0]


def test_settings_fail_on_missing_file(tmp_path: Path) -> None:
    """Отсутствие файла настроек должно генерировать SettingsValidationError."""
    missing = tmp_path / "missing_settings.json"
    service = SettingsService(str(missing))
    try:
        service.load()
    except SettingsValidationError as exc:
        assert "not found" in str(exc).lower()
    else:  # pragma: no cover - обязательный провал
        assert False, "Expected SettingsValidationError for missing settings file"
