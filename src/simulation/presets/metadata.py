"""Metadata structures describing training presets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class TrainingPresetMetadata:
    """Describe the educational intent of a training preset."""

    difficulty: str
    duration_minutes: int
    learning_objectives: Tuple[str, ...] = field(default_factory=tuple)
    recommended_modules: Tuple[str, ...] = field(default_factory=tuple)
    evaluation_metrics: Tuple[str, ...] = field(default_factory=tuple)
    scenario_id: str = ""
    notes: str = ""

    def to_payload(self) -> Dict[str, object]:
        """Return a QML-friendly serialisable payload."""

        return {
            "difficulty": self.difficulty,
            "durationMinutes": self.duration_minutes,
            "learningObjectives": list(self.learning_objectives),
            "recommendedModules": list(self.recommended_modules),
            "evaluationMetrics": list(self.evaluation_metrics),
            "scenarioId": self.scenario_id,
            "notes": self.notes,
        }

    @staticmethod
    def coerce_iterable(items: Iterable[str] | None) -> Tuple[str, ...]:
        if not items:
            return tuple()
        return tuple(str(item) for item in items if str(item).strip())
