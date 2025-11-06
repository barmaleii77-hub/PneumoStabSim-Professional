#!/usr/bin/env python3
"""Run PneumoStabSim across RHI backends with post-effect toggles."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports" / "graphics"
DEFAULT_CACHE_ROOT = PROJECT_ROOT / "logs" / "shader_cache"
SETTINGS_TEMPLATE = PROJECT_ROOT / "config" / "app_settings.json"

POST_EFFECT_KEYS = (
    ("current", "graphics", "effects", "bloom_enabled"),
    ("current", "graphics", "effects", "depth_of_field"),
    ("current", "graphics", "effects", "motion_blur"),
    ("current", "graphics", "environment", "ao_enabled"),
)

KNOWN_ERROR_SUBSTRINGS: tuple[str, ...] = (
    "QML initialisation issue (status-missing): _qquick_widget",
    "QML load failed: QML load errors",
)


@dataclass(frozen=True)
class BackendConfig:
    name: str
    env_overrides: dict[str, str]


BACKENDS: tuple[BackendConfig, ...] = (
    BackendConfig("opengl", {"QSG_RHI_BACKEND": "opengl"}),
    BackendConfig("angle", {"QSG_RHI_BACKEND": "angle", "QT_OPENGL": "angle"}),
    BackendConfig("vulkan", {"QSG_RHI_BACKEND": "vulkan"}),
)


MODES: tuple[str, ...] = ("effects_on", "effects_off")


class SweepError(RuntimeError):
    """Raised when one or more runs fail."""


def load_settings_template() -> dict:
    payload = json.loads(SETTINGS_TEMPLATE.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):  # pragma: no cover - defensive only
        raise ValueError("Settings template is not a JSON object")
    return payload


def set_nested(payload: dict, path: Iterable[str], value: bool) -> None:
    node = payload
    *parents, leaf_key = tuple(path)
    for key in parents:
        node = node.setdefault(key, {})
        if not isinstance(node, dict):  # pragma: no cover - defensive
            raise TypeError(f"Encountered non-dict node at {key}")
    node[leaf_key] = value


def build_markdown_header(
    *, backend: str, mode: str, command: str, timestamp: datetime
) -> str:
    run_time = timestamp.strftime("%Y-%m-%d %H:%M:%S %Z") or timestamp.isoformat()
    return "\n".join(
        [
            "# PneumoStabSim RHI sweep",
            "",
            f"* **Backend:** `{backend}`",
            f"* **Mode:** `{mode}`",
            f"* **Command:** `{command}`",
            f"* **Timestamp:** {run_time}",
            "",
            "## Console output",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--timestamp", help="Override timestamp suffix (UTC)")
    parser.add_argument(
        "--stop-on-failure", action="store_true", help="Abort on first failure"
    )
    args = parser.parse_args(argv)

    timestamp_str = args.timestamp or datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_dir = args.report_dir
    cache_root = args.cache_root
    report_dir.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)

    template = load_settings_template()
    summary: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []

    for backend in BACKENDS:
        for mode in MODES:
            toggle_enabled = mode.endswith("on")
            with TemporaryDirectory() as tmp_dir:
                tmp_settings = Path(tmp_dir) / "app_settings.json"
                payload = json.loads(json.dumps(template))
                for key_path in POST_EFFECT_KEYS:
                    set_nested(payload, key_path, toggle_enabled)
                tmp_settings.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
                )

                shader_cache_dir = cache_root / f"{backend.name}_{mode}_{timestamp_str}"
                shader_cache_dir.mkdir(parents=True, exist_ok=True)

                env = os.environ.copy()
                env.update(
                    {
                        "QT_QPA_PLATFORM": "offscreen",
                        "QSG_INFO": "1",
                        "QSG_RHI_DEBUG_LAYER": "1",
                        "PSS_SETTINGS_FILE": str(tmp_settings),
                        "QT_RHI_SHADER_CACHE_DIR": str(shader_cache_dir),
                    }
                )
                env.update(backend.env_overrides)

                command = [sys.executable, "app.py", "--test-mode", "--verbose"]
                command_str = " ".join(
                    [
                        *(
                            f"{key}={value}"
                            for key, value in sorted(env.items())
                            if key
                            in {
                                "QT_QPA_PLATFORM",
                                "QSG_INFO",
                                "QSG_RHI_DEBUG_LAYER",
                                "QSG_RHI_BACKEND",
                                "QT_OPENGL",
                            }
                        ),
                        sys.executable,
                        "app.py",
                        "--test-mode",
                        "--verbose",
                    ]
                )

                result = subprocess.run(
                    command,
                    cwd=PROJECT_ROOT,
                    env=env,
                    text=True,
                    capture_output=True,
                )

                stdout = result.stdout or ""
                stderr = result.stderr or ""
                combined_output = stdout + ("\n" + stderr if stderr else "")

                log_path = (
                    report_dir / f"rhi_effects_{backend.name}_{mode}_{timestamp_str}.md"
                )
                header = build_markdown_header(
                    backend=backend.name,
                    mode=mode,
                    command=command_str,
                    timestamp=datetime.now(UTC),
                )
                log_path.write_text(
                    header + "```\n" + combined_output + "\n```\n", encoding="utf-8"
                )

                lines = combined_output.splitlines()
                error_lines = [
                    line for line in lines if "ERROR" in line or "FATAL" in line
                ]
                unexpected_errors = [
                    line
                    for line in error_lines
                    if not any(pattern in line for pattern in KNOWN_ERROR_SUBSTRINGS)
                ]
                has_errors = bool(unexpected_errors)

                entry = {
                    "backend": backend.name,
                    "mode": mode,
                    "returncode": result.returncode,
                    "log_path": str(log_path.relative_to(PROJECT_ROOT)),
                    "shader_cache_dir": str(shader_cache_dir.relative_to(PROJECT_ROOT)),
                    "settings_file": str(tmp_settings),
                    "errors_detected": has_errors,
                    "error_lines": error_lines,
                    "qsg_info": [
                        line
                        for line in combined_output.splitlines()
                        if line.startswith("QSG") or "RHI" in line
                    ],
                }
                summary.append(entry)

                if result.returncode != 0 or has_errors:
                    failures.append(entry)
                    if args.stop_on_failure:
                        break
        if failures and args.stop_on_failure:
            break

    summary_path = report_dir / f"rhi_effects_summary_{timestamp_str}.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Summary written to {summary_path.relative_to(PROJECT_ROOT)}")
    if failures:
        print("One or more runs reported errors:")
        for failure in failures:
            print(
                f"  - {failure['backend']} / {failure['mode']} -> return {failure['returncode']}"
            )
        raise SweepError("RHI sweep completed with errors")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SweepError as exc:
        print(exc)
        sys.exit(1)
