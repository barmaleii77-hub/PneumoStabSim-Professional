"""Глобальные тестовые шины и ранняя настройка окружения.

(Расширено) Добавляем ранний stub для pytest-qt, чтобы заблокировать
загрузку реального плагина и устранить зависания в _process_events.
"""

from __future__ import annotations

import os
import sys
import types
from typing import Any, Iterable, Iterator

# --- РАННЯЯ НАСТРОЙКА ОКРУЖЕНИЯ --------------------------------------------
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
# Принудительно блокируем pytest-qt через stub модуль до старта pytest
if "pytestqt.plugin" not in sys.modules:
    stub_pkg = types.ModuleType("pytestqt")
    stub_plugin = types.ModuleType("pytestqt.plugin")

    def _noop(*_a, **_kw):  # noqa: ANN001, D401
        return None

    # Минимальные hook-функции, чтобы pytest не падал на вызове
    for name in (
        "pytest_configure",
        "pytest_unconfigure",
        "pytest_runtest_setup",
        "pytest_runtest_call",
        "pytest_runtest_teardown",
        "pytest_sessionstart",
        "pytest_sessionfinish",
    ):
        setattr(stub_plugin, name, _noop)

    # Предоставляем фикстуру qtbot как простую заглушку (pytest-qt ожидает её наличие)
    def qtbot():  # noqa: D401
        class _StubQtBot:
            def wait(self, ms: int) -> None:
                import time

                time.sleep(ms / 1000.0)

            def waitUntil(self, cond, timeout: int = 1000, interval: int = 25):  # noqa: ANN001
                import time

                end = time.time() + timeout / 1000.0
                while time.time() < end:
                    try:
                        if cond():
                            return None
                    except Exception:
                        pass
                    time.sleep(interval / 1000.0)
                raise AssertionError("waitUntil timeout (stub qtbot)")

        return _StubQtBot()

    stub_plugin.qtbot = qtbot  # type: ignore[attr-defined]
    sys.modules["pytestqt"] = stub_pkg
    sys.modules["pytestqt.plugin"] = stub_plugin

_addopts = os.environ.get("PYTEST_ADDOPTS", "")
_required = ["-p", "no:pytestqt", "-p", "no:pytestqt.plugin"]
if ("no:pytestqt" not in _addopts) and ("no:pytestqt.plugin" not in _addopts):
    _addopts = (f"{_addopts} {' '.join(_required)}").strip()
    os.environ["PYTEST_ADDOPTS"] = _addopts

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if sys.platform.startswith("win"):
    os.environ.setdefault("QT_QUICK_BACKEND", "rhi")
    os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
else:
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ.pop("QSG_RHI_BACKEND", None)

os.environ.setdefault("PSS_HEADLESS", "1")
os.environ.setdefault("PYTHONHASHSEED", "0")
os.environ.setdefault("PSS_FORCE_NONBLOCKING_DIALOGS", "1")
os.environ.setdefault("PSS_SUPPRESS_UI_DIALOGS", "1")

# --- СУЩЕСТВУЮЩИЕ QJSValue-ШИМЫ -------------------------------------------
try:
    from PySide6.QtQml import QJSValue
except Exception:  # pragma: no cover - PySide6 absent
    QJSValue = None  # type: ignore[assignment]


def _convert_variant(value: Any) -> Any:
    if QJSValue is not None and isinstance(value, QJSValue):
        try:
            return value.toVariant()
        except Exception:  # pragma: no cover
            return value
    return value


def _getitem(self: "QJSValue", key: Any) -> Any:  # type: ignore[annotation-unchecked]
    variant = _convert_variant(self)
    if isinstance(variant, dict):
        return variant[key]
    if isinstance(variant, (list, tuple)):
        return variant[key]
    raise TypeError("QJSValue payload does not support indexing")


def _iter(self: "QJSValue") -> Iterator[Any]:  # type: ignore[annotation-unchecked]
    variant = _convert_variant(self)
    if isinstance(variant, dict):
        return iter(variant)
    if isinstance(variant, (list, tuple)):
        return iter(variant)
    return iter(())


def _len(self: "QJSValue") -> int:  # type: ignore[annotation-unchecked]
    variant = _convert_variant(self)
    if isinstance(variant, (dict, list, tuple)):
        return len(variant)
    return 0


def _contains(self: "QJSValue", key: Any) -> bool:  # type: ignore[annotation-unchecked]
    variant = _convert_variant(self)
    if isinstance(variant, dict):
        return key in variant
    if isinstance(variant, (list, tuple)):
        try:
            return key in variant
        except Exception:  # pragma: no cover
            return False
    return False


def _keys(self: "QJSValue") -> Iterable[Any]:  # type: ignore[annotation-unchecked]
    variant = _convert_variant(self)
    if isinstance(variant, dict):
        return variant.keys()
    return ()


def _values(self: "QJSValue") -> Iterable[Any]:  # type: ignore[annotation-unchecked]
    variant = _convert_variant(self)
    if isinstance(variant, dict):
        return variant.values()
    return ()


def _items(self: "QJSValue") -> Iterable[tuple[Any, Any]]:  # type: ignore[annotation-unchecked]
    variant = _convert_variant(self)
    if isinstance(variant, dict):
        return variant.items()
    return ()


if QJSValue is not None:
    if not hasattr(QJSValue, "__getitem__"):
        QJSValue.__getitem__ = _getitem  # type: ignore[attr-defined]
    if not hasattr(QJSValue, "__iter__"):
        QJSValue.__iter__ = _iter  # type: ignore[attr-defined]
    if not hasattr(QJSValue, "__len__"):
        QJSValue.__len__ = _len  # type: ignore[attr-defined]
    if not hasattr(QJSValue, "__contains__"):
        QJSValue.__contains__ = _contains  # type: ignore[attr-defined]
    if not hasattr(QJSValue, "keys"):
        QJSValue.keys = _keys  # type: ignore[attr-defined]
    if not hasattr(QJSValue, "values"):
        QJSValue.values = _values  # type: ignore[attr-defined]
    if not hasattr(QJSValue, "items"):
        QJSValue.items = _items  # type: ignore[attr-defined]
