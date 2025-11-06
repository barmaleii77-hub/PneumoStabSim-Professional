"""Parametrised regression tests for legacy gas state thermodynamics."""

import math
from typing import Callable

import pytest

from src.pneumo.gas_state import LegacyGasState
from src.pneumo.thermo import ThermoMode
from src.common.units import GAMMA_AIR


@pytest.mark.parametrize(
    ("mode", "target_volume", "expected_pressure", "expected_temperature"),
    (
        pytest.param(
            ThermoMode.ISOTHERMAL,
            0.012,
            150_000.0 * (0.01 / 0.012),
            293.15,
            id="isothermal-expansion",
        ),
        pytest.param(
            ThermoMode.ADIABATIC,
            0.012,
            150_000.0 * ((0.01 / 0.012) ** GAMMA_AIR),
            293.15 * ((0.01 / 0.012) ** (GAMMA_AIR - 1.0)),
            id="adiabatic-expansion",
        ),
    ),
)
def test_volume_update_modes(
    legacy_gas_state_factory: Callable[..., LegacyGasState],
    mode: ThermoMode,
    target_volume: float,
    expected_pressure: float,
    expected_temperature: float,
) -> None:
    """Check that isothermal and adiabatic volume updates match analytic curves.

    The fixture produces a 10 L chamber at 150 kPa and 20 °C. Expanding it to
    12 L is expected to drop the pressure to 125 kPa in the isothermal case and
    to ≈118.4 kPa during an adiabatic process. The adiabatic expansion must also
    cool the gas to ≈283.1 K, while the isothermal trajectory keeps the
    temperature constant.
    """

    state = legacy_gas_state_factory(
        pressure=150_000.0, volume=0.01, temperature=293.15
    )
    state.update_volume(target_volume, mode=mode)

    assert math.isclose(state.pressure, expected_pressure, rel_tol=1e-9)
    assert math.isclose(state.temperature, expected_temperature, rel_tol=1e-9)
