"""Service layer entry points exposed to the UI and CLI tools."""

from __future__ import annotations

from .feedback_service import (
    FeedbackPayload,
    FeedbackService,
    FeedbackSubmissionResult,
)

__all__ = [
    "FeedbackPayload",
    "FeedbackService",
    "FeedbackSubmissionResult",
]
