"""Unit tests covering SignalsRouter handlers for the QML simulation panel."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

import pytest

from src.ui.main_window_pkg.signals_router import SignalsRouter
from src.ui.main_window_pkg.qml_bridge import QMLBridge
from src.ui.panels.modes.defaults import DEFAULT_PHYSICS_OPTIONS


class _DummySignal:
    """Lightweight stand-in for Qt signals used in tests."""

    def __init__(self) -> None:
        self.emitted: list[tuple[Any, ...]] = []

    def emit(self, *args: Any) -> None:  # pragma: no cover - behaviour exercised
        self.emitted.append(tuple(args))


class _DummyStateBus:
    def __init__(self) -> None:
        self.set_receiver_volume = _DummySignal()
        self.set_physics_dt = _DummySignal()


class _DummySimulationManager:
    def __init__(self) -> None:
        self.state_bus = _DummyStateBus()


class _DummySettingsManager:
    def __init__(self) -> None:
        self._categories: dict[str, dict[str, Any]] = {
            "pneumatic": {
                "volume_mode": "MANUAL",
            },
            "simulation": {
                "physics_dt": 0.001,
            },
            "modes": {
                "mode_preset": "standard",
                "physics": copy.deepcopy(DEFAULT_PHYSICS_OPTIONS),
            },
            "current.constants.geometry.cylinder": {
                "dead_zone_head_m3": 0.001,
                "dead_zone_rod_m3": 0.001,
            },
        }

    def get_category(self, name: str) -> dict[str, Any]:
        payload = self._categories.get(name, {})
        return copy.deepcopy(payload)

    def get(
        self, path: str, default: Any = None
    ) -> Any:  # pragma: no cover - defensive
        return copy.deepcopy(self._categories.get(path, default))


class _DummyWindow:
    def __init__(self) -> None:
        self.settings_updates: list[tuple[str, dict[str, Any]]] = []
        self.settings_manager = _DummySettingsManager()
        self.simulation_manager = _DummySimulationManager()

    def _apply_settings_update(self, category: str, payload: dict[str, Any]) -> None:
        self.settings_updates.append((category, copy.deepcopy(payload)))


def test_handle_pneumatic_settings_changed_updates_settings_and_bus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Numeric pneumatic edits must persist and forward to the state bus."""

    window = _DummyWindow()
    dispatched: list[str] = []

    monkeypatch.setattr(
        SignalsRouter,
        "_push_pneumatic_state",
        lambda w: dispatched.append("pneumatic") if w is window else None,
    )

    payload = {
        "receiver_volume": 0.0315,
        "volume_mode": "geometric",
        "cv_atmo_dp": 1500,
        "cv_tank_dp": 2200,
        "cv_atmo_dia": 0.004,
        "cv_tank_dia": 0.0035,
        "relief_min_pressure": 280000,
        "relief_stiff_pressure": 1750000,
        "relief_safety_pressure": 4200000,
        "throttle_min_dia": 0.0012,
        "throttle_stiff_dia": 0.0017,
        "diagonal_coupling_dia": 0.0009,
        "atmo_temp": 18.0,
        "master_isolation_open": True,
    }

    SignalsRouter.handle_pneumatic_settings_changed(window, payload)

    assert dispatched == ["pneumatic"], "Pneumatic state should be pushed to QML"
    assert window.settings_updates, "Settings update must be recorded"

    category, updates = window.settings_updates[-1]
    assert category == "pneumatic"
    assert updates["receiver_volume"] == pytest.approx(0.0315)
    assert updates["volume_mode"] == "GEOMETRIC"
    assert updates["master_isolation_open"] is True
    assert updates["diagonal_coupling_dia"] == pytest.approx(0.0009)
    assert window.simulation_manager.state_bus.set_receiver_volume.emitted[-1] == (
        pytest.approx(0.0315),
        "GEOMETRIC",
    )


def test_handle_simulation_settings_changed_updates_settings_and_bus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulation edits must persist and notify the simulation manager."""

    window = _DummyWindow()
    dispatched: list[str] = []

    monkeypatch.setattr(
        SignalsRouter,
        "_push_simulation_state",
        lambda w: dispatched.append("simulation") if w is window else None,
    )

    payload = {
        "physics_dt": 0.00075,
        "render_vsync_hz": 75.0,
        "max_steps_per_frame": 24,
        "max_frame_time": 0.045,
    }

    SignalsRouter.handle_simulation_settings_changed(window, payload)

    assert dispatched == ["simulation"], "Simulation state should be pushed to QML"
    category, updates = window.settings_updates[-1]
    assert category == "simulation"
    assert updates["physics_dt"] == pytest.approx(0.00075)
    assert updates["render_vsync_hz"] == pytest.approx(75.0)
    assert updates["max_steps_per_frame"] == 24
    assert updates["max_frame_time"] == pytest.approx(0.045)
    assert window.simulation_manager.state_bus.set_physics_dt.emitted[-1] == (
        pytest.approx(0.00075),
    )


def test_handle_cylinder_settings_changed_updates_constants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cylinder dead zones from QML must persist under constants geometry."""

    window = _DummyWindow()
    dispatched: list[str] = []

    monkeypatch.setattr(
        SignalsRouter,
        "_push_cylinder_state",
        lambda w: dispatched.append("cylinder") if w is window else None,
    )

    payload = {
        "dead_zone_head_m3": 0.0018,
        "dead_zone_rod_m3": 0.0016,
    }

    SignalsRouter.handle_cylinder_settings_changed(window, payload)

    assert dispatched == ["cylinder"], "Cylinder state should be pushed to QML"
    category, updates = window.settings_updates[-1]
    assert category == "constants"
    assert updates == {
        "geometry": {
            "cylinder": {
                "dead_zone_head_m3": pytest.approx(0.0018),
                "dead_zone_rod_m3": pytest.approx(0.0016),
            }
        }
    }


def test_handle_modes_physics_changed_normalises_numeric_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Physics options from QML must preserve numeric tuning parameters."""

    window = _DummyWindow()
    dispatched: List[str] = []

    monkeypatch.setattr(
        SignalsRouter,
        "_push_modes_state",
        lambda w: dispatched.append("modes") if w is window else None,
    )

    payload = {
        "include_springs": False,
        "include_dampers": True,
        "include_pneumatics": False,
        "spring_constant": "61250",  # Accept stringified floats
        "damper_coefficient": 3450.5,
        "lever_inertia_multiplier": 1.35,
    }

    SignalsRouter.handle_modes_physics_changed(window, payload)

    assert dispatched == ["modes"], "Modes state should be pushed after update"
    assert window.settings_updates, "Settings update must be recorded"

    category, updates = window.settings_updates[-1]
    assert category == "modes"
    assert updates["mode_preset"] == "custom"

    physics_updates = updates["physics"]
    assert physics_updates["include_springs"] is False
    assert physics_updates["include_dampers"] is True
    assert physics_updates["include_pneumatics"] is False
    assert physics_updates["spring_constant"] == pytest.approx(61250.0)
    assert physics_updates["damper_coefficient"] == pytest.approx(3450.5)
    assert physics_updates["lever_inertia_multiplier"] == pytest.approx(1.35)


def test_pneumo_panel_receives_qml_updates(
    qtbot: pytestqt.qtbot.QtBot,
    settings_manager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """External pneumatic updates must synchronise the legacy Qt panel."""

    from src.ui.panels.pneumo import panel_pneumo_refactored as pneumo_module

    state_manager = pneumo_module.PneumoStateManager(settings_manager=settings_manager)
    monkeypatch.setattr(pneumo_module, "PneumoStateManager", lambda: state_manager)

    panel = pneumo_module.PneumoPanel()
    qtbot.addWidget(panel)

    class _PanelWindow:
        def __init__(self) -> None:
            self.settings_updates: list[tuple[str, dict[str, Any]]] = []
            self.settings_manager = settings_manager
            self.simulation_manager = _DummySimulationManager()
            self.pneumo_panel = panel

        def _apply_settings_update(
            self, category: str, payload: dict[str, Any]
        ) -> None:
            self.settings_updates.append((category, copy.deepcopy(payload)))

    window = _PanelWindow()

    monkeypatch.setattr(SignalsRouter, "_push_pneumatic_state", lambda *_: None)

    payload = {
        "volume_mode": "GEOMETRIC",
        "receiver_diameter": 0.25,
        "receiver_length": 0.75,
        "receiver_volume": 0.035,
        "cv_atmo_dp": 0.03,
        "master_isolation_open": False,
    }

    SignalsRouter.handle_pneumatic_settings_changed(window, payload)

    assert panel.state_manager.get_volume_mode() == "GEOMETRIC"
    assert panel.state_manager.get_receiver_diameter() == pytest.approx(0.25)
    assert panel.state_manager.get_receiver_length() == pytest.approx(0.75)
    assert panel.receiver_tab.volume_mode_combo.currentIndex() == 1
    assert panel.receiver_tab.receiver_diameter_knob.value() == pytest.approx(0.25)


def test_push_pneumatic_state_skips_when_marked_qml(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Update source flags must suppress redundant QML dispatches."""

    window = _DummyWindow()
    window.pneumo_panel = object()
    SignalsRouter._mark_update_source(window, "pneumatic", "qml")

    dispatched: list[tuple[Any, ...]] = []

    monkeypatch.setattr(
        SignalsRouter,
        "_get_settings_category",
        lambda *_args, **_kwargs: {"receiver_volume": 0.02},
    )
    monkeypatch.setattr(
        QMLBridge,
        "invoke_qml_function",
        lambda *args, **kwargs: dispatched.append(args),
    )

    SignalsRouter._push_pneumatic_state(window)

    assert dispatched == []
