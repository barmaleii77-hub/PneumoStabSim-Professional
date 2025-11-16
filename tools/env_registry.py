"""Реестр критичных переменных окружения и утилиты их проверки.

Этот модуль централизует список обязательных/рекомендуемых переменных Qt и
инфраструктуры, чтобы исключить дублирование логики в различных скриптах
(trace_launch, app bootstrap, ci_tasks).

Использование:
    from tools.env_registry import validate_environment, CRITICAL_VARS
    report = validate_environment(os.environ)
    if report["missing"]:
        print("⚠ Отсутствуют переменные:", ", ".join(sorted(report["missing"])))

Структура отчёта:
{
  "checked": {NAME: VALUE_OR_EMPTY},
  "missing": [NAMES...],
  "empty": [NAMES_С_ПУСТЫМ_ЗНАЧЕНИЕМ],
  "suggested": {NAME: SUGGESTED_VALUE},
  "warnings": [STRINGS],
  "matrix": [ {"name":..., "value":..., "status": "ok|missing|empty", "suggested": "..." }, ... ]
}
"""
from __future__ import annotations

from typing import Iterable, Mapping, MutableMapping, Dict, Any

# Критичные для запуска UI / тестов переменные (порядок важен для вывода)
CRITICAL_VARS: tuple[str, ...] = (
    "QT_QPA_PLATFORM",
    "QT_PLUGIN_PATH",
    "QML2_IMPORT_PATH",
    "QT_QUICK_CONTROLS_STYLE",
    "QSG_RHI_BACKEND",
    "LIBGL_ALWAYS_SOFTWARE",
    "PSS_HEADLESS",
    "PSS_LOG_PRESET",
)

# Рекомендуемые значения / подсказки (не навязываем, отображаем при отсутствии)
SUGGESTED_DEFAULTS: dict[str, str] = {
    "QT_QUICK_CONTROLS_STYLE": "Basic",
    "QT_QPA_PLATFORM": "offscreen",  # для headless Linux
    "QSG_RHI_BACKEND": "d3d11",      # для Windows GPU с Direct3D 11
    "LIBGL_ALWAYS_SOFTWARE": "1",    # стабильность headless Linux
}

def _classify(value: str | None) -> str:
    if value is None:
        return "missing"
    if str(value).strip() == "":
        return "empty"
    return "ok"

def validate_environment(env: Mapping[str, str]) -> Dict[str, Any]:
    """Построить отчёт по состоянию критичных переменных.

    Args:
        env: Источник значений (обычно os.environ)
    Returns:
        Словарь со списком отсутствующих/пустых и матрицей.
    """
    missing: list[str] = []
    empty: list[str] = []
    matrix: list[dict[str, Any]] = []
    warnings: list[str] = []

    for name in CRITICAL_VARS:
        raw = env.get(name)
        status = _classify(raw)
        if status == "missing":
            missing.append(name)
            if name in SUGGESTED_DEFAULTS:
                warnings.append(f"Переменная {name} отсутствует (рекомендуется установить {SUGGESTED_DEFAULTS[name]})")
        elif status == "empty":
            empty.append(name)
            warnings.append(f"Переменная {name} установлена пустой строкой")
        matrix.append({
            "name": name,
            "value": raw or "",
            "status": status,
            "suggested": SUGGESTED_DEFAULTS.get(name, ""),
        })

    return {
        "checked": {m["name"]: m["value"] for m in matrix},
        "missing": missing,
        "empty": empty,
        "suggested": {k: v for k, v in SUGGESTED_DEFAULTS.items() if k in missing},
        "warnings": warnings,
        "matrix": matrix,
    }

def format_matrix_markdown(report: Mapping[str, Any]) -> str:
    """Сформировать markdown-таблицу для отчётных логов."""
    rows = ["| Name | Value | Status | Suggested |", "| --- | --- | --- | --- |"]
    for entry in report.get("matrix", []):
        rows.append(
            f"| {entry['name']} | {entry['value'] or '—'} | {entry['status']} | {entry['suggested'] or '—'} |"
        )
    return "\n".join(rows)

__all__ = ["CRITICAL_VARS", "SUGGESTED_DEFAULTS", "validate_environment", "format_matrix_markdown"]
