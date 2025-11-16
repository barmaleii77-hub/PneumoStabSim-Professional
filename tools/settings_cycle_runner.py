"""Automated multi-run settings verification for PneumoStabSim."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections.abc import Mapping

from tools.headless import prepare_launch_environment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"
SETTINGS_TEMPLATE = PROJECT_ROOT / "config" / "app_settings.json"
LOGS_DIR = PROJECT_ROOT / "logs"
GRAPHICS_LOG_DIR = LOGS_DIR / "graphics"
RUN_LOG_PATH = LOGS_DIR / "run.log"


@dataclass(frozen=True)
class Scenario:
    """Description of a single launch-and-verify cycle."""

    name: str
    updates: dict[str, Any]
    settings_expectations: Mapping[str, Any]
    log_expectations: Mapping[str, Mapping[str, Any]]


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        name="geometry_lighting_camera",
        updates={
            "current": {
                "geometry": {
                    "wheelbase": 3.6,
                    "track": 2.18,
                    "lever_length": 0.82,
                },
                "graphics": {
                    "lighting": {
                        "point": {
                            "brightness": 62.0,
                            "range": 4.4,
                        },
                        "spot": {
                            "brightness": 4800.0,
                            "cone_angle": 7.0,
                        },
                    },
                    "camera": {
                        "orbit_distance": 4.7,
                        "orbit_pitch": -17.0,
                        "orbit_yaw": 42.0,
                    },
                },
            }
        },
        settings_expectations={
            "current.geometry.wheelbase": 3.6,
            "current.geometry.track": 2.18,
            "current.geometry.lever_length": 0.82,
            "current.graphics.lighting.point.brightness": 62.0,
            "current.graphics.lighting.point.range": 4.4,
            "current.graphics.lighting.spot.cone_angle": 7.0,
            "current.graphics.lighting.spot.brightness": 4800.0,
            "current.graphics.camera.orbit_distance": 4.7,
            "current.graphics.camera.orbit_pitch": -17.0,
            "current.graphics.camera.orbit_yaw": 42.0,
        },
        log_expectations={
            "geometry_batch": {
                "frameLength": 3.6,
                "trackWidth": 2.18,
                "leverLength": 0.82,
            },
            "lighting_batch": {
                "point.brightness": 62.0,
                "point.range": 4.4,
                "spot.brightness": 4800.0,
                "spot.cone_angle": 7.0,
            },
            "camera_batch": {
                "orbit_distance": 4.7,
                "orbit_pitch": -17.0,
                "orbit_yaw": 42.0,
            },
        },
    ),
    Scenario(
        name="environment_effects_quality",
        updates={
            "current": {
                "graphics": {
                    "environment": {
                        "fog_density": 0.11,
                        "ibl_rotation": 25.0,
                        "skybox_blur": 0.11,
                        "ibl_intensity": 1.5,
                        "skybox_brightness": 1.2,
                    },
                    "effects": {
                        "bloom_intensity": 0.72,
                        "bloom_threshold": 1.1,
                        "tonemap_enabled": True,
                        "tonemap_mode": "aces",
                        "tonemap_exposure": 1.25,
                        "depth_of_field": True,
                        "dof_blur": 5.5,
                        "motion_blur": True,
                        "motion_blur_amount": 0.15,
                        "vignette": True,
                        "vignette_strength": 0.42,
                        "vignette_radius": 0.55,
                    },
                    "quality": {
                        "render_scale": 1.08,
                        "frame_rate_limit": 120.0,
                        "taa_strength": 0.55,
                        "shadows": {
                            "resolution": 2048,
                            "filter": 16,
                        },
                    },
                    "scene": {
                        "exposure": 1.1,
                        "model_metalness": 0.88,
                    },
                }
            }
        },
        settings_expectations={
            "current.graphics.environment.fog_density": 0.11,
            "current.graphics.environment.ibl_rotation": 25.0,
            "current.graphics.environment.skybox_blur": 0.11,
            "current.graphics.environment.ibl_intensity": 1.5,
            "current.graphics.environment.skybox_brightness": 1.2,
            "current.graphics.effects.bloom_intensity": 0.72,
            "current.graphics.effects.tonemap_enabled": True,
            "current.graphics.effects.tonemap_mode": "aces",
            "current.graphics.effects.tonemap_exposure": 1.25,
            "current.graphics.effects.depth_of_field": True,
            "current.graphics.effects.dof_blur": 5.5,
            "current.graphics.effects.motion_blur": True,
            "current.graphics.effects.motion_blur_amount": 0.15,
            "current.graphics.effects.vignette": True,
            "current.graphics.effects.vignette_strength": 0.42,
            "current.graphics.effects.vignette_radius": 0.55,
            "current.graphics.quality.render_scale": 1.08,
            "current.graphics.quality.frame_rate_limit": 120.0,
            "current.graphics.quality.taa_strength": 0.55,
            "current.graphics.quality.shadows.resolution": 2048,
            "current.graphics.quality.shadows.filter": 16,
            "current.graphics.scene.exposure": 1.1,
            "current.graphics.scene.model_metalness": 0.88,
        },
        log_expectations={
            "environment_batch": {
                "fog_density": 0.11,
                "ibl_rotation": 25.0,
                "skybox_blur": 0.11,
                "ibl_intensity": 1.5,
                "skybox_brightness": 1.2,
            },
            "effects_batch": {
                "bloom_intensity": 0.72,
                "bloom_threshold": 1.1,
                "tonemap_enabled": True,
                "tonemap_mode": "aces",
                "tonemap_exposure": 1.25,
                "depth_of_field": True,
                "dof_blur": 5.5,
                "motion_blur": True,
                "motion_blur_amount": 0.15,
                "vignette": True,
                "vignette_strength": 0.42,
                "vignette_radius": 0.55,
            },
            "quality_batch": {
                "render_scale": 1.08,
                "frame_rate_limit": 120.0,
                "taa_strength": 0.55,
                "shadows.resolution": 2048,
                "shadows.filter": 16,
            },
        },
    ),
)


def _run_single(name: str, settings_path: Path, updates: dict[str, Any]) -> int:
    """Run app once with provided updates and wait for exit.

    We intentionally enable QML 3D in offscreen environments to exercise the
    QML-side batching logic. This is safe because Qt can render offscreen with
    RHI+OpenGL ANGLE or software pipelines.
    """

    launch_env = prepare_launch_environment()
    # Force-enable QML 3D even when offscreen/headless is detected.
    launch_env["PSS_FORCE_ALLOW_QML_3D"] = "1"

    # Provide settings path and batched updates through environment for the app
    launch_env["PSS_SETTINGS_PATH"] = str(settings_path)
    # Encode only the graphics portion to the env consumed by SceneBridge/QML
    try:
        graphics_updates = (updates or {}).get("current", {}).get("graphics", {})
    except Exception:
        graphics_updates = {}
    if graphics_updates:
        launch_env["PSS_GRAPHICS_UPDATES_JSON"] = json.dumps(graphics_updates)

    # Verbose logging for diagnostics and ensure log directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(GRAPHICS_LOG_DIR, exist_ok=True)
    launch_env.setdefault("PSS_GRAPHICS_LOGGING", "1")

    args = [sys.executable, str(APP_PATH), "--test-mode", "--verbose"]

    print(f"→ Launching scenario '{name}' with --test-mode --verbose")
    proc = subprocess.Popen(args, env=launch_env)
    try:
        return proc.wait(timeout=25)
    except subprocess.TimeoutExpired:
        proc.kill()
        return 124


def _write_temp_settings(template_path: Path, updates: dict[str, Any]) -> Path:
    raw = template_path.read_text(encoding="utf-8")
    base = json.loads(raw)

    def _deep_update(target: dict[str, Any], payload: dict[str, Any]) -> None:
        for k, v in payload.items():
            if isinstance(v, dict) and isinstance(target.get(k), dict):
                _deep_update(target[k], v)
            else:
                target[k] = v

    _deep_update(base, updates)

    fd, tmp_path = tempfile.mkstemp(prefix="pss_settings_", suffix=".json")
    os.close(fd)
    Path(tmp_path).write_text(
        json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return Path(tmp_path)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


def _find_latest_graphics_session() -> Path | None:
    if not GRAPHICS_LOG_DIR.exists():
        return None
    candidates = sorted(GRAPHICS_LOG_DIR.glob("session_*.jsonl"))
    return candidates[-1] if candidates else None


def _verify_logs(scn: Scenario) -> bool:
    """Verify that expected batches were written to session log and run.log."""

    session_path = _find_latest_graphics_session()
    if session_path is None:
        print("✖ No graphics session log found")
        return False

    events = _read_jsonl(session_path)
    if not events:
        print(f"✖ Graphics session log is empty: {session_path}")
        return False

    ok = True

    def _find_latest(name: str) -> dict[str, Any] | None:
        for entry in reversed(events):
            if entry.get("event_type") == name:
                return entry.get("payload") or {}
        return None

    for batch_name, expectations in scn.log_expectations.items():
        payload = _find_latest(batch_name)
        if not isinstance(payload, dict):
            print(f"✖ Missing batch {batch_name}")
            ok = False
            continue
        for key, expected in expectations.items():
            actual = payload
            for token in key.split("."):
                if isinstance(actual, dict):
                    actual = actual.get(token)
                else:
                    actual = None
                    break
            if actual != expected:
                print(f"✖ {batch_name}.{key}: expected {expected!r}, got {actual!r}")
                ok = False

    # Tail run.log if present
    if RUN_LOG_PATH.exists():
        try:
            tail = RUN_LOG_PATH.read_text(encoding="utf-8")[-2000:]
            print("… run.log tail …\n" + tail)
        except Exception:
            pass

    return ok


def _verify_settings(scn: Scenario, settings_path: Path) -> bool:
    try:
        payload = json.loads(Path(settings_path).read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"✖ Failed to read settings {settings_path}: {exc}")
        return False

    def _lookup(path: str) -> Any:
        node: Any = payload
        for token in path.split("."):
            if not isinstance(node, dict):
                return None
            node = node.get(token)
        return node

    ok = True
    for dotted, expected in scn.settings_expectations.items():
        actual = _lookup(dotted)
        if actual != expected:
            print(f"✖ settings {dotted}: expected {expected!r}, got {actual!r}")
            ok = False
    return ok


def main() -> int:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    GRAPHICS_LOG_DIR.mkdir(parents=True, exist_ok=True)

    all_ok = True
    for scn in SCENARIOS:
        settings_path = _write_temp_settings(SETTINGS_TEMPLATE, scn.updates)
        code = _run_single(scn.name, settings_path, scn.updates)
        if code != 0:
            print(f"✖ Scenario '{scn.name}' exited with code {code}")
            all_ok = False
        else:
            if not _verify_logs(scn):
                print(f"✖ Scenario '{scn.name}' graphics log verification failed")
                all_ok = False
            if not _verify_settings(scn, settings_path):
                print(f"✖ Scenario '{scn.name}' settings verification failed")
                all_ok = False

    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
