"""Qt-aware wrapper around :class:`ProfileSettingsManager` for QML."""

from __future__ import annotations

from typing import List

from src.common.qt_compat import QObject, Signal, Slot
from src.core.settings_manager import ProfileSettingsManager, ProfileOperationResult


class ProfileService(QObject):
    """Expose profile management operations to QML via Qt signals/slots."""

    profilesChanged = Signal(list)
    profileSaved = Signal(str)
    profileLoaded = Signal(str)
    profileDeleted = Signal(str)
    profileError = Signal(str, str)

    def __init__(self, manager: ProfileSettingsManager) -> None:
        super().__init__()
        self._manager = manager

    def _emit_profiles(self) -> List[str]:
        names = self._safe_list_profiles()
        self.profilesChanged.emit(names)
        return names

    def _safe_list_profiles(self) -> List[str]:
        try:
            return list(self._manager.list_profiles())
        except Exception as exc:  # pragma: no cover - defensive guard for UI runtime
            self.profileError.emit("list", str(exc))
            return []

    def _handle_operation(
        self, result: ProfileOperationResult, *, operation: str, profile: str
    ) -> bool:
        if result:
            if operation == "save":
                self.profileSaved.emit(profile)
            elif operation == "load":
                self.profileLoaded.emit(profile)
            elif operation == "delete":
                self.profileDeleted.emit(profile)
            self._emit_profiles()
            return True

        self.profileError.emit(operation, result.message)
        return False

    @Slot(result=list)
    def listProfiles(self) -> List[str]:
        """Return available profile names without emitting signals."""

        return self._safe_list_profiles()

    @Slot(result=list)
    def refresh(self) -> List[str]:
        """Refresh the cached list and notify listeners."""

        return self._emit_profiles()

    @Slot(str, result=bool)
    def saveProfile(self, name: str) -> bool:
        result = self._manager.save_profile(name)
        return self._handle_operation(result, operation="save", profile=name)

    @Slot(str, result=bool)
    def loadProfile(self, name: str) -> bool:
        result = self._manager.load_profile(name)
        return self._handle_operation(result, operation="load", profile=name)

    @Slot(str, result=bool)
    def deleteProfile(self, name: str) -> bool:
        result = self._manager.delete_profile(name)
        return self._handle_operation(result, operation="delete", profile=name)


__all__ = ["ProfileService"]
