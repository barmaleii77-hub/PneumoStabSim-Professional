"""Unit tests for the physics integrator configuration helpers."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from config import constants as constants_module
from physics.integrator import (
    PhysicsLoopConfig,
    clamp_state,
    create_default_rigid_body,
    refresh_physics_loop_defaults,
)
from src.core.settings_service import SettingsService


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SETTINGS_PATH = PROJECT_ROOT / "config" / "app_settings.json"


def _write_custom_settings(tmp_path: Path) -> Path:
    payload = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))

    integrator = payload["current"]["constants"]["physics"]["integrator"]
    integrator["solver"]["primary_method"] = "RK45"
    integrator["solver"]["max_step_divisor"] = 8.0
    integrator["loop"]["max_linear_velocity_m_s"] = 2.5
    integrator["loop"]["max_angular_velocity_rad_s"] = 3.5
    integrator["loop"]["nan_replacement_value"] = -1.0
    integrator["loop"]["posinf_replacement_value"] = 4.2
    integrator["loop"]["neginf_replacement_value"] = -2.4

    payload["defaults_snapshot"]["constants"]["physics"]["integrator"] = json.loads(
        json.dumps(integrator)
    )

    settings_file = tmp_path / "app_settings.json"
    settings_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return settings_file


def test_refresh_physics_loop_defaults_reload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """refresh_physics_loop_defaults must reload solver and clamp parameters."""

    custom_settings = _write_custom_settings(tmp_path)
    service = SettingsService(settings_path=custom_settings)

    with monkeypatch.context() as patch:
        patch.setattr(
            constants_module,
            "get_settings_service",
            lambda: service,
        )
        constants_module.refresh_cache()
        refresh_physics_loop_defaults()

        config = PhysicsLoopConfig()
        assert config.solver_primary == "RK45"
        assert config.solver_max_step_divisor == pytest.approx(8.0)
        assert config.max_step == pytest.approx(config.dt_physics / 8.0)
        assert config.solver_fallbacks, "Fallback solver list must not be empty"

        params = create_default_rigid_body()
        overflowing_state = np.array([0.0, 0.0, 0.0, 12.0, 12.0, -20.0], dtype=float)
        clamped = clamp_state(overflowing_state, params)
        assert clamped[3] == pytest.approx(2.5)
        assert clamped[4] == pytest.approx(3.5)
        assert clamped[5] == pytest.approx(-3.5)

        anomalous_state = np.array(
            [np.inf, 0.0, 0.0, np.nan, 0.0, 0.0],
            dtype=float,
        )
        sanitised = clamp_state(anomalous_state, params)
        assert sanitised[0] == pytest.approx(4.2)
        assert sanitised[3] == pytest.approx(-1.0)

        negative_overflow = np.array(
            [-np.inf, 0.0, 0.0, 0.0, 0.0, 0.0],
            dtype=float,
        )
        sanitised_negative = clamp_state(negative_overflow, params)
        assert sanitised_negative[0] == pytest.approx(-2.4)

    constants_module.refresh_cache()
    refresh_physics_loop_defaults()
