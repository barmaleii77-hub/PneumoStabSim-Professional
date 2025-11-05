"""Simulation package.

The package consolidates reusable helpers for configuring and orchestrating
simulation pipelines.  Subpackages expose higher-level building blocks like
training presets.
"""

from __future__ import annotations

from .presets import (
    TrainingPreset,
    TrainingPresetLibrary,
    TrainingPresetMetadata,
    get_default_training_library,
)
from .service import TrainingPresetService

__all__ = [
    "TrainingPreset",
    "TrainingPresetLibrary",
    "TrainingPresetMetadata",
    "get_default_training_library",
    "TrainingPresetService",
]
