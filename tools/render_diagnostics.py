"""Render diagnostics tool.

Скрипт собирает состояние рендеринга из QML и окружения:
- Qt / PySide6 версии
- Переменные окружения Qt (QT_QPA_PLATFORM, QT_QUICK_BACKEND, QSG_RHI_BACKEND)
- Состояние bypass пост-эффектов и причина
- Статус reflection probe (enabled, quality, refresh)
- SSAO параметры
- Fog параметры
- Текущие значения renderScale / frameRateLimit / renderPolicyKey
- Перечень активных shader warning'ов

Вывод сохраняется в reports/quality/render_diagnostics.json и краткий markdown в reports/quality/render_diagnostics.md

Запуск:
    python -m tools.render_diagnostics [--qml-snapshot] [--no-env]

Опционально можно передать --qml-snapshot для запроса у root объекта его снапшота (ожидается метод dumpRenderSnapshot()).
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    from PySide6.QtWidgets import QApplication
except Exception:
    QApplication = None  # type: ignore


@dataclass
class RenderEnvInfo:
    python_executable: str
    python_version: str
    py_side_version: str | None
    qt_version: str | None
    platform: str
    qt_qpa_platform: str | None
    qt_quick_backend: str | None
    qsg_rhi_backend: str | None
    quick_controls_style: str | None


@dataclass
class RenderStateInfo:
    post_effects_bypassed: bool | None
    post_effects_bypass_reason: str | None
    reflection_enabled: bool | None
    reflection_quality: str | None
    reflection_refresh_mode: str | None
    reflection_time_slicing: str | None
    reflection_padding_m: float | None
    ssao: dict[str, Any]
    fog: dict[str, Any]
    render_scale: float | None
    frame_rate_limit: int | None
    render_policy_key: str | None
    shader_warnings: dict[str, str]


@dataclass
class RenderDiagnosticsReport:
    env: RenderEnvInfo
    state: RenderStateInfo
    snapshot: dict[str, Any] | None


def _collect_env() -> RenderEnvInfo:
    py_side_version = None
    qt_version = None
    try:
        import PySide6
        from PySide6.QtCore import Qt as _Qt

        py_side_version = getattr(PySide6, "__version__", None)
        try:
            qt_version = _Qt.qVersion()  # type: ignore[attr-defined]
        except Exception:
            qt_version = None
    except Exception:
        py_side_version = None
        qt_version = None
    return RenderEnvInfo(
        python_executable=sys.executable,
        python_version=sys.version.split()[0],
        py_side_version=py_side_version,
        qt_version=qt_version,
        platform=os.name,
        qt_qpa_platform=os.environ.get("QT_QPA_PLATFORM"),
        qt_quick_backend=os.environ.get("QT_QUICK_BACKEND"),
        qsg_rhi_backend=os.environ.get("QSG_RHI_BACKEND"),
        quick_controls_style=os.environ.get("QT_QUICK_CONTROLS_STYLE"),
    )


def _find_main_root(app: QApplication) -> Any | None:
    for widget in app.allWidgets():
        try:
            if widget.objectName() == "mainRoot":
                return widget
        except Exception:
            continue
    return None


def _extract_state(root_obj: Any) -> RenderStateInfo:
    def g(name: str) -> Any:
        try:
            return getattr(root_obj, name)
        except Exception:
            return None

    # Attempt to reach the active simulation root
    sim_root = None
    for attr in ("simulationRootItem", "simulationRoot", "simulation_root"):
        candidate = g(attr)
        if candidate is not None:
            sim_root = candidate
            break

    def sg(obj: Any, name: str) -> Any:
        if obj is None:
            return None
        try:
            return getattr(obj, name)
        except Exception:
            return None

    shader_warnings = {}
    if sim_root is not None:
        sw_state = sg(sim_root, "shaderWarningState")
        if isinstance(sw_state, dict):
            shader_warnings = {str(k): str(v) for k, v in sw_state.items()}
    fog = {
        "enabled": bool(g("fogEnabled")),
        "depthEnabled": bool(g("fogDepthEnabled")),
        "depthNear": g("fogDepthNear"),
        "depthFar": g("fogDepthFar"),
        "depthCurve": g("fogDepthCurve"),
    }
    ssao = {
        "enabled": bool(g("ssaoEnabled")),
        "radius": g("ssaoRadius"),
        "intensity": g("ssaoIntensity"),
        "softness": g("ssaoSoftness"),
        "bias": g("ssaoBias"),
        "dither": g("ssaoDither"),
        "sampleRate": g("ssaoSampleRate"),
    }
    return RenderStateInfo(
        post_effects_bypassed=bool(g("postProcessingBypassed")),
        post_effects_bypass_reason=g("postProcessingBypassReason"),
        reflection_enabled=bool(g("reflectionProbeEnabled")),
        reflection_quality=g("reflectionProbeQualitySetting"),
        reflection_refresh_mode=g("reflectionProbeRefreshModeSetting"),
        reflection_time_slicing=g("reflectionProbeTimeSlicingSetting"),
        reflection_padding_m=g("reflectionProbePaddingM"),
        ssao=ssao,
        fog=fog,
        render_scale=g("renderScale"),
        frame_rate_limit=g("frameRateLimit"),
        render_policy_key=g("renderPolicyKey"),
        shader_warnings=shader_warnings,
    )


def _attempt_qml_snapshot(root_obj: Any) -> dict[str, Any] | None:
    if root_obj is None:
        return None
    for name in ("dumpRenderSnapshot", "dump_render_snapshot"):
        handler = getattr(root_obj, name, None)
        if callable(handler):
            try:
                snap = handler()
                if isinstance(snap, dict):
                    return snap
            except Exception:
                return None
    return None


def run(argv: list[str]) -> int:
    want_qml_snapshot = "--qml-snapshot" in argv
    env_only = "--no-env" in argv
    app = None
    root_obj = None
    if QApplication is not None and not env_only:
        try:
            app = QApplication.instance() or QApplication([])
            root_obj = _find_main_root(app)
        except Exception:
            app = None
            root_obj = None
    env_info = _collect_env()
    state_info = (
        _extract_state(root_obj)
        if root_obj
        else RenderStateInfo(
            post_effects_bypassed=None,
            post_effects_bypass_reason=None,
            reflection_enabled=None,
            reflection_quality=None,
            reflection_refresh_mode=None,
            reflection_time_slicing=None,
            reflection_padding_m=None,
            ssao={},
            fog={},
            render_scale=None,
            frame_rate_limit=None,
            render_policy_key=None,
            shader_warnings={},
        )
    )
    snapshot = _attempt_qml_snapshot(root_obj) if want_qml_snapshot else None
    report = RenderDiagnosticsReport(env=env_info, state=state_info, snapshot=snapshot)
    out_dir = Path("reports") / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "render_diagnostics.json").write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_lines = [
        "# Render Diagnostics",
        f"Python: {env_info.python_version} ({env_info.python_executable})",
        f"PySide6: {env_info.py_side_version} Qt: {env_info.qt_version}",
        f"Platform: {env_info.platform}",
        f"QT_QPA_PLATFORM: {env_info.qt_qpa_platform}",
        f"QT_QUICK_BACKEND: {env_info.qt_quick_backend}",
        f"QSG_RHI_BACKEND: {env_info.qsg_rhi_backend}",
        f"Quick Controls Style: {env_info.quick_controls_style}",
        "",
        "## Render State",
        f"Post-effects bypassed: {state_info.post_effects_bypassed} ({state_info.post_effects_bypass_reason or ''})",
        f"Reflection enabled: {state_info.reflection_enabled} quality={state_info.reflection_quality} refresh={state_info.reflection_refresh_mode} slicing={state_info.reflection_time_slicing} padding={state_info.reflection_padding_m}",
        f"Render scale: {state_info.render_scale} Frame limit: {state_info.frame_rate_limit} Policy: {state_info.render_policy_key}",
        f"SSAO: {json.dumps(state_info.ssao, ensure_ascii=False)}",
        f"Fog: {json.dumps(state_info.fog, ensure_ascii=False)}",
        f"Shader warnings: {json.dumps(state_info.shader_warnings, ensure_ascii=False)}",
    ]
    if snapshot:
        md_lines.append("\n## Snapshot\n")
        try:
            md_lines.append("```json")
            md_lines.append(json.dumps(snapshot, ensure_ascii=False, indent=2)[:4000])
            md_lines.append("```")
        except Exception:
            pass
    (out_dir / "render_diagnostics.md").write_text(
        "\n".join(md_lines), encoding="utf-8"
    )
    print("Render diagnostics written to", out_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run(sys.argv[1:]))
