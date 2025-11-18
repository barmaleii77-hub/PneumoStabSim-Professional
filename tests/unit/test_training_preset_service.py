from __future__ import annotations

from pathlib import Path

from src.common.settings_manager import SettingsManager
from src.core.settings_orchestrator import SettingsOrchestrator
from src.simulation.presets import get_default_training_library
from src.simulation.service import TrainingPresetService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_SETTINGS = PROJECT_ROOT / "config" / "app_settings.json"


def _make_settings_manager(tmp_path: Path) -> SettingsManager:
    payload = PROJECT_SETTINGS.read_text(encoding="utf-8")
    settings_file = tmp_path / "app_settings.json"
    settings_file.write_text(payload, encoding="utf-8")
    return SettingsManager(settings_file=settings_file)


def test_training_preset_service_handles_fast_switches(tmp_path: Path) -> None:
    manager = _make_settings_manager(tmp_path)
    orchestrator = SettingsOrchestrator(settings_manager=manager, event_bus=None)
    service = TrainingPresetService(
        orchestrator=orchestrator, library=get_default_training_library()
    )

    presets = [entry for entry in service.list_presets() if entry.get("id")]
    assert len(presets) >= 2, "Expected at least two presets for toggle testing"

    first_id = str(presets[0]["id"])
    second_id = str(presets[1]["id"])

    active_events: list[str] = []
    unsubscribe = service.register_active_observer(active_events.append)

    try:
        service.apply_preset(first_id)
        after_first = dict(manager.get("current.simulation"))

        service.apply_preset(second_id)
        after_second = dict(manager.get("current.simulation"))

        service.apply_preset(first_id)
        after_third = dict(manager.get("current.simulation"))
    finally:
        unsubscribe()
        service.close()
        orchestrator.close()

    assert service.active_preset_id() == first_id

    assert after_second != after_first
    assert after_third == after_first

    assert second_id in active_events
    assert first_id == active_events[-1]
