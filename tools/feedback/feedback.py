# -*- coding: utf-8 -*-
"""
Система обратной связи
"""
import json
import time
from pathlib import Path
from contextlib import contextmanager


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
            initial_plan = {
                "prompt_id": "POST_PROMPT_1_UI_FIXES",
                "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "microsteps": [],
                "status": "in_progress",
            }
            with open(self.control_plan_path, "w", encoding="utf-8") as f:
                json.dump(initial_plan, f, indent=2, ensure_ascii=False)

    @contextmanager
    def span(self, area_step: str):
        """Контекстный менеджер для трассировки операций"""
        start_time = time.time()
        area, step = (
            area_step.split("/", 1) if "/" in area_step else ("general", area_step)
        )

        # Создаем директории для области
        area_reports = self.reports_dir / area
        area_artifacts = self.artifacts_dir / area
        area_logs = self.logs_dir / area

        for dir_path in [area_reports, area_artifacts, area_logs]:
            dir_path.mkdir(parents=True, exist_ok=True)

        print(f"Начинаю {area}/{step}...")

        try:
            yield {
                "reports_dir": area_reports,
                "artifacts_dir": area_artifacts,
                "logs_dir": area_logs,
                "area": area,
                "step": step,
            }

            duration = time.time() - start_time
            status = "completed"
            print(f"{area}/{step} завершен за {duration:.2f}с")

        except Exception as e:
            duration = time.time() - start_time
            status = "failed"
            print(f"{area}/{step} failed: {e}")
            raise

        finally:
            # Обновляем план управления
            self._update_control_plan(area, step, status, duration)

    def _update_control_plan(self, area: str, step: str, status: str, duration: float):
        with open(self.control_plan_path, "r", encoding="utf-8") as f:
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

        plan["microsteps"].append(step_info)

        with open(self.control_plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)


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
