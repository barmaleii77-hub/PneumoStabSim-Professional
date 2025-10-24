"""Profile management helpers built on top of the settings service."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol


class SupportsSettings(Protocol):
    """Protocol describing the subset of the legacy settings manager API we rely on."""

    def get(self, path: str, default: Any | None = None) -> Any:  # pragma: no cover - protocol
        ...

    def set(self, path: str, value: Any, auto_save: bool = True) -> bool:  # pragma: no cover - protocol
        ...

    def save(self) -> bool:  # pragma: no cover - protocol
        ...


@dataclass(slots=True)
class ProfileOperationResult:
    """Container describing the outcome of a profile operation."""

    success: bool
    message: str | None = None


class ProfileSettingsManager:
    """Persist and restore named graphics profiles for the simulation."""

    def __init__(self, settings: SupportsSettings, *, profile_dir: Path | None = None) -> None:
        self._settings = settings
        self._profile_dir = (profile_dir or Path.cwd() / "profiles").expanduser().resolve()
        self._profile_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def save_profile(self, name: str) -> ProfileOperationResult:
        slug = self._slugify(name)
        if not slug:
            return ProfileOperationResult(False, "Profile name must contain alphanumeric characters")

        payload = self._build_payload(name)
        path = self._profile_dir / f"{slug}.json"

        try:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            return ProfileOperationResult(False, f"Failed to write profile: {exc}")

        return ProfileOperationResult(True, None)

    def load_profile(self, name: str) -> ProfileOperationResult:
        slug = self._slugify(name)
        if not slug:
            return ProfileOperationResult(False, "Profile name must contain alphanumeric characters")

        path = self._profile_dir / f"{slug}.json"
        if not path.exists():
            return ProfileOperationResult(False, "Profile does not exist")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return ProfileOperationResult(False, f"Failed to read profile: {exc}")

        graphics = payload.get("graphics", {})
        for key in ("environment", "scene", "animation"):
            if key in graphics:
                self._settings.set(f"graphics.{key}", graphics[key], auto_save=False)

        self._settings.save()
        return ProfileOperationResult(True, None)

    def list_profiles(self) -> list[str]:
        names: list[str] = []
        for path in sorted(self._profile_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            name = payload.get("name")
            if isinstance(name, str) and name.strip():
                names.append(name)
            else:
                names.append(self._deslugify(path.stem))

        return sorted(dict.fromkeys(names))

    def delete_profile(self, name: str) -> ProfileOperationResult:
        slug = self._slugify(name)
        if not slug:
            return ProfileOperationResult(False, "Profile name must contain alphanumeric characters")

        path = self._profile_dir / f"{slug}.json"
        if not path.exists():
            return ProfileOperationResult(False, "Profile does not exist")

        try:
            path.unlink()
        except OSError as exc:
            return ProfileOperationResult(False, f"Failed to delete profile: {exc}")

        return ProfileOperationResult(True, None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_payload(self, name: str) -> dict[str, Any]:
        return {
            "name": name,
            "graphics": {
                key: self._settings.get(f"graphics.{key}") for key in self._graphics_keys()
            },
        }

    @staticmethod
    def _graphics_keys() -> Iterable[str]:
        return ("environment", "scene", "animation")

    @staticmethod
    def _slugify(name: str) -> str:
        return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", name.lower())).strip("_")

    @staticmethod
    def _deslugify(slug: str) -> str:
        parts = [part for part in slug.split("_") if part]
        return " ".join(part.capitalize() for part in parts) if parts else slug


__all__ = [
    "ProfileSettingsManager",
    "ProfileOperationResult",
]
