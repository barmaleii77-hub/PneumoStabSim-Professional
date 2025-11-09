"""Controller coordinating panel state, presets and undo/redo flows."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable, Mapping

from .history import HistoryCommand, HistoryStack

StateMapping = Mapping[str, Any]
Listener = Callable[[dict[str, Any], dict[str, Any]], None]


def _deep_merge(base: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deep copy of *base* updated with *patch*."""

    merged: dict[str, Any] = {key: deepcopy(value) for key, value in base.items()}
    for key, value in patch.items():
        if (
            key in merged
            and isinstance(merged[key], Mapping)
            and isinstance(value, Mapping)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


class SettingsSyncController:
    """Centralise panel state updates, history tracking and listeners."""

    def __init__(
        self,
        initial_state: StateMapping | None = None,
        *,
        history: HistoryStack | None = None,
    ) -> None:
        self._state: dict[str, Any] = (
            deepcopy(initial_state) if initial_state is not None else {}
        )
        self._history = history or HistoryStack()
        self._listeners: set[Listener] = set()

    # ----------------------------------------------------------------- listeners
    def register_listener(self, callback: Listener) -> Callable[[], None]:
        self._listeners.add(callback)

        def _unsubscribe() -> None:
            self._listeners.discard(callback)

        return _unsubscribe

    def _notify(self, context: dict[str, Any]) -> None:
        snapshot = self.snapshot()
        for callback in list(self._listeners):
            callback(snapshot, dict(context))

    # -------------------------------------------------------------------- helpers
    def snapshot(self) -> dict[str, Any]:
        """Return a deep copy of the current state."""

        return deepcopy(self._state)

    def bootstrap(
        self,
        state: StateMapping | None,
        *,
        notify: bool = True,
        origin: str = "bootstrap",
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Reset the controller state without recording history."""

        self._state = deepcopy(state) if state is not None else {}
        self._history.clear()
        context: dict[str, Any] = {"origin": origin, "description": "bootstrap"}
        if metadata:
            context.update(dict(metadata))
        if notify:
            self._notify(context)
        return self.snapshot()

    # ------------------------------------------------------------------- mutations
    def _record_command(
        self,
        *,
        before: dict[str, Any],
        after: dict[str, Any],
        description: str,
        metadata: Mapping[str, Any] | None,
    ) -> None:
        meta = dict(metadata or {})
        command = HistoryCommand(
            before=before, after=after, description=description, metadata=meta
        )
        self._history.record(command)

    def apply_state(
        self,
        state: StateMapping,
        *,
        description: str,
        source: str | None = None,
        origin: str = "external",
        record: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Replace the entire state and optionally append a history command."""

        before = self.snapshot()
        self._state = deepcopy(state)
        after = self.snapshot()
        if record:
            extra_meta = dict(metadata or {})
            if source is not None:
                extra_meta.setdefault("source", source)
            extra_meta.setdefault("origin", origin)
            self._record_command(
                before=before, after=after, description=description, metadata=extra_meta
            )
        context: dict[str, Any] = {"origin": origin, "description": description}
        if source is not None:
            context["source"] = source
        if metadata:
            context.update(dict(metadata))
        self._notify(context)
        return after

    def apply_patch(
        self,
        patch: Mapping[str, Any],
        *,
        description: str,
        source: str | None = None,
        origin: str = "local",
        record: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Merge *patch* into the state and optionally record history."""

        before = self.snapshot()
        self._state = _deep_merge(before, patch)
        after = self.snapshot()
        if record:
            extra_meta = dict(metadata or {})
            if source is not None:
                extra_meta.setdefault("source", source)
            extra_meta.setdefault("origin", origin)
            self._record_command(
                before=before, after=after, description=description, metadata=extra_meta
            )
        context: dict[str, Any] = {"origin": origin, "description": description}
        if source is not None:
            context["source"] = source
        if metadata:
            context.update(dict(metadata))
        self._notify(context)
        return after

    # --------------------------------------------------------------------- history
    def undo(self) -> HistoryCommand | None:
        command = self._history.undo()
        if command is None:
            return None
        self._state = deepcopy(command.before)
        context = dict(command.metadata)
        context.setdefault("origin", "undo")
        context.setdefault("description", command.description)
        self._notify(context)
        return command

    def redo(self) -> HistoryCommand | None:
        command = self._history.redo()
        if command is None:
            return None
        self._state = deepcopy(command.after)
        context = dict(command.metadata)
        context.setdefault("origin", "redo")
        context.setdefault("description", command.description)
        self._notify(context)
        return command

    def clear_history(self) -> None:
        self._history.clear()

    def can_undo(self) -> bool:
        return self._history.can_undo()

    def can_redo(self) -> bool:
        return self._history.can_redo()

    # ---------------------------------------------------------------- convenience
    def update_many(
        self,
        updates: Iterable[tuple[str, Any]],
        *,
        description: str,
        origin: str = "local",
        record: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Helper to merge a sequence of ``(key, value)`` pairs."""

        patch: dict[str, Any] = {}
        for key, value in updates:
            patch[key] = value
        return self.apply_patch(
            patch,
            description=description,
            origin=origin,
            record=record,
            metadata=metadata,
        )


__all__ = ["SettingsSyncController"]
