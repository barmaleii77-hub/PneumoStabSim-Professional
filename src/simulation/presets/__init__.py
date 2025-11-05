"""Training preset catalogue for simulation scenarios."""

from __future__ import annotations

from .library import TrainingPreset, TrainingPresetLibrary, get_default_training_library
from .metadata import TrainingPresetMetadata

__all__ = [
    "TrainingPreset",
    "TrainingPresetLibrary",
    "TrainingPresetMetadata",
    "get_default_training_library",
]
