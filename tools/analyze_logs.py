#!/usr/bin/env python3
"""
Анализ логов графики и событий Python↔QML.

Ищет последний файл logs/graphics/session_*.jsonl и строит сводку:
- всего изменений (parameter_change)
- апдейтов в QML (parameter_update)
- успешных/неуспешных
- изменения без апдейта (no-op кандидаты)
Сохраняет отчёт в logs/graphics/analysis_latest.json
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGS_DIR = Path("logs/graphics")


@dataclass
class Event:
    raw: dict[str, Any]

    @property
    def type(self) -> str:
        return str(self.raw.get("event_type", "")).lower()

    @property
    def parameter(self) -> str:
        return str(self.raw.get("parameter_name") or self.raw.get("parameter") or "")

    @property
    def category(self) -> str:
        return str(self.raw.get("category", ""))

    @property
    def applied(self) -> bool:
        return bool(self.raw.get("applied_to_qml", False))

    @property
    def error(self) -> str | None:
        err = self.raw.get("error")
        return str(err) if err is not None else None


def _latest_session_file(root: Path) -> Path | None:
    if not root.exists():
        return None
    files = sorted(root.glob("session_*.jsonl"))
    return files[-1] if files else None


def _read_jsonl(path: Path) -> list[Event]:
    items: list[Event] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            items.append(Event(payload))
    return items


def analyze_session(path: Path) -> dict[str, Any]:
    events = _read_jsonl(path)

    changes: list[Event] = [e for e in events if e.type == "parameter_change"]
    updates: list[Event] = [e for e in events if e.type == "parameter_update"]

    total_changes = len(changes)
    total_updates = len(updates)

    successful = sum(1 for e in updates if e.applied and not e.error)
    failed = sum(1 for e in updates if e.error)

    # Кандидаты на no-op: изменения, у которых нет последующего parameter_update для того же параметра
    updates_by_param: dict[str, int] = defaultdict(int)
    for u in updates:
        updates_by_param[u.parameter] += 1

    no_op_candidates: list[str] = []
    for c in changes:
        if updates_by_param.get(c.parameter, 0) == 0:
            no_op_candidates.append(c.parameter or "<unknown>")

    result = {
        "session_file": str(path),
        "total_changes": total_changes,
        "total_updates": total_updates,
        "successful_updates": successful,
        "failed_updates": failed,
        "no_op_candidates": sorted(set(no_op_candidates)),
        "no_op_count": len(set(no_op_candidates)),
        "by_category": {},
    }

    # Группировка по категориям
    cat_changes: dict[str, int] = defaultdict(int)
    cat_updates: dict[str, int] = defaultdict(int)
    cat_failed: dict[str, int] = defaultdict(int)

    for c in changes:
        cat_changes[c.category] += 1
    for u in updates:
        cat_updates[u.category] += 1
        if u.error:
            cat_failed[u.category] += 1

    cats = sorted(set(list(cat_changes) + list(cat_updates)))
    for cat in cats:
        result["by_category"][cat] = {
            "changes": cat_changes.get(cat, 0),
            "updates": cat_updates.get(cat, 0),
            "failed": cat_failed.get(cat, 0),
        }

    return result


def main(argv: list[str]) -> int:
    target = _latest_session_file(LOGS_DIR)
    if target is None:
        print("⚠️  Логи не найдены: logs/graphics/session_*.jsonl")
        return 0

    report = analyze_session(target)

    # Печать краткой сводки
    print("═" * 60)
    print("📊 GRAPHICS LOGS ANALYSIS")
    print("═" * 60)
    print(f"Session: {report['session_file']}")
    print(f"Total changes: {report['total_changes']}")
    print(f"Total updates: {report['total_updates']}")
    print(f"Successful: {report['successful_updates']}")
    print(f"Failed: {report['failed_updates']}")
    print(f"No-op candidates: {report['no_op_count']}")

    if report["by_category"]:
        print("\nBy category:")
        for cat, stats in report["by_category"].items():
            print(
                f"  - {cat}: changes={stats['changes']}, updates={stats['updates']}, failed={stats['failed']}"
            )

    # Сохранение отчёта
    out_path = LOGS_DIR / "analysis_latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n💾 Report saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
