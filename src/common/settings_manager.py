# -*- coding: utf-8 -*-
"""
Unified Settings Manager
Единый менеджер настроек для всего приложения

ТРЕБОВАНИЯ:
- Один файл настроек для ВСЕГО приложения
- Никаких дефолтов в коде
- Сквозная прослеживаемость параметров
- Дефолты = текущие настройки (обновляются по кнопке "Сохранить как дефолт")
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import copy
import re


class SettingsManager:
    """
    Централизованный менеджер настроек приложения

    Архитектура:
    1. Загрузка из config/app_settings.json (единый источник истины)
    2. Изменения только через UI
    3. Автосохранение при каждом изменении
    4. "Сброс" = загрузка snapshot дефолтов из того же файла
    5. "Сохранить как дефолт" = обновление snapshot в файле

    Структура файла:
    {
        "current": { ... текущие настройки ... },
        "defaults_snapshot": { ... сохраненные дефолты ... },
        "metadata": { "version", "last_modified", ... }
    }
    """

    def __init__(self, settings_file: str | Path = "config/app_settings.json"):
        self.logger = logging.getLogger(__name__)
        # Разрешаем путь к файлу настроек более надёжно (CWD / корень проекта / env var)
        self.settings_file = self._resolve_settings_file(settings_file)

        # Внутреннее состояние
        self._current: Dict[str, Any] = {}
        self._defaults_snapshot: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}

        # Загрузка настроек
        self.load()

    def _resolve_settings_file(self, settings_file: str | Path) -> Path:
        """Определить корректный путь к файлу настроек.

        Алгоритм:
        1) PSS_SETTINGS_FILE из окружения (если задан и существует)
        2) Относительно текущего каталога (CWD)
        3) Относительно корня проекта (../../config от src/common)
        4) Возврат пути из аргумента (как есть)
        """
        try:
            # 1) ENV override
            import os

            env_path = os.environ.get("PSS_SETTINGS_FILE")
            if env_path:
                p = Path(env_path)
                if p.exists():
                    self.logger.info(f"Settings: using PSS_SETTINGS_FILE={p}")
                    if os.environ.get("PSS_VERBOSE_CONFIG") == "1":
                        print(f"[Settings] Using PSS_SETTINGS_FILE: {p}")
                    return p
                else:
                    self.logger.warning(
                        f"Settings: PSS_SETTINGS_FILE points to missing file: {p}"
                    )

            # 2) CWD relative
            p_in_cwd = Path(settings_file)
            if not p_in_cwd.is_absolute():
                p_in_cwd = Path.cwd() / p_in_cwd
            if p_in_cwd.exists():
                self.logger.info(f"Settings: found at CWD path: {p_in_cwd}")
                if os.environ.get("PSS_VERBOSE_CONFIG") == "1":
                    print(f"[Settings] Found at CWD: {p_in_cwd}")
                return p_in_cwd

            # 3) Project root relative (../../ from this file to repo root)
            project_root = Path(__file__).resolve().parents[2]
            candidate = project_root / "config" / "app_settings.json"
            if candidate.exists():
                self.logger.info(f"Settings: found at project path: {candidate}")
                if os.environ.get("PSS_VERBOSE_CONFIG") == "1":
                    print(f"[Settings] Found at project path: {candidate}")
                return candidate

            # 4) Fallback: as given
            p_fallback = Path(settings_file)
            self.logger.warning(
                f"Settings: using fallback path (may be created): {p_fallback}"
            )
            if os.environ.get("PSS_VERBOSE_CONFIG") == "1":
                print(f"[Settings] Fallback path: {p_fallback}")
            return p_fallback
        except Exception as e:
            self.logger.warning(f"Settings path resolve failed: {e}")
            return Path(settings_file)

    def _migrate_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Миграция старых ключей к новым именам без потери данных.
        Выполняется для секции current и defaults_snapshot отдельно.
        """
        try:
            geom = data.get("geometry")
            if isinstance(geom, dict):
                # tailRodLength -> tail_rod_length_mm
                if "tailRodLength" in geom and "tail_rod_length_mm" not in geom:
                    try:
                        v = geom.get("tailRodLength")
                        if isinstance(v, (int, float)):
                            geom["tail_rod_length_mm"] = float(v)
                    except Exception:
                        pass
                # frameHeight -> frame_height_mm
                if "frameHeight" in geom and "frame_height_mm" not in geom:
                    v = geom.get("frameHeight")
                    if isinstance(v, (int, float)):
                        geom["frame_height_mm"] = float(v)
                # frameBeamSize -> frame_beam_size_mm
                if "frameBeamSize" in geom and "frame_beam_size_mm" not in geom:
                    v = geom.get("frameBeamSize")
                    if isinstance(v, (int, float)):
                        geom["frame_beam_size_mm"] = float(v)
        except Exception as e:
            self.logger.warning(f"Не удалось выполнить миграцию ключей: {e}")
        return data

    def load(self) -> bool:
        """
        Загрузить настройки из JSON файла

        Returns:
            bool: True если успешно
        """
        if not self.settings_file.exists():
            # Больше не создаём заглушки — это критическая ошибка конфигурации
            msg = f"Settings file not found: {self.settings_file}"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as jde:
                    msg = f"Invalid JSON in settings file: {self.settings_file} — {jde}"
                    self.logger.error(msg)
                    raise

            # Новая структура с разделением current/defaults
            if "current" in data:
                # Мягкая миграция ключей
                data["current"] = self._migrate_keys(data.get("current", {}))
                data["defaults_snapshot"] = self._migrate_keys(
                    data.get("defaults_snapshot", {})
                )

                units_updated = self._maybe_upgrade_units(data)

                self._current = data["current"]
                self._defaults_snapshot = data.get("defaults_snapshot", {})
                # Если дефолтный снапшот отсутствует или пуст — делаем его равным current и сохраняем обратно
                if (
                    not isinstance(self._defaults_snapshot, dict)
                    or not self._defaults_snapshot
                ):
                    self._defaults_snapshot = copy.deepcopy(self._current)
                    # Немедленно сохраняем, чтобы файл содержал все дефолты (без скрытых значений)
                    try:
                        self.save()
                    except Exception:
                        # Если сохранение не удалось — пусть поднимется позже при явном save()
                        pass
                self._metadata = data.get("metadata", {})
                if units_updated:
                    try:
                        self.save()
                    except Exception as exc:
                        self.logger.warning(
                            f"Не удалось сохранить настройки после миграции единиц: {exc}"
                        )
            else:
                # Старая структура - мигрируем
                migrated = self._migrate_keys(data)
                self._current = migrated
                self._defaults_snapshot = copy.deepcopy(migrated)
                self._metadata = {
                    "version": data.get("version", "4.9.5"),
                    "last_modified": datetime.now().isoformat(),
                }
                self._maybe_upgrade_units(
                    {
                        "current": self._current,
                        "defaults_snapshot": self._defaults_snapshot,
                        "metadata": self._metadata,
                    }
                )
                self.save()

            # Диагностика наличия критичных секций
            mats_cnt = 0
            try:
                mats = self._current.get("graphics", {}).get("materials", {})
                if isinstance(mats, dict):
                    mats_cnt = len(mats.keys())
            except Exception:
                pass
            self.logger.info(
                f"Settings loaded from {self.settings_file} (materials keys: {mats_cnt})"
            )
            try:
                import os as _os

                if _os.environ.get("PSS_VERBOSE_CONFIG") == "1":
                    print(f"[Settings] Loaded: {self.settings_file}")
                    print(f"[Settings] materials keys: {mats_cnt}")
            except Exception:
                pass
            return True

        except Exception:
            # Пропускаем вверх — заглушки запрещены
            raise

    def save(self) -> bool:
        """
        Сохранить текущие настройки в JSON файл

        Returns:
            bool: True если успешно
        """
        try:
            # Гарантируем наличие директории
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            # Обновляем metadata
            self._metadata["last_modified"] = datetime.now().isoformat()

            # Структура файла
            data = {
                "current": self._current,
                "defaults_snapshot": self._defaults_snapshot,
                "metadata": self._metadata,
            }

            # Сохраняем с отступами для читаемости
            import os as _os

            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                # Гарантируем запись на диск (без кешей ОС)
                f.flush()
                try:
                    _os.fsync(f.fileno())
                except Exception:
                    # fsync может быть не доступен на некоторых FS — игнорируем
                    pass
            try:
                size = self.settings_file.stat().st_size
                self.logger.info(
                    f"Settings saved to {self.settings_file} ({size} bytes)"
                )
            except Exception:
                self.logger.info(f"Settings saved to {self.settings_file}")
            return True

        except Exception as e:
            # Больше не скрываем ошибки сохранения
            self.logger.error(f"Failed to save settings to {self.settings_file}: {e}")
            raise

    def get(self, path: str, default: Any = None) -> Any:
        """
        Получить значение по пути (dot-notation)

        Args:
            path: Путь к параметру, например "graphics.lighting.key.brightness"
            default: Значение по умолчанию если параметр не найден

        Returns:
            Значение параметра или default

        Example:
            >>> manager.get("graphics.effects.bloom_intensity")
            0.5
        """
        keys = path.split(".")
        value = self._current

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, path: str, value: Any, auto_save: bool = True) -> bool:
        """
        Установить значение по пути

        Args:
            path: Путь к параметру
            value: Новое значение
            auto_save: Автоматически сохранить в файл

        Returns:
            bool: True если успешно

        Example:
            >>> manager.set("graphics.effects.bloom_intensity", 0.8)
            True
        """
        keys = path.split(".")
        current = self._current

        # Создаем промежуточные словари если нужно
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        # Устанавливаем значение
        current[keys[-1]] = value

        # Автосохранение
        if auto_save:
            return self.save()

        return True

    def get_category(self, category: str) -> Dict[str, Any]:
        """
        Получить всю категорию настроек

        Args:
            category: Название категории ("graphics", "geometry", и т.д.)

        Returns:
            Словарь с настройками категории (КОПИЯ для безопасности)
        """
        # ✅ ИСПРАВЛЕНИЕ: Возвращаем глубокую копию чтобы избежать случайной модификации
        return copy.deepcopy(self._current.get(category, {}))

    def set_category(
        self, category: str, data: Dict[str, Any], auto_save: bool = True
    ) -> bool:
        """
        Установить всю категорию настроек

        Args:
            category: Название категории
            data: Словарь с настройками
            auto_save: Автоматически сохранить

        Returns:
            bool: True если успешно
        """
        self._current[category] = data

        if auto_save:
            return self.save()

        return True

    def reset_to_defaults(self, category: Optional[str] = None) -> bool:
        """
        Сбросить настройки к сохраненным дефолтам

        Args:
            category: Категория для сброса (None = сброс всего)

        Returns:
            bool: True если успешно
        """
        if category is None:
            # Сброс всех настроек
            self._current = copy.deepcopy(self._defaults_snapshot)
        else:
            # Сброс конкретной категории
            if category in self._defaults_snapshot:
                self._current[category] = copy.deepcopy(
                    self._defaults_snapshot[category]
                )

        return self.save()

    def save_current_as_defaults(self, category: Optional[str] = None) -> bool:
        """
        Сохранить текущие настройки как новые дефолты
        (кнопка "Сохранить как дефолт" в UI)

        Args:
            category: Категория для сохранения (None = сохранить все)

        Returns:
            bool: True если успешно
        """
        if category is None:
            # Сохраняем все текущие настройки как дефолты
            self._defaults_snapshot = copy.deepcopy(self._current)
        else:
            # Сохраняем конкретную категорию
            if category in self._current:
                self._defaults_snapshot[category] = copy.deepcopy(
                    self._current[category]
                )

        self.logger.info(
            f"Current settings saved as defaults (category={category or 'all'})"
        )
        return self.save()

    def get_all_current(self) -> Dict[str, Any]:
        """
        Получить ВСЕ текущие настройки

        Returns:
            Словарь с полными настройками
        """
        return copy.deepcopy(self._current)

    def get_all_defaults(self) -> Dict[str, Any]:
        """
        Получить сохраненные дефолты

        Returns:
            Словарь с дефолтами
        """
        return copy.deepcopy(self._defaults_snapshot)

    def _create_default_file(self):
        """Создать файл настроек с базовыми дефолтами"""
        # Минимальная структура настроек
        self._current = {
            "graphics": {
                "lighting": {},
                "environment": {},
                "quality": {},
                "camera": {},
                "effects": {},
                "materials": {},
            },
            "geometry": {},
            "simulation": {},
            "ui": {},
        }

        self._defaults_snapshot = copy.deepcopy(self._current)
        self._metadata = {
            "version": "4.9.5",
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
        }

        # Создаем директорию если нужно
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)

        # Сохраняем
        self.save()

    def _convert_value(self, value: Any) -> float | None:
        """
        Универсальная попытка преобразовать значение в число с плавающей точкой.

        Поддерживаемые варианты входа:
        - Число (int|float) → float
        - Строка с русской/английской записью дробей ("," или ".")
        - Строка с лишними символами/единицами (удаляются)

        Возвращает None если преобразование невозможно.
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            s = value.strip().lower()
            if not s:
                return None
            # Удаляем пробелы-разделители тысяч и апострофы
            s = s.replace(" ", "").replace("'", "")
            # Оставляем только допустимые символы числа, остальные (буквы единиц) режем
            s = re.sub(r"[^0-9\,\.eE\+\-]", "", s)
            # Если есть запятая и нет точки — считаем запятую десятичной
            if "," in s and "." not in s:
                s = s.replace(",", ".")
            else:
                # Иначе запятые считаем разделителями тысяч — убираем
                s = s.replace(",", "")
            try:
                return float(s)
            except Exception:
                return None
        return None

    def _convert_geometry_to_meters(self, section: Dict[str, Any]) -> bool:
        """Перевод геометрических значений из миллиметров в метры."""
        changed = False
        geom = section.get("geometry")
        if not isinstance(geom, dict):
            return changed

        conversions = {
            "frame_height_mm": "frame_height_m",
            "frame_beam_size_mm": "frame_beam_size_m",
            "tail_rod_length_mm": "tail_rod_length_m",
            "tail_mount_offset_mm": "tail_mount_offset_m",
            "frame_length_mm": "frame_length_m",
            "lever_length_mm": "lever_length_m",
            "cylinder_body_length_mm": "cylinder_body_length_m",
            "cylinder_cap_length_mm": "cylinder_cap_length_m",
        }

        for old_key, new_key in conversions.items():
            if old_key not in geom:
                continue
            converted_value = self._convert_value(geom.pop(old_key))
            if converted_value is None:
                continue
            geom.setdefault(new_key, converted_value / 1000.0)
            changed = True

        return changed

    def _convert_pneumatic_to_pascals(self, section: Dict[str, Any]) -> bool:
        """Перевод давлений из бар в Паскали."""
        changed = False
        pneumo = section.get("pneumatic")
        if not isinstance(pneumo, dict):
            return changed

        pressure_keys = {
            "cv_atmo_dp",
            "cv_tank_dp",
            "relief_min_pressure",
            "relief_stiff_pressure",
            "relief_safety_pressure",
        }

        for key in pressure_keys:
            if key not in pneumo:
                continue
            converted_value = self._convert_value(pneumo[key])
            if converted_value is None:
                continue
            # Если значение похоже на бары (мало), конвертируем в Па
            if converted_value < 1000.0:
                pneumo[key] = converted_value * 100000.0
                changed = True

        units_raw = pneumo.get("pressure_units")
        if isinstance(units_raw, str) and units_raw.lower().startswith("бар"):
            pneumo["pressure_units"] = "Па"
            changed = True

        return changed

    def _maybe_upgrade_units(self, data: Dict[str, Any]) -> bool:
        """Переход на систему СИ (метры/Паскали)."""
        metadata = data.setdefault("metadata", {})
        units_version = metadata.get("units_version")
        if units_version == "si_v2":
            return False

        changed = False
        for section_key in ("current", "defaults_snapshot"):
            section = data.get(section_key)
            if not isinstance(section, dict):
                continue
            if self._convert_geometry_to_meters(section):
                changed = True
            if self._convert_pneumatic_to_pascals(section):
                changed = True

        metadata_changed = metadata.get("units_version") != "si_v2"
        metadata["units_version"] = "si_v2"
        return changed or metadata_changed


# Singleton instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """
    Получить singleton instance SettingsManager

    Returns:
        SettingsManager: Единственный экземпляр менеджера
    """
    global _settings_manager

    if _settings_manager is None:
        _settings_manager = SettingsManager()

    return _settings_manager
