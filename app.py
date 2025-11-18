"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point - MODULAR VERSION v2.0.1
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# --- Path bootstrap
_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))

# --- Prefer project venv python (console/python.exe in headless/trace modes)
_DEF_VENV = _PROJECT_ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin")
_VENV_PY_CONSOLE = _DEF_VENV / ("python.exe" if os.name == "nt" else "python")
_VENV_PY_GUI = _DEF_VENV / ("pythonw.exe" if os.name == "nt" else "python")

# Heuristic headless/trace detection from argv/env to avoid pythonw in CI/offscreen
_headless_argv_tokens = {"--env-check", "--env-report", "--safe", "--test-mode"}
_headless_hint = any(token in sys.argv[1:] for token in _headless_argv_tokens) or (
    (os.environ.get("PSS_HEADLESS") or "").strip().lower() in {"1", "true", "yes", "on"}
)
_target_executable = None
if _DEF_VENV.exists():
    if os.name == "nt":
        # On Windows prefer console python for headless/trace; GUI python otherwise
        preferred = _VENV_PY_CONSOLE if _headless_hint else _VENV_PY_GUI
    else:
        preferred = _VENV_PY_CONSOLE
    if preferred.exists():
        _target_executable = preferred

if _target_executable is not None:
    try:
        if Path(sys.executable).resolve() != _target_executable.resolve():
            os.execve(
                str(_target_executable),
                [str(_target_executable), __file__, *sys.argv[1:]],
                os.environ.copy(),
            )
    except Exception:
        pass

from src.cli.arguments import create_bootstrap_parser, parse_arguments  # noqa: E402
from src.diagnostics.logger_factory import get_logger  # noqa: E402
from src.diagnostics.logging_presets import apply_logging_preset  # noqa: E402
from src.diagnostics.path_diagnostics import (  # noqa: E402
    dump_path_snapshot,
    verify_repo_root,
)
from src.ui.startup import bootstrap_graphics_environment  # noqa: E402


def _set_high_dpi_policy(qapplication: object, qt_namespace: object) -> None:
    """Ensure High DPI rounding policy is configured before QApplication creation."""

    instance_exists = False
    try:
        instance_exists = bool(getattr(qapplication, "instance", lambda: None)())
    except Exception:
        instance_exists = False

    # Qt выдаёт предупреждение, если политику менять после создания QApplication.
    if instance_exists:
        return

    set_policy = getattr(qapplication, "setHighDpiScaleFactorRoundingPolicy", None)
    policy = getattr(
        getattr(qt_namespace, "HighDpiScaleFactorRoundingPolicy", None),
        "PassThrough",
        None,
    )

    if set_policy is None or policy is None:
        return

    try:
        set_policy(policy)
    except Exception:
        # DPI policy configuration is best-effort; continue bootstrap if unavailable
        return


def _ensure_qt_runtime_paths(project_root: Path) -> None:
    """Настроить Qt/QML пути и запретить offscreen на Windows в интерактиве."""
    try:
        venv_root = project_root / ".venv"
        pyside_dir = venv_root / "Lib" / "site-packages" / "PySide6"
        plugins_dir = pyside_dir / "plugins"
        qml_dir = pyside_dir / "qml"
        assets_qml = project_root / "assets" / "qml"

        if plugins_dir.exists() and not os.environ.get("QT_PLUGIN_PATH"):
            os.environ["QT_PLUGIN_PATH"] = str(plugins_dir)

        def _append(name: str, path: Path) -> None:
            if not path.exists():
                return
            cur = os.environ.get(name, "")
            parts = [p for p in cur.split(os.pathsep) if p]
            if str(path) not in parts:
                os.environ[name] = (
                    os.pathsep.join(parts + [str(path)]) if parts else str(path)
                )

        _append("QML2_IMPORT_PATH", qml_dir)
        _append("QML2_IMPORT_PATH", assets_qml)
        _append("QML_IMPORT_PATH", qml_dir)
        _append("QML_IMPORT_PATH", assets_qml)

        if os.name == "nt":
            qpa = (os.environ.get("QT_QPA_PLATFORM") or "").strip().lower()
            headless = (os.environ.get("PSS_HEADLESS") or "").strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            if not headless and qpa in {"offscreen", "minimal", "minimal:tools=auto"}:
                os.environ["QT_QPA_PLATFORM"] = "windows"
            if (
                os.environ.get("QT_QUICK_BACKEND") or ""
            ).strip().lower() == "software" and not headless:
                os.environ.pop("QT_QUICK_BACKEND", None)
            os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")

        os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
        os.environ.setdefault("PSS_QML_SCENE", "realism")
    except Exception:
        pass


# --- Parse bootstrap args once
bootstrap_parser = create_bootstrap_parser()
_initial_argv = list(sys.argv[1:])
bootstrap_args, remaining_argv = bootstrap_parser.parse_known_args(_initial_argv)
_program_name = sys.argv[0]

# Early environment diagnostics path: do NOT import Qt when --env-check/--env-report are requested
if getattr(bootstrap_args, "env_check", False) or getattr(
    bootstrap_args, "env_report", None
):
    try:
        from src.bootstrap.environment_check import (
            generate_environment_report,
            render_console_report,
        )
    except Exception:
        # If diagnostics modules are unavailable, exit gracefully
        sys.exit(0)

    report = generate_environment_report()
    target = getattr(bootstrap_args, "env_report", None)
    if isinstance(target, str) and target.strip():
        try:
            out_path = Path(target)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(report.to_markdown(), encoding="utf-8")
        except Exception:
            # Fallback to console on write failure
            try:
                print(render_console_report(report))
            except Exception:
                pass
    else:
        try:
            print(render_console_report(report))
        except Exception:
            pass
    # Exit before any Qt imports happen
    sys.exit(0)

SAFE_GRAPHICS_MODE_REQUESTED = bool(getattr(bootstrap_args, "safe_mode", False))
# ВАЖНО: --test-mode не отключает UI
SAFE_RUNTIME_MODE_REQUESTED = bool(getattr(bootstrap_args, "safe", False))
SAFE_ALIAS_REQUESTED = "--safe" in _initial_argv
LEGACY_MODE_REQUESTED = bool(getattr(bootstrap_args, "legacy", False))

_BOOTSTRAP_LOGGER = get_logger("bootstrap.graphics").bind(stage="pre-qt")

# Apply Qt paths and GUI defaults early
_ensure_qt_runtime_paths(_PROJECT_ROOT)

# Configure logging preset now that env is set
SELECTED_LOG_PRESET = apply_logging_preset(os.environ)

# Import Qt safely (deferred until after env-check early exit)
from src.bootstrap.qt_imports import safe_import_qt  # noqa: E402

QApplication, qInstallMessageHandler, Qt, QTimer = safe_import_qt(  # noqa: E402
    lambda m: None, lambda m: None
)

_set_high_dpi_policy(QApplication, Qt)

from src.app_runner import ApplicationRunner  # noqa: E402


def main() -> int:
    args = parse_arguments()

    # Передаём bootstrap-состояние в runner
    setattr(args, "bootstrap_headless", False)
    setattr(args, "bootstrap_use_qml_3d", True)
    setattr(args, "force_disable_qml_3d", False)
    setattr(args, "force_disable_qml_3d_reasons", tuple())
    setattr(args, "safe_runtime", bool(getattr(args, "safe", False)))

    runner = ApplicationRunner(
        QApplication,
        qInstallMessageHandler,
        Qt,
        QTimer,
        logging_preset=SELECTED_LOG_PRESET,
    )

    # Поддержка --env-paths для быстрой диагностики
    if getattr(args, "env_paths", False):
        snapshot_path = dump_path_snapshot()
        if snapshot_path is not None:
            print(f"[paths] snapshot written: {snapshot_path}")
        print(f"[paths] cwd_ok={verify_repo_root()}")

    return runner.run(args)


if __name__ == "__main__":
    sys.exit(main())
