# -*- coding: utf-8 -*-
"""
State Manager - управление состоянием настроек GraphicsPanel
Загрузка/сохранение через QSettings, синхронизация Python↔QML
Part of modular GraphicsPanel restructuring
"""

from PySide6.QtCore import QSettings
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class GraphicsStateManager:
    """Управление состоянием настроек графики

    Отвечает за:
    - Загрузку/сохранение настроек через QSettings
    - Валидацию параметров
    - Синхронизацию состояния между вкладками
    """

    SETTINGS_ORG = "PneumoStabSim"
    SETTINGS_APP = "GraphicsPanel"

    # Ключи для сохранения
    STATE_KEYS = {
        "lighting": "state/lighting",
        "environment": "state/environment",
        "quality": "state/quality",
        "camera": "state/camera",
        "materials": "state/materials",
        "effects": "state/effects",
    }

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Settings instance
        self.settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

        # Current state cache
        self._state_cache: Dict[str, Dict[str, Any]] = {}

    def save_state(self, category: str, state: Dict[str, Any]):
        """Сохранить состояние категории

        Args:
            category: Категория ('lighting', 'environment', и т.д.)
            state: Словарь с параметрами
        """
        if category not in self.STATE_KEYS:
            self.logger.warning(f"Unknown category: {category}")
            return

        try:
            # Convert to JSON string for storage
            state_json = json.dumps(state, ensure_ascii=False)

            # Save to QSettings
            key = self.STATE_KEYS[category]
            self.settings.setValue(key, state_json)

            # Update cache
            self._state_cache[category] = state.copy()

            self.logger.debug(f"Saved {category} state ({len(state)} params)")

        except Exception as e:
            self.logger.error(f"Failed to save {category} state: {e}")

    def load_state(self, category: str) -> Optional[Dict[str, Any]]:
        """Загрузить состояние категории

        Args:
            category: Категория ('lighting', 'environment', и т.д.)

        Returns:
            Словарь с параметрами или None если не найдено
        """
        if category not in self.STATE_KEYS:
            self.logger.warning(f"Unknown category: {category}")
            return None

        try:
            # Check cache first
            if category in self._state_cache:
                self.logger.debug(f"Loaded {category} state from cache")
                return self._state_cache[category].copy()

            # Load from QSettings
            key = self.STATE_KEYS[category]
            state_json = self.settings.value(key, None)

            if state_json is None:
                self.logger.debug(f"No saved state for {category}")
                return None

            # Parse JSON
            state = json.loads(state_json)

            # Validate
            validated_state = self._validate_state(category, state)

            # Cache
            self._state_cache[category] = validated_state.copy()

            self.logger.debug(
                f"Loaded {category} state ({len(validated_state)} params)"
            )
            return validated_state

        except Exception as e:
            self.logger.error(f"Failed to load {category} state: {e}")
            return None

    def save_all(self, full_state: Dict[str, Dict[str, Any]]):
        """Сохранить полное состояние всех категорий

        Args:
            full_state: Словарь вида {'lighting': {...}, 'environment': {...}, ...}
        """
        for category, state in full_state.items():
            self.save_state(category, state)

        # Sync to disk
        self.settings.sync()

        self.logger.info(f"Saved full graphics state ({len(full_state)} categories)")

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """Загрузить полное состояние всех категорий

        Returns:
            Словарь вида {'lighting': {...}, 'environment': {...}, ...}
        """
        full_state = {}

        for category in self.STATE_KEYS.keys():
            state = self.load_state(category)
            if state is not None:
                full_state[category] = state

        self.logger.info(f"Loaded full graphics state ({len(full_state)} categories)")
        return full_state

    def reset_category(self, category: str):
        """Сбросить категорию к дефолтным значениям

        Args:
            category: Категория для сброса
        """
        if category not in self.STATE_KEYS:
            self.logger.warning(f"Unknown category: {category}")
            return

        # Remove from settings
        key = self.STATE_KEYS[category]
        self.settings.remove(key)

        # Remove from cache
        if category in self._state_cache:
            del self._state_cache[category]

        self.logger.info(f"Reset {category} state to defaults")

    def reset_all(self):
        """Сбросить все настройки к дефолтным"""
        # Clear all keys
        for key in self.STATE_KEYS.values():
            self.settings.remove(key)

        # Clear cache
        self._state_cache.clear()

        # Sync
        self.settings.sync()

        self.logger.info("Reset all graphics settings to defaults")

    def _validate_state(self, category: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Валидировать параметры состояния

        Args:
            category: Категория состояния
            state: Состояние для валидации

        Returns:
            Валидированное состояние (исправленное если нужно)
        """
        validated = state.copy()

        # Specific validation per category
        if category == "lighting":
            validated = self._validate_lighting(validated)
        elif category == "environment":
            validated = self._validate_environment(validated)
        elif category == "quality":
            validated = self._validate_quality(validated)
        elif category == "camera":
            validated = self._validate_camera(validated)
        elif category == "materials":
            validated = self._validate_materials(validated)
        elif category == "effects":
            validated = self._validate_effects(validated)

        return validated

    def _validate_lighting(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Валидировать параметры освещения"""
        # Clamp brightness values
        for key in [
            "key_brightness",
            "fill_brightness",
            "rim_brightness",
            "point_brightness",
        ]:
            if key in state:
                state[key] = max(0.0, min(10.0, state[key]))

        # Validate colors (must be hex strings)
        for key in ["key_color", "fill_color", "rim_color", "point_color"]:
            if key in state and not isinstance(state[key], str):
                state[key] = "#ffffff"

        return state

    def _validate_environment(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Валидировать параметры окружения"""
        # Normalize and validate HDR paths без подмены значений
        qml_root = Path("assets/qml").resolve()
        for key in ["ibl_source", "ibl_fallback"]:
            if key not in state:
                continue
            raw_value = state[key]
            if raw_value is None:
                state[key] = ""
                continue
            try:
                normalized = str(raw_value).strip().replace("\\", "/")
            except Exception:
                normalized = ""
            state[key] = normalized
            if not normalized:
                continue
            candidate = Path(normalized)
            if not candidate.is_absolute():
                candidate = (qml_root / normalized).resolve()
            if not candidate.exists():
                self.logger.warning(f"IBL file not found: {candidate}")

        # Clamp scalar values к диапазонам Qt 6.10
        if "ibl_intensity" in state:
            state["ibl_intensity"] = max(0.0, min(8.0, float(state["ibl_intensity"])))
        if "probe_brightness" in state:
            state["probe_brightness"] = max(
                0.0, min(8.0, float(state["probe_brightness"]))
            )
        if "probe_horizon" in state:
            state["probe_horizon"] = max(-1.0, min(1.0, float(state["probe_horizon"])))
        if "ibl_rotation" in state:
            state["ibl_rotation"] = max(
                -1080.0, min(1080.0, float(state["ibl_rotation"]))
            )
        if "ibl_offset_x" in state:
            state["ibl_offset_x"] = max(
                -180.0, min(180.0, float(state["ibl_offset_x"]))
            )
        if "ibl_offset_y" in state:
            state["ibl_offset_y"] = max(
                -180.0, min(180.0, float(state["ibl_offset_y"]))
            )
        if "skybox_blur" in state:
            state["skybox_blur"] = max(0.0, min(1.0, float(state["skybox_blur"])))

        if "fog_density" in state:
            state["fog_density"] = max(0.0, min(1.0, float(state["fog_density"])))
        if "fog_near" in state:
            state["fog_near"] = max(0.0, min(200000.0, float(state["fog_near"])))
        if "fog_far" in state:
            state["fog_far"] = max(500.0, min(400000.0, float(state["fog_far"])))
        if "fog_height_curve" in state:
            state["fog_height_curve"] = max(
                0.0, min(4.0, float(state["fog_height_curve"]))
            )
        if "fog_transmit_curve" in state:
            state["fog_transmit_curve"] = max(
                0.0, min(4.0, float(state["fog_transmit_curve"]))
            )
        if "fog_least_intense_y" in state:
            state["fog_least_intense_y"] = max(
                -100000.0, min(100000.0, float(state["fog_least_intense_y"]))
            )
        if "fog_most_intense_y" in state:
            state["fog_most_intense_y"] = max(
                -100000.0, min(100000.0, float(state["fog_most_intense_y"]))
            )
        if state.get("fog_far", 0.0) < state.get("fog_near", 0.0):
            state["fog_far"] = state["fog_near"]

        if "ao_strength" in state:
            state["ao_strength"] = max(0.0, min(100.0, float(state["ao_strength"])))
        if "ao_radius" in state:
            state["ao_radius"] = max(0.5, min(50.0, float(state["ao_radius"])))
        if "ao_softness" in state:
            state["ao_softness"] = max(0.0, min(50.0, float(state["ao_softness"])))
        if "ao_sample_rate" in state:
            state["ao_sample_rate"] = max(1, min(4, int(state["ao_sample_rate"])))
        if "ao_dither" in state:
            state["ao_dither"] = bool(state["ao_dither"])

        # Нормализуем булевы флаги явно
        for key in [
            "ibl_enabled",
            "skybox_enabled",
            "ibl_bind_to_camera",
            "fog_enabled",
            "fog_height_enabled",
            "fog_transmit_enabled",
            "ao_enabled",
        ]:
            if key in state:
                state[key] = bool(state[key])

        if "background_mode" in state:
            mode = str(state["background_mode"]).lower()
            if mode not in {"skybox", "color", "transparent"}:
                self.logger.warning(
                    f"Unknown background_mode '{state['background_mode']}', fallback to 'skybox'"
                )
                mode = "skybox"
            state["background_mode"] = mode

        return state

    def _validate_quality(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Валидировать параметры качества"""
        # Validate AA mode
        if "antialiasing" in state:
            state["antialiasing"] = max(0, min(3, int(state["antialiasing"])))

        # Validate shadow mapsize
        if "shadow_mapsize" in state:
            valid_sizes = [512, 1024, 2048, 4096]
            if state["shadow_mapsize"] not in valid_sizes:
                state["shadow_mapsize"] = 2048

        return state

    def _validate_camera(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Валидировать параметры камеры"""
        # Clamp FOV
        if "fov" in state:
            state["fov"] = max(30.0, min(120.0, state["fov"]))

        # Clamp clipping planes
        if "near_clip" in state:
            state["near_clip"] = max(0.01, min(10.0, state["near_clip"]))

        if "far_clip" in state:
            state["far_clip"] = max(10.0, min(1000.0, state["far_clip"]))

        return state

    def _validate_materials(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Валидировать параметры материалов"""
        # Validate material sub-dicts
        for material_key in ["metal", "glass", "frame", "cylinder"]:
            if material_key in state and isinstance(state[material_key], dict):
                material = state[material_key]

                # Clamp PBR values
                for pbr_key in [
                    "metalness",
                    "roughness",
                    "clearcoat",
                    "opacity",
                    "transmission",
                ]:
                    if pbr_key in material:
                        material[pbr_key] = max(0.0, min(1.0, material[pbr_key]))

                # Clamp IOR
                if "ior" in material:
                    material["ior"] = max(1.0, min(2.5, material["ior"]))

        return state

    def _validate_effects(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Валидировать параметры эффектов"""
        # Clamp ranges
        clamp_ranges = {
            "bloom_intensity": (0.0, 2.0),
            "bloom_threshold": (0.0, 2.0),
            "ssao_strength": (0.0, 100.0),
            "ssao_radius": (0.1, 10.0),
            "dof_focus_distance": (0.1, 20.0),
            "dof_focus_range": (0.1, 10.0),
            "dof_blur_amount": (0.0, 10.0),
            "vignette_strength": (0.0, 1.0),
        }

        for key, (min_val, max_val) in clamp_ranges.items():
            if key in state:
                state[key] = max(min_val, min(max_val, state[key]))

        return state

    def export_to_file(self, filepath: str):
        """Экспортировать текущее состояние в JSON файл

        Args:
            filepath: Путь к файлу для экспорта
        """
        try:
            full_state = self.load_all()

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(full_state, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Exported graphics state to: {filepath}")

        except Exception as e:
            self.logger.error(f"Failed to export state: {e}")

    def import_from_file(self, filepath: str) -> bool:
        """Импортировать состояние из JSON файла

        Args:
            filepath: Путь к файлу для импорта

        Returns:
            True если успешно
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                full_state = json.load(f)

            # Validate and save
            self.save_all(full_state)

            self.logger.info(f"Imported graphics state from: {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to import state: {e}")
            return False
