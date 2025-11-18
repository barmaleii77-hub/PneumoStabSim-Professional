"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point - MODULAR VERSION v2.0.1
"""

from __future__ import annotations

import os
import sys
import platform
import textwrap
from pathlib import Path

# --- Path bootstrap
_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))

# --- Global toggles required by diagnostics and compatibility tests
USE_QML_3D_SCHEMA = True
app_instance = None
window_instance = None


def qt_message_handler(mode, context, message):
    """Lightweight Qt message hook used by diagnostics harnesses."""

    # The real handler is configured inside :class:`app_runner.ApplicationRunner`.
    # This shim keeps legacy entrypoints and automated tests satisfied without
    # importing PySide6 at module import time.
    return None


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

# Keep the exported schema flag aligned with bootstrap intent so diagnostics and
# compatibility shims expose the right expectations even before :func:`main`
# runs.
USE_QML_3D_SCHEMA = not (
    bool(getattr(bootstrap_args, "legacy", False))
    or bool(getattr(bootstrap_args, "no_qml", False))
)

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


def _select_preferred_locale() -> str:
    """Pick RU/EN locale for bootstrap messaging based on environment."""

    lang_hint = (os.environ.get("PSS_LOCALE") or os.environ.get("LANG") or "").lower()
    return "ru" if "ru" in lang_hint else "en"


def _log_detected_platform(locale: str) -> tuple[str, dict[str, str]]:
    """Detect host OS early and log a friendly, localised message."""

    system_name = platform.system() or "unknown"
    details = {
        "system": system_name,
        "release": platform.release() if hasattr(platform, "release") else "<n/a>",
        "version": platform.version() if hasattr(platform, "version") else "<n/a>",
    }
    message = (
        f"Обнаружена ОС: {system_name} ({details['release']})"
        if locale == "ru"
        else f"Detected OS: {system_name} ({details['release']})"
    )
    print(message, flush=True)
    _BOOTSTRAP_LOGGER.info("platform_detected", **details, locale=locale)
    return system_name, details


def _render_welcome(locale: str, os_name: str) -> str:
    """Return a bilingual welcome banner with quick pointers."""

    if locale == "ru":
        return textwrap.dedent(
            f"""
            ✅ Добро пожаловать в PneumoStabSim! Точка входа: app.py
            ℹ️  Платформа: {os_name}
            👉 Полезные команды: --help (справка), --env-check (диагностика), --test-mode (автотест UI)
            🔧 Подсказка: для безопасного запуска без QML используйте --no-qml или --legacy.
            """
        ).strip()
    return textwrap.dedent(
        f"""
        ✅ Welcome to PneumoStabSim! Entry point: app.py
        ℹ️  Platform: {os_name}
        👉 Helpful commands: --help (usage), --env-check (diagnostics), --test-mode (UI autotest)
        🔧 Hint: use --no-qml or --legacy for safe launch without QML.
        """
    ).strip()


def _render_command_menu(locale: str) -> str:
    """Provide a concise launcher menu users can skim before running Qt."""

    if locale == "ru":
        return textwrap.dedent(
            """
            Меню запуска:
              • --verbose     — подробные логи в консоль
              • --diag        — вывести диагностику после закрытия
              • --safe-mode   — передать выбор графического бэкенда Qt
              • --safe/--test-mode — безопасный режим, авто-закрытие через 5 секунд
              • --env-report=PATH — сохранить отчёт о среде перед запуском Qt
            """
        ).strip()
    return textwrap.dedent(
        """
        Launch menu:
          • --verbose     — enable verbose console logs
          • --diag        — print diagnostics after exit
          • --safe-mode   — let Qt pick the graphics backend
          • --safe/--test-mode — safe mode with 5s auto-close
          • --env-report=PATH — save environment report before Qt starts
        """
    ).strip()


def _validate_cli_arguments(args: object, locale: str) -> None:
    """Validate mutually exclusive launch options with user-friendly hints."""

    conflicts: list[str] = []
    if getattr(args, "legacy", False) and getattr(args, "no_qml", False):
        if locale == "ru":
            conflicts.append(
                "Нельзя одновременно использовать --legacy и --no-qml. Выберите один режим упрощённого UI."
            )
        else:
            conflicts.append(
                "You cannot combine --legacy with --no-qml. Choose a single simplified UI mode."
            )

    if getattr(args, "env_report", None) is not None:
        target = str(getattr(args, "env_report"))
        if target.strip() == "":
            conflicts.append(
                "Укажите путь для --env-report (пример: --env-report=reports/env.md)"
                if locale == "ru"
                else "Provide a path for --env-report (example: --env-report=reports/env.md)"
            )

    if conflicts:
        for conflict in conflicts:
            print(f"❌ {conflict}", file=sys.stderr)
        _BOOTSTRAP_LOGGER.error("argument_validation_failed", conflicts=conflicts)
        raise SystemExit(2)


def _render_exit_status(exit_code: int, locale: str) -> str:
    """Format a friendly completion message for console users."""

    success = exit_code == 0
    if locale == "ru":
        return (
            "✅ Запуск завершён успешно."
            if success
            else f"⚠️ Приложение завершилось с кодом {exit_code}."
        )
    return (
        "✅ Launch completed successfully."
        if success
        else f"⚠️ Application exited with code {exit_code}."
    )


def _sync_runner_globals(runner: ApplicationRunner) -> None:
    """Expose runner state via module-level globals for diagnostics suites."""

    globals()["USE_QML_3D_SCHEMA"] = bool(getattr(runner, "use_qml_3d_schema", False))
    globals()["app_instance"] = getattr(runner, "app_instance", None)
    globals()["window_instance"] = getattr(runner, "window_instance", None)


def _determine_qml_schema(args: object) -> bool:
    """Decide whether the Qt Quick 3D schema should be enabled for this launch."""

    disable_reasons = (
        getattr(args, "legacy", False),
        getattr(args, "no_qml", False),
        getattr(args, "force_disable_qml_3d", False),
    )
    return not any(disable_reasons)


def main(argv: list[str] | None = None) -> int:
    locale = _select_preferred_locale()
    os_name, _ = _log_detected_platform(locale)

    print(_render_welcome(locale, os_name))
    print(_render_command_menu(locale))

    args = parse_arguments(remaining_argv if argv is None else argv)
    _validate_cli_arguments(args, locale)

    use_qml_3d_schema = _determine_qml_schema(args)

    # Передаём bootstrap-состояние в runner
    setattr(args, "bootstrap_headless", False)
    setattr(args, "bootstrap_use_qml_3d", use_qml_3d_schema)
    setattr(
        args,
        "force_disable_qml_3d",
        not use_qml_3d_schema and bool(getattr(args, "no_qml", False)),
    )
    setattr(
        args,
        "force_disable_qml_3d_reasons",
        ("cli:no-qml",) if getattr(args, "no_qml", False) else tuple(),
    )
    setattr(args, "safe_runtime", bool(getattr(args, "safe", False)))

    runner = ApplicationRunner(
        QApplication,
        qInstallMessageHandler,
        Qt,
        QTimer,
        logging_preset=SELECTED_LOG_PRESET,
    )

    runner.use_qml_3d_schema = use_qml_3d_schema
    _sync_runner_globals(runner)

    # Поддержка --env-paths для быстрой диагностики
    if getattr(args, "env_paths", False):
        snapshot_path = dump_path_snapshot()
        if snapshot_path is not None:
            print(f"[paths] snapshot written: {snapshot_path}")
        print(f"[paths] cwd_ok={verify_repo_root()}")

    try:
        exit_code = runner.run(args)
    finally:
        _sync_runner_globals(runner)

    print(_render_exit_status(exit_code, locale))

    return exit_code


def __getattr__(name: str):
    """Provide compatibility globals for diagnostics harnesses.

    Older test suites expect ``USE_QML_3D_SCHEMA``, ``app_instance`` and
    ``window_instance`` to be present at module scope even when the runtime has
    not yet created any Qt objects. The values are lazily initialised so the
    attributes are always available without pulling in heavy dependencies.
    """

    if name == "USE_QML_3D_SCHEMA":
        globals().setdefault(name, True)
        return globals()[name]
    if name == "app_instance":
        globals().setdefault(name, None)
        return globals()[name]
    if name == "window_instance":
        globals().setdefault(name, None)
        return globals()[name]
    raise AttributeError(name)


if __name__ == "__main__":
    sys.exit(main())
