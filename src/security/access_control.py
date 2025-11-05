"""Role-based access control and immutable security audit logging."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

__all__ = [
    "AccessControlService",
    "AccessDeniedError",
    "RolePolicy",
    "SecurityAuditLogger",
    "UserRole",
    "get_access_control",
]


class AccessDeniedError(PermissionError):
    """Raised when a role attempts to execute a prohibited action."""


class UserRole(str, Enum):
    """Supported roles within the simulator."""

    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    GUEST = "guest"


@dataclass(frozen=True)
class RolePolicy:
    """Describe the capabilities associated with a role."""

    editable_prefixes: tuple[str, ...]
    ui_flags: Mapping[str, bool]
    simulation_profile: str
    description: str

    def allows_path(self, dotted_path: str) -> bool:
        """Return ``True`` when ``dotted_path`` is editable for this role."""

        if not dotted_path:
            return False
        normalized = dotted_path.strip()
        for prefix in self.editable_prefixes:
            if prefix == "*":
                return True
            if normalized.startswith(prefix):
                return True
        return False


def _serialise_metadata(metadata: Mapping[str, Any] | None) -> Dict[str, Any]:
    if metadata is None:
        return {}

    def _convert(value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, Mapping):
            return {str(key): _convert(val) for key, val in value.items()}
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return [_convert(item) for item in value]
        return repr(value)

    return {str(key): _convert(val) for key, val in metadata.items()}


def _resolve_log_path(path: Optional[Path | str]) -> Path:
    if path is None:
        override = os.environ.get("PSS_SECURITY_AUDIT_LOG")
        if override:
            path = override
        else:
            path = Path("reports") / "security_audit" / "audit.log"
    expanded = Path(path).expanduser()
    expanded.parent.mkdir(parents=True, exist_ok=True)
    return expanded


class SecurityAuditLogger:
    """Append-only audit log that maintains an immutable hash chain."""

    def __init__(self, log_path: Optional[Path | str] = None) -> None:
        self._path = _resolve_log_path(log_path)
        self._lock = threading.RLock()
        self._last_hash = self._load_last_hash()

    # ----------------------------------------------------------------- helpers
    def _load_last_hash(self) -> str:
        if not self._path.exists():
            return ""
        last_line = ""
        try:
            with self._path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped:
                        last_line = stripped
        except OSError:
            return ""
        if not last_line:
            return ""
        try:
            payload = json.loads(last_line)
        except json.JSONDecodeError:
            return ""
        return str(payload.get("hash", ""))

    def _digest(self, previous_hash: str, payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        data = f"{previous_hash}:{canonical}".encode("utf-8")
        return sha256(data).hexdigest()

    # ---------------------------------------------------------------- recording
    def record(
        self,
        action: str,
        actor: str,
        *,
        scope: str,
        allowed: bool,
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        """Append a new entry to the audit log and return the entry hash."""

        timestamp = datetime.now(timezone.utc).isoformat()
        entry: Dict[str, Any] = {
            "timestamp": timestamp,
            "actor": actor or "unknown",
            "action": action,
            "scope": scope,
            "allowed": bool(allowed),
            "metadata": _serialise_metadata(metadata),
        }

        with self._lock:
            previous_hash = self._last_hash
            digest = self._digest(previous_hash, entry)
            entry["previous_hash"] = previous_hash
            entry["hash"] = digest
            try:
                with self._path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except OSError:
                # Logging must never prevent application execution; swallow errors.
                return digest
            self._last_hash = digest
            return digest

    # ----------------------------------------------------------------- analysis
    def verify_chain(self) -> bool:
        """Return ``True`` when the hash chain is valid."""

        previous_hash = ""
        try:
            with self._path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    payload = json.loads(stripped)
                    expected = payload.get("hash")
                    payload_without_hash = {
                        key: value
                        for key, value in payload.items()
                        if key not in {"hash", "previous_hash"}
                    }
                    calculated = self._digest(previous_hash, payload_without_hash)
                    if calculated != expected:
                        return False
                    previous_hash = expected
        except FileNotFoundError:
            return True
        except (OSError, json.JSONDecodeError):
            return False
        return True

    @property
    def path(self) -> Path:
        return self._path


@dataclass
class _AccessProfile:
    role: UserRole
    policy: RolePolicy
    actor: str


class AccessControlService:
    """Evaluate permissions and coordinate immutable security auditing."""

    _DEFAULT_POLICIES: Dict[UserRole, RolePolicy] = {
        UserRole.ADMIN: RolePolicy(
            editable_prefixes=("*",),
            ui_flags={
                "can_edit_all": True,
                "can_edit_simulation": True,
                "can_edit_graphics": True,
                "show_admin_panels": True,
            },
            simulation_profile="full_access",
            description=(
                "Полный доступ ко всем настройкам, включая административные "
                "операции и миграции данных."
            ),
        ),
        UserRole.INSTRUCTOR: RolePolicy(
            editable_prefixes=(
                "current.simulation",
                "current.modes",
                "current.animation",
                "current.graphics.camera",
                "current.graphics.environment",
            ),
            ui_flags={
                "can_edit_all": False,
                "can_edit_simulation": True,
                "can_edit_graphics": True,
                "show_admin_panels": False,
            },
            simulation_profile="instructor_guided",
            description=(
                "Инструктор может настраивать ход тренировки, освещение и "
                "камеру, но не изменяет глобальные параметры приложения."
            ),
        ),
        UserRole.GUEST: RolePolicy(
            editable_prefixes=(),
            ui_flags={
                "can_edit_all": False,
                "can_edit_simulation": False,
                "can_edit_graphics": False,
                "show_admin_panels": False,
            },
            simulation_profile="guest_view_only",
            description=(
                "Гость просматривает симуляцию в режиме витрины без "
                "возможности модифицировать параметры."
            ),
        ),
    }

    def __init__(
        self,
        *,
        audit_logger: Optional[SecurityAuditLogger] = None,
        policies: Optional[Mapping[UserRole, RolePolicy]] = None,
    ) -> None:
        self._logger = audit_logger or SecurityAuditLogger()
        self._policies: Dict[UserRole, RolePolicy] = dict(
            policies or self._DEFAULT_POLICIES
        )
        self._role: UserRole = UserRole.ADMIN
        self._actor: str = "system"
        self._lock = threading.RLock()

    # ----------------------------------------------------------------- metadata
    def set_role(self, role: UserRole, *, actor: Optional[str] = None) -> None:
        with self._lock:
            previous = self._role
            self._role = role
            if actor:
                self._actor = actor
            self._logger.record(
                "role.change",
                self._actor,
                scope="role",
                allowed=True,
                metadata={
                    "previous_role": previous.value,
                    "new_role": role.value,
                },
            )

    def set_actor(self, actor: str) -> None:
        with self._lock:
            self._actor = actor

    def current_role(self) -> UserRole:
        with self._lock:
            return self._role

    def active_policy(self) -> _AccessProfile:
        with self._lock:
            return _AccessProfile(
                role=self._role,
                policy=self._policies[self._role],
                actor=self._actor,
            )

    # ---------------------------------------------------------------- permission
    def can_modify(self, dotted_path: str) -> bool:
        profile = self.active_policy()
        return profile.policy.allows_path(dotted_path)

    def require_permission(self, dotted_path: str, *, intent: str) -> None:
        profile = self.active_policy()
        allowed = profile.policy.allows_path(dotted_path)
        metadata = {
            "role": profile.role.value,
            "intent": intent,
        }
        self._logger.record(
            f"settings.{intent}",
            profile.actor,
            scope=dotted_path,
            allowed=allowed,
            metadata=metadata,
        )
        if not allowed:
            raise AccessDeniedError(
                f"Role '{profile.role.value}' is not permitted to modify '{dotted_path}'"
            )

    # ------------------------------------------------------------------- helpers
    def ui_flags(self) -> Mapping[str, bool]:
        return dict(self.active_policy().policy.ui_flags)

    def simulation_profile(self) -> str:
        return self.active_policy().policy.simulation_profile

    def describe_access_profile(self) -> Dict[str, Any]:
        profile = self.active_policy()
        return {
            "role": profile.role.value,
            "actor": profile.actor,
            "description": profile.policy.description,
            "uiFlags": dict(profile.policy.ui_flags),
            "simulationProfile": profile.policy.simulation_profile,
            "editablePrefixes": list(profile.policy.editable_prefixes),
        }


_access_control_singleton: Optional[AccessControlService] = None
_singleton_lock = threading.Lock()


def get_access_control() -> AccessControlService:
    global _access_control_singleton
    if _access_control_singleton is None:
        with _singleton_lock:
            if _access_control_singleton is None:
                _access_control_singleton = AccessControlService()
    return _access_control_singleton
