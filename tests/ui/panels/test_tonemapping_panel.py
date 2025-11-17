"""Unit tests for :class:`TonemappingPanel` state accessors."""

from __future__ import annotations

import pytest

from src.graphics.materials.baseline import TonemapPreset

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for TonemappingPanel tests",
    exc_type=ImportError,
)

from src.ui.panels.tonemapping_panel import TonemappingPanel


@pytest.mark.gui
def test_get_parameters_tracks_active_preset(qtbot: pytestqt.qtbot.QtBot) -> None:
    panel = TonemappingPanel()
    qtbot.addWidget(panel)

    snapshot = panel.get_parameters()
    assert "active_preset" in snapshot
    assert "effects" in snapshot and isinstance(snapshot["effects"], dict)

    combo = panel._combo  # noqa: SLF001 - test helper access
    if combo is None:
        pytest.fail("Preset combo box is expected to be available")

    if combo.count() <= 1:
        fallback_preset = TonemapPreset(
            id="test-linear",
            mode="linear",
            exposure=0.0,
            white_point=1.0,
            label_key="tonemap.test.label",
            description_key="tonemap.test.description",
            tonemap_enabled=True,
            display_order=0.0,
        )
        panel._facade.iter_tonemap_presets = lambda: [fallback_preset]  # noqa: SLF001
        panel._load_presets()
        combo = panel._combo  # noqa: SLF001 - refresh reference after reload

    assert combo is not None and combo.count() > 1, (
        "Tonemapping presets should be selectable in tests"
    )

    combo.setCurrentIndex(1)
    qtbot.wait(50)

    updated = panel.get_parameters()
    expected_id = str(combo.currentData() or "")
    assert updated["active_preset"] == expected_id

    updated["effects"]["tonemap_mode"] = "custom_marker"
    refreshed = panel.get_parameters()
    assert refreshed["effects"].get("tonemap_mode") != "custom_marker"
