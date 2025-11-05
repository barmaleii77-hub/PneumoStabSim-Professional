"""Protocol definitions for high-level application services.

The renovation plan for Phase 2 introduces a thin service layer that isolates
domain logic from the Qt-facing bridge modules.  These protocols define the
contracts that concrete implementations must satisfy so modules across
``src/core``, ``src/simulation`` and ``src/ui`` can collaborate without
importing heavyweight dependencies.

The interfaces intentionally focus on the operations that are already exercised
by the test-suite:

* :class:`SimulationService` coordinates preset management for the training
  workflows and publishes changes when settings drift away from a preset.
* :class:`VisualizationService` maintains a canonical snapshot of the latest
  geometry, camera and rendering state that QML consumers can observe.
* :class:`SettingsOrchestrator` offers a small façade over
  :class:`~src.common.settings_manager.SettingsManager`, handling dotted-path
  updates and wiring callbacks to the Qt event bus.

Concrete implementations live in their respective packages but the rest of the
codebase only relies on these narrow abstractions which keeps dependencies
acyclic and simplifies testing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SettingsOrchestrator(Protocol):
    """Coordinate access to the shared settings store and its event bus."""

    def snapshot(self, paths: Sequence[str]) -> Mapping[str, Any]:
        """Return a mapping of ``path`` → ``value`` for the requested paths."""

    def apply_updates(
        self,
        updates: Mapping[str, Any],
        *,
        auto_save: bool = True,
    ) -> Mapping[str, Any]:
        """Persist the provided dotted-path updates and return the payload."""

    def register_listener(
        self, callback: Callable[[Mapping[str, Any]], None]
    ) -> Callable[[], None]:
        """Register ``callback`` for settings change notifications."""


@runtime_checkable
class SimulationService(Protocol):
    """Expose simulation preset management to UI bridges and tests."""

    def list_presets(self) -> Sequence[Mapping[str, Any]]:
        """Return a serialisable description of all known presets."""

    def describe_preset(self, preset_id: str) -> Mapping[str, Any]:
        """Return the QML payload for ``preset_id`` or an empty mapping."""

    def apply_preset(
        self, preset_id: str, *, auto_save: bool = True
    ) -> Mapping[str, Any]:
        """Apply ``preset_id`` to the underlying settings store."""

    def active_preset_id(self) -> str:
        """Return the preset that matches the current settings snapshot."""

    def register_active_observer(
        self, callback: Callable[[str], None]
    ) -> Callable[[], None]:
        """Invoke ``callback`` whenever the active preset identifier changes."""


@runtime_checkable
class VisualizationService(Protocol):
    """Maintain a canonical view of geometry, camera and rendering state."""

    def categories(self) -> Sequence[str]:
        """Return the list of recognised update categories."""

    def state_for(self, category: str) -> Mapping[str, Any]:
        """Return the last known payload for ``category``."""

    def latest_updates(self) -> Mapping[str, Mapping[str, Any]]:
        """Return the latest batch of dispatched updates."""

    def access_profile(self) -> Mapping[str, Any]:
        """Return the active access control profile for the UI."""

    def dispatch_updates(
        self, updates: Mapping[str, Mapping[str, Any]]
    ) -> Mapping[str, Mapping[str, Any]]:
        """Normalise and persist updates, returning the sanitised payload."""

    def reset(self, categories: Iterable[str] | None = None) -> Iterable[str]:
        """Reset the stored payloads and return the affected categories."""

    def prepare_camera_payload(
        self, payload: Mapping[str, Any] | None = None
    ) -> Mapping[str, Any]:
        """Enrich ``payload`` with orbit metadata and HUD telemetry."""

    def refresh_orbit_presets(self) -> Mapping[str, Any]:
        """Reload orbit presets and return the manifest exposed to the UI."""
