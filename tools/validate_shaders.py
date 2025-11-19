"""Compatibility shim that re-exports :mod:`src.tools.validate_shaders`.

Модуль выступает тонкой прослойкой: обеспечивает запуск как
`python -m tools.validate_shaders` и импорт `from tools import validate_shaders`
без дублирования кода. Раннее добавление PROJECT_ROOT в `sys.path` необходимо
до первого обычного импорта чтобы исключить E402 и избежать расхождений в среде.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Раннее добавление корня проекта в sys.path: требуется, чтобы избежать E402
# при последующих импортов и позволить модулю быть исполняемым скриптом и
# импортируемым пакетом.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tools import validate_shaders as _impl  # noqa: E402

# Re-export the public surface so ``from tools import validate_shaders`` works
# both as a script entrypoint and as an importable helper in unit tests.
ValidationErrors = _impl.ValidationErrors
ShaderValidationReport = _impl.ShaderValidationReport
QSB_ENV_VARIABLE = _impl.QSB_ENV_VARIABLE
ShaderValidationUnavailableError = _impl.ShaderValidationUnavailableError
DEFAULT_SHADER_ROOT = _impl.DEFAULT_SHADER_ROOT
DEFAULT_REPORTS_ROOT = _impl.DEFAULT_REPORTS_ROOT
QSB_PROFILE_ARGUMENTS = _impl.QSB_PROFILE_ARGUMENTS
ShaderValidationEnvironmentError = _impl.ShaderValidationEnvironmentError

classify_shader = _impl.classify_shader
parse_args = _impl.parse_args
validate_shaders = _impl.validate_shaders
main = _impl.main

__all__ = [
    "ValidationErrors",
    "ShaderValidationReport",
    "QSB_ENV_VARIABLE",
    "ShaderValidationUnavailableError",
    "DEFAULT_SHADER_ROOT",
    "DEFAULT_REPORTS_ROOT",
    "QSB_PROFILE_ARGUMENTS",
    "ShaderValidationEnvironmentError",
    "classify_shader",
    "parse_args",
    "validate_shaders",
    "main",
]


def __getattr__(name: str):  # pragma: no cover - convenience delegation
    return getattr(_impl, name)


def __dir__() -> list[str]:  # pragma: no cover - convenience delegation
    return sorted({*globals(), *dir(_impl)})


if __name__ == "__main__":
    raise SystemExit(main())
