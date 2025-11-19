#!/usr/bin/env python
"""
Windows Interactive Launcher for PneumoStabSim-Professional

Дополнено: расширенный сбор stdout/stderr, принудительный выбор console-интерпретатора
для verbose/diag и опции консоли, углублённый анализ логов (поиск QML ошибок).
"""

from __future__ import annotations

import json
import os
import platform
import shlex
import subprocess
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Sequence
import threading
import time

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

LOGS_DIR = Path("logs")
LOG_EXTENSIONS = (".log", ".jsonl")

# --- Constants
QPA_CHOICES: list[str] = ["(auto)", "windows", "offscreen", "minimal"]
RHI_CHOICES: list[str] = ["(auto)", "d3d11", "opengl", "vulkan"]
STYLE_CHOICES: list[str] = ["(auto)", "Basic", "Fusion"]
SCENE_CHOICES: list[str] = ["(auto)", "realism"]
DEFAULT_LOG_LINES = 200
TEST_SCOPE_CHOICES: list[str] = ["main", "integration", "all"]

CreateFlag = Literal["new_console", "detached", "capture"]

DETECTED_PLATFORM = platform.system()
print(f"🖥️ Interactive launcher detected platform: {DETECTED_PLATFORM}")


def _log(message: str) -> None:
    timestamp = time.strftime("%H:%M:%S")
    print(f"[launcher {timestamp}] {message}")


def _format_command(cmd: Sequence[str]) -> str:
    return " ".join(cmd)


def run_command_logged(
    cmd: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    _log(f"Executing: {_format_command(cmd)}")
    completed = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    _log("Finished: %s (exit=%s)" % (_format_command(cmd), completed.returncode))
    return completed


def run_command_with_summary(
    cmd: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], str]:
    """Execute a command and return the completed process with a readable summary."""

    completed = run_command_logged(cmd, cwd=cwd, env=env)
    return completed, format_completed_process(cmd, completed)


def summarize_log_tail(
    log_path: Path, max_lines: int
) -> tuple[deque[str], dict[str, int], list[str]]:
    """Return tail, severity counts and highlight lines for a log file."""

    tail: deque[str] = deque(maxlen=max_lines)
    with log_path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            tail.append(line.rstrip("\n"))

    counts = _count_severities(tail)
    highlights = _extract_highlight_lines(tail)
    return tail, counts, highlights


def format_completed_process(
    cmd: Sequence[str], completed: subprocess.CompletedProcess[str]
) -> str:
    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    lines: list[str] = [f"$ {_format_command(cmd)}", f"exit={completed.returncode}"]
    if stdout:
        lines.append(stdout)
    if stderr:
        lines.append("[stderr]\n" + stderr)
    return "\n".join(lines)


def _count_severities(lines: Sequence[str]) -> dict[str, int]:
    counts = {"error": 0, "warning": 0}
    for ln in lines:
        low = ln.lower()
        if any(tok in low for tok in ("error", "traceback", "exception", "failed")):
            counts["error"] += 1
        if "warn" in low:
            counts["warning"] += 1
    return counts


def _extract_highlight_lines(lines: Sequence[str], limit: int = 50) -> list[str]:
    highlights: list[str] = []
    for ln in lines:
        low = ln.lower()
        if any(tok in low for tok in ("error", "traceback", "warning", "failed")):
            highlights.append(ln)
        if len(highlights) >= limit:
            break
    return highlights


def _detect_failure_hint(lines: Sequence[str]) -> str:
    if not lines:
        return "Пустой вывод процесса. Проверьте логи в секции 'Логи и ошибки'."

    counts = _count_severities(lines)
    hints: list[str] = []
    if counts["error"]:
        hints.append(
            f"Найдено ошибок: {counts['error']}. Проверьте ключевые строки ниже."
        )
    if counts["warning"]:
        hints.append(f"Предупреждений: {counts['warning']}.")

    text_blob = "\n".join(lines).lower()
    if "module not found" in text_blob or "no module named" in text_blob:
        hints.append(
            "Похоже, отсутствуют зависимости. Запустите 'make uv-sync' и повторите."
        )
    if "qt.qpa" in text_blob or "xcb" in text_blob:
        hints.append(
            "Проблема с Qt платформой. Попробуйте выбрать другой QPA или включить Headless."
        )
    if "permission" in text_blob:
        hints.append(
            "Есть ошибки прав доступа. Попробуйте запустить от имени администратора или проверить пути."
        )
    if "failed" in text_blob and "pytest" in text_blob:
        hints.append(
            "Похоже, упали тесты. Проверьте блок FAILURES и перезапустите с --diag."
        )
    if "ruff" in text_blob and "error" in text_blob:
        hints.append(
            "Линтер обнаружил ошибки. Запустите 'python -m ruff .' для деталей."
        )
    if not hints and (counts["error"] or counts["warning"]):
        hints.append(
            "Запустите с --diag/--verbose и просмотрите свежие логи через лаунчер."
        )
    elif not hints:
        return ""

    highlights = _extract_highlight_lines(lines, limit=10)
    if highlights:
        hints.append("Ключевые строки:\n" + "\n".join(highlights))

    return "\n".join(hints)


@dataclass
class TestRunConfig:
    """Parameters describing a test run triggered from the launcher."""

    runner: Literal["entrypoint", "pytest"]
    scope: Literal["main", "integration", "all"]
    targets: list[str]
    extra_args: list[str]
    show_canvas: bool


# --- Tooltip helper
class Tooltip:
    def __init__(self, widget: tk.Widget, text: str, *, delay_ms: int = 350) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id: str | None = None
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._on_enter, add=True)
        widget.bind("<Leave>", self._on_leave, add=True)
        widget.bind("<ButtonPress>", self._on_leave, add=True)

    def _on_enter(self, _event: tk.Event) -> None:  # type: ignore[override]
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _on_leave(self, _event: tk.Event) -> None:  # type: ignore[override]
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self._hide()

    def _show(self) -> None:
        if self._tip or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except Exception:
            return
        tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            tip,
            text=self.text,
            justify="left",
            relief="solid",
            borderwidth=1,
            background="#ffffe1",
            padx=6,
            pady=4,
            wraplength=420,
        )
        lbl.pack()
        self._tip = tip

    def _hide(self) -> None:
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


class TestAnimationCanvas:
    """Small animated canvas illustrating the test pipeline while tests run."""

    def __init__(self, parent: tk.Misc) -> None:
        self.window = tk.Toplevel(parent)
        self.window.title("Схема прогонки тестов")
        self.window.geometry("760x420")
        self.canvas = tk.Canvas(
            self.window, width=740, height=360, background="#0d1b2a"
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self._running = False
        self._step = 0
        self._status_text = self.canvas.create_text(
            370,
            330,
            text="⏳ Подготовка окружения...",
            fill="#e0e7ff",
            font=("Segoe UI", 12),
        )

        self._nodes = [
            (120, 120, "Deps"),
            (290, 120, "Lint"),
            (460, 120, "Types"),
            (630, 120, "Tests"),
        ]
        self._path = [node[:2] for node in self._nodes]
        self._indicator = None
        self._build_scene()

    def _build_scene(self) -> None:
        for idx, (x, y, label) in enumerate(self._nodes):
            self.canvas.create_oval(
                x - 34,
                y - 34,
                x + 34,
                y + 34,
                fill="#1b263b",
                outline="#4cc9f0",
                width=2,
            )
            self.canvas.create_text(
                x, y, text=label, fill="#f5f7fb", font=("Segoe UI", 11, "bold")
            )
            if idx > 0:
                prev_x, prev_y, _ = self._nodes[idx - 1]
                self.canvas.create_line(
                    prev_x + 34,
                    prev_y,
                    x - 34,
                    y,
                    fill="#4cc9f0",
                    width=3,
                    arrow=tk.LAST,
                )

        self._indicator = self.canvas.create_oval(
            0, 0, 0, 0, fill="#fca311", outline="", width=0
        )
        self._update_indicator()

    def _update_indicator(self) -> None:
        if not self._indicator:
            return
        x, y = self._path[self._step % len(self._path)]
        radius = 12
        self.canvas.coords(
            self._indicator, x - radius, y - radius, x + radius, y + radius
        )

    def start(self) -> None:
        self._running = True
        self._schedule_tick()

    def _schedule_tick(self) -> None:
        if not self._running:
            return
        self._step = (self._step + 1) % len(self._path)
        self._update_indicator()
        self.canvas.after(420, self._schedule_tick)

    def mark_complete(self, success: bool, message: str) -> None:
        self._running = False
        colour = "#38b000" if success else "#ff595e"
        try:
            self.canvas.itemconfigure(self._status_text, text=message, fill=colour)
            if self._indicator:
                self.canvas.itemconfigure(self._indicator, fill=colour)
        except Exception:
            pass

    def destroy(self) -> None:
        try:
            self.window.destroy()
        except Exception:
            pass


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def detect_venv_python(*, prefer_console: bool) -> Path:
    root = project_root()
    base = root / ".venv" / ("Scripts" if os.name == "nt" else "bin")
    if os.name == "nt":
        gui = base / "pythonw.exe"
        con = base / "python.exe"
    else:
        gui = base / "python"
        con = base / "python"
    # Всегда используем console при запросе prefer_console
    preferred = con if prefer_console else gui
    return (
        preferred
        if preferred.exists()
        else (con if con.exists() else Path(sys.executable))
    )


def _append_env_path(env: dict[str, str], name: str, path: Path) -> None:
    if not path.exists():
        return
    cur = env.get(name, "")
    parts = [p for p in cur.split(os.pathsep) if p]
    spath = str(path)
    if spath not in parts:
        env[name] = os.pathsep.join(parts + [spath]) if parts else spath


def ensure_qt_environment(env: dict[str, str]) -> None:
    root = project_root()
    venv_root = root / ".venv"
    site_packages_candidates: list[Path] = []
    if os.name == "nt":
        site_packages_candidates.append(venv_root / "Lib" / "site-packages")
    else:
        site_packages_candidates.extend(
            path
            for path in (venv_root / "lib").glob("python*/site-packages")
            if path.exists()
        )

    pyside_dir = next(
        (
            candidate / "PySide6"
            for candidate in site_packages_candidates
            if (candidate / "PySide6").exists()
        ),
        None,
    )
    if pyside_dir:
        print(f"ℹ️ PySide6 detected at: {pyside_dir}")
    else:
        print(
            "⚠️ PySide6 site-packages not found; ensure the virtual environment is synced before launching."
        )
    plugins_dir = pyside_dir / "plugins" if pyside_dir else None
    qml_dir = pyside_dir / "qml" if pyside_dir else None
    assets_qml = root / "assets" / "qml"

    if plugins_dir and plugins_dir.exists() and not env.get("QT_PLUGIN_PATH"):
        env["QT_PLUGIN_PATH"] = str(plugins_dir)

    if qml_dir:
        _append_env_path(env, "QML2_IMPORT_PATH", qml_dir)
        _append_env_path(env, "QML_IMPORT_PATH", qml_dir)
    _append_env_path(env, "QML2_IMPORT_PATH", assets_qml)
    _append_env_path(env, "QML_IMPORT_PATH", assets_qml)

    env.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    env.setdefault("PSS_QML_SCENE", "realism")


def build_args(
    *,
    verbose: bool,
    diag: bool,
    test_mode: bool,
    safe_mode: bool,
    legacy: bool,
    no_qml: bool,
    env_check: bool,
    env_report_path: str | None,
) -> list[str]:
    args: list[str] = []
    if env_check:
        args.append("--env-check")
    if env_report_path:
        args.extend(["--env-report", env_report_path])
    if no_qml:
        args.append("--no-qml")
    if test_mode:
        args.append("--test-mode")
    if verbose:
        args.append("--verbose")
    if diag:
        args.append("--diag")
    if safe_mode:
        args.append("--safe-mode")
    if legacy:
        args.append("--legacy")
    return args


def configure_runtime_env(
    *,
    base_env: dict[str, str],
    headless: bool,
    qpa_choice: str,
    rhi_choice: str,
    quick_backend: str,
    style_choice: str,
    scene_choice: str,
) -> dict[str, str]:
    env = base_env.copy()
    ensure_qt_environment(env)

    if headless:
        env["PSS_HEADLESS"] = "1"
    else:
        env.pop("PSS_HEADLESS", None)

    if qpa_choice and qpa_choice != "(auto)":
        env["QT_QPA_PLATFORM"] = qpa_choice
    if rhi_choice and rhi_choice != "(auto)":
        env["QSG_RHI_BACKEND"] = rhi_choice
    if quick_backend.strip():
        env["QT_QUICK_BACKEND"] = quick_backend.strip()
    else:
        env.pop("QT_QUICK_BACKEND", None)
    if style_choice and style_choice != "(auto)":
        env["QT_QUICK_CONTROLS_STYLE"] = style_choice
    if scene_choice and scene_choice != "(auto)":
        env["PSS_QML_SCENE"] = scene_choice
    if os.name == "nt" and "QSG_RHI_BACKEND" not in env:
        env.setdefault("QSG_RHI_BACKEND", "d3d11")

    # Включаем подробный вывод QML ошибок, если verbose
    env.setdefault("QT_FORCE_STDERR_LOGGING", "1")  # Qt < 6.7 не всегда
    return env


def build_test_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    env.setdefault("PSS_HEADLESS", "1")
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env.setdefault("QT_QUICK_BACKEND", "software")
    env.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    return env


def build_testing_entrypoint_command(
    python_exe: Path, scope: Literal["main", "integration", "all"]
) -> list[str]:
    entrypoint = project_root() / "scripts" / "testing_entrypoint.py"
    cmd = [str(python_exe), str(entrypoint)]
    if scope not in {"main", "integration", "all"}:
        scope = "main"
    cmd.extend(["--scope", scope])
    return cmd


def build_custom_pytest_command(
    python_exe: Path,
    *,
    targets: Sequence[str],
    extra_args: Sequence[str] | None = None,
) -> list[str]:
    """Build a direct pytest invocation for configurable runs."""

    cmd = [str(python_exe), "-m", "pytest", *targets]
    if extra_args:
        cmd.extend(extra_args)
    return cmd


def run_log_analysis(env: dict[str, str]) -> str:
    """Запустить анализ логов с понятными сообщениями об ошибках."""

    root = project_root()
    analyzer = root / "tools" / "analyze_logs.py"
    if not root.exists():
        return f"Каталог проекта недоступен: {root}"

    if not analyzer.exists():
        return (
            "Не найден анализатор логов: tools/analyze_logs.py. "
            "Убедитесь, что скрипт присутствует в репозитории."
        )

    graphics_logs = root / LOGS_DIR / "graphics"
    if graphics_logs.exists() and not graphics_logs.is_dir():
        return (
            f"Ожидалась директория с логами, но найден файл: {graphics_logs}. "
            "Проверьте настройки путей логов."
        )
    if not graphics_logs.exists():
        return "Логи графики отсутствуют (ожидалось: logs/graphics)."

    python_exe = detect_venv_python(prefer_console=True)
    if not python_exe.exists():
        return (
            f"Интерпретатор Python не найден: {python_exe}. "
            "Воссоздайте виртуальное окружение (make uv-sync)."
        )
    try:
        completed = run_command_logged(
            [str(python_exe), "-m", "tools.analyze_logs"], cwd=root, env=env
        )
    except FileNotFoundError as exc:
        return f"Python интерпретатор недоступен: {exc}"
    except Exception as exc:  # pragma: no cover - непредвиденные ошибки запуска
        return f"Ошибка запуска анализатора логов: {exc}"

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        detail = format_completed_process(
            [str(python_exe), "-m", "tools.analyze_logs"], completed
        )
        return f"Анализ логов завершился с ошибкой (exit={completed.returncode}).\n{detail}"
    combo = stdout
    if stderr:
        combo = f"{combo}\n[stderr]\n{stderr}" if combo else f"[stderr]\n{stderr}"
    return combo or "(analyze_logs: пустой вывод)"


def launch_app(
    *,
    args: Iterable[str],
    env: dict[str, str],
    mode: CreateFlag,
    force_console: bool,
    capture_buffer: list[str] | None = None,
) -> subprocess.Popen[bytes]:
    root = project_root()
    app_path = root / "app.py"
    if not app_path.exists():
        raise FileNotFoundError(
            f"Application entrypoint not found: {app_path}. Проверьте путь к проекту."
        )
    if not root.exists():
        raise FileNotFoundError(
            f"Project root is unavailable: {root}. Убедитесь, что каталог существует."
        )
    prefer_console = (
        force_console
        or any(
            a in ("--env-check", "--env-report", "--test-mode", "--verbose", "--diag")
            for a in args
        )
        or (env.get("PSS_HEADLESS") or "").strip().lower() in {"1", "true", "yes", "on"}
    )
    python_exe = detect_venv_python(prefer_console=prefer_console)
    if not python_exe.exists():
        raise FileNotFoundError(
            f"Python interpreter not found at {python_exe}. Выполните make uv-sync для настройки окружения."
        )

    cmd = [str(python_exe), str(root / "app.py"), *list(args)]
    _log(f"Launching app with mode={mode}: {_format_command(cmd)}")

    creationflags = 0
    popen_kwargs: dict[str, object] = {
        "cwd": str(root),
        "env": env,
    }

    if os.name == "nt" and mode == "new_console":
        creationflags |= subprocess.CREATE_NEW_CONSOLE  # type: ignore[attr-defined]
        popen_kwargs["creationflags"] = creationflags
    elif os.name == "nt" and mode == "detached":
        creationflags |= subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
        popen_kwargs["creationflags"] = creationflags
    else:  # capture
        popen_kwargs["stdout"] = subprocess.PIPE
        popen_kwargs["stderr"] = subprocess.STDOUT
        popen_kwargs["text"] = True
        popen_kwargs["encoding"] = "utf-8"
        popen_kwargs["errors"] = "replace"

    try:
        proc = subprocess.Popen(cmd, **popen_kwargs)  # type: ignore[arg-type]
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Не удалось запустить приложение: исполняемый файл недоступен ({cmd[0]})."
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            f"Не удалось запустить приложение: {exc.strerror or exc}"
        ) from exc

    if mode == "capture" and proc.stdout is not None and capture_buffer is not None:

        def _reader() -> None:
            for line in proc.stdout:  # type: ignore[union-attr]
                capture_buffer.append(line.rstrip("\n"))

        threading.Thread(target=_reader, daemon=True).start()
    return proc


class LauncherUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PneumoStabSim Launcher (Windows)")
        self.geometry("880x660")
        self.resizable(True, True)

        # State
        self.var_verbose = tk.BooleanVar(value=False)
        self.var_diag = tk.BooleanVar(value=False)
        self.var_test = tk.BooleanVar(value=False)
        self.var_safe_mode = tk.BooleanVar(value=False)
        self.var_legacy = tk.BooleanVar(value=False)
        self.var_no_qml = tk.BooleanVar(value=False)

        self.var_headless = tk.BooleanVar(value=False)
        self.var_qpa = tk.StringVar(value=QPA_CHOICES[0])
        self.var_rhi = tk.StringVar(value=RHI_CHOICES[0])
        self.var_quick_backend = tk.StringVar(value="")
        self.var_style = tk.StringVar(value=STYLE_CHOICES[0])
        self.var_scene = tk.StringVar(value=SCENE_CHOICES[1])

        self.var_env_check = tk.BooleanVar(value=False)
        self.var_env_report = tk.StringVar(value="")

        self.var_console = tk.BooleanVar(value=False)  # new console window
        self.var_capture = tk.BooleanVar(value=True)  # собирать вывод

        self.var_log_dir = tk.StringVar(value=str(self._autodetect_log_dir()))
        self.var_log_lines = tk.IntVar(value=DEFAULT_LOG_LINES)

        self.var_test_runner = tk.StringVar(value="entrypoint")
        self.var_test_scope = tk.StringVar(value=TEST_SCOPE_CHOICES[0])
        self.var_test_targets = tk.StringVar(value="tests")
        self.var_test_args = tk.StringVar(value="")
        self.var_test_canvas = tk.BooleanVar(value=True)

        self.lbl_status: ttk.Label | None = None
        self._widgets: dict[str, tk.Widget] = {}

        # Буфер вывода
        self._captured_output: list[str] = []
        self._test_canvas: TestAnimationCanvas | None = None

        self._build_ui()
        self._attach_tooltips()

    # --- UI build
    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        menubar = tk.Menu(self)
        actions_menu = tk.Menu(menubar, tearoff=0)
        actions_menu.add_command(label="Запустить приложение", command=self._on_run)
        actions_menu.add_command(
            label="Показать свежие логи", command=self._open_logs_viewer
        )
        actions_menu.add_command(
            label="Выбор конфигурации...", command=self._open_configuration_dialog
        )
        actions_menu.add_command(
            label="Быстрый статус (git+линтер)", command=self._run_repo_status
        )
        menubar.add_cascade(label="Действия", menu=actions_menu)

        tests_menu = tk.Menu(menubar, tearoff=0)
        tests_menu.add_command(
            label="Базовые тесты (entrypoint)",
            command=lambda: self._run_tests(scope="main"),
        )
        tests_menu.add_command(
            label="Интеграционные тесты",
            command=lambda: self._run_tests(scope="integration"),
        )
        menubar.add_cascade(label="Тесты", menu=tests_menu)
        self.config(menu=menubar)

        frm_launch = ttk.Labelframe(self, text="Параметры запуска (CLI)")
        frm_launch.pack(fill="x", **pad)
        self._widgets["chk_verbose"] = ttk.Checkbutton(
            frm_launch, text="Verbose (--verbose)", variable=self.var_verbose
        )
        self._widgets["chk_verbose"].grid(row=0, column=0, sticky="w", **pad)
        self._widgets["chk_diag"] = ttk.Checkbutton(
            frm_launch, text="Diagnostics (--diag)", variable=self.var_diag
        )
        self._widgets["chk_diag"].grid(row=0, column=1, sticky="w", **pad)
        self._widgets["chk_test"] = ttk.Checkbutton(
            frm_launch, text="Test mode (--test-mode)", variable=self.var_test
        )
        self._widgets["chk_test"].grid(row=1, column=0, sticky="w", **pad)
        self._widgets["chk_safe_mode"] = ttk.Checkbutton(
            frm_launch, text="Safe mode (--safe-mode)", variable=self.var_safe_mode
        )
        self._widgets["chk_safe_mode"].grid(row=1, column=1, sticky="w", **pad)
        self._widgets["chk_legacy"] = ttk.Checkbutton(
            frm_launch, text="Legacy UI (--legacy)", variable=self.var_legacy
        )
        self._widgets["chk_legacy"].grid(row=2, column=0, sticky="w", **pad)
        self._widgets["chk_no_qml"] = ttk.Checkbutton(
            frm_launch, text="No QML (--no-qml)", variable=self.var_no_qml
        )
        self._widgets["chk_no_qml"].grid(row=2, column=1, sticky="w", **pad)

        frm_env = ttk.Labelframe(self, text="Окружение Qt/QtQuick")
        frm_env.pack(fill="x", **pad)
        self._widgets["chk_headless"] = ttk.Checkbutton(
            frm_env, text="Headless (PSS_HEADLESS)", variable=self.var_headless
        )
        self._widgets["chk_headless"].grid(row=0, column=0, sticky="w", **pad)
        ttk.Label(frm_env, text="QT_QPA_PLATFORM:").grid(
            row=1, column=0, sticky="e", **pad
        )
        self._widgets["cmb_qpa"] = ttk.Combobox(
            frm_env,
            textvariable=self.var_qpa,
            values=QPA_CHOICES,
            state="readonly",
            width=20,
        )
        self._widgets["cmb_qpa"].grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(frm_env, text="QSG_RHI_BACKEND:").grid(
            row=2, column=0, sticky="e", **pad
        )
        self._widgets["cmb_rhi"] = ttk.Combobox(
            frm_env,
            textvariable=self.var_rhi,
            values=RHI_CHOICES,
            state="readonly",
            width=20,
        )
        self._widgets["cmb_rhi"].grid(row=2, column=1, sticky="w", **pad)
        ttk.Label(frm_env, text="QT_QUICK_BACKEND:").grid(
            row=3, column=0, sticky="e", **pad
        )
        self._widgets["ent_quick_backend"] = ttk.Entry(
            frm_env, textvariable=self.var_quick_backend, width=24
        )
        self._widgets["ent_quick_backend"].grid(row=3, column=1, sticky="w", **pad)
        ttk.Label(frm_env, text="QT_QUICK_CONTROLS_STYLE:").grid(
            row=4, column=0, sticky="e", **pad
        )
        self._widgets["cmb_style"] = ttk.Combobox(
            frm_env,
            textvariable=self.var_style,
            values=STYLE_CHOICES,
            state="readonly",
            width=20,
        )
        self._widgets["cmb_style"].grid(row=4, column=1, sticky="w", **pad)
        ttk.Label(frm_env, text="PSS_QML_SCENE:").grid(
            row=5, column=0, sticky="e", **pad
        )
        self._widgets["cmb_scene"] = ttk.Combobox(
            frm_env,
            textvariable=self.var_scene,
            values=SCENE_CHOICES,
            state="readonly",
            width=20,
        )
        self._widgets["cmb_scene"].grid(row=5, column=1, sticky="w", **pad)

        frm_diag = ttk.Labelframe(self, text="Диагностика окружения")
        frm_diag.pack(fill="x", **pad)
        self._widgets["chk_env_check"] = ttk.Checkbutton(
            frm_diag,
            text="--env-check (только диагностика)",
            variable=self.var_env_check,
        )
        self._widgets["chk_env_check"].grid(row=0, column=0, sticky="w", **pad)
        ttk.Label(frm_diag, text="--env-report PATH:").grid(
            row=1, column=0, sticky="e", **pad
        )
        self._widgets["ent_env_report"] = ttk.Entry(
            frm_diag, textvariable=self.var_env_report, width=40
        )
        self._widgets["ent_env_report"].grid(row=1, column=1, sticky="w", **pad)
        self._widgets["btn_browse_env"] = ttk.Button(
            frm_diag, text="Обзор...", command=self._browse_env_report
        )
        self._widgets["btn_browse_env"].grid(row=1, column=2, sticky="w", **pad)

        frm_logs = ttk.Labelframe(self, text="Логи и ошибки")
        frm_logs.pack(fill="x", **pad)
        ttk.Label(frm_logs, text="Директория логов:").grid(
            row=0, column=0, sticky="e", **pad
        )
        self._widgets["ent_log_dir"] = ttk.Entry(
            frm_logs, textvariable=self.var_log_dir, width=50
        )
        self._widgets["ent_log_dir"].grid(row=0, column=1, sticky="w", **pad)
        self._widgets["btn_browse_logs"] = ttk.Button(
            frm_logs, text="Выбрать...", command=self._browse_log_dir
        )
        self._widgets["btn_browse_logs"].grid(row=0, column=2, sticky="w", **pad)
        ttk.Label(frm_logs, text="Последние N строк:").grid(
            row=1, column=0, sticky="e", **pad
        )
        self._widgets["spn_log_lines"] = ttk.Spinbox(
            frm_logs,
            from_=50,
            to=2000,
            increment=50,
            textvariable=self.var_log_lines,
            width=10,
        )
        self._widgets["spn_log_lines"].grid(row=1, column=1, sticky="w", **pad)
        self._widgets["btn_show_logs"] = ttk.Button(
            frm_logs, text="Показать свежие логи", command=self._open_logs_viewer
        )
        self._widgets["btn_show_logs"].grid(row=1, column=2, sticky="w", **pad)

        frm_repo = ttk.Labelframe(self, text="Состояние репозитория/кода")
        frm_repo.pack(fill="x", **pad)
        self._widgets["btn_repo_status"] = ttk.Button(
            frm_repo,
            text="Быстрый статус (git + линтер)",
            command=self._run_repo_status,
        )
        self._widgets["btn_repo_status"].grid(row=0, column=0, sticky="w", **pad)

        frm_tests = ttk.Labelframe(self, text="Настройки тестирования")
        frm_tests.pack(fill="x", **pad)
        ttk.Label(frm_tests, text="Раннер:").grid(row=0, column=0, sticky="e", **pad)
        self._widgets["rad_entrypoint"] = ttk.Radiobutton(
            frm_tests,
            text="Unified entrypoint",
            variable=self.var_test_runner,
            value="entrypoint",
        )
        self._widgets["rad_entrypoint"].grid(row=0, column=1, sticky="w", **pad)
        self._widgets["rad_pytest"] = ttk.Radiobutton(
            frm_tests,
            text="Pytest напрямую",
            variable=self.var_test_runner,
            value="pytest",
        )
        self._widgets["rad_pytest"].grid(row=0, column=2, sticky="w", **pad)

        ttk.Label(frm_tests, text="Scope/таргеты:").grid(
            row=1, column=0, sticky="e", **pad
        )
        self._widgets["cmb_scope"] = ttk.Combobox(
            frm_tests,
            textvariable=self.var_test_scope,
            values=TEST_SCOPE_CHOICES,
            state="readonly",
            width=12,
        )
        self._widgets["cmb_scope"].grid(row=1, column=1, sticky="w", **pad)
        self._widgets["ent_targets"] = ttk.Entry(
            frm_tests, textvariable=self.var_test_targets, width=40
        )
        self._widgets["ent_targets"].grid(row=1, column=2, sticky="w", **pad)

        ttk.Label(frm_tests, text="Доп. аргументы:").grid(
            row=2, column=0, sticky="e", **pad
        )
        self._widgets["ent_test_args"] = ttk.Entry(
            frm_tests, textvariable=self.var_test_args, width=60
        )
        self._widgets["ent_test_args"].grid(
            row=2, column=1, columnspan=2, sticky="we", **pad
        )
        self._widgets["chk_test_canvas"] = ttk.Checkbutton(
            frm_tests, text="Показать канву со схемой", variable=self.var_test_canvas
        )
        self._widgets["chk_test_canvas"].grid(row=3, column=1, sticky="w", **pad)
        self._widgets["btn_test_run"] = ttk.Button(
            frm_tests,
            text="Запустить тесты (с настройками)",
            command=self._run_tests_with_config,
        )
        self._widgets["btn_test_run"].grid(row=3, column=2, sticky="e", **pad)

        frm_actions = ttk.Frame(self)
        frm_actions.pack(fill="x", **pad)
        self._widgets["chk_console"] = ttk.Checkbutton(
            frm_actions, text="Новое окно консоли", variable=self.var_console
        )
        self._widgets["chk_console"].pack(side="left", padx=6)
        self._widgets["chk_capture"] = ttk.Checkbutton(
            frm_actions,
            text="Собирать stdout/stderr внутри лаунчера",
            variable=self.var_capture,
        )
        self._widgets["chk_capture"].pack(side="left", padx=6)
        self._widgets["btn_run"] = ttk.Button(
            frm_actions, text="Запустить", command=self._on_run
        )
        self._widgets["btn_run"].pack(side="right", padx=6)
        self._widgets["btn_envcheck"] = ttk.Button(
            frm_actions, text="Env Check", command=self._on_env_check
        )
        self._widgets["btn_envcheck"].pack(side="right", padx=6)
        self._widgets["btn_help"] = ttk.Button(
            frm_actions, text="Справка", command=self._open_help
        )
        self._widgets["btn_help"].pack(side="right", padx=6)
        self._widgets["btn_exit"] = ttk.Button(
            frm_actions, text="Выход", command=self.destroy
        )
        self._widgets["btn_exit"].pack(side="right", padx=6)

        status_text = (
            f"Platform: {DETECTED_PLATFORM}\n"
            f"Project root: {project_root()}\n"
            f"Python: {sys.executable}"
        )
        self.lbl_status = ttk.Label(self, text=status_text)
        self.lbl_status.pack(fill="x", padx=10, pady=10)

    # --- Tooltips
    def _attach_tooltips(self) -> None:
        tips = {
            "chk_verbose": "Verbose: подробные логи (--verbose).",
            "chk_diag": "Diagnostics: итоговая диагностика (--diag).",
            "chk_test": "Test mode: ускоренный сценарий (--test-mode).",
            "chk_safe_mode": "Safe mode: Qt сам выбирает backend (--safe-mode).",
            "chk_legacy": "Legacy UI: устаревший интерфейс без QML (--legacy).",
            "chk_no_qml": "No QML: отключить загрузку сцены (--no-qml).",
            "chk_headless": "Headless: без окна (PSS_HEADLESS=1).",
            "cmb_qpa": "QT_QPA_PLATFORM: платформа (windows/offscreen/minimal).",
            "cmb_rhi": "QSG_RHI_BACKEND: движок рендеринга (d3d11/opengl/vulkan).",
            "ent_quick_backend": "QT_QUICK_BACKEND: 'software' для софтверного рендера или пусто для авто.",
            "cmb_style": "Стиль контролов Qt Quick (Basic/Fusion).",
            "cmb_scene": "QML сцена (обычно realism).",
            "chk_env_check": "--env-check: быстрая диагностика окружения и выход.",
            "ent_env_report": "Путь для отчёта (--env-report PATH).",
            "btn_browse_env": "Выбор файла отчёта окружения.",
            "chk_console": "Запуск в отдельном окне консоли.",
            "chk_capture": "Захват stdout/stderr внутри лаунчера.",
            "btn_run": "Запустить приложение.",
            "btn_envcheck": "Диагностика окружения.",
            "btn_help": "Открыть справку.",
            "btn_show_logs": "Показать последние строки свежих логов и сводку ошибок/варнингов.",
            "btn_repo_status": "Собрать git status и краткий отчёт рут-файлов от линтера.",
            "rad_entrypoint": "Использовать scripts/testing_entrypoint.py для стандартной матрицы.",
            "rad_pytest": "Запуск pytest напрямую по выбранным таргетам.",
            "cmb_scope": "Scope unified entrypoint (main/integration/all).",
            "ent_targets": "Pytest таргеты (путь к тесту, директория или маркеры через -m).",
            "ent_test_args": "Дополнительные аргументы pytest, например -k smoke или -q.",
            "chk_test_canvas": "Открыть канву с анимированной схемой тестового пайплайна.",
            "btn_test_run": "Запустить тесты с текущими настройками и визуализацией.",
        }
        for key, text in tips.items():
            w = self._widgets.get(key)
            if w:
                try:
                    Tooltip(w, text)
                except Exception:
                    pass

    def _open_configuration_dialog(self) -> None:
        win = tk.Toplevel(self)
        win.title("Выбор конфигурации")
        win.geometry("760x520")

        frm_flags = ttk.Labelframe(win, text="Флаги запуска")
        frm_flags.pack(fill="x", padx=10, pady=8)
        ttk.Checkbutton(
            frm_flags, text="Verbose (--verbose)", variable=self.var_verbose
        ).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(
            frm_flags, text="Diagnostics (--diag)", variable=self.var_diag
        ).grid(row=0, column=1, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(
            frm_flags, text="Test mode (--test-mode)", variable=self.var_test
        ).grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(
            frm_flags, text="Safe mode (--safe-mode)", variable=self.var_safe_mode
        ).grid(row=1, column=1, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(
            frm_flags, text="Legacy UI (--legacy)", variable=self.var_legacy
        ).grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(
            frm_flags, text="No QML (--no-qml)", variable=self.var_no_qml
        ).grid(row=2, column=1, sticky="w", padx=6, pady=4)

        frm_env = ttk.Labelframe(win, text="Параметры среды")
        frm_env.pack(fill="x", padx=10, pady=8)
        ttk.Checkbutton(
            frm_env, text="Headless (PSS_HEADLESS)", variable=self.var_headless
        ).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(frm_env, text="QT_QPA_PLATFORM:").grid(
            row=1, column=0, sticky="e", padx=6, pady=4
        )
        ttk.Combobox(
            frm_env,
            textvariable=self.var_qpa,
            values=QPA_CHOICES,
            state="readonly",
            width=20,
        ).grid(row=1, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(frm_env, text="QSG_RHI_BACKEND:").grid(
            row=2, column=0, sticky="e", padx=6, pady=4
        )
        ttk.Combobox(
            frm_env,
            textvariable=self.var_rhi,
            values=RHI_CHOICES,
            state="readonly",
            width=20,
        ).grid(row=2, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(frm_env, text="QT_QUICK_CONTROLS_STYLE:").grid(
            row=3, column=0, sticky="e", padx=6, pady=4
        )
        ttk.Combobox(
            frm_env,
            textvariable=self.var_style,
            values=STYLE_CHOICES,
            state="readonly",
            width=20,
        ).grid(row=3, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(frm_env, text="PSS_QML_SCENE:").grid(
            row=4, column=0, sticky="e", padx=6, pady=4
        )
        ttk.Combobox(
            frm_env,
            textvariable=self.var_scene,
            values=SCENE_CHOICES,
            state="readonly",
            width=20,
        ).grid(row=4, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(frm_env, text="QT_QUICK_BACKEND:").grid(
            row=5, column=0, sticky="e", padx=6, pady=4
        )
        ttk.Entry(frm_env, textvariable=self.var_quick_backend, width=24).grid(
            row=5, column=1, sticky="w", padx=6, pady=4
        )

        ttk.Label(
            win,
            text="Настройки обновляются мгновенно, отдельного подтверждения не требуется.",
        ).pack(fill="x", padx=10, pady=8)
        ttk.Button(win, text="Закрыть", command=win.destroy).pack(pady=6)

    # --- Helpers: logs and repo status
    def _autodetect_log_dir(self) -> Path:
        root = project_root()
        candidates = self._extract_log_dirs_from_config()
        if not candidates:
            candidates.append(root / "logs")
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def _extract_log_dirs_from_config(self) -> list[Path]:
        """Попытка найти путь к логам в config/app_settings.json."""

        config_path = project_root() / "config" / "app_settings.json"
        if not config_path.exists():
            return []

        try:
            with config_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return []

        found: list[Path] = []

        def _walk(value: object) -> None:
            if isinstance(value, dict):
                for key, val in value.items():
                    if isinstance(key, str) and isinstance(val, str):
                        k_lower = key.lower()
                        if "log" in k_lower and ("dir" in k_lower or "path" in k_lower):
                            candidate = Path(val)
                            found.append(
                                candidate
                                if candidate.is_absolute()
                                else project_root() / candidate
                            )
                    _walk(val)
            elif isinstance(value, list):
                for item in value:
                    _walk(item)

        _walk(data)
        return found

    def _browse_log_dir(self) -> None:
        try:
            selected = filedialog.askdirectory(
                title="Выберите директорию с логами",
                initialdir=self.var_log_dir.get() or str(project_root()),
                mustexist=False,
            )
            if selected:
                self.var_log_dir.set(selected)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выбрать директорию логов: {e}")

    def _open_logs_viewer(self) -> None:
        try:
            max_lines = max(int(self.var_log_lines.get()), 10)
        except Exception:
            max_lines = DEFAULT_LOG_LINES
            self.var_log_lines.set(DEFAULT_LOG_LINES)
        log_dir = Path(self.var_log_dir.get().strip() or project_root() / "logs")
        threading.Thread(
            target=self._collect_logs, args=(log_dir, max_lines), daemon=True
        ).start()

    def _collect_logs(self, log_dir: Path, max_lines: int) -> None:
        if not log_dir.exists():
            self.after(
                0,
                lambda: messagebox.showwarning(
                    "Логи", f"Директория {log_dir} не найдена."
                ),
            )
            return
        summary = self._read_recent_logs(log_dir, max_lines)
        self.after(
            0,
            lambda: self._show_text_window(
                title="Свежие логи", text=summary, geometry="1000x760"
            ),
        )

    def _read_recent_logs(self, log_dir: Path, max_lines: int) -> str:
        log_files = sorted(
            [p for p in log_dir.rglob("*") if p.suffix in LOG_EXTENSIONS],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not log_files:
            return f"Лог-файлы в {log_dir} не найдены."

        latest = log_files[0]
        try:
            tail, counts, highlights = summarize_log_tail(latest, max_lines)
        except Exception as e:
            return f"Не удалось прочитать {latest}: {e}"

        overview: list[str] = []
        for candidate in log_files[:5]:
            try:
                _, c_counts, _ = summarize_log_tail(candidate, max_lines)
            except Exception:
                continue
            overview.append(
                f"- {candidate.name}: ошибок={c_counts['error']}, предупреждений={c_counts['warning']}"
            )
        header_parts = [
            f"Файл: {latest}",
            f"Ошибок: {counts['error']} | Предупреждений: {counts['warning']}",
            f"Показаны последние {len(tail)} строк",
        ]
        if overview:
            header_parts.append("Сводка свежих логов:")
            header_parts.extend(overview)
        if highlights:
            header_parts.append("Ключевые строки (ошибки/варнинги):")
            header_parts.extend(highlights[-20:])
        header = "\n".join(header_parts)
        return f"{header}\n\n--- Хвост логов ---\n" + "\n".join(tail)

    def _show_text_window(
        self, *, title: str, text: str, geometry: str = "980x720"
    ) -> None:
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry(geometry)
        frm = ttk.Frame(win)
        frm.pack(fill="both", expand=True)
        txt = tk.Text(frm, wrap="none")
        vs = ttk.Scrollbar(frm, orient="vertical", command=txt.yview)
        hs = ttk.Scrollbar(frm, orient="horizontal", command=txt.xview)
        txt.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        vs.pack(side="right", fill="y")
        hs.pack(side="bottom", fill="x")
        txt.pack(side="left", fill="both", expand=True)
        try:
            txt.insert("1.0", text)
            txt.configure(state="disabled")
        except Exception:
            pass

    def _run_tests(self, scope: Literal["main", "integration"]) -> None:
        self.var_test_runner.set("entrypoint")
        self.var_test_scope.set(scope)
        self._run_tests_with_config()

    def _collect_test_config(self) -> TestRunConfig:
        raw_targets = self.var_test_targets.get().strip()
        targets = shlex.split(raw_targets) if raw_targets else ["tests"]
        extra = (
            shlex.split(self.var_test_args.get().strip())
            if self.var_test_args.get().strip()
            else []
        )
        scope_value = (
            self.var_test_scope.get()
            if self.var_test_scope.get() in TEST_SCOPE_CHOICES
            else TEST_SCOPE_CHOICES[0]
        )
        runner: Literal["entrypoint", "pytest"] = (
            "pytest" if self.var_test_runner.get() == "pytest" else "entrypoint"
        )
        return TestRunConfig(
            runner=runner,
            scope=scope_value,  # type: ignore[arg-type]
            targets=list(targets),
            extra_args=list(extra),
            show_canvas=self.var_test_canvas.get(),
        )

    def _ensure_test_canvas(self, enabled: bool) -> TestAnimationCanvas | None:
        if not enabled:
            if self._test_canvas:
                self._test_canvas.destroy()
            self._test_canvas = None
            return None
        if self._test_canvas is None:
            self._test_canvas = TestAnimationCanvas(self)
        self._test_canvas.start()
        return self._test_canvas

    def _run_tests_with_config(self) -> None:
        config = self._collect_test_config()
        label = (
            "pytest" if config.runner == "pytest" else f"entrypoint ({config.scope})"
        )
        self._set_status(f"Запуск тестов через {label}...")
        canvas = self._ensure_test_canvas(config.show_canvas)
        threading.Thread(
            target=self._execute_tests_with_config, args=(config, canvas), daemon=True
        ).start()

    def _execute_tests_with_config(
        self, config: TestRunConfig, canvas: TestAnimationCanvas | None
    ) -> None:
        root = project_root()
        python_exe = detect_venv_python(prefer_console=True)
        text = ""
        success = False
        if config.runner == "entrypoint":
            entrypoint = root / "scripts" / "testing_entrypoint.py"
            if not entrypoint.exists():
                text = f"Entrypoint not found: {entrypoint}"
            else:
                env = build_test_environment()
                command = build_testing_entrypoint_command(python_exe, config.scope)
                text = self._run_command(
                    command, f"testing_entrypoint ({config.scope})", cwd=root, env=env
                )
                success = "exit=0" in text or "Ошибок: 0" in text
        else:
            env = build_test_environment()
            command = build_custom_pytest_command(
                python_exe,
                targets=config.targets or ["tests"],
                extra_args=config.extra_args,
            )
            text = self._run_command(command, "pytest (custom)", cwd=root, env=env)
            success = "exit=0" in text or "Ошибок: 0" in text

        message = "✅ Тесты завершены" if success else "⚠️ Найдены ошибки"
        if canvas:
            self.after(0, lambda: canvas.mark_complete(success, message))
        self.after(
            0,
            lambda: self._show_text_window(
                title="Результаты тестов",
                text=text or "(нет вывода)",
                geometry="1100x820",
            ),
        )
        self.after(0, lambda: self._set_status("Тестовый прогон завершён."))

    def _run_repo_status(self) -> None:
        self._set_status("Сбор статуса репозитория и линтера...")
        threading.Thread(target=self._collect_repo_status, daemon=True).start()

    def _collect_repo_status(self) -> None:
        root = project_root()
        sections: list[str] = []
        sections.append(
            self._run_command(["git", "status", "-sb"], "git status", cwd=root)
        )
        python_exe = detect_venv_python(prefer_console=True)
        sections.append(
            self._run_command(
                [
                    str(python_exe),
                    "-m",
                    "ruff",
                    ".",
                    "--select",
                    "E,F,W",
                    "--output-format",
                    "concise",
                ],
                "ruff (E/F/W)",
                cwd=root,
            )
        )
        text = "\n\n".join(sections)
        self.after(
            0,
            lambda: self._show_text_window(
                title="Быстрый статус репозитория", text=text, geometry="1000x800"
            ),
        )
        self.after(0, lambda: self._set_status("Статус репозитория обновлён."))

    def _run_command(
        self,
        cmd: list[str],
        title: str,
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> str:
        try:
            completed, summary = run_command_with_summary(cmd, cwd=cwd, env=env)
        except FileNotFoundError:
            return f"{title}: команда не найдена ({cmd[0]})."
        except Exception as e:
            return f"{title}: ошибка запуска {e}"

        stdout_lines = (completed.stdout or "").splitlines()
        stderr_lines = (completed.stderr or "").splitlines()
        text = summary

        if completed.returncode != 0:
            hint = _detect_failure_hint(stdout_lines + stderr_lines)
            if hint:
                text = f"{text}\nПодсказка: {hint}"

        summary = self._render_summary(stdout_lines + stderr_lines)
        if summary:
            text = f"{text}\n\n{summary}"

        return text

    def _render_summary(self, lines: Sequence[str]) -> str:
        if not lines:
            return ""

        counts = _count_severities(lines)
        highlights = _extract_highlight_lines(lines, limit=12)
        parts = [
            "=== Итоговый анализ stdout/stderr ===",
            f"Ошибок: {counts['error']} | Предупреждений: {counts['warning']}",
        ]
        hint = _detect_failure_hint(lines)
        if hint:
            parts.append(f"Подсказка: {hint}")
        if highlights:
            parts.append("Важные строки:")
            parts.extend(highlights)
        return "\n".join(parts)

    # --- Help window
    def _open_help(self) -> None:
        win = tk.Toplevel(self)
        win.title("Справка по лаунчеру")
        win.geometry("900x700")
        frm = ttk.Frame(win)
        frm.pack(fill="both", expand=True)
        txt = tk.Text(frm, wrap="word")
        vs = ttk.Scrollbar(frm, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=vs.set)
        vs.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        text_help = (
            "Лаунчер: выбор параметров запуска, сбор stdout/stderr, анализ QML ошибок.\n\n"
            "Используйте чекбокс 'Собирать stdout/stderr', если консоль не нужна, но требуется видеть ошибки QML.\n"
            "При 'Новое окно консоли' вывод идёт в отдельное окно и не захватывается. Снимите 'Новое окно консоли' чтобы активировать захват.\n"
            "Секция 'Логи и ошибки' поможет быстро посмотреть последние строки из каталогов logs/ или пути из config/app_settings.json и увидеть подсчёт ошибок/варнингов.\n"
            "Кнопка 'Быстрый статус (git + линтер)' собирает короткий отчёт по git status и ruff (E/F/W).\n"
            "Кнопки 'Запуск тестов' выполняют unified entrypoint (python scripts/testing_entrypoint.py) с теми же переменными окружения, что и в CI: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, PSS_HEADLESS=1, QT_QPA_PLATFORM=offscreen, QT_QUICK_BACKEND=software, LIBGL_ALWAYS_SOFTWARE=1.\n"
            "Результаты тестов сохраняются в reports/tests/test_entrypoint.log и показываются в окне результатов; там же видно хвост логов и метки FAILED/ERROR.\n"
        )
        try:
            txt.insert("1.0", text_help)
            txt.configure(state="disabled")
        except Exception:
            pass

    # --- Arg/env build
    def _collect_args(self) -> list[str]:
        return build_args(
            verbose=self.var_verbose.get(),
            diag=self.var_diag.get(),
            test_mode=self.var_test.get(),
            safe_mode=self.var_safe_mode.get(),
            legacy=self.var_legacy.get(),
            no_qml=self.var_no_qml.get(),
            env_check=self.var_env_check.get(),
            env_report_path=self.var_env_report.get().strip() or None,
        )

    def _collect_env(self) -> dict[str, str]:
        return configure_runtime_env(
            base_env=os.environ.copy(),
            headless=self.var_headless.get(),
            qpa_choice=self.var_qpa.get(),
            rhi_choice=self.var_rhi.get(),
            quick_backend=self.var_quick_backend.get(),
            style_choice=self.var_style.get(),
            scene_choice=self.var_scene.get(),
        )

    # --- Launch
    def _run_with_args(self, args: list[str]) -> None:
        env = self._collect_env()
        # Режим запуска
        if self.var_console.get():
            mode: CreateFlag = "new_console"
        else:
            mode = "capture" if self.var_capture.get() else "detached"
        self._captured_output.clear()
        capture_buffer = self._captured_output if mode == "capture" else None
        try:
            proc = launch_app(
                args=args,
                env=env,
                mode=mode,
                force_console=self.var_console.get()
                or self.var_verbose.get()
                or self.var_diag.get(),
                capture_buffer=capture_buffer,
            )
        except Exception as e:
            messagebox.showerror(
                "Ошибка запуска", f"Не удалось запустить приложение: {e}"
            )
            return
        self._set_status(f"PID={proc.pid} запущено. Ожидание завершения...")
        threading.Thread(
            target=self._monitor_process, args=(proc, env, mode), daemon=True
        ).start()

    def _monitor_process(
        self, proc: subprocess.Popen[bytes], env: dict[str, str], mode: CreateFlag
    ) -> None:
        exit_code = -1
        try:
            exit_code = proc.wait()
        except Exception:
            pass
        time.sleep(0.15)
        analysis_text = self._run_log_analysis(env)
        extra = self._summarize_captured_output() if mode == "capture" else ""
        if extra:
            analysis_text = (
                f"{analysis_text}\n\n=== CAPTURED STDOUT/STDERR (tail) ===\n{extra}"
                if analysis_text
                else extra
            )
        try:
            command_repr = (
                _format_command(proc.args)
                if isinstance(proc.args, Sequence)
                else str(proc.args)
            )
        except Exception:
            command_repr = str(proc.args)
        _log(f"Application process exited with code {exit_code}: {command_repr}")
        if exit_code != 0:
            source_lines: list[str] = []
            if self._captured_output:
                source_lines = self._captured_output
            elif analysis_text:
                source_lines = analysis_text.splitlines()
            hint = _detect_failure_hint(source_lines)
            self.after(
                0,
                lambda: messagebox.showerror(
                    "Ошибка запуска",
                    f"Процесс завершился с кодом {exit_code}.\n\n{hint}",
                ),
            )
        self.after(
            0, lambda: self._show_analysis_window(analysis_text, exit_code, mode)
        )

    def _summarize_captured_output(self, max_lines: int = 200) -> str:
        if not self._captured_output:
            return "(нет захваченного вывода)"
        lines = self._captured_output
        tail = lines[-max_lines:]
        counts = _count_severities(lines)
        interesting = _extract_highlight_lines(lines)
        parts: list[str] = []
        parts.append(f"Ошибок: {counts['error']} | Предупреждений: {counts['warning']}")
        summary = self._render_summary(lines)
        if summary:
            parts.append(summary)
        if interesting:
            parts.append("-- Важные строки (фильтр по ошибкам/QML) --")
            parts.extend(interesting[-60:])
        parts.append("-- Последние строки stdout/stderr --")
        parts.extend(tail)
        return "\n".join(parts)

    # --- Log analysis
    def _run_log_analysis(self, env: dict[str, str]) -> str:
        return run_log_analysis(env)

    def _show_analysis_window(
        self, text: str, app_exit_code: int, mode: CreateFlag
    ) -> None:
        self._set_status("Завершено. Отчёт открыт.")
        win = tk.Toplevel(self)
        win.title("Анализ после завершения приложения")
        win.geometry("980x720")
        frm = ttk.Frame(win)
        frm.pack(fill="both", expand=True)
        header = ttk.Label(
            frm, text=f"Exit={app_exit_code} | launch_mode={mode}", anchor="w"
        )
        header.pack(fill="x", padx=8, pady=6)
        txt = tk.Text(frm, wrap="none")
        vs = ttk.Scrollbar(frm, orient="vertical", command=txt.yview)
        hs = ttk.Scrollbar(frm, orient="horizontal", command=txt.xview)
        txt.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        vs.pack(side="right", fill="y")
        hs.pack(side="bottom", fill="x")
        txt.pack(side="left", fill="both", expand=True)
        self._configure_analysis_tags(txt)
        self._insert_coloured_analysis(txt, text)
        txt.configure(state="disabled")

        actions = ttk.Frame(win)
        actions.pack(pady=6)
        ttk.Button(
            actions,
            text="Копировать отчёт",
            command=lambda: self._copy_to_clipboard(text),
        ).pack(side="left", padx=4)
        ttk.Button(actions, text="Закрыть", command=win.destroy).pack(
            side="left", padx=4
        )

    def _insert_coloured_analysis(self, widget: tk.Text, raw_text: str) -> None:
        content = raw_text if raw_text.strip() else "(анализатор не вернул данных)"
        try:
            for line in content.splitlines():
                severity, emoji = self._classify_line_for_display(line)
                widget.insert("end", f"{emoji}{line}\n", severity)
        except Exception:
            try:
                widget.insert("1.0", content)
            except Exception:
                pass

    def _configure_analysis_tags(self, widget: tk.Text) -> None:
        try:
            widget.tag_configure(
                "error", foreground="#ff4d6d", font=("Segoe UI", 10, "bold")
            )
            widget.tag_configure(
                "warning", foreground="#f4a261", font=("Segoe UI", 10, "bold")
            )
            widget.tag_configure(
                "success", foreground="#2a9d8f", font=("Segoe UI", 10, "bold")
            )
            widget.tag_configure("info", foreground="#1d3557")
        except Exception:
            pass

    def _classify_line_for_display(self, line: str) -> tuple[str, str]:
        low = line.lower()
        if any(token in low for token in ("error", "traceback", "exception", "failed")):
            return "error", "❌ "
        if "warn" in low:
            return "warning", "⚠️ "
        if any(
            token in low for token in ("exit=0", "успешно", "completed successfully")
        ):
            return "success", "✅ "
        return "info", "ℹ️ "

    def _copy_to_clipboard(self, text: str) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._set_status("Отчёт скопирован в буфер обмена.")
        except Exception as exc:
            messagebox.showerror(
                "Копирование не удалось", f"Не удалось скопировать текст: {exc}"
            )

    # --- Handlers
    def _on_run(self) -> None:
        args = self._collect_args()
        self._run_with_args(args)

    def _on_env_check(self) -> None:
        args = self._collect_args()
        if "--env-check" not in args:
            args = ["--env-check", *args]
        self._run_with_args(args)

    def _set_status(self, text: str) -> None:
        if self.lbl_status is not None:
            try:
                self.lbl_status.configure(text=text)
            except Exception:
                pass

    def _browse_env_report(self) -> None:
        """Диалог выбора файла для сохранения отчёта --env-report.

        Создаёт директорию reports/quality при необходимости.
        Сохраняет выбранный путь в var_env_report.
        """
        try:
            default = project_root() / "reports" / "quality" / "envcheck_manual.md"
            default.parent.mkdir(parents=True, exist_ok=True)
            path = filedialog.asksaveasfilename(
                title="Выберите файл для отчёта окружения",
                defaultextension=".md",
                initialdir=str(default.parent),
                initialfile=str(default.name),
                filetypes=[
                    ("Markdown", "*.md"),
                    ("Text", "*.txt"),
                    ("All files", "*.*"),
                ],
            )
            if path:
                self.var_env_report.set(path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выбрать файл отчёта: {e}")


def main() -> int:
    ui = LauncherUI()
    ui.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
