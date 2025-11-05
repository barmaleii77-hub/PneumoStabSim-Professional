"""Training preset catalogue for simulation scenarios."""

from __future__ import annotations

from .library import TrainingPreset, TrainingPresetLibrary, get_default_training_library
from .metadata import TrainingPresetMetadata
from .scenarios import SCENARIO_INDEX, ScenarioDescriptor

__all__ = [
    "TrainingPreset",
    "TrainingPresetLibrary",
    "TrainingPresetMetadata",
    "ScenarioDescriptor",
    "SCENARIO_INDEX",
    "get_default_training_library",
]
