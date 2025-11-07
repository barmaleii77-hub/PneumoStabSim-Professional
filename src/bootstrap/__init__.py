"""Bootstrap package helpers with defensive dependency loading."""

from __future__ import annotations

from typing import Any, Callable

from .environment import setup_qtquick3d_environment, configure_qt_environment
from .terminal import configure_terminal_encoding
from .version_check import check_python_compatibility

__all__ = [
    "setup_qtquick3d_environment",
    "configure_qt_environment",
    "configure_terminal_encoding",
    "check_python_compatibility",
    "safe_import_qt",
]

_SafeImportQt = Callable[
    [Callable[[str], None], Callable[[str], None]], tuple[Any, Any, Any, Any]
]


def _missing_numpy_stub(original_error: ModuleNotFoundError) -> _SafeImportQt:
    """Return a ``safe_import_qt`` stub that reports the missing NumPy dependency."""

    def _stub(
        _: Callable[[str], None], __: Callable[[str], None]
    ) -> tuple[Any, Any, Any, Any]:
        message = (
            "NumPy is required for PneumoStabSim but is not installed. "
            "Install the Python dependencies via 'make uv-sync' or "
            "'pip install -r requirements.txt' before launching the application."
        )
        raise ModuleNotFoundError(message) from original_error

    return _stub


try:  # pragma: no cover - exercised indirectly in tests
    import numpy  # noqa: F401 - we only need to ensure the dependency is present
except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime deps
    if getattr(exc, "name", None) == "numpy":
        safe_import_qt = _missing_numpy_stub(exc)
    else:
        raise
else:  # pragma: no cover - exercised indirectly in tests
    from .qt_imports import safe_import_qt
