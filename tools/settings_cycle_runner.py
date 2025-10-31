"""Automated multi-run settings verification for PneumoStabSim."""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

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
                "renderScale": 1.08,
                "frameRateLimit": 120.0,
                "taaStrength": 0.55,
                "shadowSettings.resolution": 2048,
                "shadowSettings.filterSamples": 16,
            },
            "scene_batch": {
                "exposure": 1.1,
                "model_metalness": 0.88,
            },
        },
    ),
    Scenario(
        name="materials_scene_animation",
        updates={
            "current": {
                "graphics": {
                    "materials": {
                        "frame": {
                            "base_color": "#4b5962",
                            "roughness": 0.38,
                        },
                        "lever": {
                            "metalness": 0.9,
                            "roughness": 0.33,
                        },
                        "cylinder": {
                            "metalness": 0.86,
                            "roughness": 0.28,
                        },
                        "piston_rod": {
                            "metalness": 0.95,
                        },
                    },
                    "scene": {
                        "scale_factor": 1.05,
                        "default_clear_color": "#1c232b",
                    },
                },
                "animation": {
                    "frequency": 1.2,
                    "amplitude": 9.5,
                    "smoothing_duration_ms": 140,
                    "smoothing_angle_snap_deg": 60.0,
                },
            }
        },
        settings_expectations={
            "current.graphics.materials.frame.base_color": "#4b5962",
            "current.graphics.materials.frame.roughness": 0.38,
            "current.graphics.materials.lever.metalness": 0.9,
            "current.graphics.materials.lever.roughness": 0.33,
            "current.graphics.materials.cylinder.metalness": 0.86,
            "current.graphics.materials.cylinder.roughness": 0.28,
            "current.graphics.materials.piston_rod.metalness": 0.95,
            "current.graphics.scene.scale_factor": 1.05,
            "current.graphics.scene.default_clear_color": "#1c232b",
            "current.animation.frequency": 1.2,
            "current.animation.amplitude": 9.5,
            "current.animation.smoothing_duration_ms": 140,
            "current.animation.smoothing_angle_snap_deg": 60.0,
        },
        log_expectations={
            "materials_batch": {
                "frame.base_color": "#4b5962",
                "frame.roughness": 0.38,
                "lever.metalness": 0.9,
                "lever.roughness": 0.33,
                "cylinder.metalness": 0.86,
                "cylinder.roughness": 0.28,
                "piston_rod.metalness": 0.95,
            },
            "scene_batch": {
                "scale_factor": 1.05,
                "default_clear_color": "#1c232b",
            },
            "animation_batch": {
                "frequency": 1.2,
                "amplitude": 9.5,
                "smoothing_duration_ms": 140,
                "smoothing_angle_snap_deg": 60.0,
            },
        },
    ),
)


def _deep_update(target: dict[str, Any], update: Mapping[str, Any]) -> None:
    for key, value in update.items():
        if isinstance(value, Mapping) and isinstance(
            existing := target.get(key), Mapping
        ):
            new_target = dict(existing)
            _deep_update(new_target, value)
            target[key] = new_target
        else:
            target[key] = value


def _write_settings(settings_path: Path, updates: Mapping[str, Any]) -> None:
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    _deep_update(payload, updates)
    settings_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _get_dotted(payload: Mapping[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, Mapping):
            raise KeyError(f"Cannot descend into non-mapping for path '{dotted_path}'")
        if part not in current:
            raise KeyError(f"Missing key '{part}' in path '{dotted_path}'")
        current = current[part]
    return current


def _compare_values(expected: Any, actual: Any, *, path: str) -> None:
    if isinstance(expected, float) or isinstance(actual, float):
        if not isinstance(actual, (int, float)):
            raise AssertionError(f"Value at {path} is not numeric: {actual!r}")
        if not math.isclose(float(actual), float(expected), rel_tol=1e-6, abs_tol=1e-9):
            raise AssertionError(
                f"Mismatch at {path}: expected {expected!r}, got {actual!r}"
            )
    else:
        if actual != expected:
            raise AssertionError(
                f"Mismatch at {path}: expected {expected!r}, got {actual!r}"
            )


def _verify_settings(settings_path: Path, expectations: Mapping[str, Any]) -> None:
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    for path, expected in expectations.items():
        actual = _get_dotted(payload, path)
        _compare_values(expected, actual, path=path)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _run_application(env: Mapping[str, str]) -> Path:
    """Launch the Qt application in test mode and return the generated log path."""
    _ensure_dir(LOGS_DIR)
    _ensure_dir(GRAPHICS_LOG_DIR)

    before = {p.name for p in GRAPHICS_LOG_DIR.glob("session_*.jsonl")}
    command = [str(sys.executable), str(APP_PATH), "--test-mode", "--verbose"]
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=dict(env),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )
    # Emit launch output for traceability
    print(completed.stdout.rstrip())

    candidates = sorted(
        GRAPHICS_LOG_DIR.glob("session_*.jsonl"),
        key=lambda p: p.stat().st_mtime,
    )
    new_logs = [p for p in candidates if p.name not in before]
    if new_logs:
        return new_logs[-1]
    if candidates:
        return candidates[-1]
    raise RuntimeError("Graphics diagnostics log not generated")


def _wait_for_file(path: Path, retries: int = 10, delay: float = 0.2) -> None:
    """Poll for *path* until it exists so later checks can safely read it."""
    for _ in range(retries):
        if path.exists():
            return
        time.sleep(delay)
    raise RuntimeError(f"File {path} not found after waiting")


def _load_applied_state(log_path: Path, parameter: str) -> Mapping[str, Any]:
    """Extract the final applied state for *parameter* from a graphics log."""
    applied: Mapping[str, Any] | None = None
    with log_path.open("r", encoding="utf-8") as stream:
        for line in stream:
            entry = json.loads(line)
            if (
                entry.get("event_type") == "parameter_update"
                and entry.get("parameter_name") == parameter
                and entry.get("applied_to_qml")
            ):
                applied = entry.get("new_value") or {}
    if applied is None:
        raise AssertionError(
            f"No applied parameter update recorded for '{parameter}' in {log_path.name}"
        )
    return applied


def _verify_logs(log_path: Path, expectations: Mapping[str, Mapping[str, Any]]) -> None:
    """Ensure telemetry for each parameter reflects the expected values."""
    for parameter, checks in expectations.items():
        state = _load_applied_state(log_path, parameter)
        for path, expected in checks.items():
            actual = _get_dotted(state, path)
            _compare_values(expected, actual, path=f"{parameter}.{path}")


def _verify_run_log(run_log_text: str) -> None:
    """Validate key warnings and diagnostics captured in the main run log."""
    if "Qt[QtWarningMsg]" not in run_log_text:
        raise AssertionError("Qt warnings were not captured in the run log")
    if "SuspensionCorner initialized" not in run_log_text:
        raise AssertionError("SuspensionCorner initialisation trace missing")
    control_pattern = re.compile(r"j_arm:\s+([-0-9.]+)\s+([-0-9.]+)\s+([-0-9.]+)")
    control_points = control_pattern.findall(run_log_text)
    if not control_points:
        raise AssertionError("Control point coordinates not found in run log")
    for triple in control_points[:4]:
        for value in triple:
            float(value)
    if "rodLengthError" not in run_log_text:
        raise AssertionError("Rod length diagnostic missing from run log")


def run_cycle() -> None:
    """Execute every scenario: write settings, run the app, and verify outputs."""
    base_payload = SETTINGS_TEMPLATE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp_dir:
        settings_path = Path(tmp_dir) / "app_settings.json"
        settings_path.write_text(base_payload, encoding="utf-8")

        env = os.environ.copy()
        env["PSS_SETTINGS_FILE"] = str(settings_path)
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        env.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

        for scenario in SCENARIOS:
            print(f"\n=== Scenario: {scenario.name} ===")
            _write_settings(settings_path, scenario.updates)
            log_path = _run_application(env)
            print(f"Captured graphics log: {log_path.relative_to(PROJECT_ROOT)}")
            _verify_settings(settings_path, scenario.settings_expectations)
            print("Settings persistence verified")
            _verify_logs(log_path, scenario.log_expectations)
            print("Graphics telemetry verified")
            _wait_for_file(RUN_LOG_PATH)
            run_log_text = RUN_LOG_PATH.read_text(encoding="utf-8")
            _verify_run_log(run_log_text)
            print("Run log diagnostics verified")

    print("\nAll scenarios completed successfully.")


def main() -> None:
    try:
        run_cycle()
    except Exception as exc:  # pragma: no cover - diagnostic runner
        print(f"\n❌ settings cycle failed: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
