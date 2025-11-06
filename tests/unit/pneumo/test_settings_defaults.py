import importlib
import json
from pathlib import Path

import pytest

from config.constants import refresh_cache


def _load_payload(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_payload(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


@pytest.mark.usefixtures("monkeypatch")
def test_check_valve_uses_settings_defaults(
    monkeypatch, temp_settings_file: Path
) -> None:
    monkeypatch.setenv("PSS_SETTINGS_FILE", str(temp_settings_file))
    payload = _load_payload(temp_settings_file)
    pneumo_constants = payload["current"]["constants"]["pneumo"]
    valve_constants = pneumo_constants["valves"]
    valve_constants["delta_open_pa"] = 7425.0
    valve_constants["equivalent_diameter_m"] = 0.0095
    valve_constants["relief_min_orifice_diameter_m"] = 0.0021
    valve_constants["relief_stiff_orifice_diameter_m"] = 0.0029
    _write_payload(temp_settings_file, payload)

    refresh_cache()
    valves_module = importlib.import_module("src.pneumo.valves")
    importlib.reload(valves_module)
    valves_module._check_valve_defaults.cache_clear()
    valves_module._relief_orifice_defaults.cache_clear()

    check_valve = valves_module.CheckValve()
    assert check_valve.delta_open_min == pytest.approx(7425.0)
    assert check_valve.d_eq == pytest.approx(0.0095)

    relief_min = valves_module.ReliefValve(
        kind=valves_module.ReliefValveKind.MIN_PRESS, p_set=50_000.0
    )
    assert relief_min.d_eq == pytest.approx(0.0021)

    relief_stiff = valves_module.ReliefValve(
        kind=valves_module.ReliefValveKind.STIFFNESS, p_set=100_000.0
    )
    assert relief_stiff.d_eq == pytest.approx(0.0029)


@pytest.mark.usefixtures("monkeypatch")
def test_gas_network_uses_settings_thresholds(
    monkeypatch, temp_settings_file: Path
) -> None:
    monkeypatch.setenv("PSS_SETTINGS_FILE", str(temp_settings_file))
    payload = _load_payload(temp_settings_file)
    pneumo_constants = payload["current"]["constants"]["pneumo"]
    gas_constants = pneumo_constants["gas"]
    gas_constants["relief_min_threshold_pa"] = 123456.0
    gas_constants["relief_stiff_threshold_pa"] = 654321.0
    gas_constants["relief_safety_threshold_pa"] = 999999.0

    valve_constants = pneumo_constants["valves"]
    valve_constants["relief_min_orifice_diameter_m"] = 0.0017
    valve_constants["relief_stiff_orifice_diameter_m"] = 0.0027
    _write_payload(temp_settings_file, payload)

    refresh_cache()

    network_module = importlib.import_module("src.pneumo.network")
    importlib.reload(network_module)
    network_module._relief_threshold_defaults.cache_clear()
    network_module._relief_orifice_defaults.cache_clear()

    from src.pneumo.enums import Line, ReceiverVolumeMode
    from src.pneumo.gas_state import create_line_gas_state, create_tank_gas_state

    lines = {
        line: create_line_gas_state(line, 101325.0, 290.0, 0.01)
        for line in (Line.A1, Line.A2, Line.B1, Line.B2)
    }
    tank = create_tank_gas_state(
        V_initial=0.02,
        p_initial=101325.0,
        T_initial=293.15,
        mode=ReceiverVolumeMode.ADIABATIC_RECALC,
    )

    system_stub = type("SystemStub", (), {})()
    system_stub.lines = {}

    network = network_module.GasNetwork(
        lines=lines,
        tank=tank,
        system_ref=system_stub,
    )

    assert network.relief_min_threshold == pytest.approx(123456.0)
    assert network.relief_stiff_threshold == pytest.approx(654321.0)
    assert network.relief_safety_threshold == pytest.approx(999999.0)
    assert network.relief_min_orifice_diameter == pytest.approx(0.0017)
    assert network.relief_stiff_orifice_diameter == pytest.approx(0.0027)
