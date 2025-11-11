"""Shared helpers to hydrate default application settings.

This module centralises the logic for constructing a safe configuration payload
when the primary settings file is missing or corrupted.  Both the simplified
``SettingsManager`` used in tests and the production ``SettingsService`` rely on
these helpers to provide deterministic fallbacks that mirror the canonical
baseline stored under ``config/baseline/app_settings.json``.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASELINE_SETTINGS_PATH = PROJECT_ROOT / "config" / "baseline" / "app_settings.json"
_DEFAULT_UNITS_VERSION = "si_v2"


def _timestamp() -> str:
    """Return an ISO-8601 timestamp with millisecond precision."""

    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _empty_payload(*, seed: str = "generated") -> dict[str, Any]:
    """Return a minimal payload containing sane metadata defaults."""

    timestamp = _timestamp()
    return {
        "metadata": {
            "units_version": _DEFAULT_UNITS_VERSION,
            "last_modified": timestamp,
            "defaults_seed": seed,
        },
        "current": {},
        "defaults_snapshot": {},
    }


def load_default_settings_payload() -> dict[str, Any]:
    """Load the canonical default settings payload.

    Preference is given to the baseline payload committed in the repository.
    When that file is not available or fails to parse we fall back to a minimal
    in-memory payload that still exposes the expected top-level sections.
    """

    try:
        raw = BASELINE_SETTINGS_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning(
            "Baseline settings not found at %s; using generated defaults.",
            BASELINE_SETTINGS_PATH,
        )
        return _empty_payload()
    except OSError as exc:
        logger.error(
            "Unable to read baseline settings %s: %s; using generated defaults.",
            BASELINE_SETTINGS_PATH,
            exc,
        )
        return _empty_payload()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(
            "Baseline settings %s contain invalid JSON: %s; using generated defaults.",
            BASELINE_SETTINGS_PATH,
            exc,
        )
        return _empty_payload()

    if not isinstance(payload, dict):
        logger.error(
            "Baseline settings root must be an object (found %s); using generated defaults.",
            type(payload).__name__,
        )
        return _empty_payload()

    fallback = _empty_payload(seed=str(BASELINE_SETTINGS_PATH))

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        payload["metadata"] = metadata = {}
    metadata.setdefault("units_version", _DEFAULT_UNITS_VERSION)
    metadata.setdefault("last_modified", fallback["metadata"]["last_modified"])
    metadata.setdefault("defaults_seed", str(BASELINE_SETTINGS_PATH))

    for section in ("current", "defaults_snapshot"):
        container = payload.get(section)
        if not isinstance(container, dict):
            payload[section] = {}

    return payload

