"""CLI utilities for synchronising feedback reports with remote trackers."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, MutableMapping, Optional

import requests

from src.services import FeedbackService


@dataclass
class FeedbackRecord:
    submission_id: str
    created_at: str
    title: str
    description: str
    category: str
    severity: str
    contact: Optional[str]
    metadata: MutableMapping[str, object]

    @classmethod
    def from_dict(cls, payload: MutableMapping[str, object]) -> "FeedbackRecord":
        return cls(
            submission_id=str(payload.get("submission_id")),
            created_at=str(payload.get("created_at")),
            title=str(payload.get("title", "")),
            description=str(payload.get("description", "")),
            category=str(payload.get("category", "unspecified")),
            severity=str(payload.get("severity", "unspecified")),
            contact=payload.get("contact") or None,
            metadata=dict(payload.get("metadata", {}) or {}),
        )


def _load_inbox(storage_dir: Path) -> List[FeedbackRecord]:
    inbox_path = storage_dir / FeedbackService.INBOX_FILENAME
    if not inbox_path.exists():
        return []

    records: List[FeedbackRecord] = []
    with inbox_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            records.append(FeedbackRecord.from_dict(payload))
    return records


def _load_sent(storage_dir: Path) -> set[str]:
    sent_path = storage_dir / "sent.log"
    if not sent_path.exists():
        return set()

    with sent_path.open("r", encoding="utf-8") as handle:
        return {line.strip() for line in handle if line.strip()}


def _append_sent(storage_dir: Path, submission_id: str) -> None:
    sent_path = storage_dir / "sent.log"
    with sent_path.open("a", encoding="utf-8") as handle:
        handle.write(submission_id + "\n")


def _prepare_payload(record: FeedbackRecord) -> MutableMapping[str, object]:
    return {
        "title": record.title,
        "body": record.description,
        "labels": ["feedback", record.category, record.severity],
        "metadata": {
            "submission_id": record.submission_id,
            "contact": record.contact,
            **record.metadata,
        },
    }


def _push_records(records: Iterable[FeedbackRecord], *, dry_run: bool) -> List[str]:
    endpoint = os.environ.get("FEEDBACK_SYNC_ENDPOINT")
    token = os.environ.get("FEEDBACK_SYNC_TOKEN")

    if not endpoint:
        if dry_run:
            endpoint = "dry-run"
        else:
            raise RuntimeError("FEEDBACK_SYNC_ENDPOINT env variable is not configured")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    processed: List[str] = []
    for record in records:
        payload = _prepare_payload(record)
        if dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            print("-- dry-run --")
            processed.append(record.submission_id)
            continue

        response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        if response.status_code // 100 != 2:
            raise RuntimeError(
                f"Failed to push feedback {record.submission_id}: {response.status_code} {response.text}"
            )

        processed.append(record.submission_id)

    return processed


def run_push(storage_dir: Path, *, dry_run: bool) -> None:
    records = _load_inbox(storage_dir)
    already_sent = _load_sent(storage_dir)

    pending = [record for record in records if record.submission_id not in already_sent]
    if not pending:
        print("No new feedback to push.")
        return

    processed = _push_records(pending, dry_run=dry_run)
    if dry_run:
        return

    for submission_id in processed:
        _append_sent(storage_dir, submission_id)

    FeedbackService(storage_dir).refresh_summary()
    print(f"Pushed {len(processed)} feedback reports.")


def run_summary(storage_dir: Path) -> None:
    service = FeedbackService(storage_dir)
    service.refresh_summary()
    summary_path = storage_dir / FeedbackService.SUMMARY_JSON_FILENAME
    if summary_path.exists():
        print(summary_path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--storage",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "reports" / "feedback",
        help="Directory containing feedback inbox artefacts.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    push_parser = subparsers.add_parser(
        "push", help="Push pending reports to the tracker"
    )
    push_parser.add_argument(
        "--dry-run", action="store_true", help="Do not perform network calls"
    )

    subparsers.add_parser("summary", help="Regenerate analytics summaries")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    storage_dir: Path = args.storage
    storage_dir.mkdir(parents=True, exist_ok=True)

    try:
        if args.command == "push":
            run_push(storage_dir, dry_run=args.dry_run)
        elif args.command == "summary":
            run_summary(storage_dir)
        else:  # pragma: no cover - defensive branch
            parser.print_help()
            return 1
    except Exception as exc:
        now = datetime.now(timezone.utc).isoformat()
        print(f"[{now}] Feedback sync failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
