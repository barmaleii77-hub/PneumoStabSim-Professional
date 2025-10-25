"""Central helpers for Python↔QML bridge metadata.

This module exposes a typed view of the bridge configuration declared in
``config/qml_bridge.yaml``.  Runtime modules such as
``src.ui.main_window.qml_bridge`` use :class:`QMLBridgeRegistry` to obtain the
list of categories and associated QML method names.  Consolidating the metadata
in one place is a key milestone from the renovation master plan (section 5.3).

The registry performs lazy loading, validates the structure, and provides a
human friendly ``dump_routes`` helper used by diagnostics overlays.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence

import yaml

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BridgeCategory:
    """Declarative description of a QML bridge category."""

    name: str
    methods: tuple[str, ...]
    description: str | None = None
    signals: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BridgeMetadata:
    """Container describing the complete bridge configuration."""

    version: int
    qml_property: str
    ack_signal: str | None
    categories: tuple[BridgeCategory, ...]

    def category_map(self) -> Dict[str, BridgeCategory]:
        return {category.name: category for category in self.categories}


class QMLBridgeRegistry:
    """Load and cache bridge metadata defined in ``config/qml_bridge.yaml``."""

    _metadata: BridgeMetadata | None = None
    _metadata_path: Path | None = None

    @classmethod
    def configure(cls, *, metadata_path: Path | None = None) -> None:
        """Override the metadata path (primarily used by tests)."""

        cls._metadata_path = metadata_path
        cls._metadata = None

    @classmethod
    def metadata_path(cls) -> Path:
        if cls._metadata_path is not None:
            return cls._metadata_path
        return Path(__file__).resolve().parents[2] / "config" / "qml_bridge.yaml"

    @classmethod
    def load_metadata(cls, *, force: bool = False) -> BridgeMetadata:
        if cls._metadata is None or force:
            metadata_path = cls.metadata_path()
            logger.debug(
                "Loading QML bridge metadata",
                extra={"path": str(metadata_path), "force": force},
            )
            cls._metadata = cls._read_metadata(metadata_path)
        return cls._metadata

    @classmethod
    def methods_map(cls) -> Dict[str, tuple[str, ...]]:
        metadata = cls.load_metadata()
        return {
            name: category.methods for name, category in metadata.category_map().items()
        }

    @classmethod
    def dump_routes(cls, *, include_descriptions: bool = True) -> str:
        """Return a Markdown table describing all configured routes."""

        metadata = cls.load_metadata()
        header = "| Category | Methods | Signals | Description |"
        divider = "| --- | --- | --- | --- |"
        rows = [header, divider]
        for category in metadata.categories:
            methods = ", ".join(category.methods) or "—"
            signals = ", ".join(category.signals) or "—"
            description = category.description or "—"
            if not include_descriptions:
                description = "—"
            rows.append(f"| {category.name} | {methods} | {signals} | {description} |")
        rows.append("")
        rows.append(f"QML property: ``{metadata.qml_property}``")
        if metadata.ack_signal:
            rows.append(f"Ack signal: ``{metadata.ack_signal}``")
        return "\n".join(rows)

    @classmethod
    def _read_metadata(cls, path: Path) -> BridgeMetadata:
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except FileNotFoundError as exc:  # pragma: no cover - configuration error
            raise RuntimeError(f"Missing QML bridge metadata file: {path}") from exc
        except yaml.YAMLError as exc:  # pragma: no cover - configuration error
            raise RuntimeError(f"Failed to parse QML bridge metadata: {path}") from exc

        version = int(raw.get("version", 1))
        qml_property = str(raw.get("qml_property", "pendingPythonUpdates"))
        ack_signal = raw.get("ack_signal")

        categories_field = raw.get("categories")
        if not isinstance(categories_field, Mapping):
            raise RuntimeError("`categories` section must be a mapping of definitions")

        categories: list[BridgeCategory] = []
        for name, definition in categories_field.items():
            if not isinstance(definition, Mapping):
                raise RuntimeError(f"Category `{name}` must be a mapping")
            methods_field = definition.get("methods")
            if not isinstance(methods_field, Sequence) or not methods_field:
                raise RuntimeError(f"Category `{name}` must define at least one method")
            methods = tuple(
                str(method).strip() for method in methods_field if str(method).strip()
            )
            if not methods:
                raise RuntimeError(
                    f"Category `{name}` must provide non-empty method names"
                )

            description = definition.get("description")
            if description is not None:
                description = str(description).strip() or None

            signals_field = definition.get("signals", ())
            if isinstance(signals_field, Sequence) and not isinstance(
                signals_field, (str, bytes, bytearray)
            ):
                signals = tuple(
                    str(signal).strip()
                    for signal in signals_field
                    if str(signal).strip()
                )
            elif signals_field:
                signals = (str(signals_field).strip(),)
            else:
                signals = ()

            categories.append(
                BridgeCategory(
                    name=str(name),
                    methods=methods,
                    description=description,
                    signals=signals,
                )
            )

        categories.sort(key=lambda category: category.name)
        return BridgeMetadata(
            version=version,
            qml_property=qml_property,
            ack_signal=str(ack_signal) if ack_signal else None,
            categories=tuple(categories),
        )


def get_qml_update_methods(*, force_reload: bool = False) -> Dict[str, tuple[str, ...]]:
    """Public helper returning a copy of the QML update method map."""

    if force_reload:
        metadata = QMLBridgeRegistry.load_metadata(force=True)
    else:
        metadata = QMLBridgeRegistry.load_metadata()
    return {
        name: tuple(category.methods)
        for name, category in metadata.category_map().items()
    }


def iter_bridge_categories() -> Iterable[BridgeCategory]:
    """Yield configured bridge categories in alphabetical order."""

    metadata = QMLBridgeRegistry.load_metadata()
    yield from metadata.categories


def dump_bridge_routes(*, include_descriptions: bool = True) -> str:
    """Convenience wrapper used by diagnostics panels."""

    return QMLBridgeRegistry.dump_routes(include_descriptions=include_descriptions)
