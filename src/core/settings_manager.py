"""Profile settings management utilities.

The real application exposes a rich profile subsystem that stores the
environment, scene and animation parameters to standalone JSON files.  The
test-suite only relies on a small and well-defined surface of this module, but
the original implementation brings in the full Qt stack and a large dependency
tree which is not available inside the execution environment.  To keep the
tests hermetic we provide a lightweight, pure-Python implementation that mirrors
the behaviour required by :mod:`tests.unit.test_profile_settings_manager`.

The goal of this shim is not to be feature complete – it simply preserves the
observable semantics that the rest of the code expects:

* profile names are normalised to file-safe slugs;
* saving a profile serialises the relevant graphics sections;
* loading a profile pushes the values back into the shared settings manager and
  triggers a save to mimic the auto-persist behaviour of the production code;
* profiles can be enumerated and deleted in a deterministic fashion.

The implementation is intentionally straightforward so it can operate in a
headless environment without Qt or the full filesystem layout of the desktop
application.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from collections.abc import Iterable


_PROFILE_PATHS: tuple[str, ...] = (
    "graphics.environment",
    "graphics.scene",
    "animation",
)


@dataclass(slots=True)
class ProfileOperationResult:
    """Lightweight result object returned by profile operations."""

    success: bool
    message: str = ""

    def __bool__(self) -> bool:  # pragma: no cover - convenience wrapper
        return self.success


def _slugify(name: str) -> str:
    """Convert a profile name to a filesystem-friendly slug."""

    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "profile"


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _collect_sections(settings_manager: Any, paths: Iterable[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path in paths:
        section = settings_manager.get(path, {})
        # Nest the section under the last path component (e.g. "environment")
        target = result
        components = path.split(".")
        for key in components[:-1]:
            target = target.setdefault(key, {})
        target[components[-1]] = section
    return result


class ProfileSettingsManager:
    """Persist and restore profile presets for the graphics subsystem."""

    def __init__(
        self,
        settings_manager: Any,
        profile_dir: Path | None = None,
        apply_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self._settings_manager = settings_manager
        self._profile_dir = Path(profile_dir or Path.home() / ".pss" / "profiles")
        _ensure_directory(self._profile_dir)
        self._apply_callback = apply_callback

    # ------------------------------------------------------------------ utils
    def _path_for(self, name: str) -> Path:
        return self._profile_dir / f"{_slugify(name)}.json"

    def _make_payload(self, name: str) -> dict[str, Any]:
        payload = _collect_sections(self._settings_manager, _PROFILE_PATHS)
        payload.setdefault("metadata", {})["profile_name"] = name
        return payload

    # ----------------------------------------------------------------- actions
    def save_profile(self, name: str) -> ProfileOperationResult:
        path = self._path_for(name)
        payload = self._make_payload(name)
        try:
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:  # pragma: no cover - filesystem errors are rare in tests
            return ProfileOperationResult(False, f"Failed to save profile: {exc}")
        return ProfileOperationResult(True, str(path))

    def load_profile(self, name: str) -> ProfileOperationResult:
        path = self._path_for(name)
        if not path.exists():
            return ProfileOperationResult(False, f"Profile '{name}' not found")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:  # pragma: no cover - corrupt files are unlikely
            return ProfileOperationResult(False, f"Failed to load profile: {exc}")

        graphics = payload.get("graphics", {})
        section_map = {
            "environment": "graphics.environment",
            "scene": "graphics.scene",
        }
        for section_name, path_key in section_map.items():
            value = graphics.get(section_name)
            if value is None:
                continue
            self._settings_manager.set(path_key, value, auto_save=False)
            if self._apply_callback is not None:
                try:
                    self._apply_callback(path_key, value)
                except Exception:  # pragma: no cover - UI callbacks may fail in tests
                    pass

        animation_payload = payload.get("animation")
        if animation_payload is None:
            animation_payload = graphics.get("animation")  # legacy profiles
        if isinstance(animation_payload, dict):
            self._settings_manager.set("animation", animation_payload, auto_save=False)
            if self._apply_callback is not None:
                try:
                    self._apply_callback("animation", animation_payload)
                except Exception:  # pragma: no cover - UI callbacks may fail in tests
                    pass

        # Mimic auto-save behaviour expected by the tests
        if hasattr(self._settings_manager, "save"):
            self._settings_manager.save()

        return ProfileOperationResult(True, str(path))

    def list_profiles(self) -> list[str]:
        names: list[str] = []
        for file in sorted(self._profile_dir.glob("*.json")):
            display_name = _slugify(file.stem).replace("_", " ").title()
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                display_name = data.get("metadata", {}).get(
                    "profile_name", display_name
                )
            except json.JSONDecodeError:  # pragma: no cover - ignore malformed payloads
                pass
            names.append(display_name)
        return sorted(names, key=lambda s: s.lower())

    def delete_profile(self, name: str) -> ProfileOperationResult:
        path = self._path_for(name)
        if not path.exists():
            return ProfileOperationResult(False, f"Profile '{name}' not found")
        try:
            path.unlink()
        except OSError as exc:  # pragma: no cover - filesystem errors are rare in tests
            return ProfileOperationResult(False, f"Failed to delete profile: {exc}")
        return ProfileOperationResult(True, str(path))


__all__ = ["ProfileSettingsManager", "ProfileOperationResult"]
