"""Signals Router Module - Signal connection and routing

Модуль подключения и роутинга сигналов между компонентами.
Управляет всеми сигнально-слотовыми соединениями главного окна.

Russian comments / English code.
"""

from __future__ import annotations

import copy
import logging
import math
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping, Optional

from importlib import import_module, util

if util.find_spec("PySide6.QtCore") is not None:
    qtcore = import_module("PySide6.QtCore")
    Qt = qtcore.Qt
    QTimer = getattr(qtcore, "QTimer", None)
    QObject = getattr(qtcore, "QObject", None)
else:  # pragma: no cover - executed only on headless environments

    class _QtStub:
        """Minimal stub providing the attribute used in tests."""

        QueuedConnection = "queued"

    Qt = _QtStub()
    QTimer = None
    QObject = None

from ...pneumo.enums import Line, Wheel
from ..panels.modes.defaults import (
    DEFAULT_PHYSICS_OPTIONS,
    MODE_PRESETS,
)
from .qml_bridge import QMLBridge


def _make_preset_id(name: str, index: int) -> str:
    token = (name or f"preset_{index}").strip().lower()
    normalized = [ch if ch.isalnum() else "_" for ch in token]
    collapsed = "".join(normalized)
    while "__" in collapsed:
        collapsed = collapsed.replace("__", "_")
    collapsed = collapsed.strip("_")
    return collapsed or f"preset_{index}"


_PRESET_LOOKUP: Dict[str, tuple[int, Dict[str, Any]]] = {}
for _preset_index, _preset_payload in MODE_PRESETS.items():
    preset_index = int(_preset_index)
    preset_name = str(_preset_payload.get("name", ""))
    preset_id = _make_preset_id(preset_name, preset_index)
    _PRESET_LOOKUP[preset_id] = (preset_index, dict(_preset_payload))
    _PRESET_LOOKUP[str(preset_index)] = (preset_index, dict(_preset_payload))
from ..environment_schema import (
    EnvironmentValidationError,
    validate_scene_settings,
)
from ..qml_bridge import register_qml_signals

if TYPE_CHECKING:
    from .main_window_refactored import MainWindow
    from ...runtime import StateSnapshot


class SignalsRouter:
    """Роутер сигналов главного окна

    Управляет:
    - Подключением сигналов панелей
    - Роутингом сигналов симуляции
    - Обработчиками событий UI

    Static methods для делегирования из MainWindow.
    """

    logger = logging.getLogger(__name__)
    _WHEEL_KEY_MAP = {
        Wheel.LP: "fl",
        Wheel.PP: "fr",
        Wheel.LZ: "rl",
        Wheel.PZ: "rr",
    }
    _CAMERA_FLOAT_TOLERANCE = 1e-5
    _CAMERA_COMMAND_KEYS = {"center_camera"}
    _HDR_SOURCE_KEYS = (
        "ibl_source",
        "iblSource",
        "ibl_primary",
        "iblPrimary",
        "hdr_source",
        "hdrSource",
    )
    _DEBOUNCE_DELAYS_MS = {
        "environment": 150,
        "effects": 150,
    }

    @staticmethod
    def _normalise_environment_payload(
        window: "MainWindow",
        params: Dict[str, Any],
        env_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Ensure HDR sources are normalised before dispatching to QML.

        The UI may report the selected HDRI through several legacy keys. We
        normalise the value using :meth:`MainWindow.normalizeHdrPath` (when
        available) so that both QML and the persisted settings share the same
        canonical representation.
        """

        source_key: str | None = None
        for candidate in SignalsRouter._HDR_SOURCE_KEYS:
            if candidate in params:
                source_key = candidate
                break

        if source_key is None:
            return SignalsRouter._apply_environment_aliases(params, env_payload)

        raw_value = params.get(source_key)
        text_value = "" if raw_value is None else str(raw_value)
        stripped_value = text_value.strip()
        allow_empty_selection = SignalsRouter._allow_empty_selection(
            raw_value, stripped_value
        )
        normalised_value = stripped_value

        if not allow_empty_selection:
            if hasattr(window, "normalizeHdrPath"):
                try:
                    candidate_value = window.normalizeHdrPath(stripped_value)
                    normalised_value = str(candidate_value).strip() or ""
                except Exception:  # pragma: no cover - logged for diagnostics
                    logger = getattr(window, "logger", SignalsRouter.logger)
                    logger.warning(
                        "Failed to normalise HDR path '%s'",
                        stripped_value,
                        exc_info=True,
                    )
            else:
                normalised_value = stripped_value
        else:
            normalised_value = ""

        filtered_params = {
            key: value
            for key, value in params.items()
            if key not in SignalsRouter._HDR_SOURCE_KEYS
        }
        params.clear()
        params.update(filtered_params)
        params["ibl_source"] = normalised_value

        updated_payload = {
            key: value
            for key, value in env_payload.items()
            if key not in SignalsRouter._HDR_SOURCE_KEYS
        }
        updated_payload["ibl_source"] = normalised_value
        return SignalsRouter._apply_environment_aliases(params, updated_payload)

    @staticmethod
    def _apply_environment_aliases(
        params: Dict[str, Any], env_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Augment payload with nested keys documented for environment updates."""

        def _first_mapping(*candidates: Any) -> Dict[str, Any] | None:
            for candidate in candidates:
                if isinstance(candidate, Mapping):
                    return dict(candidate)
            return None

        def _setdefault(target: Dict[str, Any], key: str, value: Any) -> None:
            if value is None:
                return
            if key not in target:
                target[key] = value

        background_section = _first_mapping(
            env_payload.get("background"), params.get("background")
        )
        if background_section:
            _setdefault(env_payload, "background_mode", background_section.get("mode"))
            _setdefault(
                env_payload, "background_color", background_section.get("color")
            )
            _setdefault(
                env_payload,
                "skybox_enabled",
                background_section.get("skybox_enabled"),
            )
            if "background_mode" in env_payload:
                params.setdefault("background_mode", env_payload["background_mode"])
            if "background_color" in env_payload:
                params.setdefault("background_color", env_payload["background_color"])
            if "skybox_enabled" in env_payload:
                params.setdefault("skybox_enabled", env_payload["skybox_enabled"])

        ibl_section = _first_mapping(env_payload.get("ibl"), params.get("ibl"))
        if ibl_section:
            ibl_map = {
                "enabled": "ibl_enabled",
                "intensity": "ibl_intensity",
                "source": "ibl_source",
                "fallback": "ibl_fallback",
                "lighting_enabled": "ibl_lighting_enabled",
                "background_enabled": "ibl_background_enabled",
                "skybox_brightness": "skybox_brightness",
                "probe_brightness": "probe_brightness",
                "probe_horizon": "probe_horizon",
                "rotation": "ibl_rotation",
                "rotation_x": "ibl_offset_x",
                "rotation_y": "ibl_rotation_deg",
                "rotation_z": "ibl_offset_y",
                "bind_to_camera": "ibl_bind_to_camera",
            }
            for source_key, target_key in ibl_map.items():
                value = ibl_section.get(source_key)
                _setdefault(env_payload, target_key, value)
                if target_key in env_payload:
                    params.setdefault(target_key, env_payload[target_key])

        fog_section = _first_mapping(env_payload.get("fog"), params.get("fog"))
        if fog_section:
            fog_map = {
                "enabled": "fog_enabled",
                "color": "fog_color",
                "density": "fog_density",
                "near": "fog_near",
                "far": "fog_far",
                "least_intense_y": "fog_least_intense_y",
                "most_intense_y": "fog_most_intense_y",
                "height_curve": "fog_height_curve",
                "height_enabled": "fog_height_enabled",
                "transmit_enabled": "fog_transmit_enabled",
                "transmit_curve": "fog_transmit_curve",
            }
            for source_key, target_key in fog_map.items():
                value = fog_section.get(source_key)
                _setdefault(env_payload, target_key, value)
                if target_key in env_payload:
                    params.setdefault(target_key, env_payload[target_key])

        ambient_section = _first_mapping(
            env_payload.get("ambient_occlusion"), params.get("ambient_occlusion")
        )
        if ambient_section:
            ao_map = {
                "enabled": "ao_enabled",
                "strength": "ao_strength",
                "radius": "ao_radius",
                "softness": "ao_softness",
                "dither": "ao_dither",
                "sample_rate": "ao_sample_rate",
                "bias": "ao_bias",
            }
            for source_key, target_key in ao_map.items():
                value = ambient_section.get(source_key)
                _setdefault(env_payload, target_key, value)
                if target_key in env_payload:
                    params.setdefault(target_key, env_payload[target_key])

            ssao_patch: Dict[str, Any] = {}
            if "enabled" in ambient_section:
                ssao_patch["enabled"] = ambient_section["enabled"]
            if "strength" in ambient_section:
                ssao_patch["intensity"] = ambient_section["strength"]
            if "radius" in ambient_section:
                ssao_patch["radius"] = ambient_section["radius"]
            if "softness" in ambient_section:
                ssao_patch["softness"] = ambient_section["softness"]
            if "dither" in ambient_section:
                ssao_patch["dither"] = ambient_section["dither"]
            if "sample_rate" in ambient_section:
                ssao_patch["sample_rate"] = ambient_section["sample_rate"]
            if ssao_patch:
                existing_ssao = env_payload.get("ssao")
                if isinstance(existing_ssao, Mapping):
                    merged_ssao = dict(existing_ssao)
                else:
                    merged_ssao = {}
                merged_ssao.update(ssao_patch)
                env_payload["ssao"] = merged_ssao
                params.setdefault("ssao", merged_ssao)

        return env_payload

    @staticmethod
    def _allow_empty_selection(
        raw_value: Any, stripped_value: str | None = None
    ) -> bool:
        """Return ``True`` when the HDR selector explicitly requests "no file".

        The FileCyclerWidget fix from PR #346 treats whitespace-only strings the
        same as an explicit empty selection. We mirror that behaviour here so the
        Python bridge does not reintroduce phantom paths when the UI clears the
        HDR field.
        """

        if raw_value is None:
            return True

        candidate = (
            stripped_value if stripped_value is not None else str(raw_value).strip()
        )
        return candidate == ""

    @staticmethod
    def _sanitize_camera_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
        cleaned: Dict[str, Any] = {}
        for key, value in payload.items():
            if value is None:
                continue
            if isinstance(value, Mapping):
                nested = SignalsRouter._sanitize_camera_payload(value)
                if nested:
                    cleaned[key] = nested
                continue
            cleaned[key] = value
        return cleaned

    @staticmethod
    def _normalize_camera_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(value, Mapping):
                nested = SignalsRouter._normalize_camera_payload(value)
                if nested:
                    normalized[key] = nested
                continue
            if isinstance(value, bool):
                normalized[key] = bool(value)
            elif isinstance(value, (int, float)):
                normalized[key] = float(value)
            else:
                normalized[key] = value
        return normalized

    @staticmethod
    def _normalize_quality_payload(params: Mapping[str, Any]) -> Dict[str, Any]:
        """Convert graphics quality payload into QML-friendly types."""

        def coerce_bool(value: Any) -> Optional[bool]:
            if value is None:
                return None
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {"true", "1", "yes", "on"}:
                    return True
                if lowered in {"false", "0", "no", "off"}:
                    return False
            return bool(value)

        def coerce_int(value: Any) -> Optional[int]:
            if value is None:
                return None
            if isinstance(value, bool):
                return int(value)
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return None
            if not math.isfinite(numeric):
                return None
            return int(round(numeric))

        def coerce_float(value: Any) -> Optional[float]:
            if value is None:
                return None
            if isinstance(value, bool):
                return float(int(value))
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return None
            if not math.isfinite(numeric):
                return None
            return numeric

        def coerce_str(value: Any) -> Optional[str]:
            if value is None:
                return None
            return str(value)

        normalized: Dict[str, Any] = {}

        antialiasing = (
            params.get("antialiasing") if isinstance(params, Mapping) else None
        )
        if isinstance(antialiasing, Mapping):
            aa_primary = antialiasing.get("primary")
            aa_quality = antialiasing.get("quality")
            aa_post = antialiasing.get("post")
        else:
            aa_primary = aa_quality = aa_post = None

        primary_value = params.get("aaPrimaryMode", aa_primary)
        primary_value = coerce_str(primary_value)
        if primary_value is not None:
            normalized["aaPrimaryMode"] = primary_value

        quality_value = params.get("aaQualityLevel", aa_quality)
        quality_value = coerce_str(quality_value)
        if quality_value is not None:
            normalized["aaQualityLevel"] = quality_value

        post_value = params.get("aaPostMode", aa_post)
        post_value = coerce_str(post_value)
        if post_value is not None:
            normalized["aaPostMode"] = post_value

        taa_enabled = params.get("taaEnabled", params.get("taa_enabled"))
        taa_enabled = coerce_bool(taa_enabled)
        if taa_enabled is not None:
            normalized["taaEnabled"] = taa_enabled

        taa_strength = params.get("taaStrength", params.get("taa_strength"))
        taa_strength = coerce_float(taa_strength)
        if taa_strength is not None:
            normalized["taaStrength"] = taa_strength

        taa_motion = params.get("taaMotionAdaptive", params.get("taa_motion_adaptive"))
        taa_motion = coerce_bool(taa_motion)
        if taa_motion is not None:
            normalized["taaMotionAdaptive"] = taa_motion

        fxaa_enabled = params.get("fxaaEnabled", params.get("fxaa_enabled"))
        fxaa_enabled = coerce_bool(fxaa_enabled)
        if fxaa_enabled is not None:
            normalized["fxaaEnabled"] = fxaa_enabled

        specular_enabled = params.get("specularAAEnabled", params.get("specular_aa"))
        specular_enabled = coerce_bool(specular_enabled)
        if specular_enabled is not None:
            normalized["specularAAEnabled"] = specular_enabled

        dithering_enabled = params.get("ditheringEnabled", params.get("dithering"))
        dithering_enabled = coerce_bool(dithering_enabled)
        if dithering_enabled is not None:
            normalized["ditheringEnabled"] = dithering_enabled

        oit_mode = params.get("oitMode", params.get("oit"))
        oit_mode = coerce_str(oit_mode)
        if oit_mode is not None:
            normalized["oitMode"] = oit_mode

        render_scale = params.get("renderScale", params.get("render_scale"))
        render_scale = coerce_float(render_scale)
        if render_scale is not None:
            normalized["renderScale"] = render_scale

        render_policy = params.get("renderPolicy", params.get("render_policy"))
        render_policy = coerce_str(render_policy)
        if render_policy is not None:
            normalized["renderPolicy"] = render_policy

        frame_limit = params.get("frameRateLimit", params.get("frame_rate_limit"))
        frame_limit = coerce_float(frame_limit)
        if frame_limit is not None:
            normalized["frameRateLimit"] = frame_limit

        mesh = params.get("mesh")
        if isinstance(mesh, Mapping):
            mesh_payload: Dict[str, Any] = {}
            segments = coerce_int(
                mesh.get("cylinderSegments", mesh.get("cylinder_segments"))
            )
            rings = coerce_int(mesh.get("cylinderRings", mesh.get("cylinder_rings")))
            if segments is not None:
                mesh_payload["cylinderSegments"] = segments
            if rings is not None:
                mesh_payload["cylinderRings"] = rings
            if mesh_payload:
                normalized["meshQuality"] = mesh_payload

        shadows = params.get("shadowSettings", params.get("shadows"))
        if isinstance(shadows, Mapping):
            shadow_payload: Dict[str, Any] = {}
            enabled = coerce_bool(shadows.get("enabled"))
            if enabled is not None:
                shadow_payload["enabled"] = enabled
            resolution = coerce_int(
                shadows.get("resolution", shadows.get("shadowResolution"))
            )
            if resolution is not None:
                shadow_payload["resolution"] = resolution
            filter_samples = coerce_int(
                shadows.get("filterSamples", shadows.get("filter"))
            )
            if filter_samples is not None:
                shadow_payload["filterSamples"] = filter_samples
            bias = coerce_float(shadows.get("bias", shadows.get("shadowBias")))
            if bias is not None:
                shadow_payload["bias"] = bias
            factor = coerce_float(
                shadows.get(
                    "factor", shadows.get("darkness", shadows.get("shadowFactor"))
                )
            )
            if factor is not None:
                shadow_payload["factor"] = factor
            if shadow_payload:
                normalized["shadowSettings"] = shadow_payload

        passthrough_aliases = {
            "msaa": coerce_int,
            "taa": coerce_bool,
            "shadows": coerce_str,
            "vSync": coerce_bool,
        }
        for alias, converter in passthrough_aliases.items():
            if alias in params and alias not in normalized:
                value = converter(params.get(alias)) if converter else params.get(alias)
                if value is not None:
                    normalized[alias] = value

        return normalized

    @staticmethod
    def _strip_camera_commands(payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Remove command-style keys that should not be persisted."""

        cleaned: Dict[str, Any] = {}
        for key, value in payload.items():
            if key in SignalsRouter._CAMERA_COMMAND_KEYS:
                continue
            if isinstance(value, Mapping):
                nested = SignalsRouter._strip_camera_commands(value)
                if nested:
                    cleaned[key] = nested
                continue
            cleaned[key] = value
        return cleaned

    @staticmethod
    def _contains_camera_commands(payload: Mapping[str, Any]) -> bool:
        for key, value in payload.items():
            if key in SignalsRouter._CAMERA_COMMAND_KEYS:
                return True
            if isinstance(value, Mapping) and SignalsRouter._contains_camera_commands(
                value
            ):
                return True
        return False

    @staticmethod
    def _camera_payloads_equal(
        first: Mapping[str, Any], second: Mapping[str, Any]
    ) -> bool:
        if first.keys() != second.keys():
            return False

        for key in first.keys():
            left = first[key]
            right = second[key]

            if isinstance(left, Mapping) and isinstance(right, Mapping):
                if not SignalsRouter._camera_payloads_equal(left, right):
                    return False
                continue

            if isinstance(left, float) and isinstance(right, float):
                if not math.isclose(
                    left,
                    right,
                    rel_tol=SignalsRouter._CAMERA_FLOAT_TOLERANCE,
                    abs_tol=SignalsRouter._CAMERA_FLOAT_TOLERANCE,
                ):
                    return False
                continue

            if left != right:
                return False

        return True

    @staticmethod
    def _build_simulation_payload(snapshot: "StateSnapshot") -> Dict[str, Any]:
        if snapshot is None:
            return {}

        levers: Dict[str, float] = {}
        pistons: Dict[str, float] = {}
        for wheel_enum, state in snapshot.wheels.items():
            corner = SignalsRouter._WHEEL_KEY_MAP.get(wheel_enum)
            if not corner:
                continue
            levers[corner] = float(state.lever_angle)
            pistons[corner] = float(state.piston_position)

        lines: Dict[str, Dict[str, Any]] = {}
        for line_enum, line_state in snapshot.lines.items():
            lines[line_enum.value] = {
                "pressure": float(line_state.pressure),
                "temperature": float(line_state.temperature),
                "flowAtmo": float(line_state.flow_atmo),
                "flowTank": float(line_state.flow_tank),
                "cvAtmoOpen": bool(line_state.cv_atmo_open),
                "cvTankOpen": bool(line_state.cv_tank_open),
            }

        aggregates = snapshot.aggregates
        aggregates_payload = {
            "kineticEnergy": float(aggregates.kinetic_energy),
            "potentialEnergy": float(aggregates.potential_energy),
            "pneumaticEnergy": float(aggregates.pneumatic_energy),
            "totalFlowIn": float(aggregates.total_flow_in),
            "totalFlowOut": float(aggregates.total_flow_out),
            "netFlow": float(aggregates.net_flow),
            "physicsStepTime": float(aggregates.physics_step_time),
            "integrationSteps": int(aggregates.integration_steps),
            "integrationFailures": int(aggregates.integration_failures),
            "stepNumber": int(snapshot.step_number),
            "simulationTime": float(snapshot.simulation_time),
        }

        frame_state = snapshot.frame
        frame_payload = {
            "heave": float(frame_state.heave),
            "roll": float(frame_state.roll),
            "pitch": float(frame_state.pitch),
            "heaveRate": float(frame_state.heave_rate),
            "rollRate": float(frame_state.roll_rate),
            "pitchRate": float(frame_state.pitch_rate),
        }

        tank_state = snapshot.tank
        tank_payload = {
            "pressure": float(tank_state.pressure),
            "temperature": float(tank_state.temperature),
            "volume": float(tank_state.volume),
        }

        return {
            "levers": levers,
            "pistons": pistons,
            "lines": lines,
            "aggregates": aggregates_payload,
            "frame": frame_payload,
            "tank": tank_payload,
            "masterIsolationOpen": bool(snapshot.master_isolation_open),
            "thermoMode": snapshot.thermo_mode,
        }

    @staticmethod
    def _queue_simulation_update(
        window: "MainWindow", snapshot: Optional["StateSnapshot"]
    ) -> None:
        if snapshot is None:
            return

        payload = SignalsRouter._build_simulation_payload(snapshot)
        if not payload:
            return

        if not SignalsRouter._should_emit_update(window, "simulation", payload):
            return

        QMLBridge.queue_update(window, "simulation", payload)
        SignalsRouter._record_dispatched_payload(window, "simulation", payload)

    # ------------------------------------------------------------------
    # Setup Connections
    # ------------------------------------------------------------------
    @staticmethod
    def connect_all_signals(window: MainWindow) -> None:
        """Подключить все сигналы окна

        Args:
            window: MainWindow instance
        """
        SignalsRouter._connect_panel_signals(window)
        SignalsRouter._connect_simulation_signals(window)
        SignalsRouter._connect_qml_signals(window)

        SignalsRouter.logger.info("✅ Все сигналы подключены")

    @staticmethod
    def _connect_panel_signals(window: MainWindow) -> None:
        """Подключить сигналы панелей к обработчикам

        Args:
            window: MainWindow instance
        """
        # Geometry panel
        if window.geometry_panel:
            window.geometry_panel.parameter_changed.connect(
                lambda name, val: SignalsRouter.logger.debug(
                    f"🔧 GeometryPanel: {name}={val}"
                )
            )
            window.geometry_panel.geometry_changed.connect(
                window._on_geometry_changed_qml
            )
            SignalsRouter.logger.info("✅ GeometryPanel signals connected")

        # Pneumo panel
        if window.pneumo_panel:
            window.pneumo_panel.mode_changed.connect(
                lambda mode_type, new_mode: SignalsRouter.logger.debug(
                    f"🔧 Mode changed: {mode_type} -> {new_mode}"
                )
            )
            window.pneumo_panel.parameter_changed.connect(
                lambda name, value: SignalsRouter.logger.debug(
                    f"🔧 Pneumo param: {name} = {value}"
                )
            )
            SignalsRouter.logger.info("✅ PneumoPanel signals connected")

        # Modes panel
        if window.modes_panel:
            window.modes_panel.simulation_control.connect(window._on_sim_control)
            window.modes_panel.mode_changed.connect(
                lambda mode_type, new_mode: SignalsRouter.logger.debug(
                    f"🔧 Mode changed: {mode_type} -> {new_mode}"
                )
            )
            window.modes_panel.parameter_changed.connect(
                lambda n, v: SignalsRouter.logger.debug(f"🔧 Param: {n} = {v}")
            )
            window.modes_panel.animation_changed.connect(window._on_animation_changed)
            SignalsRouter.logger.info("✅ ModesPanel signals connected")

        # Graphics panel
        if window.graphics_panel:
            window.graphics_panel.lighting_changed.connect(window._on_lighting_changed)
            window.graphics_panel.material_changed.connect(window._on_material_changed)
            window.graphics_panel.environment_changed.connect(
                window._on_environment_changed
            )
            window.graphics_panel.quality_changed.connect(window._on_quality_changed)
            window.graphics_panel.camera_changed.connect(window._on_camera_changed)
            window.graphics_panel.effects_changed.connect(window._on_effects_changed)
            if hasattr(window.graphics_panel, "scene_changed"):
                window.graphics_panel.scene_changed.connect(window._on_scene_changed)
            window.graphics_panel.preset_applied.connect(window._on_preset_applied)
            SignalsRouter.logger.info("✅ GraphicsPanel signals connected")

    @staticmethod
    def _connect_simulation_signals(window: MainWindow) -> None:
        """Подключить сигналы симуляции

        Args:
            window: MainWindow instance
        """
        try:
            bus = window.simulation_manager.state_bus
            bus.state_ready.connect(window._on_state_update, Qt.QueuedConnection)
            bus.physics_error.connect(window._on_physics_error, Qt.QueuedConnection)
            SignalsRouter.logger.info("✅ Simulation signals connected")
        except Exception as e:
            SignalsRouter.logger.error(f"Failed to connect simulation signals: {e}")

    @staticmethod
    def _connect_qml_signals(window: MainWindow) -> None:
        """Подключить сигналы QML

        Args:
            window: MainWindow instance
        """
        if not window._qml_root_object:
            return

        connected = register_qml_signals(window, window._qml_root_object)
        if connected:
            for spec in connected:
                SignalsRouter.logger.info(
                    "✅ QML signal %s connected to %s", spec.name, spec.handler
                )
        else:
            SignalsRouter.logger.warning("⚠️ No QML signals connected")

    # ------------------------------------------------------------------
    # Signal Handlers - Graphics
    # ------------------------------------------------------------------
    @staticmethod
    def handle_lighting_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle lighting changes from GraphicsPanel

        Args:
            window: MainWindow instance
            params: Lighting parameters
        """
        if not isinstance(params, dict):
            return

        if SignalsRouter._should_emit_update(window, "lighting", params):
            applied = QMLBridge.invoke_qml_function(
                window, "applyLightingUpdates", params
            )
            if not applied:
                QMLBridge.queue_update(window, "lighting", params)
            QMLBridge._log_graphics_change(window, "lighting", params, applied=applied)
            SignalsRouter._record_dispatched_payload(window, "lighting", params)

        window._apply_settings_update("graphics.lighting", params)

    @staticmethod
    def handle_material_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle material changes from GraphicsPanel"""
        if not isinstance(params, dict):
            return

        if SignalsRouter._should_emit_update(window, "materials", params):
            applied = QMLBridge.invoke_qml_function(
                window, "applyMaterialUpdates", params
            )
            if not applied:
                QMLBridge.queue_update(window, "materials", params)
            QMLBridge._log_graphics_change(window, "materials", params, applied=applied)
            SignalsRouter._record_dispatched_payload(window, "materials", params)

        window._apply_settings_update("graphics.materials", params)

    @staticmethod
    def handle_environment_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle environment changes from GraphicsPanel"""
        if not isinstance(params, dict):
            return

        SignalsRouter._schedule_debounced_update(
            window, "environment", params, SignalsRouter._dispatch_environment_update
        )

    @staticmethod
    def _dispatch_environment_update(
        window: MainWindow, params: Dict[str, Any]
    ) -> None:
        if not isinstance(params, dict):
            return

        reflection_keys = {
            "reflection_enabled",
            "reflection_padding_m",
            "reflection_quality",
            "reflection_refresh_mode",
            "reflection_time_slicing",
        }

        env_payload = {k: v for k, v in params.items() if k not in reflection_keys}
        if not env_payload:
            env_payload = dict(params)

        env_payload = SignalsRouter._normalise_environment_payload(
            window, params, env_payload
        )

        if SignalsRouter._should_emit_update(window, "environment", env_payload):
            applied = QMLBridge.invoke_qml_function(
                window, "applyEnvironmentUpdates", env_payload
            )
            if not applied:
                QMLBridge.queue_update(window, "environment", env_payload)
            QMLBridge._log_graphics_change(
                window, "environment", env_payload, applied=applied
            )
            SignalsRouter._record_dispatched_payload(window, "environment", env_payload)

        reflection_updates = {}
        if params.get("reflection_enabled") is not None:
            reflection_updates["enabled"] = bool(params["reflection_enabled"])
        if params.get("reflection_padding_m") is not None:
            reflection_updates["padding"] = float(params["reflection_padding_m"])
        if params.get("reflection_quality"):
            reflection_updates["quality"] = str(params["reflection_quality"])
        if params.get("reflection_refresh_mode"):
            reflection_updates["refreshMode"] = str(params["reflection_refresh_mode"])
        if params.get("reflection_time_slicing"):
            reflection_updates["timeSlicing"] = str(params["reflection_time_slicing"])

        if reflection_updates:
            three_d_payload = {"reflectionProbe": reflection_updates}
            if SignalsRouter._should_emit_update(window, "threeD", three_d_payload):
                applied = QMLBridge.invoke_qml_function(
                    window, "apply3DUpdates", three_d_payload
                )
                if not applied:
                    QMLBridge.queue_update(window, "threeD", three_d_payload)
                QMLBridge._log_graphics_change(
                    window, "threeD", three_d_payload, applied=applied
                )
                SignalsRouter._record_dispatched_payload(
                    window, "threeD", three_d_payload
                )

        window._apply_settings_update("graphics.environment", params)

    @staticmethod
    def handle_quality_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle quality changes from GraphicsPanel"""
        if not isinstance(params, dict):
            return

        normalized = SignalsRouter._normalize_quality_payload(params)

        if SignalsRouter._should_emit_update(window, "quality", normalized):
            applied = QMLBridge.invoke_qml_function(
                window, "applyQualityUpdates", normalized
            )
            if not applied:
                QMLBridge.queue_update(window, "quality", normalized)
            QMLBridge._log_graphics_change(
                window, "quality", normalized, applied=applied
            )
            SignalsRouter._record_dispatched_payload(window, "quality", normalized)

        window._apply_settings_update("graphics.quality", params)

    @staticmethod
    def handle_camera_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle camera changes from GraphicsPanel"""
        if not isinstance(params, dict):
            return

        sanitized = SignalsRouter._sanitize_camera_payload(params)
        if not sanitized:
            return

        stripped = SignalsRouter._strip_camera_commands(sanitized)
        normalized = SignalsRouter._normalize_camera_payload(stripped)
        last_payload = getattr(window, "_last_camera_payload", {})
        has_commands = SignalsRouter._contains_camera_commands(sanitized)
        if (
            not has_commands
            and last_payload
            and SignalsRouter._camera_payloads_equal(last_payload, normalized)
        ):
            SignalsRouter.logger.debug("⏭️ Skipping redundant camera update")
            return

        if not QMLBridge.invoke_qml_function(window, "applyCameraUpdates", sanitized):
            QMLBridge.queue_update(window, "camera", sanitized)
            QMLBridge._log_graphics_change(window, "camera", sanitized, applied=False)
        else:
            QMLBridge._log_graphics_change(window, "camera", sanitized, applied=True)

        SignalsRouter._record_dispatched_payload(window, "camera", sanitized)
        window._last_camera_payload = normalized

        if stripped:
            window._apply_settings_update("graphics.camera", stripped)

    @staticmethod
    def handle_effects_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle effects changes from GraphicsPanel"""
        if not isinstance(params, dict):
            return

        SignalsRouter._schedule_debounced_update(
            window, "effects", params, SignalsRouter._dispatch_effects_update
        )

    @staticmethod
    def _dispatch_effects_update(window: MainWindow, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return

        if SignalsRouter._should_emit_update(window, "effects", params):
            applied = QMLBridge.invoke_qml_function(
                window, "applyEffectsUpdates", params
            )
            if not applied:
                QMLBridge.queue_update(window, "effects", params)
            QMLBridge._log_graphics_change(window, "effects", params, applied=applied)
            SignalsRouter._record_dispatched_payload(window, "effects", params)

        window._apply_settings_update("graphics.effects", params)

    @staticmethod
    def handle_scene_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle scene changes from GraphicsPanel."""

        if not isinstance(params, dict):
            return

        try:
            validated = validate_scene_settings(params)
        except EnvironmentValidationError as exc:
            logger = getattr(window, "logger", SignalsRouter.logger)
            logger.warning("Invalid scene payload received: %s", exc)
            return

        if SignalsRouter._should_emit_update(window, "scene", validated):
            applied = QMLBridge.invoke_qml_function(
                window, "applySceneUpdates", validated
            )
            if not applied:
                QMLBridge.queue_update(window, "scene", validated)
            QMLBridge._log_graphics_change(window, "scene", validated, applied=applied)
            SignalsRouter._record_dispatched_payload(window, "scene", validated)

        window._apply_settings_update("graphics.scene", validated)

    @staticmethod
    def handle_preset_applied(window: MainWindow, full_state: Dict[str, Any]) -> None:
        """Handle graphics preset application

        Args:
            window: MainWindow instance
            full_state: Full graphics state
        """
        if not isinstance(full_state, dict):
            return

        environment_state = full_state.get("environment")
        if isinstance(environment_state, dict):
            env_payload = SignalsRouter._normalise_environment_payload(
                window,
                environment_state,
                dict(environment_state),
            )
        elif isinstance(environment_state, Mapping):
            env_dict = dict(environment_state)
            env_payload = SignalsRouter._normalise_environment_payload(
                window,
                env_dict,
                dict(env_dict),
            )
            full_state["environment"] = env_dict
        else:
            env_payload = {}

        def _coerce_payload(value: Any) -> Dict[str, Any]:
            if isinstance(value, Mapping):
                return dict(value)
            return {}

        # Queue all categories as batch
        updates: list[tuple[str, Dict[str, Any]]] = []
        updates.append(("environment", env_payload))
        updates.append(("lighting", _coerce_payload(full_state.get("lighting", {}))))
        updates.append(("materials", _coerce_payload(full_state.get("materials", {}))))
        quality_payload = SignalsRouter._normalize_quality_payload(
            full_state.get("quality", {})
        )
        updates.append(("quality", quality_payload))
        camera_state = SignalsRouter._sanitize_camera_payload(
            full_state.get("camera", {})
        )
        if camera_state:
            updates.append(("camera", camera_state))
            window._last_camera_payload = SignalsRouter._normalize_camera_payload(
                camera_state
            )
        updates.append(("effects", _coerce_payload(full_state.get("effects", {}))))

        for category, payload in updates:
            if not payload:
                continue
            if not SignalsRouter._should_emit_update(window, category, payload):
                continue
            QMLBridge.queue_update(window, category, payload)
            SignalsRouter._record_dispatched_payload(window, category, payload)

        window._apply_settings_update("graphics", full_state)

    @staticmethod
    def handle_animation_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle animation changes from ModesPanel"""
        if not isinstance(params, dict):
            return

        qml_payload: Dict[str, Any] = {}
        settings_payload: Dict[str, Any] = {}
        modes_payload: Dict[str, Any] = {}

        modes_key_map = {
            "amplitude": "amplitude",
            "frequency": "frequency",
            "phase_global": "phase",
            "phase_fl": "lf_phase",
            "phase_fr": "rf_phase",
            "phase_rl": "lr_phase",
            "phase_rr": "rr_phase",
            "smoothing_enabled": "smoothing_enabled",
            "smoothing_duration_ms": "smoothing_duration_ms",
            "smoothing_angle_snap_deg": "smoothing_angle_snap_deg",
            "smoothing_piston_snap_m": "smoothing_piston_snap_m",
            "smoothing_easing": "smoothing_easing",
        }

        def _assign_numeric(source_key: str, settings_key: str, qml_key: str) -> None:
            if settings_key in settings_payload and qml_key in qml_payload:
                return
            value = params.get(source_key)
            if value is None:
                return
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return
            settings_payload[settings_key] = numeric
            qml_payload[qml_key] = numeric
            modes_key = modes_key_map.get(settings_key)
            if modes_key:
                modes_payload[modes_key] = numeric

        def _assign_bool(source_keys, settings_key: str, qml_key: str) -> None:
            for key in source_keys:
                if key in params:
                    value = bool(params.get(key))
                    settings_payload[settings_key] = value
                    qml_payload[qml_key] = value
                    modes_key = modes_key_map.get(settings_key)
                    if modes_key:
                        modes_payload[modes_key] = value
                    return

        _assign_numeric("amplitude", "amplitude", "amplitude")
        _assign_numeric("frequency", "frequency", "frequency")
        _assign_numeric("animation_time", "animation_time", "simulationTime")
        _assign_numeric("simulationTime", "animation_time", "simulationTime")

        # Global phase aliases
        if "phase_global" not in settings_payload:
            _assign_numeric("phase_global", "phase_global", "phase_global")
        if "phase_global" not in settings_payload:
            _assign_numeric("phase", "phase_global", "phase_global")

        phase_aliases = {
            "phase_fl": ("phase_fl", "phase_fl"),
            "lf_phase": ("phase_fl", "phase_fl"),
            "phase_fr": ("phase_fr", "phase_fr"),
            "rf_phase": ("phase_fr", "phase_fr"),
            "phase_rl": ("phase_rl", "phase_rl"),
            "lr_phase": ("phase_rl", "phase_rl"),
            "phase_rr": ("phase_rr", "phase_rr"),
            "rr_phase": ("phase_rr", "phase_rr"),
        }
        for source_key, (settings_key, qml_key) in phase_aliases.items():
            if settings_key in settings_payload and qml_key in qml_payload:
                continue
            _assign_numeric(source_key, settings_key, qml_key)

        _assign_bool(
            ["smoothing_enabled", "smoothingEnabled"],
            "smoothing_enabled",
            "smoothingEnabled",
        )
        _assign_numeric(
            "smoothing_duration_ms", "smoothing_duration_ms", "smoothingDurationMs"
        )
        _assign_numeric(
            "smoothingDurationMs", "smoothing_duration_ms", "smoothingDurationMs"
        )
        _assign_numeric(
            "smoothing_angle_snap_deg",
            "smoothing_angle_snap_deg",
            "angleSnapThresholdDeg",
        )
        _assign_numeric(
            "smoothingAngleSnapDeg", "smoothing_angle_snap_deg", "angleSnapThresholdDeg"
        )
        _assign_numeric(
            "smoothing_piston_snap_m", "smoothing_piston_snap_m", "pistonSnapThresholdM"
        )
        _assign_numeric(
            "smoothingPistonSnapM", "smoothing_piston_snap_m", "pistonSnapThresholdM"
        )

        easing_value = (
            params.get("smoothing_easing")
            if params.get("smoothing_easing") is not None
            else params.get("smoothingEasing")
        )
        if easing_value is None and params.get("smoothingEasingName") is not None:
            easing_value = params.get("smoothingEasingName")
        if easing_value is not None:
            text = str(easing_value)
            settings_payload["smoothing_easing"] = text
            qml_payload["smoothingEasingName"] = text
            modes_key = modes_key_map.get("smoothing_easing")
            if modes_key:
                modes_payload[modes_key] = text

        running_value = None
        if "is_running" in params:
            running_value = params["is_running"]
        elif "isRunning" in params:
            running_value = params["isRunning"]
        if running_value is not None:
            running_flag = bool(running_value)
            settings_payload["is_running"] = running_flag
            qml_payload["isRunning"] = running_flag

        if qml_payload and SignalsRouter._should_emit_update(
            window, "animation", qml_payload
        ):
            applied = QMLBridge.invoke_qml_function(
                window, "applyAnimationUpdates", qml_payload
            )
            if not applied:
                QMLBridge.queue_update(window, "animation", qml_payload)
            QMLBridge._log_graphics_change(
                window,
                "animation",
                settings_payload if settings_payload else qml_payload,
                applied=applied,
            )
            SignalsRouter._record_dispatched_payload(window, "animation", qml_payload)

        if settings_payload:
            window._apply_settings_update("animation", settings_payload)
        if modes_payload:
            window._apply_settings_update("modes", modes_payload)
            SignalsRouter._push_modes_state(window)
        SignalsRouter._push_animation_panel(window)

    @staticmethod
    def handle_modes_preset_selected(
        window: MainWindow, preset_id: str
    ) -> None:
        """Apply a preset selected from the QML simulation panel."""

        key = (preset_id or "").strip().lower()
        if not key:
            return

        entry = _PRESET_LOOKUP.get(key)
        if entry is None:
            SignalsRouter.logger.debug("Unknown modes preset id: %s", preset_id)
            return

        _, preset = entry
        modes_updates: Dict[str, Any] = {
            "mode_preset": key,
        }

        sim_type = preset.get("sim_type")
        if sim_type:
            modes_updates["sim_type"] = str(sim_type)

        thermo_mode = preset.get("thermo_mode")
        if thermo_mode:
            modes_updates["thermo_mode"] = str(thermo_mode)

        physics_payload: Dict[str, bool] = {}
        for option in DEFAULT_PHYSICS_OPTIONS.keys():
            if option in preset:
                physics_payload[option] = bool(preset[option])
        if physics_payload:
            modes_updates["physics"] = physics_payload

        window._apply_settings_update("modes", modes_updates)
        SignalsRouter._push_modes_state(window)

        if thermo_mode:
            try:
                bus = window.simulation_manager.state_bus
                bus.set_thermo_mode.emit(str(thermo_mode))
            except Exception as exc:
                SignalsRouter.logger.debug(
                    "Failed to emit thermo mode change: %s", exc
                )

    @staticmethod
    def handle_modes_mode_changed(
        window: MainWindow, mode_type: str, new_mode: str
    ) -> None:
        """Handle simulation/thermo mode toggles from QML."""

        mode_key = (mode_type or "").strip()
        if not mode_key:
            return

        value = (new_mode or "").strip()
        if not value:
            return

        modes_updates = {mode_key: value}
        # Manual change implies custom preset
        modes_updates.setdefault("mode_preset", "custom")
        window._apply_settings_update("modes", modes_updates)
        SignalsRouter._push_modes_state(window)

        if mode_key.lower() == "thermo_mode":
            try:
                bus = window.simulation_manager.state_bus
                bus.set_thermo_mode.emit(value)
            except Exception as exc:
                SignalsRouter.logger.debug(
                    "Failed to emit thermo mode change: %s", exc
                )

    @staticmethod
    def handle_modes_physics_changed(
        window: MainWindow, payload: Mapping[str, Any]
    ) -> None:
        """Handle physics option toggles from QML."""

        if not isinstance(payload, Mapping):
            return

        physics_updates: Dict[str, bool] = {}
        for key in DEFAULT_PHYSICS_OPTIONS.keys():
            if key in payload:
                physics_updates[key] = bool(payload[key])

        if not physics_updates:
            return

        window._apply_settings_update(
            "modes",
            {
                "physics": physics_updates,
                "mode_preset": "custom",
            },
        )
        SignalsRouter._push_modes_state(window)

    @staticmethod
    def handle_pneumatic_settings_changed(
        window: MainWindow, payload: Mapping[str, Any]
    ) -> None:
        """Handle pneumatic parameter edits from QML."""

        if not isinstance(payload, Mapping):
            return

        numeric_keys = {
            "receiver_volume",
            "cv_atmo_dp",
            "cv_tank_dp",
            "cv_atmo_dia",
            "cv_tank_dia",
            "relief_min_pressure",
            "relief_stiff_pressure",
            "relief_safety_pressure",
            "throttle_min_dia",
            "throttle_stiff_dia",
            "atmo_temp",
        }
        pneumatic_updates: Dict[str, Any] = {}
        for key in numeric_keys:
            if key not in payload:
                continue
            try:
                pneumatic_updates[key] = float(payload[key])
            except (TypeError, ValueError):
                SignalsRouter.logger.debug(
                    "Skipping non-numeric pneumatic value %s=%r", key, payload[key]
                )

        if "master_isolation_open" in payload:
            pneumatic_updates["master_isolation_open"] = bool(
                payload.get("master_isolation_open")
            )

        if "volume_mode" in payload:
            pneumatic_updates["volume_mode"] = str(payload.get("volume_mode", "")).upper()

        if not pneumatic_updates:
            return

        window._apply_settings_update("pneumatic", pneumatic_updates)
        SignalsRouter._push_pneumatic_state(window)

        if "receiver_volume" in pneumatic_updates:
            receiver_volume = pneumatic_updates.get("receiver_volume")
            manager = getattr(window, "settings_manager", None)
            receiver_mode = pneumatic_updates.get("volume_mode")
            if receiver_mode is None and manager is not None:
                try:
                    current = manager.get_category("pneumatic") or {}
                    receiver_mode = current.get("volume_mode", "MANUAL")
                except Exception:
                    receiver_mode = "MANUAL"
            try:
                bus = window.simulation_manager.state_bus
                bus.set_receiver_volume.emit(float(receiver_volume), str(receiver_mode))
            except Exception as exc:
                SignalsRouter.logger.debug(
                    "Failed to emit receiver volume update: %s", exc
                )

    @staticmethod
    def handle_simulation_settings_changed(
        window: MainWindow, payload: Mapping[str, Any]
    ) -> None:
        """Handle core simulation settings edits from QML."""

        if not isinstance(payload, Mapping):
            return

        numeric_map = {
            "physics_dt": float,
            "render_vsync_hz": float,
            "max_steps_per_frame": int,
            "max_frame_time": float,
        }
        simulation_updates: Dict[str, Any] = {}
        for key, caster in numeric_map.items():
            if key not in payload:
                continue
            try:
                simulation_updates[key] = caster(payload[key])
            except (TypeError, ValueError):
                SignalsRouter.logger.debug(
                    "Skipping invalid simulation value %s=%r", key, payload[key]
                )

        if not simulation_updates:
            return

        window._apply_settings_update("simulation", simulation_updates)
        SignalsRouter._push_simulation_state(window)

        if "physics_dt" in simulation_updates:
            try:
                bus = window.simulation_manager.state_bus
                bus.set_physics_dt.emit(float(simulation_updates["physics_dt"]))
            except Exception as exc:
                SignalsRouter.logger.debug(
                    "Failed to emit physics_dt update: %s", exc
                )

    @staticmethod
    def handle_cylinder_settings_changed(
        window: MainWindow, payload: Mapping[str, Any]
    ) -> None:
        """Handle cylinder constant updates (dead zones) from QML."""

        if not isinstance(payload, Mapping):
            return

        numeric_keys = {"dead_zone_head_m3", "dead_zone_rod_m3"}
        cylinder_updates: Dict[str, float] = {}
        for key in numeric_keys:
            if key not in payload:
                continue
            try:
                cylinder_updates[key] = float(payload[key])
            except (TypeError, ValueError):
                SignalsRouter.logger.debug(
                    "Skipping invalid cylinder value %s=%r", key, payload[key]
                )

        if not cylinder_updates:
            return

        window._apply_settings_update(
            "constants",
            {"geometry": {"cylinder": cylinder_updates}},
        )
        SignalsRouter._push_cylinder_state(window)

    @staticmethod
    def handle_animation_toggled(window: MainWindow, running: bool) -> None:
        """Persist animation toggle coming from QML."""

        window._apply_settings_update("animation", {"is_running": bool(running)})

    # ------------------------------------------------------------------
    # Signal Handlers - Simulation
    # ------------------------------------------------------------------
    @staticmethod
    def handle_state_update(window: MainWindow, snapshot: StateSnapshot) -> None:
        """Handle simulation state update

        Args:
            window: MainWindow instance
            snapshot: Current simulation state
        """
        latest_snapshot: Optional[StateSnapshot] = snapshot

        try:
            if (
                hasattr(window, "simulation_manager")
                and window.simulation_manager is not None
                and hasattr(window.simulation_manager, "get_latest_state")
            ):
                fresh_snapshot = window.simulation_manager.get_latest_state()
                if fresh_snapshot is not None:
                    latest_snapshot = fresh_snapshot
        except Exception as exc:
            SignalsRouter.logger.debug(
                "Failed to fetch latest snapshot: %s", exc, exc_info=exc
            )

        window.current_snapshot = latest_snapshot

        try:
            if latest_snapshot:
                # Update status bar metrics
                window.sim_time_label.setText(
                    f"Sim Time: {latest_snapshot.simulation_time:.3f}s"
                )
                window.step_count_label.setText(f"Steps: {latest_snapshot.step_number}")

                if latest_snapshot.aggregates.physics_step_time > 0:
                    fps = 1.0 / latest_snapshot.aggregates.physics_step_time
                    window.fps_label.setText(f"Physics FPS: {fps:.1f}")

            # Update charts
            if window.chart_widget:
                window.chart_widget.update_from_snapshot(latest_snapshot)

            telemetry_bridge = getattr(window, "telemetry_bridge", None)
            if telemetry_bridge is not None and latest_snapshot is not None:
                try:
                    telemetry_bridge.push_snapshot(latest_snapshot)
                except Exception as telemetry_exc:
                    SignalsRouter.logger.debug(
                        "Telemetry bridge push failed: %s",
                        telemetry_exc,
                        exc_info=telemetry_exc,
                    )

            # Push state to QML (meters/pascals/radians)
            SignalsRouter._queue_simulation_update(window, latest_snapshot)
        except Exception as e:
            SignalsRouter.logger.error(f"State update error: {e}")

    @staticmethod
    def handle_physics_error(window: MainWindow, message: str) -> None:
        """Handle physics engine error

        Args:
            window: MainWindow instance
            message: Error message
        """
        SignalsRouter.logger.error(f"Physics engine error: {message}")

        if hasattr(window, "status_bar") and window.status_bar:
            window.status_bar.showMessage(f"Physics error: {message}", 5000)

    # ------------------------------------------------------------------
    # Signal Handlers - Simulation Control
    # ------------------------------------------------------------------
    @staticmethod
    def handle_sim_control(window: MainWindow, command: str) -> None:
        """Handle simulation control command

        Args:
            window: MainWindow instance
            command: Control command (start/pause/stop/reset)
        """
        cmd = (command or "").lower()

        animation_toggle: Optional[bool] = None

        if cmd == "start":
            window.is_simulation_running = True
            animation_toggle = True
        elif cmd == "pause":
            window.is_simulation_running = False
            animation_toggle = False
        elif cmd == "stop":
            window.is_simulation_running = False
            animation_toggle = False
        elif cmd == "reset":
            QMLBridge.invoke_qml_function(window, "fullResetView")
        else:
            SignalsRouter.logger.warning("Unknown simulation command: %s", command)
            return

        try:
            bus = window.simulation_manager.state_bus
        except Exception as exc:
            SignalsRouter.logger.error("Failed to access simulation bus: %s", exc)
            return

        try:
            if cmd == "start":
                bus.start_simulation.emit()
            elif cmd == "pause":
                bus.pause_simulation.emit()
            elif cmd == "stop":
                bus.stop_simulation.emit()
            elif cmd == "reset":
                bus.reset_simulation.emit()
        except Exception as exc:
            SignalsRouter.logger.error("Simulation control emit failed: %s", exc)

        if animation_toggle is not None:
            payload = {"isRunning": animation_toggle}
            applied = QMLBridge.invoke_qml_function(
                window, "applyAnimationUpdates", payload
            )
            if not applied:
                QMLBridge.queue_update(window, "animation", payload)
            SignalsRouter.handle_animation_toggled(window, animation_toggle)

    @staticmethod
    def _clone_value(value: Any) -> Any:
        """Return a best-effort deep copy of ``value`` suitable for caching."""

        if isinstance(value, Mapping):
            return {
                key: SignalsRouter._clone_value(nested) for key, nested in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [SignalsRouter._clone_value(item) for item in value]
        try:
            return copy.deepcopy(value)
        except Exception:
            return value

    @staticmethod
    def _clone_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Create a detached copy of a mapping payload."""

        base = dict(payload)
        try:
            return copy.deepcopy(base)
        except Exception:
            return {
                key: SignalsRouter._clone_value(value) for key, value in base.items()
            }

    @staticmethod
    def _merge_payload(target: Dict[str, Any], updates: Mapping[str, Any]) -> None:
        """Recursively merge ``updates`` into ``target``."""

        for key, value in updates.items():
            if isinstance(value, Mapping):
                nested_update = dict(value)
                existing = target.get(key)
                if not isinstance(existing, dict):
                    existing = {}
                target[key] = existing
                SignalsRouter._merge_payload(existing, nested_update)
            else:
                target[key] = SignalsRouter._clone_value(value)

    @staticmethod
    def _payloads_equal(left: Any, right: Any) -> bool:
        """Recursively compare two payload structures with float tolerance."""

        if left is right:
            return True

        if isinstance(left, Mapping) and isinstance(right, Mapping):
            if set(left.keys()) != set(right.keys()):
                return False
            return all(
                SignalsRouter._payloads_equal(left[key], right[key])
                for key in left.keys()
            )

        if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
            if len(left) != len(right):
                return False
            return all(
                SignalsRouter._payloads_equal(l_item, r_item)
                for l_item, r_item in zip(left, right)
            )

        numeric_types = (int, float)
        if isinstance(left, numeric_types) and isinstance(right, numeric_types):
            return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-9)

        return left == right

    @staticmethod
    def _get_last_payloads(window: "MainWindow") -> Dict[str, Any]:
        """Return the map tracking the last dispatched payload per category."""

        payloads: Dict[str, Any] | None = getattr(
            window, "_last_dispatched_payloads", None
        )
        if payloads is None:
            payloads = {}
            window._last_dispatched_payloads = payloads
        return payloads

    @staticmethod
    def _should_emit_update(
        window: "MainWindow", category: str, payload: Mapping[str, Any]
    ) -> bool:
        """Return ``True`` when the payload differs from cached state."""

        if not payload:
            return False

        last_payloads = getattr(window, "_last_dispatched_payloads", {})
        cached = last_payloads.get(category)
        if cached is not None and SignalsRouter._payloads_equal(cached, payload):
            SignalsRouter.logger.debug(
                "⏭️ Skipping redundant %s update (same as last payload)", category
            )
            return False

        queued = getattr(window, "_qml_update_queue", None)
        if queued is not None:
            existing = queued.get(category)
            if existing is not None and SignalsRouter._payloads_equal(
                existing, payload
            ):
                SignalsRouter.logger.debug(
                    "⏭️ %s update already queued; ignoring duplicate payload", category
                )
                return False

        return True

    @staticmethod
    def _record_dispatched_payload(
        window: "MainWindow", category: str, payload: Mapping[str, Any]
    ) -> None:
        """Cache the last payload dispatched for ``category``."""

        payloads = SignalsRouter._get_last_payloads(window)
        payloads[category] = SignalsRouter._clone_payload(payload)

    @staticmethod
    def _schedule_debounced_update(
        window: "MainWindow",
        category: str,
        payload: Dict[str, Any],
        dispatcher: Callable[["MainWindow", Dict[str, Any]], None],
    ) -> None:
        delay = SignalsRouter._DEBOUNCE_DELAYS_MS.get(category)
        if (
            not delay
            or delay <= 0
            or QTimer is None
            or QObject is None
            or not isinstance(window, QObject)
        ):
            dispatcher(window, payload)
            return

        if not isinstance(payload, Mapping):
            dispatcher(window, payload)
            return

        registry: Dict[str, Dict[str, Any]] | None = getattr(
            window, "_qml_debounce_registry", None
        )
        if registry is None:
            registry = {}
            window._qml_debounce_registry = registry

        entry = registry.get(category)
        if entry is None:
            parent = (
                window if QObject is not None and isinstance(window, QObject) else None
            )
            timer = QTimer(parent)
            timer.setSingleShot(True)
            try:
                timer.timeout.connect(
                    lambda cat=category: SignalsRouter._flush_debounced_update(
                        window, cat
                    )
                )
            except Exception:
                dispatcher(window, payload)
                return
            entry = {"timer": timer, "pending": None, "dispatcher": dispatcher}
            registry[category] = entry
        else:
            entry["dispatcher"] = dispatcher

        if entry.get("pending") is None:
            entry["pending"] = SignalsRouter._clone_payload(payload)
        else:
            SignalsRouter._merge_payload(entry["pending"], payload)

        timer = entry["timer"]
        try:
            if timer.isActive():
                timer.stop()
            timer.start(delay)
        except Exception:
            entry["pending"] = None
            dispatcher(window, payload)

    @staticmethod
    def _flush_debounced_update(window: "MainWindow", category: str) -> None:
        registry: Dict[str, Dict[str, Any]] | None = getattr(
            window, "_qml_debounce_registry", None
        )
        if not registry:
            return

        entry = registry.get(category)
        if not entry:
            return

        pending = entry.get("pending")
        entry["pending"] = None
        dispatcher = entry.get("dispatcher")
        if dispatcher is None:
            return

        if not isinstance(pending, dict) or not pending:
            return

        dispatcher(window, pending)

    # ------------------------------------------------------------------
    # Settings helpers (Python → QML synchronisation)
    # ------------------------------------------------------------------
    @staticmethod
    def _get_settings_category(window: "MainWindow", category: str) -> Dict[str, Any]:
        manager = getattr(window, "settings_manager", None)
        if manager is None:
            return {}
        try:
            payload = manager.get_category(category) or {}
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        return dict(payload)

    @staticmethod
    def _get_settings_path(window: "MainWindow", path: str) -> Dict[str, Any]:
        manager = getattr(window, "settings_manager", None)
        if manager is None:
            return {}
        try:
            payload = manager.get(path, {}) or {}
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        return dict(payload)

    @staticmethod
    def _push_modes_state(window: "MainWindow") -> None:
        payload = SignalsRouter._get_settings_category(window, "modes")
        QMLBridge.invoke_qml_function(window, "applyModesSettings", dict(payload))

    @staticmethod
    def _push_pneumatic_state(window: "MainWindow") -> None:
        payload = SignalsRouter._get_settings_category(window, "pneumatic")
        QMLBridge.invoke_qml_function(window, "applyPneumaticSettings", dict(payload))

    @staticmethod
    def _push_simulation_state(window: "MainWindow") -> None:
        payload = SignalsRouter._get_settings_category(window, "simulation")
        QMLBridge.invoke_qml_function(window, "applySimulationSettings", dict(payload))

    @staticmethod
    def _push_cylinder_state(window: "MainWindow") -> None:
        payload = SignalsRouter._get_settings_path(
            window, "current.constants.geometry.cylinder"
        )
        QMLBridge.invoke_qml_function(window, "applyCylinderSettings", dict(payload))

    @staticmethod
    def _push_animation_panel(window: "MainWindow") -> None:
        manager = getattr(window, "settings_manager", None)
        if manager is None:
            return
        try:
            payload = manager.get("animation", {}) or {}
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        QMLBridge.invoke_qml_function(window, "applyAnimationSettings", dict(payload))
