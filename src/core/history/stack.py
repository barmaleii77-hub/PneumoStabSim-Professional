"""Undo/redo primitives shared by UI panels."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class HistoryCommand:
    """Snapshot of a state transition stored in :class:`HistoryStack`."""

    before: dict[str, Any]
    after: dict[str, Any]
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


class HistoryStack:
    """Bounded undo/redo stack used by :class:`SettingsSyncController`."""

    def __init__(self, *, limit: int = 100) -> None:
        self._limit = max(1, int(limit))
        self._undo: list[HistoryCommand] = []
        self._redo: list[HistoryCommand] = []

    # ------------------------------------------------------------------ helpers
    def _enforce_limit(self) -> None:
        if len(self._undo) > self._limit:
            # Keep the newest commands; discard oldest entries.
            del self._undo[: len(self._undo) - self._limit]

    # ------------------------------------------------------------------ recording
    def record(self, command: HistoryCommand) -> None:
        """Append *command* to the undo stack and clear redo history."""

        self._undo.append(command)
        self._enforce_limit()
        self._redo.clear()

    # --------------------------------------------------------------------- query
    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    # ------------------------------------------------------------------- actions
    def undo(self) -> HistoryCommand | None:
        """Pop the latest command and stage it for redo."""

        if not self._undo:
            return None
        command = self._undo.pop()
        self._redo.append(command)
        return command

    def redo(self) -> HistoryCommand | None:
        """Re-apply the most recent undone command."""

        if not self._redo:
            return None
        command = self._redo.pop()
        self._undo.append(command)
        return command

    # ------------------------------------------------------------------- cleanup
    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()


__all__ = ["HistoryCommand", "HistoryStack"]
