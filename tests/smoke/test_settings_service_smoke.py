"""Smoke tests for the settings service."""

from __future__ import annotations

from pathlib import Path

from src.core.settings_service import SettingsService, SettingsValidationError


def test_settings_file_loads_without_mutation(tmp_path: Path) -> None:
    """SettingsService.load should not mutate the underlying file."""

    source = Path("config/app_settings.json")
    copy = tmp_path / "app_settings.json"
    copy.write_bytes(source.read_bytes())

    service = SettingsService(settings_path=copy)

    before = copy.read_bytes()
    settings = service.load()
    after = copy.read_bytes()

    assert before == after, "load() must not change the file on disk"
    assert settings.metadata.last_migration == "0002_remove_geometry_mesh_extras"


def test_settings_service_rejects_geometry_mesh_fields(tmp_path: Path) -> None:
    """Invalid geometry mesh fields should fail validation in smoke runs too."""

    source = Path("config/app_settings.json")
    payload = source.read_bytes().decode("utf-8")
    copy = tmp_path / "app_settings.json"

    # Inject legacy fields into the geometry block.
    # Use a field that definitely exists in current.geometry
    patched = payload.replace(
        '"frame_beam_size_m"',
        '"cylinder_segments": 18, "cylinder_rings": 8, "frame_beam_size_m"',
        1,
    )
    copy.write_text(patched, encoding="utf-8")

    service = SettingsService(settings_path=copy)

    try:
        service.load()
    except SettingsValidationError:
        pass
    else:  # pragma: no cover - safeguard if validation unexpectedly passes
        raise AssertionError("SettingsService.load must reject legacy mesh fields")
