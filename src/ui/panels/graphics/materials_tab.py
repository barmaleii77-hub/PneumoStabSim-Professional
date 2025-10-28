# -*- coding: utf-8 -*-
"""
Materials Tab - вкладка настроек PBR материалов всех компонентов
Полный набор параметров PrincipledMaterial (Qt 6.10)
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QHBoxLayout,
    QGridLayout,
)
from PySide6.QtCore import Signal
from typing import Dict, Any, Optional

from .widgets import ColorButton, LabeledSlider


class MaterialsTab(QWidget):
    """Вкладка настроек материалов: 8 компонентов с полным PBR набором

    Signals:
        material_changed: Dict[str, Any] - параметры материалов изменились
    """

    material_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._controls: Dict[str, Any] = {}
        self._updating_ui = False
        # Кэш состояний по каждому материалу
        self._materials_state: Dict[str, Dict[str, Any]] = {}
        self._current_key: Optional[str] = None
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
        self._setup_ui()
        # Инициализируем текущий ключ после создания селектора
        self._current_key = self.get_current_material_key()

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

        # Base
        r = self._add_color_control(grid, r, "Базовый цвет", "base_color")
        r = self._add_slider_control(
            grid, r, "Непрозрачность", "opacity", 0.0, 1.0, 0.01
        )

        # Metal/Rough/Specular
        r = self._add_slider_control(
            grid, r, "Металличность", "metalness", 0.0, 1.0, 0.01
        )
        r = self._add_slider_control(
            grid, r, "Шероховатость", "roughness", 0.0, 1.0, 0.01
        )
        r = self._add_slider_control(
            grid, r, "Specular Amount", "specular", 0.0, 1.0, 0.01
        )
        r = self._add_color_control(grid, r, "Specular Tint", "specular_tint")

        # Clearcoat
        r = self._add_slider_control(grid, r, "Clearcoat", "clearcoat", 0.0, 1.0, 0.01)
        r = self._add_slider_control(
            grid, r, "Clearcoat Roughness", "clearcoat_roughness", 0.0, 1.0, 0.01
        )

        # Transmission / IOR / Thickness
        r = self._add_slider_control(
            grid, r, "Transmission", "transmission", 0.0, 1.0, 0.01
        )
        r = self._add_slider_control(
            grid, r, "Index of Refraction (IOR)", "ior", 1.0, 3.0, 0.01
        )
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

        # Normal/Occlusion
        r = self._add_slider_control(
            grid, r, "Normal Strength", "normal_strength", 0.0, 2.0, 0.01
        )
        r = self._add_slider_control(
            grid, r, "Occlusion Amount", "occlusion_amount", 0.0, 1.0, 0.01
        )

        # Alpha Mode/Mask
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

    # ========== HELPERS ==========
    def _coerce_color(self, value: Any, *, default: str = "#ffffff") -> str:
        """Преобразовать значение к hex цвету
        Поддерживает str (hex), tuple/list (r,g,b[,a]) и число [0..1] → оттенок серого
        """
        try:
            if isinstance(value, str) and value:
                return value
            if isinstance(value, (tuple, list)) and len(value) >= 3:
                components = []
                is_normalized = True
                for channel in value[:3]:
                    if not isinstance(channel, (int, float)):
                        is_normalized = False
                        break
                    components.append(float(channel))
                    if channel < 0 or channel > 1:
                        is_normalized = False
                if components:
                    if is_normalized:
                        converted = [int(round(max(0.0, min(1.0, c)) * 255)) for c in components]
                    else:
                        converted = [int(round(c)) for c in components]
                    r, g, b = (max(0, min(255, comp)) for comp in converted)
                    return f"#{r:02x}{g:02x}{b:02x}"
            if isinstance(value, (int, float)):
                v = max(0.0, min(1.0, float(value)))
                c = int(round(v * 255))
                return f"#{c:02x}{c:02x}{c:02x}"
        except Exception:
            pass
        return default

    def _coerce_material_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализовать типы значений для совместимости со старыми пресетами"""
        normalized = dict(state) if isinstance(state, dict) else {}
        # Цвета
        for ckey in (
            "base_color",
            "specular_tint",
            "attenuation_color",
            "emissive_color",
        ):
            if ckey in normalized:
                normalized[ckey] = self._coerce_color(
                    normalized.get(ckey),
                    default=("#000000" if ckey == "specular_tint" else "#ffffff"),
                )
        return normalized

    def _apply_controls_from_state(self, state: Dict[str, Any]) -> None:
        """Установить значения контролов из состояния (без эмита сигналов)"""
        if not isinstance(state, dict):
            return
        st = self._coerce_material_state(state)
        print(f"    🔧 _apply_controls_from_state: {len(st)} params to apply")
        self._updating_ui = True
        # Блокируем сигналы на время установки
        for control in self._controls.values():
            try:
                control.blockSignals(True)
            except Exception:
                pass
        applied_count = 0
        try:

            def set_if(k: str):
                nonlocal applied_count
                if k in st and k in self._controls:
                    ctrl = self._controls[k]
                    v = st[k]
                    if isinstance(ctrl, ColorButton):
                        print(f"      🎨 {k}: {ctrl.color().name()} → {v}")
                        ctrl.set_color(v)
                        applied_count += 1
                    elif isinstance(ctrl, LabeledSlider):
                        old_val = ctrl.value()
                        print(f"      🎚️ {k}: {old_val} → {v}")
                        ctrl.set_value(v)
                        applied_count += 1
                    elif hasattr(ctrl, "findData"):
                        old_idx = ctrl.currentIndex()
                        idx = ctrl.findData(v)
                        if idx >= 0:
                            print(f"      📋 {k}: index {old_idx} → {idx} (value: {v})")
                            ctrl.setCurrentIndex(idx)
                            applied_count += 1

            for k in (
                "base_color",
                "metalness",
                "roughness",
                "specular",
                "specular_tint",
                "opacity",
                "clearcoat",
                "clearcoat_roughness",
                "transmission",
                "ior",
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
            print(f"    ✅ Applied {applied_count}/{len(st)} controls")
        finally:
            for control in self._controls.values():
                try:
                    control.blockSignals(False)
                except Exception:
                    pass
            self._updating_ui = False

    def _save_current_into_cache(self) -> None:
        """Сохранить текущее состояние контролов в кэш для выбранного материала"""
        key = self.get_current_material_key()
        if not key:
            return
        self._materials_state[key] = self.get_current_material_state()

    # ========== EVENTS ==========
    def _on_material_selection_changed(self, index: int) -> None:
        # Смена выбранного материала: загружаем новый из кэша
        if self._updating_ui:
            return
        print(
            f"🔄 MaterialsTab: Changing selection from '{self._current_key}' to material at index {index}"
        )

        # ❌ УДАЛЕНО: НЕ сохраняем текущее состояние при переключении!
        # Контролы могут быть в промежуточном состоянии редактирования
        # Сохранение происходит ТОЛЬКО при изменении пользователем (_on_control_changed)

        # Получаем новый ключ
        new_key = self.get_current_material_key()
        print(f"  🔑 New material key: {new_key}")

        # КРИТИЧНО: Загружаем состояние для нового материала из кэша
        st = self._materials_state.get(new_key)
        if st:
            print(f"  ✅ Loading saved state for '{new_key}' ({len(st)} params)")
            self._apply_controls_from_state(st)
        else:
            print(f"  ⚠️ No saved state for '{new_key}' - using control defaults")
            # НЕ применяем контролы - пользователь видит дефолты
            # Но добавляем в кэш, чтобы сохранить при следующем изменении
            self._materials_state[new_key] = self.get_current_material_state()
            print(f"  📝 Initialized cache for '{new_key}' from controls")

        # Обновляем текущий ключ
        self._current_key = new_key

        # Эмитим payload текущего материала, чтобы сцена сразу отразила выбор
        if new_key:
            self.material_changed.emit(self.get_state())
            print(f"  📡 Emitted material_changed for '{new_key}'")

    def _on_control_changed(self, key: str, value: Any) -> None:
        if self._updating_ui:
            return
        # КРИТИЧНО: Обновляем кэш текущего материала ПЕРЕД эмитом
        cur_key = self.get_current_material_key()
        if cur_key:
            # Сначала обновляем параметр в кэше
            if cur_key not in self._materials_state:
                self._materials_state[cur_key] = {}
            self._materials_state[cur_key][key] = value
            # Потом обновляем полное состояние
            self._materials_state[cur_key] = self.get_current_material_state()
        # Эмитим payload ТОЛЬКО для текущего материала
        self.material_changed.emit(
            {"current_material": cur_key, cur_key: self.get_current_material_state()}
        )

    # ========== STATE API ==========
    def get_current_material_key(self) -> str:
        return self._material_selector.currentData()

    def get_current_material_state(self) -> Dict[str, Any]:
        return {
            "base_color": self._controls["base_color"].color().name(),
            "metalness": self._controls["metalness"].value(),
            "roughness": self._controls["roughness"].value(),
            "specular": self._controls["specular"].value(),
            "specular_tint": self._controls["specular_tint"].color().name(),
            "opacity": self._controls["opacity"].value(),
            "clearcoat": self._controls.get("clearcoat").value(),
            "clearcoat_roughness": self._controls.get("clearcoat_roughness").value(),
            "transmission": self._controls.get("transmission").value(),
            "ior": self._controls.get("ior").value(),
            "thickness": self._controls.get("thickness").value(),
            "attenuation_distance": self._controls.get("attenuation_distance").value(),
            "attenuation_color": self._controls.get("attenuation_color").color().name(),
            "emissive_color": self._controls["emissive_color"].color().name(),
            "emissive_intensity": self._controls["emissive_intensity"].value(),
            "normal_strength": self._controls["normal_strength"].value(),
            "occlusion_amount": self._controls["occlusion_amount"].value(),
            "alpha_mode": self._controls["alpha_mode"].currentData(),
            "alpha_cutoff": self._controls["alpha_cutoff"].value(),
        }

    def get_state(self) -> Dict[str, Any]:
        """Вернуть payload только для текущего материала (для сигналов/UI)
        Формат: {"current_material": key, key: {..params..}}
        """
        current_key = self.get_current_material_key()
        # Обновляем кэш перед возвратом
        if current_key:
            self._materials_state[current_key] = self.get_current_material_state()
        return {
            "current_material": current_key,
            current_key: self.get_current_material_state(),
        }

    def get_all_state(self) -> Dict[str, Dict[str, Any]]:
        """Вернуть состояние ВСЕХ материалов для сохранения/пресетов"""
        # Обновим кэш текущего
        cur_key = self.get_current_material_key()
        if cur_key:
            self._materials_state[cur_key] = self.get_current_material_state()
        # Возвращаем копию только известных ключей
        result: Dict[str, Dict[str, Any]] = {}
        for key in self._material_labels.keys():
            if key in self._materials_state:
                result[key] = dict(self._materials_state[key])
        # DEBUG: Логируем количество материалов в результате
        print(f"🔍 MaterialsTab.get_all_state(): returning {len(result)} materials")
        return result

    def set_material_state(self, material_key: str, state: Dict[str, Any]):
        # Обновляем кэш состояния
        if not isinstance(state, dict):
            return
        self._materials_state[material_key] = self._coerce_material_state(state)
        # Если этот материал текущий — применяем к контролам
        if material_key == self.get_current_material_key():
            self._apply_controls_from_state(self._materials_state[material_key])

    def set_state(self, state: Dict[str, Any]):
        """Установить состояния нескольких материалов сразу (из SettingsManager)
        Ожидается словарь { material_key: {..params..}, ... }
        """
        if not isinstance(state, dict):
            print(f"⚠️ MaterialsTab.set_state: state is not dict, got {type(state)}")
            return
        print(f"🔍 MaterialsTab.set_state: loading {len(state)} materials")
        # КРИТИЧНО: Сначала очищаем старый кэш
        self._materials_state.clear()
        # Заполняем кэш без трогания селектора
        alias_map = {"tail": "tail_rod"}

        for material_key, material_state in state.items():
            normalized_key = alias_map.get(material_key, material_key)
            if normalized_key in self._material_labels and isinstance(
                material_state, dict
            ):
                # Принудительно сохраняем ВСЕ поля в кэш (даже если их нет в контролах)
                coerced_state = self._coerce_material_state(material_state)
                self._materials_state[normalized_key] = coerced_state
                print(f"  ✅ Loaded {normalized_key}: {len(material_state)} params")
            else:
                print(f"  ⚠️ Skipped {material_key}: not in labels or not dict")
        # Обновляем контролы для текущего выбранного
        cur_key = self.get_current_material_key()
        if cur_key and cur_key in self._materials_state:
            self._apply_controls_from_state(self._materials_state[cur_key])
            print(f"  ✅ Applied controls for current material: {cur_key}")
        else:
            # Если текущий материал не найден в кэше — инициализируем его из контролов
            if cur_key and cur_key not in self._materials_state:
                self._materials_state[cur_key] = self.get_current_material_state()
                print(f"  ⚠️ Initialized {cur_key} from controls (was missing in state)")
        print(f"  📊 Total materials in cache: {len(self._materials_state)}")

    def get_controls(self) -> Dict[str, Any]:
        return self._controls

    def set_updating_ui(self, updating: bool) -> None:
        self._updating_ui = updating
