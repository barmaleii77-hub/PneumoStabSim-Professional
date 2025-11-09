"""Integration-style tests for geometry payload validation."""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from src.ui.main_window_pkg.main_window_refactored import MainWindow


class GeometryHarness:
    """Minimal object mimicking the parts of MainWindow used in tests."""

    def __init__(self) -> None:
        self._last_geometry_payload: dict[str, float] = {}
        self.logger = logging.getLogger("geometry-harness")
        self.logger.setLevel(logging.DEBUG)
        self.status_bar = SimpleNamespace(showMessage=lambda *_args, **_kwargs: None)
        self.applied_settings: list[tuple[str, dict[str, float]]] = []

    def _apply_settings_update(self, path: str, payload: dict[str, float]) -> None:
        self.applied_settings.append((path, dict(payload)))

    def _sanitize_geometry_payload(
        self, payload: dict[str, float]
    ) -> tuple[dict[str, float], list[str]]:
        return MainWindow._sanitize_geometry_payload(self, payload)

    def _geometry_settings_payload(self, payload: dict[str, float]) -> dict[str, float]:
        return MainWindow._geometry_settings_payload(self, payload)


@pytest.mark.parametrize(
    "payload,expected_frame,expected_lever",
    [
        ({"trackWidth": 2.0, "frameToPivot": 1.2, "leverLength": 1.0}, 1.0, 0.0),
        ({"trackWidth": 2.2, "frameToPivot": 0.8, "leverLength": 0.5}, 0.8, 0.3),
    ],
)
def test_geometry_relationships_clamped(
    payload, expected_frame, expected_lever, caplog
):
    harness = GeometryHarness()
    caplog.set_level(logging.WARNING, logger="geometry-harness")

    sanitized, adjustments = MainWindow._sanitize_geometry_payload(
        harness, dict(payload)
    )

    assert sanitized["frameToPivot"] == pytest.approx(expected_frame)
    assert sanitized["leverLength"] == pytest.approx(expected_lever)
    assert sanitized["frameToPivot"] + sanitized["leverLength"] == pytest.approx(
        sanitized["trackWidth"] / 2.0
    )
    assert sanitized["maxSuspTravel"] == pytest.approx(2.0 * sanitized["leverLength"])
    if not pytest.approx(payload.get("frameToPivot", sanitized["frameToPivot"])) == sanitized[
        "frameToPivot"
    ]:
        assert any("frameToPivot" in note for note in adjustments)
    if not pytest.approx(payload.get("leverLength", sanitized["leverLength"])) == sanitized[
        "leverLength"
    ]:
        assert any("leverLength" in note for note in adjustments)


def test_stroke_and_rod_constraints_raise_to_minimum(caplog):
    harness = GeometryHarness()
    caplog.set_level(logging.WARNING, logger="geometry-harness")

    payload = {
        "trackWidth": 2.0,
        "frameToPivot": 0.8,
        "leverLength": 0.2,
        "strokeM": 0.2,
        "cylinderBodyLength": 0.4,
        "pistonRodLengthM": 0.35,
    }

    sanitized, adjustments = MainWindow._sanitize_geometry_payload(harness, payload)

    min_stroke = 2.0 * sanitized["leverLength"]
    min_rod = 1.1 * sanitized["cylinderBodyLength"]

    assert sanitized["strokeM"] == pytest.approx(min_stroke)
    assert sanitized["maxSuspTravel"] == pytest.approx(min_stroke)
    assert sanitized["pistonRodLengthM"] == pytest.approx(min_rod)
    assert any("stroke" in note for note in adjustments)
    assert any("pistonRodLength" in note for note in adjustments)


def test_lever_update_without_track_recomputes_dependencies(caplog):
    harness = GeometryHarness()
    harness._last_geometry_payload.update(
        {
            "trackWidth": 2.0,
            "frameToPivot": 0.4,
            "leverLength": 0.6,
            "strokeM": 1.2,
        }
    )
    caplog.set_level(logging.WARNING, logger="geometry-harness")

    payload = {"leverLength": 0.8, "strokeM": 0.5}

    sanitized, adjustments = MainWindow._sanitize_geometry_payload(harness, payload)

    assert sanitized["leverLength"] == pytest.approx(0.8)
    assert sanitized["frameToPivot"] == pytest.approx(0.2)
    assert sanitized["maxSuspTravel"] == pytest.approx(1.6)
    assert sanitized["strokeM"] == pytest.approx(1.6)
    assert any("frameToPivot" in note for note in adjustments)
    assert any("stroke" in note for note in adjustments)


def test_pressure_scale_clamped_and_persisted(monkeypatch, caplog):
    harness = GeometryHarness()
    caplog.set_level(logging.WARNING, logger="geometry-harness")

    recorded_invocations: list[dict[str, float]] = []
    recorded_queued: list[dict[str, float]] = []

    def _invoke_stub(_window, method: str, params: dict[str, float]) -> bool:
        assert method == "applyGeometryUpdates"
        recorded_invocations.append(dict(params))
        return False

    def _queue_stub(_window, category: str, payload: dict[str, float]) -> None:
        assert category == "geometry"
        recorded_queued.append(dict(payload))

    monkeypatch.setattr(
        "src.ui.main_window_pkg.main_window_refactored.QMLBridge.invoke_qml_function",
        _invoke_stub,
    )
    monkeypatch.setattr(
        "src.ui.main_window_pkg.main_window_refactored.QMLBridge.queue_update",
        _queue_stub,
    )

    payload = {
        "trackWidth": 2.0,
        "frameToPivot": 0.9,
        "leverLength": 0.1,
        "pressureScaleMin": -500000.0,
        "pressureScaleMax": -1000.0,
    }

    MainWindow._on_geometry_changed_qml(harness, payload)

    assert harness.applied_settings
    settings_path, settings_payload = harness.applied_settings[-1]
    assert settings_path == "current.geometry"
    assert "pressure_scale_min_pa" in settings_payload
    assert "pressure_scale_max_pa" in settings_payload
    assert (
        settings_payload["pressure_scale_max_pa"]
        > settings_payload["pressure_scale_min_pa"]
    )

    assert recorded_invocations
    applied_payload = recorded_invocations[-1]
    assert applied_payload["pressureScaleMax"] > applied_payload["pressureScaleMin"]
    assert recorded_queued, "Adjusted values should be queued for QML consistency"


def test_adjusted_values_are_queued_even_on_success(monkeypatch, caplog):
    harness = GeometryHarness()
    caplog.set_level(logging.WARNING, logger="geometry-harness")

    recorded_invocations: list[dict[str, float]] = []
    recorded_queued: list[dict[str, float]] = []

    def _invoke_stub(_window, method: str, params: dict[str, float]) -> bool:
        assert method == "applyGeometryUpdates"
        recorded_invocations.append(dict(params))
        return True

    def _queue_stub(_window, category: str, payload: dict[str, float]) -> None:
        assert category == "geometry"
        recorded_queued.append(dict(payload))

    monkeypatch.setattr(
        "src.ui.main_window_pkg.main_window_refactored.QMLBridge.invoke_qml_function",
        _invoke_stub,
    )
    monkeypatch.setattr(
        "src.ui.main_window_pkg.main_window_refactored.QMLBridge.queue_update",
        _queue_stub,
    )

    payload = {"trackWidth": 2.0, "frameToPivot": 1.5, "leverLength": 0.7}

    MainWindow._on_geometry_changed_qml(harness, payload)

    assert recorded_invocations
    assert recorded_queued, "Corrections must be pushed back to QML"

    queued_payload = recorded_queued[-1]
    applied_payload = recorded_invocations[-1]

    assert queued_payload["frameToPivot"] == pytest.approx(
        applied_payload["frameToPivot"]
    )
    assert queued_payload["leverLength"] == pytest.approx(
        applied_payload["leverLength"]
    )
