import importlib
import sys
import time

import pytest

from src.core.settings_service import load_runtime_defaults


def test_runtime_package_import_is_lazy():
    sys.modules.pop("src.runtime.sim_loop", None)
    sys.modules.pop("src.physics.integrator", None)
    sys.modules.pop("src.physics.odes", None)

    start = time.perf_counter()
    runtime = importlib.import_module("src.runtime")
    elapsed = time.perf_counter() - start

    assert "src.runtime.sim_loop" not in sys.modules
    assert "src.physics.integrator" not in sys.modules
    assert "src.physics.odes" not in sys.modules
    assert elapsed < 0.5
    assert hasattr(runtime, "StateSnapshot")


def test_runtime_defaults_loaded_from_config():
    load_runtime_defaults.cache_clear()
    defaults = load_runtime_defaults()

    assert defaults["simulation"]["physics_dt"] == pytest.approx(0.001)
    assert defaults["simulation"]["render_vsync_hz"] == pytest.approx(60.0)
    assert defaults["simulation"]["max_frame_time"] == pytest.approx(0.05)
    assert defaults["pneumatic"]["receiver_volume_limits"]["max_m3"] == pytest.approx(
        1.0
    )
    assert defaults["constants"]["pneumo"]["valves"][
        "relief_min_orifice_diameter_m"
    ] == pytest.approx(0.001)


def test_runtime_defaults_include_gas_thresholds_and_rendering():
    load_runtime_defaults.cache_clear()
    defaults = load_runtime_defaults()

    gas_constants = defaults["constants"]["pneumo"]["gas"]
    assert gas_constants["relief_safety_threshold_pa"] == pytest.approx(5_000_000.0)
    assert gas_constants["relief_min_threshold_pa"] == pytest.approx(250_000.0)
    assert defaults["advanced"]["target_fps"] == pytest.approx(60.0)
