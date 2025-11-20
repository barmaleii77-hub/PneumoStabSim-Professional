import os
from pathlib import Path
from src.common.settings_manager import SettingsManager, get_settings_manager

def test_hdr_round_trip(tmp_path: Path):
    settings_file = tmp_path / "app_settings.json"
    payload = {
        "metadata": {"units_version": "legacy"},
        "current": {"graphics": {"environment": {"ibl_source": str(tmp_path / "assets" / "hdr" / "EnvMap.HDR")}}},
        "defaults_snapshot": {"graphics": {"environment": {}}},
    }
    settings_file.write_text(__import__("json").dumps(payload), encoding="utf-8")
    mgr = SettingsManager(settings_file)
    norm = mgr.get("current.graphics.environment.ibl_source")
    raw = mgr.get("current.graphics.environment.ibl_source_original_raw")
    assert raw.lower().endswith("envmap.hdr")
    assert "\\" not in norm
    assert norm.endswith("envmap.hdr")
    # Update with same value should not re-normalize differently
    mgr.set("current.graphics.environment.ibl_source", raw, auto_save=False)
    norm2 = mgr.get("current.graphics.environment.ibl_source")
    assert norm == norm2
