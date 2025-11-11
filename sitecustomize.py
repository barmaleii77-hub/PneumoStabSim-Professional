"""Test harness compatibility shims for PySide6."""

from __future__ import annotations

from typing import Any, Iterable, Iterator

try:
    from PySide6.QtQml import QJSValue
except Exception:  # pragma: no cover - PySide6 absent
    QJSValue = None  # type: ignore[assignment]


def _convert_variant(value: Any) -> Any:
    """Resolve the underlying Python representation for a ``QJSValue``."""

    if QJSValue is not None and isinstance(value, QJSValue):
        try:
            return value.toVariant()
        except Exception:  # pragma: no cover - defensive guard
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
        except Exception:  # pragma: no cover - defensive guard
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
    # Only install shims when the methods are missing; this keeps compatibility
    # with environments that still ship the legacy mapping-aware wrapper.
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
