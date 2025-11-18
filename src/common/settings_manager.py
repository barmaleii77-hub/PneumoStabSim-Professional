"""Lightweight settings manager used for unit tests.

The original project ships with a very feature-rich configuration system that
interacts with Qt, performs schema migrations and manages complex defaults.  The
test-suite in this kata exercises only a tiny portion of that behaviour, so the
heavy implementation makes the tests brittle in a headless environment.  This
module provides a compact drop-in replacement that offers the pieces the tests
rely on:

* loading a JSON configuration file with ``current`` and ``defaults_snapshot``
  sections;
* coercing the ``units_version`` metadata to ``si_v2`` when legacy payloads are
  encountered;
* basic dotted-path ``get`` and ``set`` helpers;
* an opt-in singleton accessor exposed via :func:`get_settings_manager`.

The implementation intentionally stays conservative – it validates the presence
of the primary sections but otherwise keeps the payload opaque, letting the unit
tests drive the requirements.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module, util
from pathlib import Path, PureWindowsPath
from typing import Any
from collections.abc import Iterable

from src.core.settings_defaults import load_default_settings_payload
from src.core.settings_manager import (
    ProfileSettingsManager as _CoreProfileSettingsManager,
)
from src.security.access_control import get_access_control
from src.settings.orbit_presets import orbit_presets_path


logger = logging.getLogger(__name__)


DEFAULT_SETTINGS_PATH = Path("config/app_settings.json")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_UNITS_VERSION = "si_v2"
_MM_PER_M = 1000.0
_WINDOWS_DRIVE_PATTERN = re.compile(r"^[a-zA-Z]:[\\/]")

_GEOMETRY_LINEAR_KEYS: dict[str, None] = {
    "wheelbase": None,
    "track": None,
    "frame_to_pivot": None,
    "lever_length": None,
    "cylinder_length": None,
    "frame_height_m": None,
    "frame_beam_size_m": None,
    "frame_length_m": None,
    "lever_length_m": None,
    "cyl_diam_m": None,
    "stroke_m": None,
    "dead_gap_m": None,
    "rod_diameter_m": None,
    "rod_diameter_rear_m": None,
    "piston_rod_length_m": None,
    "piston_thickness_m": None,
    "cylinder_body_length_m": None,
    "tail_rod_length_m": None,
}

_GEOMETRY_KEY_ALIASES: dict[str, str] = {
    # Legacy millimetre keys promoted to explicit metre suffixes
    "frame_length_mm": "frame_length_m",
    "frame_length": "frame_length_m",
    "frame_height_mm": "frame_height_m",
    "frame_height": "frame_height_m",
    "frame_beam_size_mm": "frame_beam_size_m",
    "frame_beam_size": "frame_beam_size_m",
    "lever_length_mm": "lever_length_m",
    "lever_length_visual_mm": "lever_length_m",
    "lever_length_visual": "lever_length_m",
    "cylinder_body_length_mm": "cylinder_body_length_m",
    "cylinder_body_length": "cylinder_body_length_m",
    "tail_rod_length_mm": "tail_rod_length_m",
    "tail_rod_length": "tail_rod_length_m",
    "track_width_mm": "track",
    "track_width": "track",
    "frame_to_pivot_mm": "frame_to_pivot",
    "cyl_diam_mm": "cyl_diam_m",
    "cyl_diam": "cyl_diam_m",
    "stroke_mm": "stroke_m",
    "stroke": "stroke_m",
    "dead_gap_mm": "dead_gap_m",
    "dead_gap": "dead_gap_m",
    "rod_diameter_front_mm": "rod_diameter_m",
    "rod_diameter_rear_mm": "rod_diameter_rear_m",
    "rod_diameter_rear": "rod_diameter_rear_m",
    "rod_diameter_mm": "rod_diameter_m",
    "rod_diameter": "rod_diameter_m",
    "piston_rod_length_mm": "piston_rod_length_m",
    "piston_rod_length": "piston_rod_length_m",
    "piston_thickness_mm": "piston_thickness_m",
    "piston_thickness": "piston_thickness_m",
    "wheelbase_mm": "wheelbase",
    "wheel_base_mm": "wheelbase",
    "wheel_base": "wheelbase",
}

_GEOMETRY_MIRROR_KEYS: dict[str, str] = {
    # Maintain both the UI-facing ``lever_length`` and the visualisation
    # ``lever_length_m`` entries so that legacy payloads hydrate both code paths.
    "lever_length": "lever_length_m",
}

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")

_ENVIRONMENT_KEY_ALIASES: dict[str, str] = {
    "ibl_background_enabled": "skybox_enabled",
    "iblbackgroundenabled": "skybox_enabled",
    "ibl_lighting_enabled": "ibl_enabled",
    "ibllightingenabled": "ibl_enabled",
    "probe_brightness": "skybox_brightness",
}

_EFFECTS_KEY_ALIASES: dict[str, str] = {
    "tonemap_active": "tonemap_enabled",
    "tonemapenabled": "tonemap_enabled",
    "tonemap_mode_name": "tonemap_mode",
    "tonemapmodename": "tonemap_mode",
    "depth_of_field_enabled": "depth_of_field",
    "depthoffieldenabled": "depth_of_field",
    "vignette_enabled": "vignette",
    "vignetteenabled": "vignette",
    "lens_flare_enabled": "lens_flare",
    "lensflareenabled": "lens_flare",
    "motion_blur_enabled": "motion_blur",
    "motionblur_enabled": "motion_blur",
    "color_brightness": "adjustment_brightness",
    "color_contrast": "adjustment_contrast",
    "color_saturation": "adjustment_saturation",
    "bloom_hdr_maximum": "bloom_hdr_max",
    # Дополнительный fallback для случаев когда акронимы не были слиты (до обновления функции):
    "bloom_h_d_r_maximum": "bloom_hdr_max",
}

_CAMERA_KEY_ALIASES: dict[str, str] = {"manual_mode": "manual_camera"}


def _expand_path(path: Path | str) -> Path:
    """Expand environment variables and ``~`` in a path-like value."""

    raw = str(path)
    expanded = os.path.expandvars(raw)
    return Path(expanded).expanduser()


def _resolve_settings_file(settings_file: Path | str | None) -> Path:
    if settings_file is not None:
        return _expand_path(settings_file)

    env_path = os.environ.get("PSS_SETTINGS_FILE")
    if env_path:
        return _expand_path(env_path)

    return _expand_path(DEFAULT_SETTINGS_PATH)


def _deep_copy(data: Any) -> Any:
    return json.loads(json.dumps(data))


def _deep_update(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Recursively merge ``source`` into ``target``."""

    for key, value in source.items():
        existing = target.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            _deep_update(existing, value)
        else:
            target[key] = _deep_copy(value)


def _camel_to_snake(name: Any) -> Any:
    if not isinstance(name, str):
        return name
    token = name.strip()
    if not token:
        return token
    token = token.replace("-", "_")
    snake = _CAMEL_BOUNDARY.sub("_", token)
    while "__" in snake:
        snake = snake.replace("__", "_")
    snake = snake.lower()
    # Усиленная нормализация акронимов: соединяем разорванные буквы (h_d_r -> hdr, i_b_l -> ibl, s_s_a_o -> ssao)
    # Выполняем глобальные замены без опоры на границы слова – это устойчивее к позициям внутри идентификатора
    for acronym_parts, fused in (
        ("h_d_r", "hdr"),
        ("i_b_l", "ibl"),
        ("s_s_a_o", "ssao"),
        (
            "t_o_n_e_m_a_p",
            "tonemap",
        ),  # встречается в некоторых плохо сформированных payload
    ):
        if acronym_parts in snake:
            snake = snake.replace(acronym_parts, fused)
    return snake


def _scale_mm_value(value: Any) -> tuple[Any, bool]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return value, False
    converted = numeric / _MM_PER_M
    return converted, True


def _normalise_dict_keys(
    payload: dict[str, Any],
    aliases: dict[str, str],
) -> bool:
    changed = False
    normalised: dict[str, Any] = {}

    for raw_key, value in list(payload.items()):
        canonical = _camel_to_snake(raw_key)
        mapped = aliases.get(canonical, canonical)
        if mapped != raw_key or mapped != canonical:
            changed = True
        if mapped in normalised:
            continue
        normalised[mapped] = value

    if normalised != payload:
        payload.clear()
        payload.update(normalised)
        changed = True

    return changed


def _load_qt_core():
    try:
        spec = util.find_spec("PySide6.QtCore")
    except ModuleNotFoundError:
        return None
    if spec is None:
        return None
    return import_module("PySide6.QtCore")


_qt_core = _load_qt_core()

if _qt_core is not None:
    QObject = _qt_core.QObject
    Signal = _qt_core.Signal
else:

    class QObject:  # type: ignore[override]
        """Minimal QObject stand-in for headless environments."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - Qt compatibility
            super().__init__()

    class _SignalInstance:
        def __init__(self) -> None:
            self._subscribers: list[Any] = []

        def connect(self, callback: Any) -> None:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

        def disconnect(self, callback: Any) -> None:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

        def isSignalConnected(self) -> bool:  # noqa: N802 - mirror Qt API
            return bool(self._subscribers)

        def emit(self, *args: Any, **kwargs: Any) -> None:
            for callback in list(self._subscribers):
                callback(*args, **kwargs)

    class _Signal:
        def __init__(self) -> None:
            self._name: str | None = None

        def __set_name__(self, owner: type, name: str) -> None:
            self._name = f"__signal_{name}"

        def __get__(self, instance: Any, owner: type | None = None) -> Any:
            if instance is None:
                return self
            assert self._name is not None
            signal = instance.__dict__.get(self._name)
            if signal is None:
                signal = _SignalInstance()
                instance.__dict__[self._name] = signal
            return signal

    def Signal(*_args: Any, **_kwargs: Any) -> Any:  # noqa: N802 - mirror Qt API
        return _Signal()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _last_modified_timestamp() -> str:
    """Return an ISO-8601 timestamp suitable for ``metadata.last_modified``."""

    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


@dataclass
class _SettingsChange:
    path: str
    category: str
    changeType: str
    newValue: Any
    oldValue: Any
    timestamp: str


class SettingsEventBus(QObject):
    """Event bus mirroring the project's Qt-based settings notifications."""

    settingChanged = Signal(dict)
    settingsBatchUpdated = Signal(dict)

    def emit_setting_changed(self, payload: dict[str, Any]) -> None:
        self.settingChanged.emit(payload)

    def emit_settings_batch(self, payload: dict[str, Any]) -> None:
        self.settingsBatchUpdated.emit(payload)


ProfileSettingsManager = _CoreProfileSettingsManager


class SettingsManager:
    """Minimal settings manager tailored for the unit tests."""

    def __init__(self, settings_file: Path | str | None = None) -> None:
        self._settings_path = _resolve_settings_file(settings_file)
        self._data: dict[str, Any] = {}
        self._defaults: dict[str, Any] = {}
        self._metadata: dict[str, Any] = {}
        self._extra: dict[str, Any] = {}
        self._original_units_version: str = _DEFAULT_UNITS_VERSION
        self._dirty: bool = False
        self._orbit_presets: dict[str, Any] | None = None
        self._orbit_presets_path = orbit_presets_path()
        self._access_control = get_access_control()
        self._runtime_defaults: dict[str, Any] | None = None
        self.load()

    # ------------------------------------------------------------------ helpers
    @property
    def settings_file(self) -> Path:
        return self._settings_path

    def _ensure_units_version(self) -> bool:
        changed = False
        raw_units_version = self._metadata.get("units_version")
        if isinstance(raw_units_version, str):
            normalized = raw_units_version.strip()
            self._original_units_version = normalized or "legacy"
        elif raw_units_version is None:
            self._original_units_version = "legacy"
        else:
            self._original_units_version = str(raw_units_version).strip() or "legacy"

        target = (
            _DEFAULT_UNITS_VERSION
            if self._original_units_version != _DEFAULT_UNITS_VERSION
            else self._original_units_version
        )
        if self._metadata.get("units_version") != target:
            self._metadata["units_version"] = target
            changed = True

        return changed

    # ----------------------------------------------------------------- migration

    def _convert_geometry_section(self, section: dict[str, Any]) -> bool:
        # Сохраняем исходный набор ключей до нормализации для определения, какие были в мм
        original_keys = set(section.keys())
        changed = _normalise_dict_keys(section, _GEOMETRY_KEY_ALIASES)

        # Определяем какие метрические ключи должны масштабироваться (только если исходный mm-ключ присутствовал)
        mm_source_map: dict[str, bool] = {}
        for src, dst in _GEOMETRY_KEY_ALIASES.items():
            if src.endswith("_mm") and dst in _GEOMETRY_LINEAR_KEYS:
                if src in original_keys:
                    mm_source_map[dst] = True
        # Специальные визуальные алиасы с суффиксом _visual_mm
        for src, dst in _GEOMETRY_KEY_ALIASES.items():
            if src.endswith("_visual_mm") and dst in _GEOMETRY_LINEAR_KEYS:
                if src in original_keys:
                    mm_source_map[dst] = True

        for key in _GEOMETRY_LINEAR_KEYS:
            if key not in section:
                continue
            # Масштабируем только если исходный ключ был mm-вариантом и значение выглядит как миллиметры (>=10.0)
            if not mm_source_map.get(key, False):
                continue
            raw_value = section[key]
            try:
                numeric = float(raw_value)
            except (TypeError, ValueError):
                continue
            if numeric < 10.0:  # Уже метры или малый коэффициент — не масштабируем
                continue
            value, did_convert = _scale_mm_value(numeric)
            if did_convert:
                section[key] = value
                changed = True

        for source, mirror in _GEOMETRY_MIRROR_KEYS.items():
            if source in section and mirror not in section:
                section[mirror] = section[source]
                changed = True
            elif mirror in section and source not in section:
                section[source] = section[mirror]
                changed = True

        return changed

    def _normalise_units(self) -> bool:
        if self._original_units_version == _DEFAULT_UNITS_VERSION:
            return False

        changed = False

        for container in (self._data, self._defaults):
            geometry = (
                container.get("geometry") if isinstance(container, dict) else None
            )
            if isinstance(geometry, dict) and self._convert_geometry_section(geometry):
                changed = True

        return changed

    def _normalise_environment_section(self, section: dict[str, Any]) -> bool:
        if not isinstance(section, dict):
            return False
        changed = _normalise_dict_keys(section, _ENVIRONMENT_KEY_ALIASES)
        if "skybox_brightness" not in section and "probe_brightness" in section:
            section["skybox_brightness"] = section.pop("probe_brightness")
            changed = True
        else:
            removed = section.pop("probe_brightness", None)
            if removed is not None:
                changed = True
        return changed

    def _normalise_effects_section(self, section: dict[str, Any]) -> bool:
        if not isinstance(section, dict):
            return False
        changed = _normalise_dict_keys(section, _EFFECTS_KEY_ALIASES)
        # Дополнительный fallback: если после нормализации остался bloom_hdr_maximum вместо bloom_hdr_max
        if "bloom_hdr_max" not in section and "bloom_hdr_maximum" in section:
            section["bloom_hdr_max"] = section.pop("bloom_hdr_maximum")
            changed = True
        return changed

    def _normalise_lighting_section(self, lighting: dict[str, Any]) -> bool:
        if not isinstance(lighting, dict):
            return False

        point = lighting.get("point")
        if not isinstance(point, dict):
            return False

        changed = False

        def _positive(value: Any, fallback: float) -> float:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return fallback
            if not math.isfinite(numeric) or numeric <= 0.0:
                return fallback
            return numeric

        range_value = _positive(point.get("range"), 0.0)
        if range_value <= 0.0:
            range_value = 3.6  # движковый дефолт радиуса действия точечного света
            point["range"] = range_value
            changed = True

        constant = _positive(point.get("constant_fade"), 1.0)
        if constant != point.get("constant_fade"):
            point["constant_fade"] = constant
            changed = True

        linear_default = max(0.0, 2.0 / range_value)
        linear = _positive(point.get("linear_fade"), linear_default)
        if linear != point.get("linear_fade"):
            point["linear_fade"] = linear
            changed = True

        quadratic = _positive(point.get("quadratic_fade"), 1.0)
        if quadratic != point.get("quadratic_fade"):
            point["quadratic_fade"] = quadratic
            changed = True

        return changed

    def _normalise_camera_section(self, section: dict[str, Any]) -> bool:
        if not isinstance(section, dict):
            return False
        return _normalise_dict_keys(section, _CAMERA_KEY_ALIASES)

    def _strip_legacy_material_keys(self, materials: dict[str, Any]) -> bool:
        """Удаляет устаревшие свойства материалов, не поддерживаемые Qt 6.10.

        Секции ``graphics.materials`` могут содержать ключи specular/specular_tint/
        transmission/ior из старых конфигов. Эти параметры больше не применяются
        и должны быть убраны, чтобы UI и рантайм не ссылались на них.
        """
        if not isinstance(materials, dict):
            return False
        changed = False
        legacy_keys = ("specular", "specular_tint", "transmission", "ior")
        for mat_key, payload in list(materials.items()):
            if not isinstance(payload, dict):
                continue
            for legacy in legacy_keys:
                if legacy in payload:
                    payload.pop(legacy, None)
                    changed = True
        return changed

    def _normalise_graphics_sections(self) -> bool:
        changed = False
        for container in (self._data, self._defaults):
            graphics = (
                container.get("graphics") if isinstance(container, dict) else None
            )
            if not isinstance(graphics, dict):
                continue
            environment = graphics.get("environment")
            if isinstance(environment, dict) and self._normalise_environment_section(
                environment
            ):
                changed = True
            effects = graphics.get("effects")
            if isinstance(effects, dict) and self._normalise_effects_section(effects):
                changed = True
            camera = graphics.get("camera")
            if isinstance(camera, dict) and self._normalise_camera_section(camera):
                changed = True
            lighting = graphics.get("lighting")
            if isinstance(lighting, dict) and self._normalise_lighting_section(
                lighting
            ):
                changed = True
            materials = graphics.get("materials")
            if isinstance(materials, dict) and self._strip_legacy_material_keys(
                materials
            ):
                changed = True
        return changed

    @staticmethod
    def _normalise_hdr_path_value(value: Any) -> str:
        """Нормализация пути HDR.

        Шаги:
        1. Стандартизация разделителей на '/'
        2. Исправление legacy формата без двоеточия вида 'C/...' → 'C:/...'
        3. Приведение к нижнему регистру для стабильных сравнений
        4. Попытка получить относительный путь к PROJECT_ROOT (если внутри репозитория)
        5. Возврат либо относительного, либо абсолютного Windows POSIX пути в lowercase
        """
        if value is None:
            return ""
        try:
            text = str(value).strip()
        except Exception:
            return ""
        if not text:
            return ""
        lowered = text.lower()
        if lowered.startswith("file://"):
            text = text[7:]
        elif lowered.startswith("file:/"):
            text = text[6:]
        # Унифицируем обратные слеши
        text = text.replace("\\", "/")
        # Исправляем формат 'C/...' (без двоеточия после буквы диска)
        import re

        if re.match(r"^[A-Za-z]/", text):
            # Вставляем двоеточие после буквы диска
            text = f"{text[0]}:/" + text[2:]
        # Гарантируем слеш после 'C:' если указан диск
        if re.match(r"^[A-Za-z]:[^/].*", text):
            text = text[0:2] + "/" + text[2:]
        # Приводим к lowercase для дальнейшей обработки (но сохраним исходный для Path)
        text_lower = text.lower()
        try:
            candidate = Path(text_lower).expanduser()
        except Exception:
            return text_lower
        try:
            resolved = candidate.resolve(strict=False)
        except Exception:
            resolved = candidate

        # Use lower-case normalisation for consistent comparisons across platforms.
        normalised = resolved.as_posix().lower()
        project_root = PROJECT_ROOT.resolve()
        project_root_prefix = project_root.as_posix().lower().rstrip("/") + "/"
        relative_override: str | None = None

        if resolved.is_absolute():
            try:
                relative = resolved.relative_to(project_root)
            except ValueError:
                # Fall back to a case-insensitive comparison: normalise both strings
                # to lower-case and strip the repository prefix if it matches.
                if normalised.startswith(project_root_prefix):
                    relative_override = normalised[len(project_root_prefix) :]
            else:
                relative_override = relative.as_posix().lower()

        if relative_override:
            return relative_override
        # Если путь соответствует формату диска, используем windows normalised напрямую
        if _WINDOWS_DRIVE_PATTERN.match(text + "/") or re.match(
            r"^[a-zA-Z]:/", text_lower
        ):
            windows_normalised = PureWindowsPath(text_lower).as_posix().lower()
            if windows_normalised and windows_normalised not in normalised:
                normalised = windows_normalised
        return normalised

    def _normalise_hdr_paths(self) -> bool:
        changed = False

        for container in (self._data, self._defaults):
            if not isinstance(container, dict):
                continue
            graphics = container.get("graphics")
            if not isinstance(graphics, dict):
                continue
            environment = graphics.get("environment")
            if not isinstance(environment, dict):
                continue

            if "ibl_source" in environment:
                current_value = environment.get("ibl_source")
                normalised = self._normalise_hdr_path_value(current_value)
                if normalised != current_value:
                    environment["ibl_source"] = normalised
                    changed = True

        return changed

    def _assign_sections(self, payload: dict[str, Any]) -> None:
        def _section_payload(name: str) -> dict[str, Any]:
            raw = payload.get(name)
            if isinstance(raw, dict):
                return raw
            if raw is None:
                logger.warning(
                    "Settings payload missing '%s' section; using empty defaults.", name
                )
            else:
                logger.warning(
                    "Settings payload has invalid '%s' section (%s); using empty defaults.",
                    name,
                    type(raw).__name__,
                )
            return {}

        self._metadata = _deep_copy(_section_payload("metadata"))
        self._data = _deep_copy(_section_payload("current"))
        self._defaults = _deep_copy(_section_payload("defaults_snapshot"))
        self._extra = {
            key: _deep_copy(value)
            for key, value in payload.items()
            if key not in {"metadata", "current", "defaults_snapshot"}
        }
        dirty = False
        if self._migrate_known_extras():
            dirty = True
        if self._ensure_units_version():
            dirty = True
        if self._normalise_units():
            dirty = True
        if self._normalise_graphics_sections():
            dirty = True
        if self._normalise_hdr_paths():
            dirty = True
        if self._hydrate_new_sections():
            dirty = True
        self._dirty = dirty
        self._warn_missing_required_paths()

    def _hydrate_new_sections(self) -> bool:
        """Backfill recently added sections and values from baseline defaults."""

        try:
            baseline = load_default_settings_payload()
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug(
                "Unable to load defaults for hydration: %s", exc, exc_info=True
            )
            return False

        changed = False

        def _copy_missing(
            target_root: dict[str, Any], source_root: dict[str, Any], path: str
        ) -> None:
            nonlocal changed
            segments = [segment for segment in path.split(".") if segment]
            if not segments:
                return
            target_node: dict[str, Any] = target_root
            source_node: Any = source_root

            for segment in segments[:-1]:
                if not isinstance(source_node, dict):
                    return
                source_node = source_node.get(segment)
                if not isinstance(source_node, dict):
                    return
                if not isinstance(target_node.get(segment), dict):
                    target_node[segment] = {}
                    changed = True
                target_node = target_node[segment]

            leaf = segments[-1]
            if leaf in target_node:
                return
            if not isinstance(source_node, dict) or leaf not in source_node:
                return
            target_node[leaf] = _deep_copy(source_node[leaf])
            changed = True

        for section_name, target_root in (
            ("current", self._data),
            ("defaults_snapshot", self._defaults),
        ):
            if not isinstance(target_root, dict):
                continue
            source_root = baseline.get(section_name)
            if not isinstance(source_root, dict):
                continue
            for path in (
                "pneumatic.dead_zone_head_m3",
                "pneumatic.dead_zone_rod_m3",
                "pneumatic.chamber_volumes",
                "pneumatic.line_pressures",
                "pneumatic.tank_pressure_pa",
                "pneumatic.relief_pressure_pa",
                "road",
                "advanced",
            ):
                _copy_missing(target_root, source_root, path)

        return changed

    def _warn_missing_required_paths(self) -> None:
        try:
            from src.common import settings_requirements as req
        except Exception as exc:  # pragma: no cover - optional dependency at runtime
            logger.debug("Settings requirements unavailable: %s", exc, exc_info=True)
            return

        sentinel = object()

        def _value(path: str) -> Any:
            return self.get(path, sentinel)

        for section_path in getattr(req, "REQUIRED_CURRENT_SECTIONS", ()):  # type: ignore[attr-defined]
            value = _value(section_path)
            if value is sentinel or not isinstance(value, dict):
                logger.warning(
                    "Settings payload missing required section '%s'; defaults may be used.",
                    section_path,
                )

        numeric_paths: set[str] = set()
        numeric_paths.update(
            f"current.simulation.{key}"
            for key in getattr(req, "NUMERIC_SIMULATION_KEYS", ())
        )
        numeric_paths.update(
            f"current.pneumatic.{key}"
            for key in getattr(req, "NUMERIC_PNEUMATIC_KEYS", ())
        )
        numeric_paths.update(
            f"current.pneumatic.receiver_volume_limits.{key}"
            for key in getattr(req, "RECEIVER_VOLUME_LIMIT_KEYS", ())
        )
        numeric_paths.update(
            f"current.pneumatic.line_pressures.{key}"
            for key in getattr(req, "LINE_PRESSURE_KEYS", ())
        )
        numeric_paths.update(
            f"current.pneumatic.chamber_volumes.{key}"
            for key in getattr(req, "CHAMBER_VOLUME_KEYS", ())
        )

        string_paths: set[str] = {
            f"current.pneumatic.{key}"
            for key in getattr(req, "STRING_PNEUMATIC_KEYS", ())
        }
        bool_paths: set[str] = {
            f"current.pneumatic.{key}"
            for key in getattr(req, "BOOL_PNEUMATIC_KEYS", ())
        }

        for numeric_path in numeric_paths:
            value = _value(numeric_path)
            if value is sentinel:
                logger.warning(
                    "Settings payload missing required numeric value '%s'; using defaults.",
                    numeric_path,
                )
            elif isinstance(value, bool) or not isinstance(value, (int, float)):
                logger.warning(
                    "Settings value '%s' expected to be numeric but received %r; coerced defaults may apply.",
                    numeric_path,
                    type(value).__name__,
                )

        for string_path in string_paths:
            value = _value(string_path)
            if value is sentinel:
                logger.warning(
                    "Settings payload missing required string value '%s'; using defaults.",
                    string_path,
                )
            elif not isinstance(value, str) or not value.strip():
                logger.warning(
                    "Settings value '%s' expected to be a non-empty string but received %r; defaults will be applied.",
                    string_path,
                    type(value).__name__,
                )

        for bool_path in bool_paths:
            value = _value(bool_path)
            if value is sentinel:
                logger.warning(
                    "Settings payload missing required boolean value '%s'; using defaults.",
                    bool_path,
                )
            elif not isinstance(value, bool):
                logger.warning(
                    "Settings value '%s' expected to be boolean but received %r; coercion may apply.",
                    bool_path,
                    type(value).__name__,
                )

    # ------------------------------------------------------------------- units
    def get_units_version(self, *, normalised: bool = True) -> str:
        """Return the settings units version.

        Args:
            normalised: When ``True`` (default) the coerced ``si_v2`` value is
                returned. When ``False`` the original value found in the
                settings payload is returned, allowing callers to detect
                legacy files and perform migrations safely.
        """

        if normalised:
            return str(self._metadata.get("units_version", _DEFAULT_UNITS_VERSION))

        return self._original_units_version or _DEFAULT_UNITS_VERSION

    # ------------------------------------------------------------------- public
    def load(self) -> None:
        payload: dict[str, Any]
        used_fallback = False

        if not self._settings_path.exists():
            logger.warning(
                "Settings file does not exist: %s; hydrating defaults.",
                self._settings_path,
            )
            payload = load_default_settings_payload()
            used_fallback = True
        else:
            raw_payload = self._settings_path.read_text(encoding="utf-8")
            try:
                payload = json.loads(raw_payload)
            except json.JSONDecodeError as exc:
                logger.error(
                    "Failed to parse settings file %s: %s. Falling back to defaults.",
                    self._settings_path,
                    exc,
                    exc_info=True,
                )
                payload = load_default_settings_payload()
                used_fallback = True
            else:
                if not isinstance(payload, dict):
                    logger.error(
                        "Settings file %s does not contain a JSON object (found %s). "
                        "Using default payload.",
                        self._settings_path,
                        type(payload).__name__,
                    )
                    payload = load_default_settings_payload()
                    used_fallback = True

        for key in ("current", "defaults_snapshot", "metadata"):
            if key not in payload:
                logger.warning(
                    "Settings payload missing required section '%s'; defaults will be empty.",
                    key,
                )
                payload[key] = {}

        self._assign_sections(payload)
        if used_fallback:
            self._dirty = True

    def save(self) -> None:
        if not isinstance(self._metadata, dict):
            self._metadata = {}

        self._metadata["last_modified"] = _last_modified_timestamp()

        payload: dict[str, Any] = {
            "metadata": _deep_copy(self._metadata),
            "current": _deep_copy(self._data),
            "defaults_snapshot": _deep_copy(self._defaults),
        }
        payload.update(self._extra)
        self._settings_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._dirty = False

    def save_if_dirty(self) -> None:
        if self._dirty:
            self.save()

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    # ----------------------------------------------------------------- orbit presets

    def _load_orbit_presets(self) -> dict[str, Any]:
        path = _expand_path(self._orbit_presets_path)
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("Orbit preset manifest not found: %s", path)
            return {"version": 0, "presets": [], "index": {}}
        except OSError as exc:
            logger.error("Unable to read orbit preset manifest %s: %s", path, exc)
            return {"version": 0, "presets": [], "index": {}}

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error(
                "Failed to parse orbit preset manifest %s: %s",
                path,
                exc,
            )
            return {"version": 0, "presets": [], "index": {}}

        if not isinstance(payload, dict):
            logger.error(
                "Orbit preset manifest root must be a JSON object (found %s)",
                type(payload).__name__,
            )
            return {"version": 0, "presets": [], "index": {}}

        presets: list[dict[str, Any]] = []
        index: dict[str, dict[str, Any]] = {}

        raw_presets = payload.get("presets")
        if isinstance(raw_presets, list):
            for entry in raw_presets:
                if not isinstance(entry, dict):
                    continue
                preset_id = entry.get("id")
                if not isinstance(preset_id, str) or not preset_id:
                    continue
                preset_copy = _deep_copy(entry)
                presets.append(preset_copy)
                index[preset_id] = preset_copy

        version = payload.get("version")
        if isinstance(version, int):
            version_value = version
        else:
            try:
                version_value = int(version)
            except (TypeError, ValueError):
                version_value = 0

        manifest: dict[str, Any] = {
            "version": version_value,
            "default": payload.get("default"),
            "presets": presets,
            "index": index,
        }
        return manifest

    def get_orbit_presets(self) -> dict[str, Any]:
        if self._orbit_presets is None:
            self._orbit_presets = self._load_orbit_presets()
        return _deep_copy(self._orbit_presets)

    def refresh_orbit_presets(self) -> dict[str, Any]:
        self._orbit_presets_path = orbit_presets_path()
        self._orbit_presets = None
        return self.get_orbit_presets()

    def _notify_change(self, change: _SettingsChange) -> None:
        if _settings_event_bus is None:
            return
        payload = {
            "path": change.path,
            "category": change.category,
            "changeType": change.changeType,
            "newValue": _deep_copy(change.newValue),
            "oldValue": _deep_copy(change.oldValue),
            "timestamp": change.timestamp,
        }
        _settings_event_bus.emit_setting_changed(payload)

    def _notify_batch(
        self, changes: list[_SettingsChange], summary: dict[str, Any]
    ) -> None:
        if _settings_event_bus is None or not changes:
            return
        payload = {
            "changes": [
                {
                    "path": change.path,
                    "category": change.category,
                    "changeType": change.changeType,
                    "newValue": _deep_copy(change.newValue),
                    "oldValue": _deep_copy(change.oldValue),
                    "timestamp": change.timestamp,
                }
                for change in changes
            ],
            "summary": summary,
        }
        _settings_event_bus.emit_settings_batch(payload)

    # Dotted-path helpers -----------------------------------------------------
    def _traverse(
        self, root: dict[str, Any], path: Iterable[str], create: bool
    ) -> dict[str, Any]:
        node = root
        for key in path:
            if key not in node:
                if not create:
                    return {}
                node[key] = {}
            value = node[key]
            if not isinstance(value, dict):
                if create:
                    node[key] = {}
                    value = node[key]
                else:
                    return {}
            node = value
        return node

    def _check_permission(self, dotted_path: str, *, intent: str) -> None:
        self._access_control.require_permission(dotted_path, intent=intent)

    def get(self, dotted_path: str, default: Any = None) -> Any:
        parts = dotted_path.split(".") if dotted_path else []
        if not parts:
            return _deep_copy(self._data)

        head = parts[0]
        if head == "metadata":
            node: Any = self._metadata
            parts = parts[1:]
        elif head == "defaults_snapshot":
            node = self._defaults
            parts = parts[1:]
        elif head == "current":
            node = self._data
            parts = parts[1:]
        elif head in self._extra:
            node = self._extra[head]
            parts = parts[1:]
        else:
            node = self._data

        if not parts:
            return _deep_copy(node)

        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return _deep_copy(node)

    def set(self, dotted_path: str, value: Any, auto_save: bool = True) -> bool:
        if not dotted_path:
            raise ValueError("Path must be non-empty")

        self._check_permission(dotted_path, intent="set")

        segments = dotted_path.split(".")
        head = segments[0]
        tail = segments[1:]
        timestamp = _utc_now()
        category = dotted_path.split(".", 1)[0]

        def _emit_change(
            path: str, category_name: str, new_value: Any, previous: Any
        ) -> None:
            self._notify_change(
                _SettingsChange(
                    path=path,
                    category=category_name,
                    changeType="set",
                    newValue=new_value,
                    oldValue=previous,
                    timestamp=timestamp,
                )
            )

        if head == "current" and not tail:
            if not isinstance(value, Mapping):
                raise TypeError("The 'current' section must be a mapping")
            previous = _deep_copy(self._data)
            new_payload = _deep_copy(value)
            self._data = new_payload
            self._dirty = True
            if auto_save:
                self.save()
            _emit_change("current", "current", new_payload, previous)
            return True

        if head == "defaults_snapshot" and not tail:
            if not isinstance(value, Mapping):
                raise TypeError("The 'defaults_snapshot' section must be a mapping")
            previous = _deep_copy(self._defaults)
            new_payload = _deep_copy(value)
            self._defaults = new_payload
            self._dirty = True
            if auto_save:
                self.save()
            _emit_change(
                "defaults_snapshot", "defaults_snapshot", new_payload, previous
            )
            return True

        if head == "metadata" and not tail:
            if not isinstance(value, Mapping):
                raise TypeError("The 'metadata' section must be a mapping")
            previous = _deep_copy(self._metadata)
            self._metadata = _deep_copy(value)
            self._ensure_units_version()
            self._dirty = True
            normalised = _deep_copy(self._metadata)
            if auto_save:
                self.save()
            _emit_change("metadata", "metadata", normalised, previous)
            return True

        if head in self._extra and not tail:
            previous = _deep_copy(self._extra[head])
            new_payload = _deep_copy(value)
            self._extra[head] = new_payload
            self._dirty = True
            if auto_save:
                self.save()
            _emit_change(head, head, new_payload, previous)
            return True

        if head == "current":
            root = self._data
            target_segments = tail
        elif head == "defaults_snapshot":
            root = self._defaults
            target_segments = tail
        elif head == "metadata":
            root = self._metadata
            target_segments = tail
        elif head in self._extra:
            section = self._extra.get(head)
            if not isinstance(section, dict):
                section = {}
                self._extra[head] = section
            root = section
            target_segments = tail
        elif len(segments) == 1:
            if head in self._data or head in self._defaults:
                root = self._data
            else:
                root = self._extra
            target_segments = segments
        else:
            root = self._data
            target_segments = segments

        if not target_segments:
            leaf = head
            node = root
        else:
            *parents, leaf = target_segments
            node = self._traverse(root, parents, create=True) if parents else root

        previous = (
            _deep_copy(node.get(leaf))
            if isinstance(node, dict) and leaf in node
            else None
        )
        if not isinstance(node, dict):
            raise TypeError(f"Cannot set value on non-mapping node at '{dotted_path}'")
        node[leaf] = _deep_copy(value)

        # Normalise HDR paths after applying the new value so that Windows
        # style separators never leak back into the stored payload or events.
        self._normalise_hdr_paths()

        self._dirty = True
        if auto_save:
            self.save()
        stored_value = (
            _deep_copy(node[leaf]) if isinstance(node, dict) else _deep_copy(value)
        )
        _emit_change(dotted_path, category, stored_value, previous)
        return True

    def _migrate_known_extras(self) -> bool:
        """Merge legacy top-level sections back into ``current``."""

        changed = False

        def _ensure_graphics_section() -> dict[str, Any]:
            section = self._data.setdefault("graphics", {})
            if not isinstance(section, dict):
                section = {}
                self._data["graphics"] = section
            return section

        graphics_extra = self._extra.pop("graphics", None)
        if isinstance(graphics_extra, dict):
            graphics_section = _ensure_graphics_section()
            _deep_update(graphics_section, graphics_extra)
            changed = True

        for category in (
            "camera",
            "environment",
            "materials",
            "effects",
            "lighting",
            "quality",
            "scene",
        ):
            payload = self._extra.pop(category, None)
            if not isinstance(payload, dict):
                continue
            graphics_section = _ensure_graphics_section()
            existing = graphics_section.get(category)
            if isinstance(existing, dict):
                _deep_update(existing, payload)
            else:
                graphics_section[category] = _deep_copy(payload)
            changed = True

        animation_extra = self._extra.pop("animation", None)
        if isinstance(animation_extra, dict):
            self._data["animation"] = _deep_copy(animation_extra)
            changed = True

        return changed

    # Defaults ---------------------------------------------------------------
    def get_all_defaults(self) -> dict[str, Any]:
        return _deep_copy(self._defaults)

    def get_runtime_defaults(self) -> dict[str, Any]:
        if self._runtime_defaults is None:
            from src.core.settings_service import load_runtime_defaults

            self._runtime_defaults = load_runtime_defaults()
        return _deep_copy(self._runtime_defaults)

    def get_physics_factories(self):
        """Lazy import factories for rigid body creation.

        The imports live here to avoid triggering heavyweight defaults when
        runtime modules are merely imported. Callers should rely on this
        method instead of importing the factories at module level.
        """

        from src.physics.integrator import create_default_rigid_body
        from src.physics.odes import RigidBody3DOF, create_initial_conditions

        return create_default_rigid_body, create_initial_conditions, RigidBody3DOF

    def create_default_system_configuration(self) -> dict[str, Any]:
        from src.core.settings_manager import (
            create_default_system_configuration as _create_default_system_configuration,
        )

        return _create_default_system_configuration(settings_manager=self)

    def create_default_gas_network(self, system: Any):
        from src.core.settings_manager import (
            create_default_gas_network as _create_default_gas_network,
        )

        return _create_default_gas_network(system, settings_manager=self)

    # Category helpers -------------------------------------------------------
    def get_category(
        self, category: str, default: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Return a deep copy of a category from the ``current`` section."""

        if not category:
            raise ValueError("Category name must be non-empty")

        if category in self._data:
            return _deep_copy(self._data[category])

        if default is None:
            return None

        return _deep_copy(default)

    def set_category(
        self, category: str, payload: dict[str, Any], *, auto_save: bool = True
    ) -> None:
        """Replace a category inside the ``current`` section."""

        if not category:
            raise ValueError("Category name must be non-empty")
        self._check_permission(f"current.{category}", intent="set_category")
        previous = _deep_copy(self._data.get(category))

        self._data[category] = _deep_copy(payload)

        self._dirty = True
        if auto_save:
            self.save()

        self._notify_change(
            _SettingsChange(
                path=f"current.{category}",
                category=category,
                changeType="set_category",
                newValue=payload,
                oldValue=previous,
                timestamp=_utc_now(),
            )
        )

    def reset_to_defaults(
        self, *, category: str | None = None, auto_save: bool = True
    ) -> None:
        """Reset ``current`` values to the defaults snapshot."""

        timestamp = _utc_now()
        changes: list[_SettingsChange] = []

        if category is None:
            self._check_permission("current", intent="reset_all")
            before = _deep_copy(self._data)
            self._data = _deep_copy(self._defaults)
            changes.append(
                _SettingsChange(
                    path="current",
                    category="*",
                    changeType="reset_all",
                    newValue=self._data,
                    oldValue=before,
                    timestamp=timestamp,
                )
            )
        else:
            if category not in self._defaults:
                raise KeyError(f"Unknown defaults category: {category}")
            self._check_permission(f"current.{category}", intent="reset")
            before = _deep_copy(self._data.get(category))
            self._data[category] = _deep_copy(self._defaults[category])
            changes.append(
                _SettingsChange(
                    path=f"current.{category}",
                    category=category,
                    changeType="reset",
                    newValue=self._defaults[category],
                    oldValue=before,
                    timestamp=timestamp,
                )
            )

        self._dirty = True
        if auto_save:
            self.save()

        if changes:
            summary = {
                "count": len(changes),
                "categories": sorted({change.category for change in changes}),
                "operation": "reset",
            }
            if len(changes) == 1:
                self._notify_change(changes[0])
            else:
                self._notify_batch(changes, summary)

    def save_current_as_defaults(
        self, *, category: str | None = None, auto_save: bool = True
    ) -> None:
        """Persist the current values into the defaults snapshot."""

        timestamp = _utc_now()
        changes: list[_SettingsChange] = []

        if category is None:
            self._check_permission("defaults_snapshot", intent="save_defaults_all")
            before = _deep_copy(self._defaults)
            self._defaults = _deep_copy(self._data)
            changes.append(
                _SettingsChange(
                    path="defaults_snapshot",
                    category="*",
                    changeType="save_defaults_all",
                    newValue=self._defaults,
                    oldValue=before,
                    timestamp=timestamp,
                )
            )
        else:
            if category not in self._data:
                raise KeyError(f"Unknown current category: {category}")
            self._check_permission(
                f"defaults_snapshot.{category}", intent="save_defaults"
            )
            before = _deep_copy(self._defaults.get(category))
            self._defaults[category] = _deep_copy(self._data[category])
            changes.append(
                _SettingsChange(
                    path=f"defaults_snapshot.{category}",
                    category=category,
                    changeType="save_defaults",
                    newValue=self._defaults[category],
                    oldValue=before,
                    timestamp=timestamp,
                )
            )

        self._dirty = True
        if auto_save:
            self.save()

        if changes:
            summary = {
                "count": len(changes),
                "categories": sorted({change.category for change in changes}),
                "operation": "save_defaults",
            }
            if len(changes) == 1:
                self._notify_change(changes[0])
            else:
                self._notify_batch(changes, summary)


_settings_manager: SettingsManager | None = None
_settings_event_bus: SettingsEventBus | None = None


def get_settings_manager(settings_file: Path | str | None = None) -> SettingsManager:
    global _settings_manager
    if _settings_manager is None or settings_file is not None:
        _settings_manager = SettingsManager(settings_file)
    return _settings_manager


def get_settings_event_bus() -> SettingsEventBus:
    global _settings_event_bus
    if _settings_event_bus is None:
        _settings_event_bus = SettingsEventBus()
    return _settings_event_bus


__all__ = [
    "ProfileSettingsManager",
    "SettingsEventBus",
    "SettingsManager",
    "get_settings_event_bus",
    "get_settings_manager",
]
