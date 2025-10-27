import importlib
import sys
import types
from pathlib import Path

import pytest


def _load_geometry_state_manager():
    repo_root = Path(__file__).resolve().parents[2]
    panels_path = repo_root / "src" / "ui" / "panels"
    geometry_path = panels_path / "geometry"

    if "src.common.settings_manager" not in sys.modules:
        settings_stub = types.ModuleType("src.common.settings_manager")

        class _StubSettingsManager:  # pragma: no cover - used for import wiring only
            pass

        settings_stub.SettingsManager = _StubSettingsManager
        sys.modules["src.common.settings_manager"] = settings_stub

    if "src.ui.panels" not in sys.modules:
        panels_module = types.ModuleType("src.ui.panels")
        panels_module.__path__ = [str(panels_path)]
        sys.modules["src.ui.panels"] = panels_module
    else:
        module = sys.modules["src.ui.panels"]
        if not hasattr(module, "__path__"):
            module.__path__ = []
        module.__path__ = [str(panels_path)]

    if "src.ui.panels.geometry" not in sys.modules:
        geometry_module = types.ModuleType("src.ui.panels.geometry")
        geometry_module.__path__ = [str(geometry_path)]
        sys.modules["src.ui.panels.geometry"] = geometry_module
    else:
        module = sys.modules["src.ui.panels.geometry"]
        if not hasattr(module, "__path__"):
            module.__path__ = []
        module.__path__ = [str(geometry_path)]

    return importlib.import_module(
        "src.ui.panels.geometry.state_manager"
    ).GeometryStateManager


GeometryStateManager = _load_geometry_state_manager()


def test_get_3d_geometry_update_returns_meters() -> None:
    manager = GeometryStateManager(settings_manager=None)

    update = manager.get_3d_geometry_update()

    assert update["frameLength"] == pytest.approx(3.2)
    assert update["frameHeight"] == pytest.approx(0.65)
    assert update["frameBeamSize"] == pytest.approx(0.12)
    assert update["leverLength"] == pytest.approx(0.8)
    assert update["cylinderBodyLength"] == pytest.approx(0.5)
    assert update["tailRodLength"] == pytest.approx(0.1)
    assert update["trackWidth"] == pytest.approx(1.6)
    assert update["frameToPivot"] == pytest.approx(0.6)
    assert update["rodPosition"] == pytest.approx(0.6)
    assert update["cylDiamM"] == pytest.approx(0.08)
    assert update["strokeM"] == pytest.approx(0.3)
    assert update["deadGapM"] == pytest.approx(0.005)
    assert update["rodDiameterM"] == pytest.approx(0.035)
    assert update["pistonRodLengthM"] == pytest.approx(0.2)
    assert update["pistonThicknessM"] == pytest.approx(0.025)


def test_get_3d_geometry_update_respects_state_overrides() -> None:
    manager = GeometryStateManager(settings_manager=None)
    manager.update_parameters(
        {
            "wheelbase": 2.75,
            "frame_height_m": 0.7,
            "frame_beam_size_m": 0.15,
            "lever_length": 0.95,
            "cylinder_length": 0.45,
            "tail_rod_length_m": 0.12,
            "track": 1.72,
            "frame_to_pivot": 0.55,
            "rod_position": 0.72,
            "cyl_diam_m": 0.09,
            "stroke_m": 0.32,
            "dead_gap_m": 0.004,
            "rod_diameter_m": 0.028,
            "piston_rod_length_m": 0.24,
            "piston_thickness_m": 0.018,
        }
    )

    update = manager.get_3d_geometry_update()

    assert update["frameLength"] == pytest.approx(2.75)
    assert update["frameHeight"] == pytest.approx(0.7)
    assert update["frameBeamSize"] == pytest.approx(0.15)
    assert update["leverLength"] == pytest.approx(0.95)
    assert update["cylinderBodyLength"] == pytest.approx(0.45)
    assert update["tailRodLength"] == pytest.approx(0.12)
    assert update["trackWidth"] == pytest.approx(1.72)
    assert update["frameToPivot"] == pytest.approx(0.55)
    assert update["rodPosition"] == pytest.approx(0.72)
    assert update["cylDiamM"] == pytest.approx(0.09)
    assert update["strokeM"] == pytest.approx(0.32)
    assert update["deadGapM"] == pytest.approx(0.004)
    assert update["rodDiameterM"] == pytest.approx(0.028)
    assert update["pistonRodLengthM"] == pytest.approx(0.24)
    assert update["pistonThicknessM"] == pytest.approx(0.018)
