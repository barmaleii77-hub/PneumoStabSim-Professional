"""Profile-aware settings helpers used by the QML bridge."""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sys
from typing import Any, Callable, Dict, List, Optional

from src.common.qt_compat import QObject, Signal, Slot

try: # pragma: no cover - optional during headless tests
 from typing import TypedDict
except Exception: # pragma: no cover
 TypedDict = dict # type: ignore[misc,assignment]


def _load_environment_schema_module():
 module_name = "pss_environment_schema_core"
 if module_name in sys.modules:
 return sys.modules[module_name]
 module_path = (
 Path(__file__).resolve().parents[2] / "src" / "ui" / "environment_schema.py"
 )
 spec = importlib.util.spec_from_file_location(module_name, module_path)
 if spec is None or spec.loader is None:
 raise ImportError(f"Unable to resolve environment schema at {module_path}")
 module = importlib.util.module_from_spec(spec)
 sys.modules[module_name] = module
 spec.loader.exec_module(module) # type: ignore[attr-defined]
 return module


_schema_module = _load_environment_schema_module()

EnvironmentValidationError = _schema_module.EnvironmentValidationError
validate_environment_settings = _schema_module.validate_environment_settings
validate_scene_settings = _schema_module.validate_scene_settings
validate_animation_settings = _schema_module.validate_animation_settings


class ProfilePayload(TypedDict, total=False): # type: ignore[misc,valid-type]
 name: str
 updated: str
 graphics: Dict[str, Any]


def _default_profile_directory() -> Path:
 return Path(__file__).resolve().parents[2] / "config" / "profiles"


def _sanitize_filename(name: str) -> str:
 normalized = name.strip()
 normalized = re.sub(r"\s+", "_", normalized)
 normalized = re.sub(r"[^A-Za-z0-9_\-]", "", normalized)
 return normalized.lower()


@dataclass
class ProfileOperationResult:
 success: bool
 message: Optional[str] = None


class ProfileSettingsManager(QObject):
 """Manage saving/loading user profile snapshots for graphics settings."""

 profilesChanged = Signal(list)
 profileSaved = Signal(str)
 profileLoaded = Signal(str)
 profileDeleted = Signal(str)
 profileError = Signal(str, str)

 def __init__(
 self,
 settings_manager: Any,
 *,
 apply_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
 profile_dir: Optional[Path] = None,
 ) -> None:
 super().__init__()
 self._settings_manager = settings_manager
 self._apply_callback = apply_callback
 self._profile_dir = profile_dir or _default_profile_directory()
 self._profile_dir.mkdir(parents=True, exist_ok=True)
 self.logger = logging.getLogger(__name__)
 self.logger.debug("ProfileSettingsManager initialized at %s", self._profile_dir)

 # ------------------------------------------------------------------
 # Helpers
 # ------------------------------------------------------------------
 def _profile_path(self, name: str) -> Path:
 safe_name = _sanitize_filename(name)
 if not safe_name:
 raise ValueError("Profile name must contain alphanumeric characters")
 return self._profile_dir / f"{safe_name}.json"

 def _read_profile_file(self, path: Path) -> ProfilePayload:
 with path.open("r", encoding="utf-8") as stream:
 payload = json.load(stream)
 if not isinstance(payload, dict):
 raise ValueError("Profile payload must be a JSON object")
 payload.setdefault("name", path.stem)
 payload.setdefault("updated", datetime.now(UTC).isoformat())
 return payload # type: ignore[return-value]

 def _write_profile_file(self, path: Path, payload: ProfilePayload) -> None:
 tmp_path = path.with_suffix(path.suffix + ".tmp")
 with tmp_path.open("w", encoding="utf-8") as stream:
 json.dump(payload, stream, indent=2, ensure_ascii=False)
 stream.flush()
 try:
 os.fsync(stream.fileno())
 except OSError:
 self.logger.debug("fsync not supported for %s", tmp_path)
 os.replace(tmp_path, path)

 def _emit_profiles(self) -> None:
 self.profilesChanged.emit(self.list_profiles())

 def _apply_section(self, path: str, payload: Dict[str, Any]) -> None:
 if not payload:
 return
 if self._apply_callback is not None:
 self._apply_callback(path, payload)
 else:
 self._settings_manager.set(path, payload, auto_save=True)

 def _gather_current_section(self, section: str) -> Dict[str, Any]:
 raw = self._settings_manager.get(f"graphics.{section}", {}) or {}
 if not isinstance(raw, dict):
 raw = {}
 return raw

 # ------------------------------------------------------------------
 # Qt exposed API
 # ------------------------------------------------------------------
 @Slot(result="QVariantList")
 def listProfiles(self) -> List[str]:
 return self.list_profiles()

 def list_profiles(self) -> List[str]:
 names: List[str] = []
 if not self._profile_dir.exists():
 return names
 for path in sorted(self._profile_dir.glob("*.json")):
 try:
 payload = self._read_profile_file(path)
 names.append(str(payload.get("name", path.stem)))
 except Exception as exc: # pragma: no cover - corrupted profile
 self.logger.warning("Failed to read profile %s: %s", path, exc)
 return names

 @Slot(str, result=bool)
 def saveProfile(self, name: str) -> bool:
 return self.save_profile(name).success

 def save_profile(self, name: str) -> ProfileOperationResult:
 try:
 path = self._profile_path(name)
 except ValueError as exc:
 self.profileError.emit("save", str(exc))
 return ProfileOperationResult(False, str(exc))

 environment = self._gather_current_section("environment")
 scene = self._gather_current_section("scene")
 animation = self._gather_current_section("animation")

 try:
 env_payload = validate_environment_settings(environment)
 except EnvironmentValidationError as exc:
 message = f"Environment validation failed: {exc}"
 self.profileError.emit("save", message)
 self.logger.error(message)
 return ProfileOperationResult(False, message)

 scene_payload = validate_scene_settings(scene)
 animation_payload = validate_animation_settings(animation)

 payload: ProfilePayload = {
 "name": name.strip() or path.stem,
 "updated": datetime.now(UTC).isoformat(),
 "graphics": {
 "environment": env_payload,
 "scene": scene_payload,
 "animation": animation_payload,
 },
 }

 try:
 self._write_profile_file(path, payload)
 except Exception as exc: # pragma: no cover - disk errors
 message = f"Failed to save profile {name}: {exc}"
 self.profileError.emit("save", message)
 self.logger.error(message)
 return ProfileOperationResult(False, message)

 self.logger.info("Profile '%s' saved to %s", name, path)
 self.profileSaved.emit(payload["name"])
 self._emit_profiles()
 return ProfileOperationResult(True)

 @Slot(str, result=bool)
 def loadProfile(self, name: str) -> bool:
 return self.load_profile(name).success

 def load_profile(self, name: str) -> ProfileOperationResult:
 try:
 path = self._profile_path(name)
 except ValueError as exc:
 self.profileError.emit("load", str(exc))
 return ProfileOperationResult(False, str(exc))

 if not path.exists():
 message = f"Profile '{name}' not found"
 self.profileError.emit("load", message)
 return ProfileOperationResult(False, message)

 try:
 payload = self._read_profile_file(path)
 except Exception as exc:
 message = f"Failed to read profile '{name}': {exc}"
 self.profileError.emit("load", message)
 self.logger.error(message)
 return ProfileOperationResult(False, message)

 graphics = payload.get("graphics", {})
 if not isinstance(graphics, dict):
 message = "Profile graphics payload must be a dict"
 self.profileError.emit("load", message)
 return ProfileOperationResult(False, message)

 try:
 env_payload = validate_environment_settings(
 graphics.get("environment", {})
 )
 scene_payload = validate_scene_settings(graphics.get("scene", {}))
 animation_payload = validate_animation_settings(
 graphics.get("animation", {})
 )
 except EnvironmentValidationError as exc:
 message = f"Profile validation failed: {exc}"
 self.profileError.emit("load", message)
 self.logger.error(message)
 return ProfileOperationResult(False, message)

 self._apply_section("graphics.environment", env_payload)
 self._apply_section("graphics.scene", scene_payload)
 self._apply_section("graphics.animation", animation_payload)

 self.logger.info("Profile '%s' loaded", name)
 self.profileLoaded.emit(str(payload.get("name", name)))
 return ProfileOperationResult(True)

 @Slot(str, result=bool)
 def deleteProfile(self, name: str) -> bool:
 return self.delete_profile(name).success

 def delete_profile(self, name: str) -> ProfileOperationResult:
 try:
 path = self._profile_path(name)
 except ValueError as exc:
 self.profileError.emit("delete", str(exc))
 return ProfileOperationResult(False, str(exc))

 if not path.exists():
 message = f"Profile '{name}' not found"
 self.profileError.emit("delete", message)
 return ProfileOperationResult(False, message)

 try:
 path.unlink()
 except Exception as exc: # pragma: no cover - filesystem errors
 message = f"Failed to delete profile '{name}': {exc}"
 self.profileError.emit("delete", message)
 self.logger.error(message)
 return ProfileOperationResult(False, message)

 self.logger.info("Profile '%s' deleted", name)
 self.profileDeleted.emit(name)
 self._emit_profiles()
 return ProfileOperationResult(True)

 @Slot()
 def refresh(self) -> None:
 self._emit_profiles()
