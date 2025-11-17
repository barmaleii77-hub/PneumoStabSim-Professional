#!/usr/bin/env python
"""
Windows Interactive Launcher for PneumoStabSim-Professional

Дополнено: расширенный сбор stdout/stderr, принудительный выбор console-интерпретатора
для verbose/diag и опции консоли, углублённый анализ логов (поиск QML ошибок).
"""
from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import Iterable, Literal
import threading
import time

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --- Constants
QPA_CHOICES: list[str] = ["(auto)", "windows", "offscreen", "minimal"]
RHI_CHOICES: list[str] = ["(auto)", "d3d11", "opengl", "vulkan"]
STYLE_CHOICES: list[str] = ["(auto)", "Basic", "Fusion"]
SCENE_CHOICES: list[str] = ["(auto)", "realism"]

CreateFlag = Literal["new_console", "detached", "capture"]


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
    return preferred if preferred.exists() else (con if con.exists() else Path(sys.executable))


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
    pyside_dir = venv_root / "Lib" / "site-packages" / "PySide6"
    plugins_dir = pyside_dir / "plugins"
    qml_dir = pyside_dir / "qml"
    assets_qml = root / "assets" / "qml"

    if plugins_dir.exists() and not env.get("QT_PLUGIN_PATH"):
        env["QT_PLUGIN_PATH"] = str(plugins_dir)

    _append_env_path(env, "QML2_IMPORT_PATH", qml_dir)
    _append_env_path(env, "QML2_IMPORT_PATH", assets_qml)
    _append_env_path(env, "QML_IMPORT_PATH", qml_dir)
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


def launch_app(
    *, args: Iterable[str], env: dict[str, str], mode: CreateFlag, force_console: bool, capture_buffer: list[str] | None = None
) -> subprocess.Popen[bytes]:
    root = project_root()
    prefer_console = force_console or any(
        a in ("--env-check", "--env-report", "--test-mode", "--verbose", "--diag") for a in args
    ) or (env.get("PSS_HEADLESS") or "").strip().lower() in {"1", "true", "yes", "on"}
    python_exe = detect_venv_python(prefer_console=prefer_console)

    cmd = [str(python_exe), str(root / "app.py"), *list(args)]

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

    proc = subprocess.Popen(cmd, **popen_kwargs)  # type: ignore[arg-type]

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
        self.var_capture = tk.BooleanVar(value=True)   # собирать вывод

        self.lbl_status: ttk.Label | None = None
        self._widgets: dict[str, tk.Widget] = {}

        # Буфер вывода
        self._captured_output: list[str] = []

        self._build_ui()
        self._attach_tooltips()

    # --- UI build
    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        frm_launch = ttk.Labelframe(self, text="Параметры запуска (CLI)")
        frm_launch.pack(fill="x", **pad)
        self._widgets["chk_verbose"] = ttk.Checkbutton(frm_launch, text="Verbose (--verbose)", variable=self.var_verbose)
        self._widgets["chk_verbose"].grid(row=0, column=0, sticky="w", **pad)
        self._widgets["chk_diag"] = ttk.Checkbutton(frm_launch, text="Diagnostics (--diag)", variable=self.var_diag)
        self._widgets["chk_diag"].grid(row=0, column=1, sticky="w", **pad)
        self._widgets["chk_test"] = ttk.Checkbutton(frm_launch, text="Test mode (--test-mode)", variable=self.var_test)
        self._widgets["chk_test"].grid(row=1, column=0, sticky="w", **pad)
        self._widgets["chk_safe_mode"] = ttk.Checkbutton(frm_launch, text="Safe mode (--safe-mode)", variable=self.var_safe_mode)
        self._widgets["chk_safe_mode"].grid(row=1, column=1, sticky="w", **pad)
        self._widgets["chk_legacy"] = ttk.Checkbutton(frm_launch, text="Legacy UI (--legacy)", variable=self.var_legacy)
        self._widgets["chk_legacy"].grid(row=2, column=0, sticky="w", **pad)
        self._widgets["chk_no_qml"] = ttk.Checkbutton(frm_launch, text="No QML (--no-qml)", variable=self.var_no_qml)
        self._widgets["chk_no_qml"].grid(row=2, column=1, sticky="w", **pad)

        frm_env = ttk.Labelframe(self, text="Окружение Qt/QtQuick")
        frm_env.pack(fill="x", **pad)
        self._widgets["chk_headless"] = ttk.Checkbutton(frm_env, text="Headless (PSS_HEADLESS)", variable=self.var_headless)
        self._widgets["chk_headless"].grid(row=0, column=0, sticky="w", **pad)
        ttk.Label(frm_env, text="QT_QPA_PLATFORM:").grid(row=1, column=0, sticky="e", **pad)
        self._widgets["cmb_qpa"] = ttk.Combobox(frm_env, textvariable=self.var_qpa, values=QPA_CHOICES, state="readonly", width=20)
        self._widgets["cmb_qpa"].grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(frm_env, text="QSG_RHI_BACKEND:").grid(row=2, column=0, sticky="e", **pad)
        self._widgets["cmb_rhi"] = ttk.Combobox(frm_env, textvariable=self.var_rhi, values=RHI_CHOICES, state="readonly", width=20)
        self._widgets["cmb_rhi"].grid(row=2, column=1, sticky="w", **pad)
        ttk.Label(frm_env, text="QT_QUICK_BACKEND:").grid(row=3, column=0, sticky="e", **pad)
        self._widgets["ent_quick_backend"] = ttk.Entry(frm_env, textvariable=self.var_quick_backend, width=24)
        self._widgets["ent_quick_backend"].grid(row=3, column=1, sticky="w", **pad)
        ttk.Label(frm_env, text="QT_QUICK_CONTROLS_STYLE:").grid(row=4, column=0, sticky="e", **pad)
        self._widgets["cmb_style"] = ttk.Combobox(frm_env, textvariable=self.var_style, values=STYLE_CHOICES, state="readonly", width=20)
        self._widgets["cmb_style"].grid(row=4, column=1, sticky="w", **pad)
        ttk.Label(frm_env, text="PSS_QML_SCENE:").grid(row=5, column=0, sticky="e", **pad)
        self._widgets["cmb_scene"] = ttk.Combobox(frm_env, textvariable=self.var_scene, values=SCENE_CHOICES, state="readonly", width=20)
        self._widgets["cmb_scene"].grid(row=5, column=1, sticky="w", **pad)

        frm_diag = ttk.Labelframe(self, text="Диагностика окружения")
        frm_diag.pack(fill="x", **pad)
        self._widgets["chk_env_check"] = ttk.Checkbutton(frm_diag, text="--env-check (только диагностика)", variable=self.var_env_check)
        self._widgets["chk_env_check"].grid(row=0, column=0, sticky="w", **pad)
        ttk.Label(frm_diag, text="--env-report PATH:").grid(row=1, column=0, sticky="e", **pad)
        self._widgets["ent_env_report"] = ttk.Entry(frm_diag, textvariable=self.var_env_report, width=40)
        self._widgets["ent_env_report"].grid(row=1, column=1, sticky="w", **pad)
        self._widgets["btn_browse_env"] = ttk.Button(frm_diag, text="Обзор...", command=self._browse_env_report)
        self._widgets["btn_browse_env"].grid(row=1, column=2, sticky="w", **pad)

        frm_actions = ttk.Frame(self)
        frm_actions.pack(fill="x", **pad)
        self._widgets["chk_console"] = ttk.Checkbutton(frm_actions, text="Новое окно консоли", variable=self.var_console)
        self._widgets["chk_console"].pack(side="left", padx=6)
        self._widgets["chk_capture"] = ttk.Checkbutton(frm_actions, text="Собирать stdout/stderr внутри лаунчера", variable=self.var_capture)
        self._widgets["chk_capture"].pack(side="left", padx=6)
        self._widgets["btn_run"] = ttk.Button(frm_actions, text="Запустить", command=self._on_run)
        self._widgets["btn_run"].pack(side="right", padx=6)
        self._widgets["btn_envcheck"] = ttk.Button(frm_actions, text="Env Check", command=self._on_env_check)
        self._widgets["btn_envcheck"].pack(side="right", padx=6)
        self._widgets["btn_help"] = ttk.Button(frm_actions, text="Справка", command=self._open_help)
        self._widgets["btn_help"].pack(side="right", padx=6)
        self._widgets["btn_exit"] = ttk.Button(frm_actions, text="Выход", command=self.destroy)
        self._widgets["btn_exit"].pack(side="right", padx=6)

        self.lbl_status = ttk.Label(self, text=f"Project root: {project_root()}\nPython: {sys.executable}")
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
        }
        for key, text in tips.items():
            w = self._widgets.get(key)
            if w:
                try:
                    Tooltip(w, text)
                except Exception:
                    pass

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
                force_console=self.var_console.get() or self.var_verbose.get() or self.var_diag.get(),
                capture_buffer=capture_buffer,
            )
        except Exception as e:
            messagebox.showerror("Ошибка запуска", f"Не удалось запустить приложение: {e}")
            return
        self._set_status(f"PID={proc.pid} запущено. Ожидание завершения...")
        threading.Thread(target=self._monitor_process, args=(proc, env, mode), daemon=True).start()

    def _monitor_process(self, proc: subprocess.Popen[bytes], env: dict[str, str], mode: CreateFlag) -> None:
        exit_code = -1
        try:
            exit_code = proc.wait()
        except Exception:
            pass
        time.sleep(0.15)
        analysis_text = self._run_log_analysis(env)
        extra = self._summarize_captured_output() if mode == "capture" else ""
        if extra:
            analysis_text = f"{analysis_text}\n\n=== CAPTURED STDOUT/STDERR (tail) ===\n{extra}" if analysis_text else extra
        self.after(0, lambda: self._show_analysis_window(analysis_text, exit_code, mode))

    def _summarize_captured_output(self, max_lines: int = 200) -> str:
        if not self._captured_output:
            return "(нет захваченного вывода)"
        lines = self._captured_output
        # Поиск QML/ошибок
        error_tokens = {"qml", "error", "traceback", "warning", "failed"}
        interesting: list[str] = []
        for ln in lines:
            low = ln.lower()
            if any(tok in low for tok in error_tokens):
                interesting.append(ln)
        tail = lines[-max_lines:]
        parts: list[str] = []
        if interesting:
            parts.append("-- Важные строки (фильтр по ошибкам/QML) --")
            parts.extend(interesting[-60:])
        parts.append("-- Последние строки stdout/stderr --")
        parts.extend(tail)
        return "\n".join(parts)

    # --- Log analysis
    def _run_log_analysis(self, env: dict[str, str]) -> str:
        root = project_root()
        python_exe = detect_venv_python(prefer_console=True)
        cmd = [str(python_exe), "-m", "tools.analyze_logs"]
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(root),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except Exception as e:
            return f"Ошибка запуска анализатора логов: {e}"
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        combo = stdout
        if stderr:
            combo = f"{combo}\n[stderr]\n{stderr}" if combo else f"[stderr]\n{stderr}"
        return combo or "(analyze_logs: пустой вывод)"

    def _show_analysis_window(self, text: str, app_exit_code: int, mode: CreateFlag) -> None:
        self._set_status("Завершено. Отчёт открыт.")
        win = tk.Toplevel(self)
        win.title("Анализ после завершения приложения")
        win.geometry("980x720")
        frm = ttk.Frame(win)
        frm.pack(fill="both", expand=True)
        header = ttk.Label(frm, text=f"Exit={app_exit_code} | launch_mode={mode}", anchor="w")
        header.pack(fill="x", padx=8, pady=6)
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
        ttk.Button(win, text="Закрыть", command=win.destroy).pack(pady=4)

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
                filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All files", "*.*")],
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
