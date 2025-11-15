"""Materials Tab - вкладка настроек PBR материалов всех компонентов."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from .widgets import ColorButton, LabeledSlider, FileCyclerWidget
from .texture_discovery import discover_texture_files
from src.common.settings_manager import get_settings_manager

# Импорт сервиса настроек графики для доступа к baseline без дублирования логики
from src.ui.panels.graphics.panel_graphics_settings_manager import (
    GraphicsSettingsService,
    GraphicsSettingsError,
)


class MaterialsTab(QWidget):
    """Вкладка настроек материалов: 8 компонентов (минимальный поддерживаемый набор Qt 6.10)

    Удалены устаревшие поля specular / specular_tint / transmission / ior:
    - Qt 6.10 PrincipledMaterial не поддерживает эти свойства прямо
    - Управляем бликами через комбинацию metalness + roughness + clearcoat

    Signals:
        material_changed: dict[str, Any] - параметры материалов изменились
    """

    material_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._controls: dict[str, Any] = {}
        self._updating_ui = False
        self._materials_state: dict[str, dict[str, Any]] = {}
        self._current_key: str | None = None
        self._qml_root = Path(__file__).resolve().parents[4] / "assets" / "qml"
        self._material_labels = {
            "frame": "Рама",
            "lever": "Рычаг",
            "tail_rod": "Хвостовик",
            "cylinder": "Цилиндр (стекло)",
            "piston_body": "Корпус поршня",
            "piston_rod": "Шток",
            "joint_tail": "Шарнир хвостовика",
            "joint_arm": "Шарнир рычага",
            "joint_rod": "Шарнир штока",
        }
        self._texture_items = self._discover_texture_files()
        self._initial_texture_paths = self._load_initial_texture_paths()
        self._setup_ui()
        self._apply_initial_texture_selection()
        self._current_key = self.get_current_material_key()
        if self._current_key:
            self._materials_state[self._current_key] = self.get_current_material_state()
        # 🔄 ДОПОЛНИТЕЛЬНО: Предварительно гидратируем ВСЕ материалы baseline'ом,
        # чтобы get_all_state() сразу возвращал полный набор (для тестов гидратации).
        self._prepopulate_all_material_states()

    # --- PUBLIC TEST-COMPAT API ---
    def get_controls(self) -> dict[str, Any]:  # pragma: no cover - тестовый доступ
        """Вернуть словарь контролов (совместимость со старыми тестами).
        Возвращаем прямую ссылку для упрощения взаимодействия.
        """
        return self._controls

    def _prepopulate_all_material_states(self) -> None:
        """Заполнить кэш состояния для всех материалов.

        Источник значений:
        1. Пытаемся взять актуальный `current.graphics.materials` из SettingsManager (если файл содержит).
        2. Если раздел отсутствует / урезан, используем baseline из GraphicsSettingsService.
        3. Если baseline недоступен (непредвиденная ошибка), создаём дефолт на основе текущего состояния активного материала.

        Это предотвращает падение теста `graphics_panel_hydrates_missing_categories`,
        который ожидает полный набор ключей до первого переключения вкладки.
        """
        try:
            existing = {}
            sm = get_settings_manager()
            graphics_state = sm.get_category("graphics")
            if isinstance(graphics_state, dict):
                mats = graphics_state.get("materials", {})
                if isinstance(mats, dict):
                    existing = mats
        except Exception:
            existing = {}

        # Попытка прочитать baseline через сервис (гарантирует одинаковую гидратацию с GraphicsPanel)
        baseline = {}
        try:
            svc = GraphicsSettingsService()
            baseline = svc._baseline_graphics_current.get("materials", {})  # type: ignore[attr-defined]
            if not isinstance(baseline, dict):
                baseline = {}
        except GraphicsSettingsError:
            baseline = {}
        except Exception:
            baseline = {}

        # Состояние активного материала как дефолтный шаблон (если baseline пустой)
        active_state_template = self.get_current_material_state() if self._current_key else {
            "base_color": "#ffffff",
            "texture_path": "",
            "metalness": 0.0,
            "roughness": 0.5,
            "opacity": 1.0,
            "clearcoat": 0.0,
            "clearcoat_roughness": 0.3,
            "thickness": 0.0,
            "attenuation_distance": 0.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
            "normal_strength": 1.0,
            "occlusion_amount": 1.0,
            "alpha_mode": "default",
            "alpha_cutoff": 0.5,
        }

        for key in self._material_labels.keys():
            if key in self._materials_state:
                # Даже если уже есть, приоритетно применим сохранённый texture_path БЕЗ нормализации
                if key in self._initial_texture_paths:
                    raw_path = self._initial_texture_paths[key]
                    # Сохраняем путь как есть, даже если файл missing
                    self._materials_state[key]["texture_path"] = raw_path.replace("\\", "/") if raw_path else ""
                continue
            source_bucket = existing.get(key) or baseline.get(key) or active_state_template
            normed = self._coerce_material_state(dict(source_bucket)) if isinstance(source_bucket, dict) else {}
            # Всегда применяем сохранённый texture_path БЕЗ нормализации (сохраняем missing paths)
            if key in self._initial_texture_paths:
                raw_path = self._initial_texture_paths[key]
                normed["texture_path"] = raw_path.replace("\\", "/") if raw_path else ""
            self._materials_state[key] = normed

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Компонент", self))
        self._material_selector = QComboBox(self)
        for key, label in self._material_labels.items():
            self._material_selector.addItem(label, key)
        self._material_selector.currentIndexChanged.connect(
            self._on_material_selection_changed
        )
        selector_row.addWidget(self._material_selector, 1)
        selector_row.addStretch(1)
        layout.addLayout(selector_row)

        group = QGroupBox("Параметры материала (Qt 6.10 PrincipledMaterial)", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        r = 0

        # Base color + texture
        r = self._add_color_control(grid, r, "Базовый цвет", "base_color")
        grid.addWidget(QLabel("Текстура", self), r, 0)
        texture_widget = FileCyclerWidget(self)
        texture_widget.set_resolution_roots([self._qml_root])
        texture_widget.currentChanged.connect(
            lambda path: self._on_texture_changed(path)
        )
        self._controls["texture_path"] = texture_widget
        grid.addWidget(texture_widget, r, 1)
        r += 1

        # Opacity
        r = self._add_slider_control(
            grid, r, "Непрозрачность", "opacity", 0.0, 1.0, 0.01
        )

        # Metalness / Roughness
        r = self._add_slider_control(
            grid, r, "Металличность", "metalness", 0.0, 1.0, 0.01
        )
        r = self._add_slider_control(
            grid, r, "Шероховатость", "roughness", 0.0, 1.0, 0.01
        )

        # Clearcoat
        r = self._add_slider_control(grid, r, "Clearcoat", "clearcoat", 0.0, 1.0, 0.01)
        r = self._add_slider_control(
            grid, r, "Clearcoat Roughness", "clearcoat_roughness", 0.0, 1.0, 0.01
        )

        # Thickness
        r = self._add_slider_control(
            grid, r, "Толщина (thickness)", "thickness", 0.0, 500.0, 1.0, decimals=0
        )

        # Attenuation
        r = self._add_slider_control(
            grid, r, "Attenuation Distance", "attenuation_distance", 0.0, 100000.0, 10.0
        )
        r = self._add_color_control(grid, r, "Attenuation Color", "attenuation_color")

        # Emissive
        r = self._add_color_control(grid, r, "Излучающий цвет", "emissive_color")
        r = self._add_slider_control(
            grid, r, "Яркость излучения", "emissive_intensity", 0.0, 50.0, 0.1
        )

        # Normal / Occlusion
        r = self._add_slider_control(
            grid, r, "Normal Strength", "normal_strength", 0.0, 2.0, 0.01
        )
        r = self._add_slider_control(
            grid, r, "Occlusion Amount", "occlusion_amount", 0.0, 1.0, 0.01
        )

        # Alpha Mode + cutoff
        alpha_row = QHBoxLayout()
        alpha_row.addWidget(QLabel("Alpha Mode", self))
        alpha_combo = QComboBox(self)
        alpha_combo.addItem("Default", "default")
        alpha_combo.addItem("Mask", "mask")
        alpha_combo.addItem("Blend", "blend")
        alpha_combo.currentIndexChanged.connect(
            lambda _: self._on_control_changed("alpha_mode", alpha_combo.currentData())
        )
        self._controls["alpha_mode"] = alpha_combo
        alpha_row.addWidget(alpha_combo)
        alpha_row.addStretch(1)
        grid.addLayout(alpha_row, r, 0, 1, 2)
        r += 1
        r = self._add_slider_control(
            grid, r, "Alpha Cutoff (Mask)", "alpha_cutoff", 0.0, 1.0, 0.01
        )

        layout.addWidget(group)
        layout.addStretch(1)

    def _add_color_control(
        self, grid: QGridLayout, row: int, title: str, key: str
    ) -> int:
        container = QWidget(self)
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(6)
        hbox.addWidget(QLabel(title, self))
        button = ColorButton()
        button.color_changed.connect(lambda c: self._on_control_changed(key, c))
        self._controls[key] = button
        hbox.addWidget(button)
        hbox.addStretch(1)
        grid.addWidget(container, row, 0, 1, 2)
        return row + 1

    def _add_slider_control(
        self,
        grid: QGridLayout,
        row: int,
        title: str,
        key: str,
        minimum: float,
        maximum: float,
        step: float,
        *,
        decimals: int = 2,
    ) -> int:
        slider = LabeledSlider(title, minimum, maximum, step, decimals=decimals)
        slider.valueChanged.connect(lambda v: self._on_control_changed(key, v))
        self._controls[key] = slider
        grid.addWidget(slider, row, 0, 1, 2)
        return row + 1

    # ---------------- HELPERS ----------------
    def _coerce_color(self, value: Any, *, default: str = "#ffffff") -> str:
        try:
            if isinstance(value, str) and value:
                return value
            if isinstance(value, (tuple, list)) and len(value) >= 3:
                comps = []
                norm = True
                for channel in value[:3]:
                    if not isinstance(channel, (int, float)):
                        norm = False
                        break
                    comps.append(float(channel))
                    if channel < 0 or channel > 1:
                        norm = False
                if comps:
                    if norm:
                        # Нормализованные значения [0.0, 1.0] → [0, 255]
                        # Логика: floor для всех кроме точного .5, который округляется вверх
                        import math
                        conv: list[int] = []
                        for c in comps:
                            c = max(0.0, min(1.0, c))
                            raw = c * 255.0
                            floor_val = math.floor(raw)
                            frac = raw - floor_val
                            if abs(frac - 0.5) < 1e-9:
                                comp = floor_val + 1  # Округляем вверх для .5
                            else:
                                comp = floor_val  # Иначе floor
                            conv.append(comp)
                    else:
                        # Для значений вне диапазона [0,1] используем прямое приведение
                        conv = [int(c) if c >= 0 else 0 for c in comps]
                    r, g, b = (max(0, min(255, c)) for c in conv)
                    return f"#{r:02x}{g:02x}{b:02x}"
            if isinstance(value, (int, float)):
                import math
                v = max(0.0, min(1.0, float(value)))
                raw = v * 255.0
                floor_val = math.floor(raw)
                frac = raw - floor_val
                c = floor_val + 1 if abs(frac - 0.5) < 1e-9 else floor_val
                return f"#{c:02x}{c:02x}{c:02x}"
        except Exception:
            pass
        return default

    @staticmethod
    def _normalise_material_key(key: Any) -> str:
        if not isinstance(key, str):
            return str(key)
        token = key.strip()
        if not token:
            return ""
        if "_" in token:
            return token.lower()
        return re.sub(r"(?<!^)(?=[A-Z])", "_", token).lower()

    def _coerce_material_state(self, state: dict[str, Any]) -> dict[str, Any]:
        norm: dict[str, Any] = {}
        if isinstance(state, dict):
            for raw_key, value in state.items():
                ck = self._normalise_material_key(raw_key)
                if not ck:
                    continue
                norm[ck] = value
        if "color" in norm and "base_color" not in norm:
            norm["base_color"] = norm["color"]
        norm.pop("color", None)
        # Нормализуем только разделители слэшей,НЕ проверяем существование файла
        if "texture_path" in norm:
            raw_path = norm.get("texture_path")
            norm["texture_path"] = str(raw_path).replace("\\", "/") if raw_path else ""
        for ckey in ("base_color", "attenuation_color", "emissive_color"):
            if ckey in norm:
                norm[ckey] = self._coerce_color(norm.get(ckey), default="#ffffff")
        for legacy in ("specular", "specular_tint", "transmission", "ior"):
            norm.pop(legacy, None)
        return norm

    def _apply_controls_from_state(self, state: dict[str, Any]) -> None:
        if not isinstance(state, dict):
            return
        st = self._coerce_material_state(state)
        self._logger.debug("Applying %d parameters to material controls", len(st))
        self._updating_ui = True
        for control in self._controls.values():
            try:
                control.blockSignals(True)
            except Exception:
                pass
        try:

            def set_if(k: str):
                if k in st and k in self._controls:
                    ctrl = self._controls[k]
                    v = st[k]
                    if isinstance(ctrl, ColorButton):
                        ctrl.set_color(v)
                    elif isinstance(ctrl, LabeledSlider):
                        ctrl.set_value(v)
                    elif isinstance(ctrl, FileCyclerWidget):
                        # Подавляем warnings при программном применении состояния
                        ctrl.set_current_data(v, emit=False, suppress_warnings=True)
                    elif hasattr(ctrl, "findData"):
                        idx = ctrl.findData(v)
                        if idx >= 0:
                            ctrl.setCurrentIndex(idx)

            for k in (
                "base_color",
                "texture_path",
                "metalness",
                "roughness",
                "opacity",
                "clearcoat",
                "clearcoat_roughness",
                "thickness",
                "attenuation_distance",
                "attenuation_color",
                "emissive_color",
                "emissive_intensity",
                "normal_strength",
                "occlusion_amount",
                "alpha_mode",
                "alpha_cutoff",
            ):
                set_if(k)
        finally:
            for control in self._controls.values():
                try:
                    control.blockSignals(False)
                except Exception:
                    pass
            self._updating_ui = False

    def _save_current_into_cache(self) -> None:
        key = self.get_current_material_key()
        if not key:
            return
        self._materials_state[key] = self.get_current_material_state()

    # ---------------- EVENTS ----------------
    def _on_texture_changed(self, raw_path: str) -> None:
        normalized = self._normalize_texture_path(raw_path)
        self._on_control_changed("texture_path", normalized)

    def _on_material_selection_changed(self, index: int) -> None:
        if self._updating_ui:
            return
        new_key = self.get_current_material_key()
        st = self._materials_state.get(new_key)
        if st:
            self._apply_controls_from_state(st)
        else:
            self._materials_state[new_key] = self.get_current_material_state()
        self._current_key = new_key
        if new_key:
            self.material_changed.emit(self.get_state())

    def _on_control_changed(self, key: str, value: Any) -> None:
        if self._updating_ui:
            return
        cur_key = self.get_current_material_key()
        if cur_key:
            if cur_key not in self._materials_state:
                self._materials_state[cur_key] = {}
            # Прямо сохраняем значение в кэш (включая texture_path)
            self._materials_state[cur_key][key] = value
            # Обновляем полное состояние (но не перезаписываем texture_path если он уже есть)
            full_state = self.get_current_material_state()
            # Восстанавливаем texture_path из кэша если он был установлен выше
            if key == "texture_path":
                full_state["texture_path"] = value
            self._materials_state[cur_key] = full_state
        payload = {
            "current_material": cur_key,
            cur_key: self._materials_state.get(cur_key, self.get_current_material_state()),
        }
        self.material_changed.emit(payload)

    # ---------------- STATE API ----------------
    def get_current_material_key(self) -> str:
        return self._material_selector.currentData()

    def get_current_material_state(self) -> dict[str, Any]:
        cur_key = self.get_current_material_key()
        
        # Определяем актуальный texture_path:
        # 1. Если есть в кэше И ключ совпадает с текущим — используем кэш
        # 2. Иначе берём из виджета
        texture_path = ""
        if cur_key and cur_key in self._materials_state:
            cached_texture = self._materials_state[cur_key].get("texture_path", "")
            if cached_texture:
                texture_path = cached_texture
        
        # Если кэш пустой или отсутствует, берём из виджета
        if not texture_path:
            widget_path = self._controls["texture_path"].current_path()
            texture_path = widget_path.replace("\\", "/") if widget_path else ""
        
        return {
            "base_color": self._controls["base_color"].color().name(),
            "texture_path": texture_path,
            "metalness": self._controls["metalness"].value(),
            "roughness": self._controls["roughness"].value(),
            "opacity": self._controls["opacity"].value(),
            "clearcoat": self._controls.get("clearcoat").value(),
            "clearcoat_roughness": self._controls.get("clearcoat_roughness").value(),
            "thickness": self._controls.get("thickness").value(),
            "attenuation_distance": self._controls.get("attenuation_distance").value(),
            "attenuation_color": self._controls.get("attenuation_color").color().name(),
            "emissive_color": self._controls.get("emissive_color").color().name(),
            "emissive_intensity": self._controls.get("emissive_intensity").value(),
            "normal_strength": self._controls.get("normal_strength").value(),
            "occlusion_amount": self._controls.get("occlusion_amount").value(),
            "alpha_mode": self._controls.get("alpha_mode").currentData(),
            "alpha_cutoff": self._controls.get("alpha_cutoff").value(),
        }

    def get_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {}
        for key in self._material_labels.keys():
            if key in self._materials_state:
                state[key] = self._materials_state[key]
        state["current_material"] = self.get_current_material_key()
        return state

    def get_all_state(
        self,
    ) -> dict[str, dict[str, Any]]:  # pragma: no cover - тестовая функция
        """Вернуть копию всех кэшированных состояний материалов."""
        return {k: v.copy() for k, v in self._materials_state.items()}

    # ---------------- TEXTURE DISCOVERY ----------------
    def _discover_texture_files(self) -> list[tuple[str, str]]:
        try:
            search_dirs = [self._qml_root]
            tex_dir = self._qml_root / "textures"
            if tex_dir.exists():
                search_dirs.append(tex_dir)
            return discover_texture_files(search_dirs, qml_root=self._qml_root)
        except Exception as exc:  # pragma: no cover
            self._logger.warning("Не удалось получить список текстур: %s", exc)
            return []

    def _load_initial_texture_paths(self) -> dict[str, str]:
        sm = get_settings_manager()
        paths: dict[str, str] = {}
        try:
            materials_cfg: dict[str, Any] | None = None
            if hasattr(sm, "get_category"):
                try:
                    graphics_cat = sm.get_category("graphics")
                    if isinstance(graphics_cat, dict):
                        materials_cfg = graphics_cat.get("materials", {})
                except Exception:
                    materials_cfg = None
            if materials_cfg is None:
                direct = (
                    sm.get("current.graphics.materials", {})
                    if hasattr(sm, "get")
                    else {}
                )
                if isinstance(direct, dict):
                    materials_cfg = direct
            if isinstance(materials_cfg, dict):
                for key, cfg in materials_cfg.items():
                    if isinstance(cfg, dict):
                        raw = cfg.get("texture_path", "")
                        if isinstance(raw, str):
                            paths[key] = raw
        except Exception:
            pass
        return paths

    def _normalize_texture_path(self, raw: Any) -> str:
        if not raw:
            return ""
        text = str(raw).strip()
        if not text or text == "—":
            return ""
        # Нормализуем любые обратные слэши в POSIX разделители, но сохраняем путь
        return text.replace("\\", "/")

    def _apply_initial_texture_selection(self) -> None:
        tw = self._controls.get("texture_path")
        if not tw:
            return
        initial_key = self.get_current_material_key()
        saved = self._initial_texture_paths.get(initial_key, "") if initial_key else ""
        if saved:
            # Подавляем warnings при автозагрузке из настроек
            tw.set_current_data(saved, emit=False, suppress_warnings=True)
        tw.set_items(self._texture_items)
        # Второй вызов также с suppress_warnings для избежания дублирования
        tw.set_current_data(saved, emit=False, suppress_warnings=True)

    def _apply_saved_texture_path(self) -> None:
        tw = self._controls.get("texture_path")
        if not tw:
            return
        key = self.get_current_material_key()
        saved = self._initial_texture_paths.get(key, "") if key else ""
        if saved:
            # Подавляем warnings при программном восстановлении из настроек
            tw.set_current_data(saved, emit=False, suppress_warnings=True)

    def set_state(
        self, payload: dict[str, dict[str, Any]]
    ) -> None:  # pragma: no cover - тестовая функция
        if not isinstance(payload, dict):
            return
        self._materials_state.clear()
        for key, state in payload.items():
            if not isinstance(state, dict):
                continue
            normed = self._coerce_material_state(state)
            self._materials_state[key] = normed
        cur = self.get_current_material_key()
        if cur and cur in self._materials_state:
            self._apply_controls_from_state(self._materials_state[cur])
        # ВАЖНО: НЕ вызываем _prepopulate после внешней загрузки - это перезапишет payload из UI
        # _prepopulate_all_material_states()
