# -*- coding: utf-8 -*-
"""Utilities for tracking the diagnostics profiler overlay state."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

from src.common.settings_manager import SettingsManager, get_settings_manager


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ProfilerOverlayState:
    """Snapshot describing the diagnostics profiler overlay configuration."""

    overlay_enabled: bool
    recorded_at: datetime
    source: str
    scenario: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the snapshot."""

        payload: Dict[str, Any] = {
            "overlayEnabled": bool(self.overlay_enabled),
            "recordedAt": self.recorded_at.isoformat(),
            "source": self.source,
        }
        if self.scenario:
            payload["scenario"] = self.scenario
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


_STATE_LOCK = Lock()
_OVERLAY_STATE: Optional[ProfilerOverlayState] = None


def _read_diagnostics_payload(
    manager: SettingsManager | None,
) -> Dict[str, Any]:
    if manager is None:
        return {}
    try:
        payload = manager.get("diagnostics", {}) or {}
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.warning("Unable to read diagnostics defaults: %s", exc)
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def load_profiler_overlay_state(
    settings_manager: SettingsManager | None = None,
) -> ProfilerOverlayState:
    """Return the cached overlay snapshot, bootstrapping it from settings."""

    global _OVERLAY_STATE
    with _STATE_LOCK:
        if _OVERLAY_STATE is not None:
            return _OVERLAY_STATE

        manager = settings_manager
        if manager is None:
            try:
                manager = get_settings_manager()
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.debug("SettingsManager unavailable, using defaults: %s", exc)
                manager = None

        diagnostics_payload = _read_diagnostics_payload(manager)
        signal_trace = diagnostics_payload.get("signal_trace", {})
        if not isinstance(signal_trace, dict):
            signal_trace = {}

        raw_overlay = signal_trace.get(
            "overlay_enabled", signal_trace.get("overlayEnabled", False)
        )
        overlay_enabled = bool(raw_overlay)

        _OVERLAY_STATE = ProfilerOverlayState(
            overlay_enabled=overlay_enabled,
            recorded_at=datetime.now(timezone.utc),
            source="settings" if manager is not None else "defaults",
            metadata={
                "settingsAvailable": manager is not None,
                "historyLimit": signal_trace.get(
                    "history_limit", signal_trace.get("historyLimit")
                ),
            },
        )
        return _OVERLAY_STATE


def get_profiler_overlay_defaults(
    settings_manager: SettingsManager | None = None,
) -> Dict[str, Any]:
    """Return diagnostics defaults ensuring the overlay flag reflects runtime state."""

    manager = settings_manager
    if manager is None:
        try:
            manager = get_settings_manager()
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.debug("SettingsManager unavailable when reading defaults: %s", exc)
            manager = None

    diagnostics_payload = _read_diagnostics_payload(manager)
    signal_trace = diagnostics_payload.get("signal_trace", {})
    if not isinstance(signal_trace, dict):
        signal_trace = {}

    state = load_profiler_overlay_state(manager)
    signal_trace["overlay_enabled"] = bool(state.overlay_enabled)
    signal_trace.setdefault("overlayEnabled", bool(state.overlay_enabled))
    diagnostics_payload["signal_trace"] = signal_trace
    return diagnostics_payload


def record_profiler_overlay(
    enabled: bool,
    *,
    source: str = "runtime",
    scenario: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ProfilerOverlayState:
    """Persist an overlay snapshot sourced from a runtime event."""

    global _OVERLAY_STATE
    update_metadata = dict(metadata or {})
    with _STATE_LOCK:
        previous = _OVERLAY_STATE
        if previous is None:
            previous = load_profiler_overlay_state()
        merged_metadata = dict(previous.metadata)
        merged_metadata.update(update_metadata)
        _OVERLAY_STATE = ProfilerOverlayState(
            overlay_enabled=bool(enabled),
            recorded_at=datetime.now(timezone.utc),
            source=source,
            scenario=scenario or previous.scenario,
            metadata=merged_metadata,
        )
        return _OVERLAY_STATE


def export_profiler_report(
    path: Path,
    state: Optional[ProfilerOverlayState] = None,
    *,
    scenario: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Path:
    """Write the profiler overlay snapshot to a JSON report."""

    path = Path(path)
    snapshot = state or load_profiler_overlay_state()
    if scenario and snapshot.scenario != scenario:
        snapshot = ProfilerOverlayState(
            overlay_enabled=snapshot.overlay_enabled,
            recorded_at=snapshot.recorded_at,
            source=snapshot.source,
            scenario=scenario,
            metadata=dict(snapshot.metadata),
        )

    payload = snapshot.to_payload()
    if extra:
        payload["extra"] = extra

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    LOGGER.info("Profiler overlay report exported to %s", path)
    return path


def _reset_profiler_state_for_tests() -> None:
    """Clear cached overlay state (test helper)."""

    global _OVERLAY_STATE
    with _STATE_LOCK:
        _OVERLAY_STATE = None


__all__ = [
    "ProfilerOverlayState",
    "export_profiler_report",
    "get_profiler_overlay_defaults",
    "load_profiler_overlay_state",
    "record_profiler_overlay",
    "_reset_profiler_state_for_tests",
]
