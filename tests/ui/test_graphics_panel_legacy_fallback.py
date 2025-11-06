import json
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for graphics panel tests",
    exc_type=ImportError,
)

from src.ui.panels.graphics.panel_graphics import GraphicsPanel


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_graphics_panel_hydrates_missing_categories(
    tmp_path, monkeypatch, qapp
) -> None:
    settings_path = tmp_path / "app_settings.json"
    payload = json.loads(Path("config/app_settings.json").read_text(encoding="utf-8"))

    for section in ("current", "defaults_snapshot"):
        graphics_section = payload.get(section, {}).get("graphics", {})
        graphics_section.pop("camera", None)
        graphics_section.pop("materials", None)
        if section in payload and "graphics" in payload[section]:
            payload[section]["graphics"] = graphics_section
        if "animation" in payload.get(section, {}):
            payload[section].pop("animation")

    settings_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("PSS_SETTINGS_FILE", str(settings_path))

    panel = GraphicsPanel()

    try:
        baseline_graphics = panel.settings_service._baseline_graphics_current  # type: ignore[attr-defined]
        baseline_animation = panel.settings_service._baseline_animation_current  # type: ignore[attr-defined]

        assert panel.state["camera"] == baseline_graphics["camera"]
        assert panel.state["materials"] == baseline_graphics["materials"]
        assert panel.state["animation"] == baseline_animation

        collected = panel.collect_state()
        for category in panel.settings_service.REQUIRED_CATEGORIES:
            assert category in collected
        assert collected["camera"] == panel.state["camera"]
        assert collected["materials"] == panel.state["materials"]
    finally:
        panel.deleteLater()
