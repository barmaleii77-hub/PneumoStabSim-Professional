from __future__ import annotations

import os

import pytest


pytestmark = [
    pytest.mark.unit,
    pytest.mark.headless,
    pytest.mark.usefixtures("headless_env", "headless_qt_modules"),
]


def test_training_preset_service_tracks_active_id_headless(
    settings_manager, headless_qtbot
):
    """Ensure TrainingPresetService works without a GUI backend.

    The test relies on lightweight PySide6/pytest-qt shims provided by the
    headless fixtures. Environment variables configured by ``headless_env``
    allow Qt to operate in an offscreen mode suitable for CI runners.
    """

    from PySide6.QtCore import QCoreApplication

    from src.core.settings_orchestrator import SettingsOrchestrator
    from src.simulation.presets import get_default_training_library
    from src.simulation.service import TrainingPresetService
    from tests._qt_headless import HEADLESS_FLAG

    assert os.environ.get(HEADLESS_FLAG) == "1"

    orchestrator = SettingsOrchestrator(settings_manager=settings_manager)
    service = TrainingPresetService(
        orchestrator=orchestrator,
        library=get_default_training_library(),
    )

    changes: list[str] = []
    unsubscribe = service.register_active_observer(changes.append)

    try:
        presets = list(service.list_presets())
        assert presets, "Preset catalogue should not be empty"
        default_id = str(presets[0].get("id", ""))
        assert default_id

        service.apply_preset(default_id)

        headless_qtbot.waitUntil(lambda: changes and changes[-1] == default_id)

        simulation_snapshot = settings_manager.get("current.simulation", {})
        assert simulation_snapshot["physics_dt"] == pytest.approx(0.001)

        settings_manager.set("current.simulation.physics_dt", 0.123, auto_save=False)
        settings_manager.save_if_dirty()
        QCoreApplication.processEvents()
        headless_qtbot.waitUntil(lambda: changes and changes[-1] == "")
    finally:
        unsubscribe()
        service.close()
        orchestrator.close()
