"""Integration tests covering pneumatic simulation coordination."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.settings_orchestrator import SettingsOrchestrator
from src.pneumo.enums import ThermoMode
from src.simulation.service import TrainingPresetService

from .sim_helpers import (
    apply_body_roll,
    compute_road_metrics,
    create_simulation_context,
    run_oscillation_cycle,
    simulation_logger,
    store_metrics,
)


ROAD_METRIC_BASELINES = {
    "highway_100kmh": {
        "axle_delay": 0.11510791366906475,
        "velocity": 27.8,
        "profile_stats": {
            "LF": {
                "max": 3.760597067740161e-07,
                "min": -3.9476489069569455e-07,
                "rms": 1.1671786957599e-07,
                "std": 1.1671786957599e-07,
            },
            "LR": {
                "max": 3.760597067740161e-07,
                "min": -3.9476489069569455e-07,
                "rms": 1.1635146656182366e-07,
                "std": 1.1634414427106508e-07,
            },
            "RF": {
                "max": 3.449889433062928e-07,
                "min": -3.69773245066991e-07,
                "rms": 1.1652706021252863e-07,
                "std": 1.1652706021252863e-07,
            },
            "RR": {
                "max": 3.449889433062928e-07,
                "min": -3.69773245066991e-07,
                "rms": 1.1509475287656475e-07,
                "std": 1.1506461041842986e-07,
            },
        },
    },
    "urban_50kmh": {
        "axle_delay": 0.2302158273381295,
        "velocity": 13.9,
        "profile_stats": {
            "LF": {
                "max": 7.088867086754944e-07,
                "min": -8.851869911475623e-07,
                "rms": 3.2619018813549333e-07,
                "std": 3.2619018813549333e-07,
            },
            "LR": {
                "max": 7.088867086754944e-07,
                "min": -8.851869911475623e-07,
                "rms": 3.211359248585518e-07,
                "std": 3.2097641056266165e-07,
            },
            "RF": {
                "max": 7.012406121488484e-07,
                "min": -9.356096387432415e-07,
                "rms": 3.127213542945253e-07,
                "std": 3.127213542945253e-07,
            },
            "RR": {
                "max": 6.862429341533892e-07,
                "min": -9.356096387432415e-07,
                "rms": 2.9733168521559334e-07,
                "std": 2.9658851683112525e-07,
            },
        },
    },
    "offroad_moderate": {
        "axle_delay": 0.21333333333333335,
        "velocity": 15.0,
        "profile_stats": {
            "LF": {
                "max": 2.5181761132981716e-06,
                "min": -2.355231414812566e-06,
                "rms": 9.039430181135889e-07,
                "std": 9.039430181135889e-07,
            },
            "LR": {
                "max": 2.5181761132981716e-06,
                "min": -2.355231414812566e-06,
                "rms": 8.834298376383996e-07,
                "std": 8.831364268397431e-07,
            },
            "RF": {
                "max": 3.4072809109486934e-06,
                "min": -4.074246978701351e-06,
                "rms": 1.518382202041201e-06,
                "std": 1.518382202041201e-06,
            },
            "RR": {
                "max": 3.4072809109486934e-06,
                "min": -4.074246978701351e-06,
                "rms": 1.4685012104915382e-06,
                "std": 1.4677048928416838e-06,
            },
        },
    },
    "test_sine": {
        "axle_delay": 0.19161676646706588,
        "velocity": 16.7,
        "profile_stats": {
            "LF": {
                "max": 0.049999993630605484,
                "min": -0.04999999271360534,
                "rms": 0.03550345181449262,
                "std": 0.03542928613987631,
            },
            "LR": {
                "max": 0.049999993630605484,
                "min": -0.04999999271360534,
                "rms": 0.03424035672400567,
                "std": 0.03423873573338609,
            },
            "RF": {
                "max": 0.049999993630605484,
                "min": -0.04999999271360534,
                "rms": 0.03550345181449262,
                "std": 0.03542928613987631,
            },
            "RR": {
                "max": 0.049999993630605484,
                "min": -0.04999999271360534,
                "rms": 0.03424035672400567,
                "std": 0.03423873573338609,
            },
        },
    },
}


def _assert_baseline_loaded() -> None:
    if not ROAD_METRIC_BASELINES:
        raise AssertionError(
            "ROAD_METRIC_BASELINES is empty; update with reference data"
        )


@pytest.mark.integration
def test_body_roll_generates_balanced_pressure_delta(
    integration_reports_dir: Path,
) -> None:
    """A static body roll should change left/right pressures in opposite directions."""

    context = create_simulation_context(duration=3.0)
    with simulation_logger(integration_reports_dir, "body_roll") as (logger, log_path):
        metrics = apply_body_roll(context, logger=logger)

    metrics_path = integration_reports_dir / "body_roll_metrics.json"
    store_metrics(metrics, metrics_path)

    assert log_path.exists(), "Simulation log missing"
    assert metrics_path.exists(), "Metrics artefact missing"

    delta = metrics["pressure_delta"]
    delta_values = list(delta.values())
    assert all(value > 0.0 for value in delta_values)
    assert max(delta_values) == pytest.approx(min(delta_values), rel=1e-6)

    volume_delta = metrics["volume_delta"]
    volume_values = list(volume_delta.values())
    assert all(value < 0.0 for value in volume_values)
    assert max(abs(value) for value in volume_values) == pytest.approx(
        min(abs(value) for value in volume_values),
        rel=1e-6,
    )

    total_volume_shift = sum(volume_values)
    assert total_volume_shift < 0.0


@pytest.mark.integration
def test_isothermal_cycle_preserves_mass(integration_reports_dir: Path) -> None:
    """Running an oscillation cycle should conserve the total gas mass."""

    context = create_simulation_context(duration=4.0)
    with simulation_logger(integration_reports_dir, "cycle_isothermal") as (
        logger,
        log_path,
    ):
        metrics = run_oscillation_cycle(
            context,
            thermo_mode=ThermoMode.ISOTHERMAL,
            amplitude_deg=2.0,
            frequency_hz=1.5,
            cycles=2.0,
            dt=0.01,
            logger=logger,
        )

    metrics_path = integration_reports_dir / "cycle_isothermal_metrics.json"
    store_metrics(metrics, metrics_path)

    assert log_path.exists()
    assert metrics_path.exists()
    assert metrics["mass_range"] < 5e-5
    assert metrics["max_pressure_range"] > 10.0


@pytest.mark.integration
def test_thermo_mode_switch_changes_pressure_response(
    integration_reports_dir: Path,
) -> None:
    """Adiabatic mode should amplify pressure swings compared to isothermal mode."""

    iso_context = create_simulation_context(duration=4.0)
    with simulation_logger(integration_reports_dir, "cycle_iso_vs_adiabatic_iso") as (
        iso_logger,
        iso_log_path,
    ):
        iso_metrics = run_oscillation_cycle(
            iso_context,
            thermo_mode=ThermoMode.ISOTHERMAL,
            amplitude_deg=2.0,
            frequency_hz=1.2,
            cycles=2.5,
            dt=0.0125,
            logger=iso_logger,
        )

    adi_context = create_simulation_context(duration=4.0)
    with simulation_logger(integration_reports_dir, "cycle_iso_vs_adiabatic_adi") as (
        adi_logger,
        adi_log_path,
    ):
        adi_metrics = run_oscillation_cycle(
            adi_context,
            thermo_mode=ThermoMode.ADIABATIC,
            amplitude_deg=2.0,
            frequency_hz=1.2,
            cycles=2.5,
            dt=0.0125,
            logger=adi_logger,
        )

    store_metrics(
        {"isothermal": iso_metrics, "adiabatic": adi_metrics},
        integration_reports_dir / "cycle_iso_vs_adiabatic_metrics.json",
    )

    assert iso_log_path.exists()
    assert adi_log_path.exists()
    assert adi_metrics["max_pressure_range"] > iso_metrics["max_pressure_range"]


@pytest.mark.integration
def test_training_service_tracks_mode_switches(
    settings_manager, integration_reports_dir: Path
) -> None:
    """Switching simulation modes should keep the preset coordinator consistent."""

    orchestrator = SettingsOrchestrator(settings_manager=settings_manager)
    service = TrainingPresetService(orchestrator=orchestrator)

    try:
        assert service.active_preset_id() == "baseline"

        orchestrator.apply_updates({"current.simulation.sim_type": "KINEMATICS"})
        assert service.active_preset_id() == "baseline"

        orchestrator.apply_updates({"current.simulation.sim_type": "DYNAMICS"})
        assert service.active_preset_id() == "baseline"

        orchestrator.apply_updates({"current.pneumatic.thermo_mode": "ADIABATIC"})
        assert service.active_preset_id() == ""

        service.apply_preset("precision_mode")
        assert service.active_preset_id() == "precision_mode"

        state_snapshot = orchestrator.snapshot(
            ["current.simulation", "current.pneumatic"]
        )

        store_metrics(
            {
                "active_preset": service.active_preset_id(),
                "simulation": state_snapshot.get("current.simulation", {}),
                "pneumatic": state_snapshot.get("current.pneumatic", {}),
            },
            integration_reports_dir / "coordinator_state.json",
        )
    finally:
        service.close()
        orchestrator.close()


@pytest.mark.integration
@pytest.mark.parametrize("preset_name", sorted(ROAD_METRIC_BASELINES.keys()))
def test_road_profiles_match_baseline(
    preset_name: str, integration_reports_dir: Path
) -> None:
    """Road preset previews should match deterministic baseline metrics."""

    _assert_baseline_loaded()
    context = create_simulation_context(road_preset=preset_name, duration=4.0)
    metrics = compute_road_metrics(context.road_input)

    store_metrics(
        metrics,
        integration_reports_dir / f"road_metrics_{preset_name}.json",
    )

    expected = ROAD_METRIC_BASELINES[preset_name]

    assert metrics["velocity"] == pytest.approx(expected["velocity"], rel=1e-6)
    assert metrics["axle_delay"] == pytest.approx(expected["axle_delay"], rel=1e-3)

    for wheel, stats in expected["profile_stats"].items():
        measured = metrics["profile_stats"][wheel]
        for key, value in stats.items():
            assert measured[key] == pytest.approx(value, rel=1e-2)
