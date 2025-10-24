import json
from pathlib import Path

import pytest

from config import constants as constants_module
from src.core.settings_service import SettingsService


@pytest.fixture()
def settings_payload(tmp_path: Path) -> Path:
 data = {
 "metadata": {
 "version": "1.0.0",
 "last_modified": "2025-01-01T00:00:00",
 "units_version": "si_v3",
 },
 "current": {
 "constants": {
 "geometry": {"kinematics": {"track_width_m":2.0}},
 "pneumo": {
 "valves": {"delta_open_pa":123.0, "equivalent_diameter_m":0.01},
 "receiver": {
 "volume_min_m3":0.1,
 "volume_max_m3":0.2,
 "initial_volume_m3":0.15,
 "initial_pressure_pa":150000.0,
 "initial_temperature_k":280.0,
 "volume_mode": "ADIABATIC_RECALC",
 },
 "gas": {
 "tank_volume_initial_m3":0.42,
 "tank_pressure_initial_pa":200000.0,
 "tank_temperature_initial_k":285.0,
 "tank_volume_mode": "NO_RECALC",
 "time_step_s":0.01,
 "total_time_s":10.0,
 "thermo_mode": "ISOTHERMAL",
 },
 "master_isolation_open": True,
 },
 }
 },
 }
 settings_file = tmp_path / "app_settings.json"
 settings_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
 return settings_file


def test_settings_service_get_and_set(settings_payload: Path) -> None:
 service = SettingsService(settings_path=settings_payload)

 assert service.get("current.constants.geometry.kinematics.track_width_m") ==2.0

 service.set("current.constants.geometry.kinematics.track_width_m",2.5)
 assert service.get("current.constants.geometry.kinematics.track_width_m") ==2.5

 reloaded = json.loads(settings_payload.read_text(encoding="utf-8"))
 assert reloaded["current"]["constants"]["geometry"]["kinematics"]["track_width_m"] ==2.5


def test_settings_service_update_merges(settings_payload: Path) -> None:
 service = SettingsService(settings_path=settings_payload)

 service.update("current.constants.geometry.kinematics", {"rod_attach_fraction":0.55})

 payload = service.load()
 assert payload["current"]["constants"]["geometry"]["kinematics"]["rod_attach_fraction"] ==0.55


def test_constants_accessors_use_settings_service(
 settings_payload: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
 monkeypatch.setattr(
 constants_module,
 "get_settings_service",
 lambda: SettingsService(settings_path=settings_payload),
 )

 constants_module.refresh_cache()

 valves = constants_module.get_pneumo_valve_constants()
 assert valves["delta_open_pa"] ==123.0

 receiver = constants_module.get_pneumo_receiver_constants()
 assert receiver["initial_volume_m3"] ==0.15

 gas = constants_module.get_pneumo_gas_constants()
 assert gas["total_time_s"] ==10.0

 assert constants_module.get_pneumo_master_isolation_default() is True
