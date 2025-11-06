#!/usr/bin/env python3
# ruff: noqa
"""Manual helper to verify the centralized settings save pipeline.

The script inspects the current ``app_settings.json`` payload and reports
whether the key panels expose ``collect_state``.  It does not modify any
project files – its output is purely informational and intended for
interactive troubleshooting sessions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.common.settings_manager import SettingsManager

try:  # Optional in environments without Qt libraries
    from src.ui import panels
except Exception as exc:  # pragma: no cover - manual diagnostics
    panels = None  # type: ignore[assignment]
    PANELS_IMPORT_ERROR = exc
else:
    PANELS_IMPORT_ERROR = None


PANEL_EXPORTS = (
    "GraphicsPanel",
    "GeometryPanel",
    "PneumoPanel",
    "ModesPanel",
)


def _panel_status() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if panels is None:
        results.append(
            {
                "panel": "*",
                "status": "unavailable",
                "detail": f"Qt panels could not be imported: {PANELS_IMPORT_ERROR}",
            }
        )
        return results

    for name in PANEL_EXPORTS:
        try:
            panel_cls = getattr(panels, name)
        except Exception as exc:  # pragma: no cover - manual diagnostics
            results.append(
                {
                    "panel": name,
                    "status": "import-error",
                    "detail": str(exc),
                }
            )
            continue

        has_collect = hasattr(panel_cls, "collect_state")
        detail = "collect_state available" if has_collect else "collect_state missing"
        results.append(
            {
                "panel": name,
                "status": "ready" if has_collect else "incomplete",
                "detail": detail,
            }
        )
    return results


def _settings_summary(manager: SettingsManager) -> dict[str, Any]:
    categories: dict[str, Any] = {}
    for category in ("graphics", "geometry", "pneumatic", "modes"):
        payload = manager.get_category(category)
        if payload is None:
            categories[category] = "missing"
        elif payload:
            categories[category] = "loaded"
        else:
            categories[category] = "empty"

    summary = {
        "settings_file": str(Path(manager.settings_file)),
        "units_version": manager.get_units_version(),
        "is_dirty": manager.is_dirty,
        "categories": categories,
    }
    return summary


def main() -> None:
    manager = SettingsManager()
    summary = _settings_summary(manager)
    status_report = {
        "settings": summary,
        "panels": _panel_status(),
    }

    print(json.dumps(status_report, indent=2, ensure_ascii=False))


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()
