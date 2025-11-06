"""Expose a Qt friendly controller for the feedback form."""

from __future__ import annotations

import logging
from typing import Any, Mapping, MutableMapping

from PySide6.QtCore import QObject, Signal, Slot

try:  # pragma: no cover - runtime availability depends on Qt build
    from PySide6.QtCore import QVariant as _QtVariant  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - Qt 6.10 removed direct QVariant export
    _QtVariant = None

from src.services import FeedbackPayload, FeedbackService

_LOGGER = logging.getLogger(__name__)


class FeedbackController(QObject):
    """Qt bridge that forwards QML form submissions to the service layer."""

    submissionAccepted = Signal(dict)
    submissionFailed = Signal(str)

    def __init__(
        self,
        service: FeedbackService | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service or FeedbackService()

    @Slot(str, str, str, str, str, "QVariant", result="QVariant")
    def submitFeedback(
        self,
        title: str,
        description: str,
        category: str,
        severity: str,
        contact: str,
        metadata: QVariant,
    ) -> MutableMapping[str, Any]:
        """Submit a feedback report coming from QML."""

        try:
            metadata_payload: Mapping[str, Any]
            candidate: Any = metadata
            if _QtVariant is not None and isinstance(candidate, _QtVariant):
                candidate = candidate.value()
            elif hasattr(candidate, "value") and callable(getattr(candidate, "value")):
                candidate = candidate.value()

            if isinstance(candidate, Mapping):
                metadata_payload = candidate
            else:
                metadata_payload = {}

            payload = FeedbackPayload(
                title=title,
                description=description,
                category=category,
                severity=severity,
                contact=contact or None,
                metadata=dict(metadata_payload),
            )

            result = self._service.submit_feedback(payload)
        except Exception as exc:  # pragma: no cover - defensive logging path
            message = f"Не удалось отправить отзыв: {exc}"
            _LOGGER.exception(message)
            self.submissionFailed.emit(message)
            return {"ok": False, "error": str(exc)}

        response: MutableMapping[str, Any] = result.as_dict()
        response["ok"] = True
        self.submissionAccepted.emit(dict(response))
        return response


__all__ = ["FeedbackController"]
