import json
from pathlib import Path

from src.common.settings_manager import SettingsManager, get_settings_manager
from src.common import settings_manager as settings_manager_module


def test_settings_manager_si_units_migration(tmp_path):
    source = Path("config/app_settings.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    data.setdefault("metadata", {})["units_version"] = "legacy"

    target_dir = tmp_path / "config"
    target_dir.mkdir()
    target_file = target_dir / "app_settings.json"
    target_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    manager = SettingsManager(settings_file=target_file)

    assert manager._metadata.get("units_version") == "si_v2"


def test_get_settings_manager_si_units(tmp_path, monkeypatch):
    source = Path("config/app_settings.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    data.setdefault("metadata", {})["units_version"] = "legacy"

    target_dir = tmp_path / "config"
    target_dir.mkdir()
    target_file = target_dir / "app_settings.json"
    target_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    monkeypatch.setenv("PSS_SETTINGS_FILE", str(target_file))
    monkeypatch.setattr(settings_manager_module, "_settings_manager", None)

    manager = get_settings_manager()

    assert manager._metadata.get("units_version") == "si_v2"
