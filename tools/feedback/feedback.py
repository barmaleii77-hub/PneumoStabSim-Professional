"""Примитивная система обратной связи для микрошагов проекта."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class FeedbackSystem:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.reports_dir = self.base_dir / "reports"
        self.artifacts_dir = self.base_dir / "artifacts"
        self.logs_dir = self.base_dir / "logs"

        # Создаем необходимые директории
        for dir_path in [self.reports_dir, self.artifacts_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        self.control_plan_path = self.reports_dir / "feedback" / "CONTROL_PLAN.json"
        self.control_plan_path.parent.mkdir(parents=True, exist_ok=True)

        # Инициализируем план управления если его нет
        self._init_control_plan()

    def _init_control_plan(self):
        if not self.control_plan_path.exists():
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            initial_plan = {
                "prompt_id": "POST_PROMPT_1_UI_FIXES",
                "start_time": timestamp,
                "current_time": timestamp,
                "microsteps": [],
                "status": "in_progress",
            }
            with open(self.control_plan_path, "w", encoding="utf-8") as f:
                json.dump(initial_plan, f, indent=2, ensure_ascii=False)

    @contextmanager
    def span(self, area_step: str):
        """Контекстный менеджер для трассировки операций."""

        start_time = time.time()
        area, step = (
            area_step.split("/", 1) if "/" in area_step else ("general", area_step)
        )

        area_reports = self.reports_dir / area
        area_artifacts = self.artifacts_dir / area
        area_logs = self.logs_dir / area

        for dir_path in (area_reports, area_artifacts, area_logs):
            dir_path.mkdir(parents=True, exist_ok=True)

        print(f"Начинаю {area}/{step}...")

        details: dict[str, Any] = {}

        def record_details(**metadata: Any) -> None:
            for key, value in metadata.items():
                if value is None:
                    details.pop(key, None)
                else:
                    details[key] = value

        span_payload: dict[str, Any] = {
            "reports_dir": area_reports,
            "artifacts_dir": area_artifacts,
            "logs_dir": area_logs,
            "area": area,
            "step": step,
            "record_details": record_details,
            "metadata": details,
        }

        try:
            yield span_payload
        except Exception as exc:  # pragma: no cover - handled for reporting only
            duration = time.time() - start_time
            print(f"{area}/{step} failed: {exc}")
            self._update_control_plan(area, step, "failed", duration, details)
            raise
        else:
            duration = time.time() - start_time
            print(f"{area}/{step} завершен за {duration:.2f}с")
            self._update_control_plan(area, step, "completed", duration, details)

    def _update_control_plan(
        self,
        area: str,
        step: str,
        status: str,
        duration: float,
        details: dict[str, Any],
    ) -> None:
        with open(self.control_plan_path, encoding="utf-8") as f:
            plan = json.load(f)

        step_info = {
            "area": area,
            "step": step,
            "status": status,
            "duration_sec": round(duration, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "artifacts": {
                "reports": f"reports/{area}/",
                "artifacts": f"artifacts/{area}/",
                "logs": f"logs/{area}/",
            },
        }

        if details:
            step_info.update(details)

        plan.setdefault("microsteps", []).append(step_info)
        plan["current_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        plan["status"] = self._derive_overall_status(plan["microsteps"])

        with open(self.control_plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

    def _derive_overall_status(self, microsteps: list[dict[str, Any]]) -> str:
        if not microsteps:
            return "in_progress"

        if any(step.get("status") == "failed" for step in microsteps):
            return "attention_required"

        if all(step.get("status") == "completed" for step in microsteps):
            return "ready_for_acceptance"

        return "in_progress"


# Global instance
_feedback_instance = None


def init_feedback(base_dir: str = ".") -> FeedbackSystem:
    """Инициализация системы обратной связи"""
    global _feedback_instance
    if _feedback_instance is None:
        _feedback_instance = FeedbackSystem(base_dir)
    return _feedback_instance


def get_feedback() -> FeedbackSystem:
    """Получить существующий экземпляр системы обратной связи"""
    global _feedback_instance
    if _feedback_instance is None:
        _feedback_instance = init_feedback()
    return _feedback_instance
