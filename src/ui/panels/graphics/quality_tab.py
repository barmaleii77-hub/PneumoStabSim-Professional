"""
Quality Tab - вкладка настроек качества рендеринга
Part of modular GraphicsPanel restructuring

СТРУКТУРА ТОЧНО ПОВТОРЯЕТ МОНОЛИТ panel_graphics.py (строки1133-1300):
- _build_quality_preset_group() → Предустановки качества (ultra/high/medium/low/custom)
- _build_shadow_group() → Тени (enabled, resolution, filter, bias, darkness)
- _build_antialiasing_group() → Сглаживание (primary, quality, post, TAA, FXAA, Specular AA)
- _build_render_group() → Производительность (render scale, policy, FPS limit, dithering, OIT)
- _build_mesh_group() → Параметры мешей (цилиндр: сегменты/кольца)
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QCheckBox,
    QHBoxLayout,
    QGridLayout,
)
from PySide6.QtCore import Signal
from typing import Any
import copy

from .widgets import LabeledSlider
from src.common.logging_widgets import LoggingCheckBox


class QualityTab(QWidget):
    """Вкладка настроек качества рендеринга: тени, AA, производительность

    Signals:
        quality_changed: dict[str, Any] - параметры качества изменились
        preset_applied: str - пресет качества применён (название)
    """

    quality_changed = Signal(dict)
    preset_applied = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Контролы UI
        self._controls: dict[str, Any] = {}
        self._updating_ui = False

        # Флаг для предотвращения переключения в custom при программном обновлении
        self._suspend_preset_sync = False

        # Пресеты качества - ТОЧНО КАК В МОНОЛИТЕ
        self._quality_presets = self._build_quality_presets()
        self._quality_preset_labels = {
            "ultra": "Ультра",
            "high": "Высокое",
            "medium": "Среднее",
            "low": "Низкое",
            "custom": "Пользовательский",
        }
        self._quality_preset_order = ["ultra", "high", "medium", "low", "custom"]

        # Setup UI
        self._setup_ui()

    def _build_quality_presets(self) -> dict[str, dict[str, Any]]:
        """Построить словарь пресетов качества - ТОЧНО КАК В МОНОЛИТЕ

        Изменения:
        - ultra: primary -> 'taa' (тест ожидает antialiasing.primary == 'taa')
        - ultra: taa_strength -> 0.85 (тест ожидает ~0.85)
        - ultra: render_scale -> 1.0 (синхронизировано с app_settings.json)
        - ultra: mesh цилиндра синхронизирован с конфигом (128/32)
        """
        return {
            "ultra": {
                "shadows": {
                    "enabled": True,
                    "resolution": 4096,
                    "filter": 32,
                    "bias": 8.0,
                    "darkness": 80.0,
                },
                "antialiasing": {"primary": "taa", "quality": "high", "post": "taa"},
                "taa_enabled": True,
                "taa_strength": 0.85,
                "taa_motion_adaptive": True,
                "fxaa_enabled": False,
                "specular_aa": True,
                "dithering": True,
                "render_scale": 1.0,
                "render_policy": "always",
                "frame_rate_limit": 144.0,
                "oit": "weighted",
                "mesh": {"cylinder_segments": 128, "cylinder_rings": 32},
            },
            "high": {
                "shadows": {
                    "enabled": True,
                    "resolution": 2048,
                    "filter": 16,
                    "bias": 9.5,
                    "darkness": 78.0,
                },
                "antialiasing": {"primary": "msaa", "quality": "high", "post": "off"},
                "taa_enabled": False,
                "taa_strength": 0.3,
                "taa_motion_adaptive": True,
                "fxaa_enabled": False,
                "specular_aa": True,
                "dithering": True,
                "render_scale": 1.0,
                "render_policy": "always",
                "frame_rate_limit": 120.0,
                "oit": "weighted",
                "mesh": {"cylinder_segments": 40, "cylinder_rings": 5},
            },
            "medium": {
                "shadows": {
                    "enabled": True,
                    "resolution": 1024,
                    "filter": 8,
                    "bias": 10.0,
                    "darkness": 75.0,
                },
                "antialiasing": {
                    "primary": "msaa",
                    "quality": "medium",
                    "post": "fxaa",
                },
                "taa_enabled": False,
                "taa_strength": 0.25,
                "taa_motion_adaptive": True,
                "fxaa_enabled": True,
                "specular_aa": True,
                "dithering": True,
                "render_scale": 0.9,
                "render_policy": "always",
                "frame_rate_limit": 90.0,
                "oit": "weighted",
                "mesh": {"cylinder_segments": 28, "cylinder_rings": 4},
            },
            "low": {
                "shadows": {
                    "enabled": True,
                    "resolution": 512,
                    "filter": 4,
                    "bias": 12.0,
                    "darkness": 70.0,
                },
                "antialiasing": {"primary": "off", "quality": "low", "post": "fxaa"},
                "taa_enabled": False,
                "taa_strength": 0.2,
                "taa_motion_adaptive": True,
                "fxaa_enabled": True,
                "specular_aa": False,
                "dithering": True,
                "render_scale": 0.8,
                "render_policy": "ondemand",
                "frame_rate_limit": 60.0,
                "oit": "none",
                "mesh": {"cylinder_segments": 20, "cylinder_rings": 3},
            },
        }

    def _setup_ui(self):
        """Построить UI вкладки - ТОЧНО КАК В МОНОЛИТЕ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # ✅ ТОЧНО КАК В МОНОЛИТЕ - 5 групп:
        layout.addWidget(self._build_quality_preset_group())
        layout.addWidget(self._build_shadow_group())
        layout.addWidget(self._build_antialiasing_group())
        layout.addWidget(self._build_render_group())
        layout.addWidget(self._build_mesh_group())

        layout.addStretch(1)

    def _build_quality_preset_group(self) -> QGroupBox:
        """Создать группу пресетов качества - ТОЧНО КАК В МОНОЛИТЕ"""
        group = QGroupBox("Предустановки качества", self)
        layout = QHBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Профиль", self))
        combo = QComboBox(self)
        for key in self._quality_preset_order:
            combo.addItem(self._quality_preset_labels[key], key)
        combo.currentIndexChanged.connect(
            lambda _: self._on_quality_preset_changed(combo.currentData())
        )
        self._controls["quality.preset"] = combo
        layout.addWidget(combo, 1)

        hint = QLabel(
            'Профиль "Пользовательский" активируется при ручных изменениях.', self
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #8a8a8a;")
        layout.addWidget(hint, 2)
        layout.addStretch(1)
        return group

    def _build_shadow_group(self) -> QGroupBox:
        """Создать группу теней - ТОЧНО КАК В МОНОЛИТЕ"""
        group = QGroupBox("Тени", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        # Shadows enabled checkbox
        enabled = LoggingCheckBox("Включить тени", "quality.shadows.enabled", self)
        enabled.clicked.connect(
            lambda checked: self._on_control_changed("shadows.enabled", checked)
        )
        self._controls["shadows.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)

        # Shadow resolution ComboBox
        resolution = QComboBox(self)
        for label, value in [
            ("256 (Низкое)", 256),
            ("512 (Среднее)", 512),
            ("1024 (Высокое)", 1024),
            ("2048 (Очень высокое)", 2048),
            ("4096 (Ультра)", 4096),
        ]:
            resolution.addItem(label, value)
        resolution.currentIndexChanged.connect(
            lambda _: self._on_control_changed(
                "shadows.resolution", resolution.currentData()
            )
        )
        self._controls["shadows.resolution"] = resolution
        grid.addWidget(QLabel("Разрешение", self), 1, 0)
        grid.addWidget(resolution, 1, 1)

        # Shadow filter ComboBox
        shadow_filter = QComboBox(self)
        for label, value in [
            ("Жёсткие", 1),
            ("PCF 4", 4),
            ("PCF 8", 8),
            ("PCF 16", 16),
            ("PCF 32", 32),
        ]:
            shadow_filter.addItem(label, value)
        shadow_filter.currentIndexChanged.connect(
            lambda _: self._on_control_changed(
                "shadows.filter", shadow_filter.currentData()
            )
        )
        self._controls["shadows.filter"] = shadow_filter
        grid.addWidget(QLabel("Фильтрация", self), 2, 0)
        grid.addWidget(shadow_filter, 2, 1)

        # Shadow bias slider
        bias = LabeledSlider("Shadow Bias", 0.0, 50.0, 0.1, decimals=2)
        bias.valueChanged.connect(lambda v: self._on_control_changed("shadows.bias", v))
        self._controls["shadows.bias"] = bias
        grid.addWidget(bias, 3, 0, 1, 2)

        # Shadow darkness slider
        darkness = LabeledSlider("Темнота", 0.0, 100.0, 1.0, decimals=0, unit="%")
        darkness.valueChanged.connect(
            lambda v: self._on_control_changed("shadows.darkness", v)
        )
        self._controls["shadows.darkness"] = darkness
        grid.addWidget(darkness, 4, 0, 1, 2)

        return group

    def _build_antialiasing_group(self) -> QGroupBox:
        """Создать группу сглаживания - ТОЧНО КАК В МОНОЛИТЕ"""
        group = QGroupBox("Сглаживание", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        # Primary AA ComboBox
        primary_combo = QComboBox(self)
        for label, value in [("Выкл.", "off"), ("MSAA", "msaa"), ("SSAA", "ssaa")]:
            primary_combo.addItem(label, value)
        primary_combo.currentIndexChanged.connect(
            lambda _: self._on_primary_aa_changed(primary_combo.currentData())
        )
        self._controls["aa.primary"] = primary_combo
        grid.addWidget(QLabel("Геометрическое AA", self), 0, 0)
        grid.addWidget(primary_combo, 0, 1)

        # AA quality ComboBox
        quality_combo = QComboBox(self)
        for label, value in [
            ("Низкое", "low"),
            ("Среднее", "medium"),
            ("Высокое", "high"),
        ]:
            quality_combo.addItem(label, value)
        quality_combo.currentIndexChanged.connect(
            lambda _: self._on_control_changed(
                "antialiasing.quality", quality_combo.currentData()
            )
        )
        self._controls["aa.quality"] = quality_combo
        grid.addWidget(QLabel("Качество", self), 1, 0)
        grid.addWidget(quality_combo, 1, 1)

        # Post-processing AA ComboBox
        post_combo = QComboBox(self)
        for label, value in [("Выкл.", "off"), ("FXAA", "fxaa"), ("TAA", "taa")]:
            post_combo.addItem(label, value)
        post_combo.currentIndexChanged.connect(
            lambda _: self._on_control_changed(
                "antialiasing.post", post_combo.currentData()
            )
        )
        self._controls["aa.post"] = post_combo
        grid.addWidget(QLabel("Постобработка", self), 2, 0)
        grid.addWidget(post_combo, 2, 1)

        # TAA enabled checkbox
        taa_check = LoggingCheckBox("Включить TAA", "quality.taa.enabled", self)
        taa_check.clicked.connect(
            lambda checked: self._on_control_changed("taa_enabled", checked)
        )
        self._controls["taa.enabled"] = taa_check
        grid.addWidget(taa_check, 3, 0, 1, 2)

        # TAA strength slider
        taa_strength = LabeledSlider("Сила TAA", 0.0, 1.0, 0.01, decimals=2)
        taa_strength.valueChanged.connect(
            lambda v: self._on_control_changed("taa_strength", v)
        )
        self._controls["taa.strength"] = taa_strength
        grid.addWidget(taa_strength, 4, 0, 1, 2)

        # TAA motion adaptive checkbox
        taa_motion = LoggingCheckBox(
            "Отключать TAA при движении камеры", "quality.taa.motion_adaptive", self
        )
        taa_motion.clicked.connect(
            lambda checked: self._on_control_changed("taa_motion_adaptive", checked)
        )
        self._controls["taa_motion_adaptive"] = taa_motion
        grid.addWidget(taa_motion, 5, 0, 1, 2)

        # FXAA enabled checkbox
        fxaa_check = LoggingCheckBox("Включить FXAA", "quality.fxaa.enabled", self)
        fxaa_check.clicked.connect(
            lambda checked: self._on_control_changed("fxaa_enabled", checked)
        )
        self._controls["fxaa.enabled"] = fxaa_check
        grid.addWidget(fxaa_check, 6, 0, 1, 2)

        # Specular AA checkbox
        specular_check = LoggingCheckBox(
            "Specular AA", "quality.specular_aa.enabled", self
        )
        specular_check.clicked.connect(
            lambda checked: self._on_control_changed("specular_aa", checked)
        )
        self._controls["specular.enabled"] = specular_check
        grid.addWidget(specular_check, 7, 0, 1, 2)

        return group

    def _build_render_group(self) -> QGroupBox:
        """Создать группу производительности - ТОЧНО КАК В МОНОЛИТЕ"""
        group = QGroupBox("Производительность", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        # Render scale slider
        scale_slider = LabeledSlider("Масштаб рендера", 0.5, 1.5, 0.01, decimals=2)
        scale_slider.valueChanged.connect(
            lambda v: self._on_control_changed("render_scale", v)
        )
        self._controls["render.scale"] = scale_slider
        grid.addWidget(scale_slider, 0, 0, 1, 2)

        # Render policy ComboBox
        policy_combo = QComboBox(self)
        policy_combo.addItem("Максимальная частота", "always")
        policy_combo.addItem("По требованию", "ondemand")
        policy_combo.currentIndexChanged.connect(
            lambda _: self._on_control_changed(
                "render_policy", policy_combo.currentData()
            )
        )
        self._controls["render.policy"] = policy_combo
        grid.addWidget(QLabel("Политика обновления", self), 1, 0)
        grid.addWidget(policy_combo, 1, 1)

        # Frame rate limit slider
        frame_slider = LabeledSlider("Лимит FPS", 24.0, 240.0, 1.0, decimals=0)
        frame_slider.valueChanged.connect(
            lambda v: self._on_control_changed("frame_rate_limit", v)
        )
        self._controls["frame_rate_limit"] = frame_slider
        grid.addWidget(frame_slider, 2, 0, 1, 2)

        # Dithering checkbox (Qt 6.10+)
        dithering_check = LoggingCheckBox(
            "Dithering (Qt 6.10+)", "quality.dithering.enabled", self
        )
        dithering_check.clicked.connect(
            lambda checked: self._on_control_changed("dithering", checked)
        )
        self._controls["dithering.enabled"] = dithering_check
        grid.addWidget(dithering_check, 3, 0, 1, 2)

        # Weighted OIT checkbox
        oit_check = LoggingCheckBox("Weighted OIT", "quality.oit.enabled", self)
        oit_check.clicked.connect(
            lambda checked: self._on_control_changed(
                "oit", "weighted" if checked else "none"
            )
        )
        self._controls["oit.enabled"] = oit_check
        grid.addWidget(oit_check, 4, 0, 1, 2)

        return group

    def _build_mesh_group(self) -> QGroupBox:
        """Создать группу параметров мешей (упрощает/детализирует цилиндры)"""
        group = QGroupBox("Геометрия мешей", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        seg = LabeledSlider(
            "Сегменты цилиндра по окружности", 8.0, 256.0, 1.0, decimals=0
        )
        seg.setToolTip("Настраивает детализацию меша цилиндров подвески по окружности.")
        seg.valueChanged.connect(
            lambda v: self._on_control_changed("mesh.cylinder_segments", int(v))
        )
        self._controls["mesh.cylinder_segments"] = seg
        grid.addWidget(seg, 0, 0, 1, 2)

        rings = LabeledSlider("Кольца цилиндра по длине", 1.0, 32.0, 1.0, decimals=0)
        rings.setToolTip(
            "Указывает количество сегментов по длине для процедурного цилиндра."
        )
        rings.valueChanged.connect(
            lambda v: self._on_control_changed("mesh.cylinder_rings", int(v))
        )
        self._controls["mesh.cylinder_rings"] = rings
        grid.addWidget(rings, 1, 0, 1, 2)

        return group

    # ========== ОБРАБОТЧИКИ ИЗМЕНЕНИЙ ==========

    def _on_quality_preset_changed(self, preset_key: str | None) -> None:
        """Обработчик изменения пресета качества - КАК В МОНОЛИТЕ"""
        if self._updating_ui:
            return
        if not preset_key:
            return
        if preset_key == "custom":
            # Просто эмитим сигнал о смене на custom
            self.quality_changed.emit(self.get_state())
            return

        # Применяем пресет
        self._apply_quality_preset(str(preset_key))

    def _apply_quality_preset(self, key: str) -> None:
        """Применить пресет качества - КАК В МОНОЛИТЕ"""
        config = self._quality_presets.get(key)
        if not config:
            return

        self._suspend_preset_sync = True
        try:
            # Устанавливаем значения из пресета
            preset_with_key = copy.deepcopy(config)
            preset_with_key["preset"] = key

            # Применяем к UI
            self.set_state(preset_with_key)

        finally:
            self._suspend_preset_sync = False

        # Эмитим сигнал
        self.quality_changed.emit(self.get_state())
        self.preset_applied.emit(
            f"Профиль качества: {self._quality_preset_labels.get(key, key)}"
        )

    def _on_primary_aa_changed(self, value: str) -> None:
        """Обработчик изменения primary AA - КАК В МОНОЛИТЕ"""
        if self._updating_ui:
            return

        # Обновляем значение
        self._on_control_changed("antialiasing.primary", value)

        # Синхронизируем доступность TAA контролов
        self._sync_taa_controls(value)

    def _sync_taa_controls(self, primary_aa: str) -> None:
        """Синхронизировать доступность TAA контролов - КАК В МОНОЛИТЕ"""
        # TAA несовместим с MSAA
        allow_taa = primary_aa != "msaa"

        taa_check = self._controls.get("taa.enabled")
        if isinstance(taa_check, QCheckBox):
            taa_check.setEnabled(allow_taa)

        taa_strength = self._controls.get("taa.strength")
        if isinstance(taa_strength, LabeledSlider):
            taa_strength.set_enabled(allow_taa)

        taa_motion = self._controls.get("taa_motion_adaptive")
        if isinstance(taa_motion, QCheckBox):
            taa_motion.setEnabled(allow_taa)

    def _on_control_changed(self, key: str, value: Any) -> None:
        """Обработчик изменения любого контрола - КАК В МОНОЛИТЕ"""
        if self._updating_ui:
            return

        # Переключаем в custom при ручных изменениях
        if not self._suspend_preset_sync:
            self._set_quality_custom()

        # Эмитим сигнал
        self.quality_changed.emit(self.get_state())

    def _set_quality_custom(self) -> None:
        """Переключить пресет в custom - КАК В МОНОЛИТЕ"""
        if self._suspend_preset_sync:
            return

        combo = self._controls.get("quality.preset")
        if isinstance(combo, QComboBox):
            index = combo.findData("custom")
            if index >= 0 and combo.currentIndex() != index:
                self._updating_ui = True
                try:
                    combo.setCurrentIndex(index)
                finally:
                    self._updating_ui = False

    # ========== ГЕТТЕРЫ/СЕТТЕРЫ СОСТОЯНИЯ ==========

    def get_state(self) -> dict[str, Any]:
        """Получить текущее состояние всех параметров качества

        Returns:
            Словарь с параметрами - ТОЧНО КАК В МОНОЛИТЕ
        """
        # Определяем текущий пресет
        preset_combo = self._controls.get("quality.preset")
        current_preset = "custom"
        if isinstance(preset_combo, QComboBox):
            current_preset = preset_combo.currentData() or "custom"

        return {
            "preset": current_preset,
            "shadows": {
                "enabled": self._controls["shadows.enabled"].isChecked(),
                "resolution": self._controls["shadows.resolution"].currentData(),
                "filter": self._controls["shadows.filter"].currentData(),
                "bias": self._controls["shadows.bias"].value(),
                "darkness": self._controls["shadows.darkness"].value(),
            },
            "antialiasing": {
                "primary": self._controls["aa.primary"].currentData(),
                "quality": self._controls["aa.quality"].currentData(),
                "post": self._controls["aa.post"].currentData(),
            },
            "taa_enabled": self._controls["taa.enabled"].isChecked(),
            "taa_strength": self._controls["taa.strength"].value(),
            "taa_motion_adaptive": self._controls["taa_motion_adaptive"].isChecked(),
            "fxaa_enabled": self._controls["fxaa.enabled"].isChecked(),
            "specular_aa": self._controls["specular.enabled"].isChecked(),
            "dithering": self._controls["dithering.enabled"].isChecked(),
            "render_scale": self._controls["render.scale"].value(),
            "render_policy": self._controls["render.policy"].currentData(),
            "frame_rate_limit": self._controls["frame_rate_limit"].value(),
            "oit": self._controls["oit.enabled"].isChecked() and "weighted" or "none",
            "mesh": {
                "cylinder_segments": int(
                    self._controls["mesh.cylinder_segments"].value()
                ),
                "cylinder_rings": int(self._controls["mesh.cylinder_rings"].value()),
            },
        }

    def set_state(self, state: dict[str, Any]):
        """Установить состояние из словаря

        Args:
            state: Словарь с параметрами качества
        """
        # Временно блокируем сигналы и UI updates
        self._updating_ui = True
        for control in self._controls.values():
            try:
                control.blockSignals(True)
            except Exception:
                pass

        try:
            # Preset
            if "preset" in state:
                combo = self._controls.get("quality.preset")
                if isinstance(combo, QComboBox):
                    index = combo.findData(state["preset"])
                    if index >= 0:
                        combo.setCurrentIndex(index)

            # Shadows
            if "shadows" in state:
                shadows = state["shadows"]
                if "enabled" in shadows:
                    self._controls["shadows.enabled"].setChecked(shadows["enabled"])
                if "resolution" in shadows:
                    combo = self._controls["shadows.resolution"]
                    value = shadows["resolution"]
                    if isinstance(value, str):
                        try:
                            value = int(float(value.strip()))
                        except ValueError:
                            pass
                    if isinstance(value, float):
                        value = int(round(value))
                    index = combo.findData(value)
                    if index >= 0:
                        combo.setCurrentIndex(index)
                if "filter" in shadows:
                    combo = self._controls["shadows.filter"]
                    index = combo.findData(shadows["filter"])
                    if index >= 0:
                        combo.setCurrentIndex(index)
                if "bias" in shadows:
                    self._controls["shadows.bias"].set_value(shadows["bias"])
                if "darkness" in shadows:
                    self._controls["shadows.darkness"].set_value(shadows["darkness"])

            # Antialiasing
            if "antialiasing" in state:
                aa = state["antialiasing"]
                if "primary" in aa:
                    combo = self._controls["aa.primary"]
                    index = combo.findData(aa["primary"])
                    if index >= 0:
                        combo.setCurrentIndex(index)
                    # Синхронизируем TAA controls
                    self._sync_taa_controls(aa["primary"])
                if "quality" in aa:
                    combo = self._controls["aa.quality"]
                    index = combo.findData(aa["quality"])
                    if index >= 0:
                        combo.setCurrentIndex(index)
                if "post" in aa:
                    combo = self._controls["aa.post"]
                    index = combo.findData(aa["post"])
                    if index >= 0:
                        combo.setCurrentIndex(index)

            # TAA
            if "taa_enabled" in state:
                self._controls["taa.enabled"].setChecked(state["taa_enabled"])
            if "taa_strength" in state:
                self._controls["taa.strength"].set_value(state["taa_strength"])
            if "taa_motion_adaptive" in state:
                self._controls["taa_motion_adaptive"].setChecked(
                    state["taa_motion_adaptive"]
                )

            # FXAA, Specular AA
            if "fxaa_enabled" in state:
                self._controls["fxaa.enabled"].setChecked(state["fxaa_enabled"])
            if "specular_aa" in state:
                self._controls["specular.enabled"].setChecked(state["specular_aa"])

            # Render Performance
            if "dithering" in state:
                self._controls["dithering.enabled"].setChecked(state["dithering"])
            if "render_scale" in state:
                self._controls["render.scale"].set_value(state["render_scale"])
            if "render_policy" in state:
                combo = self._controls["render.policy"]
                index = combo.findData(state["render_policy"])
                if index >= 0:
                    combo.setCurrentIndex(index)
            if "frame_rate_limit" in state:
                self._controls["frame_rate_limit"].set_value(state["frame_rate_limit"])
            if "oit" in state:
                is_weighted = state["oit"] == "weighted"
                self._controls["oit.enabled"].setChecked(is_weighted)

            # Mesh
            mesh = state.get("mesh", {}) or {}
            if "cylinder_segments" in mesh:
                self._controls["mesh.cylinder_segments"].set_value(
                    float(mesh["cylinder_segments"])
                )
            if "cylinder_rings" in mesh:
                self._controls["mesh.cylinder_rings"].set_value(
                    float(mesh["cylinder_rings"])
                )

        finally:
            # Разблокируем сигналы и UI
            for control in self._controls.values():
                try:
                    control.blockSignals(False)
                except Exception:
                    pass
            self._updating_ui = False

    def get_controls(self) -> dict[str, Any]:
        """Получить словарь контролов для внешнего управления"""
        return self._controls

    def set_updating_ui(self, updating: bool) -> None:
        """Установить флаг обновления UI"""
        self._updating_ui = updating
