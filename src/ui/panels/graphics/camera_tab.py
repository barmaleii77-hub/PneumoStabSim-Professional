# -*- coding: utf-8 -*-
"""
Camera Tab - вкладка настроек камеры
Расширено: ручной режим, позиция/углы камеры, орбита, цель орбиты, мировые трансформации модели
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QCheckBox,
    QGridLayout,
    QPushButton,
    QLabel,
    QHBoxLayout,
)
from PySide6.QtCore import Signal
from typing import Dict, Any

from .widgets import LabeledSlider


class CameraTab(QWidget):
    """Вкладка настроек камеры: FOV, clipping, auto-rotate, auto-fit, ручной режим, орбита, мир

    Signals:
        camera_changed: Dict[str, Any] - параметры камеры изменились
    """

    camera_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._controls: Dict[str, Any] = {}
        self._updating_ui = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_camera_group())
        layout.addWidget(self._build_orbit_group())
        layout.addWidget(self._build_world_group())

        layout.addStretch(1)

    def _build_camera_group(self) -> QGroupBox:
        group = QGroupBox("Камера", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        r = 0

        # FOV / near / far / speed
        fov = LabeledSlider("Поле зрения", 10.0, 120.0, 0.5, decimals=1, unit="°")
        fov.valueChanged.connect(lambda v: self._emit())
        self._controls["fov"] = fov
        grid.addWidget(fov, r, 0, 1, 2)
        r += 1
        near_clip = LabeledSlider(
            "Ближняя плоскость", 0.1, 1000.0, 0.1, decimals=1, unit="мм"
        )
        near_clip.valueChanged.connect(lambda v: self._emit())
        self._controls["near"] = near_clip
        grid.addWidget(near_clip, r, 0, 1, 2)
        r += 1
        far_clip = LabeledSlider(
            "Дальняя плоскость", 100.0, 1000000.0, 100.0, decimals=0, unit="мм"
        )
        far_clip.valueChanged.connect(lambda v: self._emit())
        self._controls["far"] = far_clip
        grid.addWidget(far_clip, r, 0, 1, 2)
        r += 1
        speed = LabeledSlider("Скорость камеры", 0.01, 10.0, 0.01, decimals=2)
        speed.valueChanged.connect(lambda v: self._emit())
        self._controls["speed"] = speed
        grid.addWidget(speed, r, 0, 1, 2)
        r += 1

        # Автоповорот / автофит
        auto_rotate = QCheckBox("Автоповорот", self)
        auto_rotate.clicked.connect(lambda checked: self._emit())
        self._controls["auto_rotate"] = auto_rotate
        grid.addWidget(auto_rotate, r, 0, 1, 2)
        r += 1
        rotate_speed = LabeledSlider(
            "Скорость автоповорота", 0.0, 30.0, 0.1, decimals=1
        )
        rotate_speed.valueChanged.connect(lambda v: self._emit())
        self._controls["auto_rotate_speed"] = rotate_speed
        grid.addWidget(rotate_speed, r, 0, 1, 2)
        r += 1
        auto_fit = QCheckBox("Автоподгон камеры при изменении геометрии", self)
        auto_fit.clicked.connect(lambda checked: self._emit())
        self._controls["auto_fit"] = auto_fit
        grid.addWidget(auto_fit, r, 0, 1, 2)
        r += 1
        center_btn = QPushButton("Центрировать сейчас", self)
        center_btn.clicked.connect(lambda: self._emit(center=True))
        grid.addWidget(center_btn, r, 0, 1, 2)
        r += 1

        # Ручной режим камеры
        manual = QCheckBox("Ручной режим камеры (позиция/углы ниже)", self)
        manual.clicked.connect(lambda checked: self._emit())
        self._controls["manual_camera"] = manual
        grid.addWidget(manual, r, 0, 1, 2)
        r += 1
        camx = LabeledSlider(
            "Камера X", -100000.0, 100000.0, 10.0, decimals=0, unit="мм"
        )
        camx.valueChanged.connect(lambda v: self._emit())
        self._controls["camera_pos_x"] = camx
        grid.addWidget(camx, r, 0, 1, 2)
        r += 1
        camy = LabeledSlider(
            "Камера Y", -100000.0, 100000.0, 10.0, decimals=0, unit="мм"
        )
        camy.valueChanged.connect(lambda v: self._emit())
        self._controls["camera_pos_y"] = camy
        grid.addWidget(camy, r, 0, 1, 2)
        r += 1
        camz = LabeledSlider(
            "Камера Z", -100000.0, 100000.0, 10.0, decimals=0, unit="мм"
        )
        camz.valueChanged.connect(lambda v: self._emit())
        self._controls["camera_pos_z"] = camz
        grid.addWidget(camz, r, 0, 1, 2)
        r += 1
        rotx = LabeledSlider("Поворот X", -180.0, 180.0, 0.5, decimals=1, unit="°")
        rotx.valueChanged.connect(lambda v: self._emit())
        self._controls["camera_rot_x"] = rotx
        grid.addWidget(rotx, r, 0, 1, 2)
        r += 1
        roty = LabeledSlider("Поворот Y", -180.0, 180.0, 0.5, decimals=1, unit="°")
        roty.valueChanged.connect(lambda v: self._emit())
        self._controls["camera_rot_y"] = roty
        grid.addWidget(roty, r, 0, 1, 2)
        r += 1
        rotz = LabeledSlider("Поворот Z", -180.0, 180.0, 0.5, decimals=1, unit="°")
        rotz.valueChanged.connect(lambda v: self._emit())
        self._controls["camera_rot_z"] = rotz
        grid.addWidget(rotz, r, 0, 1, 2)
        r += 1

        return group

    def _build_orbit_group(self) -> QGroupBox:
        group = QGroupBox("Орбита камеры", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        r = 0

        tx = LabeledSlider("Цель X", -100000.0, 100000.0, 10.0, decimals=0, unit="мм")
        tx.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_target_x"] = tx
        grid.addWidget(tx, r, 0, 1, 2)
        r += 1
        ty = LabeledSlider("Цель Y", -100000.0, 100000.0, 10.0, decimals=0, unit="мм")
        ty.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_target_y"] = ty
        grid.addWidget(ty, r, 0, 1, 2)
        r += 1
        tz = LabeledSlider("Цель Z", -100000.0, 100000.0, 10.0, decimals=0, unit="мм")
        tz.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_target_z"] = tz
        grid.addWidget(tz, r, 0, 1, 2)
        r += 1
        yaw = LabeledSlider("Yaw", -99999.0, 99999.0, 1.0, decimals=0, unit="°")
        yaw.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_yaw"] = yaw
        grid.addWidget(yaw, r, 0, 1, 2)
        r += 1
        pitch = LabeledSlider("Pitch", -99999.0, 99999.0, 1.0, decimals=0, unit="°")
        pitch.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_pitch"] = pitch
        grid.addWidget(pitch, r, 0, 1, 2)
        r += 1
        dist = LabeledSlider("Дистанция", 1.0, 100000.0, 10.0, decimals=0, unit="мм")
        dist.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_distance"] = dist
        grid.addWidget(dist, r, 0, 1, 2)
        r += 1

        # Плавность и инерция
        inertia_enabled = QCheckBox("Инерция (мягкий старт/стоп)", self)
        inertia_enabled.clicked.connect(lambda checked: self._emit())
        self._controls["orbit_inertia_enabled"] = inertia_enabled
        grid.addWidget(inertia_enabled, r, 0, 1, 2)
        r += 1
        inertia_factor = LabeledSlider("Сила инерции", 0.0, 1.0, 0.01, decimals=2)
        inertia_factor.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_inertia"] = inertia_factor
        grid.addWidget(inertia_factor, r, 0, 1, 2)
        r += 1
        rotate_smooth = LabeledSlider(
            "Сглаживание вращения", 0.0, 1.0, 0.01, decimals=2
        )
        rotate_smooth.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_rotate_smoothing"] = rotate_smooth
        grid.addWidget(rotate_smooth, r, 0, 1, 2)
        r += 1
        pan_smooth = LabeledSlider(
            "Сглаживание панорамирования", 0.0, 1.0, 0.01, decimals=2
        )
        pan_smooth.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_pan_smoothing"] = pan_smooth
        grid.addWidget(pan_smooth, r, 0, 1, 2)
        r += 1
        zoom_smooth = LabeledSlider("Сглаживание зума", 0.0, 1.0, 0.01, decimals=2)
        zoom_smooth.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_zoom_smoothing"] = zoom_smooth
        grid.addWidget(zoom_smooth, r, 0, 1, 2)
        r += 1
        friction = LabeledSlider("Трение (затухание)", 0.0, 1.0, 0.01, decimals=2)
        friction.valueChanged.connect(lambda v: self._emit())
        self._controls["orbit_friction"] = friction
        grid.addWidget(friction, r, 0, 1, 2)
        r += 1

        # Пресеты
        presets_row = QHBoxLayout()
        lbl = QLabel("Пресеты камеры:", self)
        btn_rigid = QPushButton("Жёстко", self)
        btn_smooth = QPushButton("Сглажено", self)
        btn_cinematic = QPushButton("Кино", self)
        btn_rigid.clicked.connect(lambda: self._apply_preset("rigid"))
        btn_smooth.clicked.connect(lambda: self._apply_preset("smooth"))
        btn_cinematic.clicked.connect(lambda: self._apply_preset("cinematic"))
        presets_row.addWidget(lbl)
        presets_row.addStretch(1)
        presets_row.addWidget(btn_rigid)
        presets_row.addWidget(btn_smooth)
        presets_row.addWidget(btn_cinematic)
        grid.addLayout(presets_row, r, 0, 1, 2)
        r += 1

        return group

    def _build_world_group(self) -> QGroupBox:
        group = QGroupBox("Мировые трансформации модели", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        r = 0

        wx = LabeledSlider(
            "Позиция X", -100000.0, 100000.0, 10.0, decimals=0, unit="мм"
        )
        wx.valueChanged.connect(lambda v: self._emit())
        self._controls["world_pos_x"] = wx
        grid.addWidget(wx, r, 0, 1, 2)
        r += 1
        wy = LabeledSlider(
            "Позиция Y", -100000.0, 100000.0, 10.0, decimals=0, unit="мм"
        )
        wy.valueChanged.connect(lambda v: self._emit())
        self._controls["world_pos_y"] = wy
        grid.addWidget(wy, r, 0, 1, 2)
        r += 1
        wz = LabeledSlider(
            "Позиция Z", -100000.0, 100000.0, 10.0, decimals=0, unit="мм"
        )
        wz.valueChanged.connect(lambda v: self._emit())
        self._controls["world_pos_z"] = wz
        grid.addWidget(wz, r, 0, 1, 2)
        r += 1
        rx = LabeledSlider("Поворот X", -180.0, 180.0, 0.5, decimals=1, unit="°")
        rx.valueChanged.connect(lambda v: self._emit())
        self._controls["world_rot_x"] = rx
        grid.addWidget(rx, r, 0, 1, 2)
        r += 1
        ry = LabeledSlider("Поворот Y", -180.0, 180.0, 0.5, decimals=1, unit="°")
        ry.valueChanged.connect(lambda v: self._emit())
        self._controls["world_rot_y"] = ry
        grid.addWidget(ry, r, 0, 1, 2)
        r += 1
        rz = LabeledSlider("Поворот Z", -180.0, 180.0, 0.5, decimals=1, unit="°")
        rz.valueChanged.connect(lambda v: self._emit())
        self._controls["world_rot_z"] = rz
        grid.addWidget(rz, r, 0, 1, 2)
        r += 1
        sc = LabeledSlider("Масштаб", 0.001, 100.0, 0.001, decimals=3, unit="x")
        sc.valueChanged.connect(lambda v: self._emit())
        self._controls["world_scale"] = sc
        grid.addWidget(sc, r, 0, 1, 2)
        r += 1

        return group

    def _apply_preset(self, name: str) -> None:
        """Применить пресет параметров орбиты камеры."""
        presets: dict[str, dict[str, float | bool]] = {
            "rigid": {
                "orbit_inertia_enabled": False,
                "orbit_inertia": 0.0,
                "orbit_rotate_smoothing": 0.08,
                "orbit_pan_smoothing": 0.08,
                "orbit_zoom_smoothing": 0.08,
                "orbit_friction": 0.0,
            },
            "smooth": {
                "orbit_inertia_enabled": False,
                "orbit_inertia": 0.0,
                "orbit_rotate_smoothing": 0.18,
                "orbit_pan_smoothing": 0.18,
                "orbit_zoom_smoothing": 0.18,
                "orbit_friction": 0.0,
            },
            "cinematic": {
                "orbit_inertia_enabled": True,
                "orbit_inertia": 0.30,
                "orbit_rotate_smoothing": 0.22,
                "orbit_pan_smoothing": 0.25,
                "orbit_zoom_smoothing": 0.20,
                "orbit_friction": 0.08,
            },
        }
        preset = presets.get(name)
        if not preset:
            return
        # Обновляем UI без каскада сигналов
        self._updating_ui = True
        try:
            for key, val in preset.items():
                ctrl = self._controls.get(key)
                if not ctrl:
                    continue
                try:
                    if isinstance(val, bool):
                        from PySide6.QtWidgets import QCheckBox as _QCB

                        if isinstance(ctrl, _QCB):
                            ctrl.setChecked(bool(val))
                    else:
                        if isinstance(ctrl, LabeledSlider):
                            ctrl.set_value(float(val))
                except Exception:
                    pass
        finally:
            self._updating_ui = False
        # Отправляем единый payload
        self._emit()

    def _emit(self, center: bool | None = None) -> None:
        if self._updating_ui:
            return
        payload = self.get_state()
        if center is True:
            payload["center_camera"] = True
        self.camera_changed.emit(payload)

    def get_state(self) -> Dict[str, Any]:
        return {
            "fov": self._controls["fov"].value(),
            "near": self._controls["near"].value(),
            "far": self._controls["far"].value(),
            "speed": self._controls["speed"].value(),
            "auto_rotate": self._controls["auto_rotate"].isChecked(),
            "auto_rotate_speed": self._controls["auto_rotate_speed"].value(),
            "auto_fit": self._controls["auto_fit"].isChecked(),
            "manual_camera": self._controls["manual_camera"].isChecked(),
            "camera_pos_x": self._controls["camera_pos_x"].value(),
            "camera_pos_y": self._controls["camera_pos_y"].value(),
            "camera_pos_z": self._controls["camera_pos_z"].value(),
            "camera_rot_x": self._controls["camera_rot_x"].value(),
            "camera_rot_y": self._controls["camera_rot_y"].value(),
            "camera_rot_z": self._controls["camera_rot_z"].value(),
            "orbit_target_x": self._controls["orbit_target_x"].value(),
            "orbit_target_y": self._controls["orbit_target_y"].value(),
            "orbit_target_z": self._controls["orbit_target_z"].value(),
            "orbit_yaw": self._controls["orbit_yaw"].value(),
            "orbit_pitch": self._controls["orbit_pitch"].value(),
            "orbit_distance": self._controls["orbit_distance"].value(),
            "orbit_inertia_enabled": self._controls[
                "orbit_inertia_enabled"
            ].isChecked(),
            "orbit_inertia": self._controls["orbit_inertia"].value(),
            "orbit_rotate_smoothing": self._controls["orbit_rotate_smoothing"].value(),
            "orbit_pan_smoothing": self._controls["orbit_pan_smoothing"].value(),
            "orbit_zoom_smoothing": self._controls["orbit_zoom_smoothing"].value(),
            "orbit_friction": self._controls["orbit_friction"].value(),
            "world_pos_x": self._controls["world_pos_x"].value(),
            "world_pos_y": self._controls["world_pos_y"].value(),
            "world_pos_z": self._controls["world_pos_z"].value(),
            "world_rot_x": self._controls["world_rot_x"].value(),
            "world_rot_y": self._controls["world_rot_y"].value(),
            "world_rot_z": self._controls["world_rot_z"].value(),
            "world_scale": self._controls["world_scale"].value(),
        }

    def set_state(self, state: Dict[str, Any]):
        self._updating_ui = True
        for control in self._controls.values():
            try:
                control.blockSignals(True)
            except:
                pass
        try:
            for key, value in state.items():
                if key in self._controls:
                    ctrl = self._controls[key]
                    from PySide6.QtWidgets import QCheckBox as _QCB

                    if isinstance(ctrl, _QCB):
                        ctrl.setChecked(bool(value))
                    elif isinstance(ctrl, LabeledSlider):
                        try:
                            ctrl.set_value(float(value))
                        except Exception:
                            pass
        finally:
            for control in self._controls.values():
                try:
                    control.blockSignals(False)
                except:
                    pass
            self._updating_ui = False

    def get_controls(self) -> Dict[str, Any]:
        return self._controls

    def set_updating_ui(self, updating: bool) -> None:
        self._updating_ui = updating
