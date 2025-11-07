"""Feedback intake and analytics service.

The feedback module is responsible for accepting structured reports from the
UI, persisting them to disk so that offline testers do not lose context, and
maintaining lightweight analytics that power daily status summaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections.abc import MutableMapping

_DEFAULT_STORAGE_DIR = Path(__file__).resolve().parents[2] / "reports" / "feedback"


@dataclass(frozen=True)
class FeedbackPayload:
    """Normalised payload that arrives from the UI."""

    title: str
    description: str
    category: str
    severity: str
    contact: str | None = None
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return a serialisable representation of the payload."""

        payload = {
            "title": self.title.strip(),
            "description": self.description.strip(),
            "category": self.category.strip() or "unspecified",
            "severity": self.severity.strip() or "unspecified",
        }
        if self.contact:
            payload["contact"] = self.contact.strip()

        metadata: dict[str, Any] = {}
        for key, value in (self.metadata or {}).items():
            if not key:
                continue
            try:
                json.dumps(value)
            except (TypeError, ValueError):
                continue
            metadata[str(key)] = value

        if metadata:
            payload["metadata"] = metadata

        return payload


@dataclass(frozen=True)
class FeedbackSubmissionResult:
    """Result returned after a feedback payload has been persisted."""

    submission_id: str
    created_at: datetime
    storage_path: Path

    def as_dict(self) -> dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "created_at": self.created_at.isoformat(),
            "storage_path": str(self.storage_path),
        }


class FeedbackService:
    """Persist feedback reports and maintain analytics summaries."""

    _INBOX_FILE = "inbox.jsonl"
    _SUMMARY_JSON = "summary.json"
    _SUMMARY_MARKDOWN = "summary.md"

    INBOX_FILENAME = _INBOX_FILE
    SUMMARY_JSON_FILENAME = _SUMMARY_JSON
    SUMMARY_MARKDOWN_FILENAME = _SUMMARY_MARKDOWN

    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = Path(storage_dir or _DEFAULT_STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Submission lifecycle
    # ------------------------------------------------------------------
    def submit_feedback(self, payload: FeedbackPayload) -> FeedbackSubmissionResult:
        """Store a feedback payload and update analytics."""

        normalised = payload.as_dict()
        submission_id = uuid.uuid4().hex
        timestamp = datetime.now(timezone.utc)

        record = {
            "submission_id": submission_id,
            "created_at": timestamp.isoformat(),
            **normalised,
        }

        inbox_path = self.storage_dir / self._INBOX_FILE

        with self._lock:
            with inbox_path.open("a", encoding="utf-8") as handle:
                json_record = json.dumps(record, ensure_ascii=False)
                handle.write(json_record + "\n")

            self._refresh_summary()

        return FeedbackSubmissionResult(
            submission_id=submission_id,
            created_at=timestamp,
            storage_path=inbox_path,
        )

    def refresh_summary(self) -> None:
        """Public helper to regenerate analytics artefacts."""

        with self._lock:
            self._refresh_summary()

    # ------------------------------------------------------------------
    # Analytics helpers
    # ------------------------------------------------------------------
    def _refresh_summary(self) -> None:
        """Recalculate analytics artefacts for dashboard consumption."""

        entries = self._iter_entries()
        totals = {
            "reports": len(entries),
            "categories": {},
            "severity": {},
        }

        newest_at: datetime | None = None

        for entry in entries:
            category = entry.get("category", "unspecified") or "unspecified"
            severity = entry.get("severity", "unspecified") or "unspecified"

            totals["categories"][category] = totals["categories"].get(category, 0) + 1
            totals["severity"][severity] = totals["severity"].get(severity, 0) + 1

            created_raw = entry.get("created_at")
            if created_raw:
                try:
                    created_at = datetime.fromisoformat(created_raw)
                except ValueError:
                    continue
                if newest_at is None or created_at > newest_at:
                    newest_at = created_at

        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "totals": totals,
            "last_submission_at": newest_at.isoformat() if newest_at else None,
        }

        summary_path = self.storage_dir / self._SUMMARY_JSON
        markdown_path = self.storage_dir / self._SUMMARY_MARKDOWN

        with summary_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)

        markdown_lines = self._build_markdown_summary(summary)
        with markdown_path.open("w", encoding="utf-8") as handle:
            handle.write("\n".join(markdown_lines) + "\n")

    def _iter_entries(self) -> list[dict[str, Any]]:
        inbox_path = self.storage_dir / self._INBOX_FILE
        if not inbox_path.exists():
            return []

        entries: list[dict[str, Any]] = []
        with inbox_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                entries.append(data)
        return entries

    @staticmethod
    def _build_markdown_summary(summary: dict[str, Any]) -> list[str]:
        totals = summary.get("totals", {}) or {}
        categories = totals.get("categories", {}) or {}
        severity = totals.get("severity", {}) or {}

        lines = ["# Feedback summary", ""]
        lines.append(f"_Generated at_: {summary.get('generated_at', 'unknown')}")
        last_submission_at = summary.get("last_submission_at") or "—"
        lines.append(f"_Last submission_: {last_submission_at}")
        lines.append("")
        lines.append(f"**Total reports:** {totals.get('reports', 0)}")
        lines.append("")

        def _emit_table(title: str, mapping: dict[str, Any]) -> None:
            lines.append(f"## {title}")
            if not mapping:
                lines.append("Нет данных")
                lines.append("")
                return
            lines.append("| Значение | Количество |")
            lines.append("| --- | ---: |")
            for key, count in sorted(
                mapping.items(), key=lambda item: (-item[1], item[0])
            ):
                lines.append(f"| {key} | {count} |")
            lines.append("")

        _emit_table("Категории", categories)
        _emit_table("Критичность", severity)

        return lines


__all__ = [
    "FeedbackPayload",
    "FeedbackService",
    "FeedbackSubmissionResult",
]
