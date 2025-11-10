"""Геометрия узлов пневмосистемы.

Все расчёты выполняются в СИ (метры, радианы, паскали).
"""

import math
from dataclasses import dataclass, field
from src.common.units import MIN_VOLUME_FRACTION
from src.common.errors import GeometryError
from .types import ValidationResult


@dataclass
class FrameGeom:
    """Геометрия рамы с плоскостью симметрии YZ при ``X = 0``.

    Система координат:
    * задняя нижняя точка рамы: ``(0, 0, 0)``;
    * передняя нижняя точка: ``(0, 0, L_wb)``;
    * плоскость симметрии: ``YZ`` (``X = 0``).
    """

    L_wb: float  # Длина колёсной базы (м)

    def __post_init__(self) -> None:
        if self.L_wb <= 0:
            raise GeometryError(
                f"Длина базы L_wb должна быть положительной, получено {self.L_wb}"
            )

    def validate_invariants(self) -> ValidationResult:
        """Проверить инварианты рамы."""
        errors: list[str] = []
        warnings: list[str] = []

        if self.L_wb <= 0:
            errors.append(
                f"Длина базы L_wb должна быть положительной, получено {self.L_wb}"
            )
        elif self.L_wb < 2.0:
            warnings.append(
                f"Длина базы L_wb={self.L_wb} м выглядит слишком маленькой для шасси"
            )
        elif self.L_wb > 10.0:
            warnings.append(
                f"Длина базы L_wb={self.L_wb} м выглядит чрезмерно большой для шасси"
            )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )


@dataclass
class LeverGeom:
    """Геометрия рычага с проверкой инвариантов."""

    L_lever: float  # Длина рычага (м)
    rod_joint_frac: float  # Доля длины до шарнира штока (0.1…0.9)
    d_frame_to_lever_hinge: float  # Расстояние от рамы до оси рычага (м)

    _cylinder_geom: "CylinderGeom | None" = field(default=None, init=False, repr=False)
    _neutral_length: float | None = field(default=None, init=False, repr=False)
    _axis_unit: tuple[float, float, float] | None = field(
        default=None, init=False, repr=False
    )
    _displacement_blend: float | None = field(default=None, init=False, repr=False)
    _min_effective_angle: float | None = field(default=None, init=False, repr=False)
    _min_angle_active: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Проверить параметры рычага."""
        if self.L_lever <= 0:
            raise GeometryError(
                f"Длина рычага L_lever должна быть положительной, получено {self.L_lever}"
            )

        if not (0.1 <= self.rod_joint_frac <= 0.9):
            raise GeometryError(
                "Доля расположения шарнира должна лежать в диапазоне 0.1…0.9"
                f", получено {self.rod_joint_frac}"
            )

        if self.d_frame_to_lever_hinge <= 0:
            raise GeometryError(
                "Расстояние от рамы до оси рычага должно быть положительным"
                f", получено {self.d_frame_to_lever_hinge}"
            )

    def lever_tip_pos(self, angle: float) -> tuple[float, float]:
        """Вычислить положение конца рычага в плоскости оси."""
        x = self.L_lever * math.cos(angle)
        y = self.L_lever * math.sin(angle)
        return (x, y)

    def rod_joint_pos(self, angle: float) -> tuple[float, float]:
        """Вычислить положение шарнира штока на рычаге."""
        dist_from_hinge = self.rod_joint_frac * self.L_lever
        x = dist_from_hinge * math.cos(angle)
        y = dist_from_hinge * math.sin(angle)
        return (x, y)

    def attach_cylinder_geometry(self, geometry: "CylinderGeom") -> None:
        """Привязать геометрию цилиндра и подготовить вспомогательные величины."""

        self._cylinder_geom = geometry

        lever_arm = self.rod_joint_frac * self.L_lever
        tail_point = (0.0, geometry.Y_tail, geometry.Z_axle)
        neutral_joint = (0.0, lever_arm, geometry.Z_axle)

        axis_vec = (
            neutral_joint[0] - tail_point[0],
            neutral_joint[1] - tail_point[1],
            neutral_joint[2] - tail_point[2],
        )
        axis_length = math.sqrt(
            axis_vec[0] * axis_vec[0]
            + axis_vec[1] * axis_vec[1]
            + axis_vec[2] * axis_vec[2]
        )

        if axis_length < 1e-9:
            # Вырожденная конфигурация: направляем ось вдоль отрицательной Y.
            self._axis_unit = (0.0, -1.0, 0.0)
            self._neutral_length = 0.0
        else:
            self._axis_unit = (
                axis_vec[0] / axis_length,
                axis_vec[1] / axis_length,
                axis_vec[2] / axis_length,
            )
            self._neutral_length = axis_length

        # Коэффициент смешивания между простой моделью и проекцией на ось цилиндра.
        frame_offset = max(self.d_frame_to_lever_hinge, 1e-6)
        blend = lever_arm / (geometry.Y_tail + frame_offset)
        self._displacement_blend = max(0.0, min(1.0, blend))

        # Поведение при малых углах: из-за несовпадения осей возникает «слэк-зона».
        # Моделируем её минимальным эффективным углом, ограниченным мягким пределом
        # около трёх градусов.
        slack_angle = math.atan2(
            abs(geometry.Y_tail - lever_arm), geometry.Z_axle + frame_offset
        )
        self._min_effective_angle = min(slack_angle * 0.4, math.radians(3.0))

    def angle_to_displacement(self, angle: float) -> float:
        """Преобразовать угол рычага в осевое смещение штока."""

        if self._cylinder_geom and self._axis_unit and self._neutral_length is not None:
            geometry = self._cylinder_geom
            lever_arm = self.rod_joint_frac * self.L_lever

            abs_angle = abs(angle)
            if (
                self._min_angle_active
                and self._min_effective_angle
                and abs_angle > 0.0
                and abs_angle < self._min_effective_angle
            ):
                angle_eff = math.copysign(self._min_effective_angle, angle)
            else:
                angle_eff = angle

            simple = lever_arm * math.sin(angle_eff)

            rod_x, rod_y = self.rod_joint_pos(angle_eff)
            tail_point = (0.0, geometry.Y_tail, geometry.Z_axle)
            joint_point = (0.0, rod_x, geometry.Z_axle + rod_y)

            vec = (
                joint_point[0] - tail_point[0],
                joint_point[1] - tail_point[1],
                joint_point[2] - tail_point[2],
            )
            projected = sum(
                component * basis for component, basis in zip(vec, self._axis_unit)
            )
            displacement_axis = projected - self._neutral_length
            signed_axis = math.copysign(abs(displacement_axis), angle_eff)

            blend = (
                self._displacement_blend
                if self._displacement_blend is not None
                else 1.0
            )
            return blend * simple + (1.0 - blend) * signed_axis

        lever_radius = self.rod_joint_frac * self.L_lever
        return lever_radius * math.sin(angle)

    def displacement_to_angle(
        self,
        displacement: float,
        *,
        initial_guess: float | None = None,
        max_iterations: int = 16,
        tolerance: float = 1e-9,
    ) -> float:
        """Найти угол рычага, обеспечивающий указанное смещение."""

        # Начальное приближение: в чистой модели рычага смещение равно r*sin(θ).
        lever_radius = max(self.rod_joint_frac * self.L_lever, 1e-9)
        if initial_guess is None:
            ratio = displacement / lever_radius
            # Ограничиваем аргумент arcsin допустимыми значениями, сохраняя знак.
            clamped = max(-1.0, min(1.0, ratio))
            try:
                guess = math.asin(clamped)
            except ValueError:  # pragma: no cover - защита от выхода из области
                guess = math.copysign(math.pi / 2.0, displacement)
            if abs(ratio) > 1.0:
                # Если сложная кинематика выходит за пределы простой модели,
                # итерации уточняют насыщённое начальное значение.
                guess = math.copysign(math.pi / 2.0, displacement)
        else:
            guess = float(initial_guess)

        # Ограничиваем итерации механическими пределами рычага.
        lower_bound = -math.pi / 2.0
        upper_bound = math.pi / 2.0
        angle = max(lower_bound, min(upper_bound, guess))

        for _ in range(max(1, max_iterations)):
            delta = self.angle_to_displacement(angle) - displacement
            if abs(delta) <= tolerance:
                break

            derivative = self.mechanical_advantage(angle)
            if abs(derivative) <= 1e-9:
                # Якобиан вырожден: возвращаем текущее приближение.
                break

            angle -= delta / derivative
            angle = max(lower_bound, min(upper_bound, angle))

        return angle

    def mechanical_advantage(self, angle: float) -> float:
        """Вернуть мгновенную производную смещения по углу."""

        if self._cylinder_geom and self._axis_unit and self._neutral_length is not None:
            epsilon = 1e-5
            disp_plus = self.angle_to_displacement(angle + epsilon)
            disp_minus = self.angle_to_displacement(angle - epsilon)
            return (disp_plus - disp_minus) / (2.0 * epsilon)

        lever_radius = self.rod_joint_frac * self.L_lever
        return lever_radius * math.cos(angle)

    def validate_invariants(self) -> ValidationResult:
        """Проверить инварианты геометрии рычага."""
        errors: list[str] = []
        warnings: list[str] = []

        try:
            self._validate_parameters()
        except GeometryError as e:
            errors.append(str(e))

        # Контроль разумных размеров
        if self.L_lever < 0.1:
            warnings.append(
                f"Длина рычага L_lever={self.L_lever} м выглядит подозрительно малой"
            )
        elif self.L_lever > 2.0:
            warnings.append(
                f"Длина рычага L_lever={self.L_lever} м выглядит чрезмерно большой"
            )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )


@dataclass
class CylinderGeom:
    """Геометрия цилиндра с полной проверкой ограничений."""

    # Геометрические параметры цилиндра
    D_in_front: float  # Внутренний диаметр передней секции (м)
    D_in_rear: float  # Внутренний диаметр задней секции (м)
    D_out_front: float  # Наружный диаметр передней секции (м)
    D_out_rear: float  # Наружный диаметр задней секции (м)
    L_inner: float  # Полная длина внутренней полости (м)
    t_piston: float  # Толщина поршня (м)

    # Параметры штока
    D_rod: float  # Диаметр штока (м)
    link_rod_diameters_front_rear: bool  # Совпадает ли диаметр штока в обеих секциях

    # Мёртвые зоны
    L_dead_head: float  # Длина мёртвой зоны со стороны крышки (м)
    L_dead_rod: float  # Длина мёртвой зоны со стороны штока (м)

    # Параметры безопасности
    residual_frac_min: float = (
        MIN_VOLUME_FRACTION  # Минимальная доля остаточного объёма
    )

    # Положение цилиндра в пространстве
    Y_tail: float = 0.0  # Координата хвостовой опоры по оси Y (м)
    Z_axle: float = 0.0  # Высота оси цилиндра по Z (м)

    def __post_init__(self) -> None:
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Проверить параметры цилиндра."""
        # Положительные размеры
        params_positive = [
            (self.D_in_front, "D_in_front"),
            (self.D_in_rear, "D_in_rear"),
            (self.D_out_front, "D_out_front"),
            (self.D_out_rear, "D_out_rear"),
            (self.L_inner, "L_inner"),
            (self.t_piston, "t_piston"),
            (self.D_rod, "D_rod"),
            (self.L_dead_head, "L_dead_head"),
            (self.L_dead_rod, "L_dead_rod"),
        ]

        for value, name in params_positive:
            if value <= 0:
                raise GeometryError(
                    f"Параметр {name} должен быть положительным, получено {value}"
                )

        # Ограничения по диаметрам
        if self.D_in_front >= self.D_out_front:
            raise GeometryError(
                "Внутренний диаметр передней секции должен быть меньше наружного"
            )
        if self.D_in_rear >= self.D_out_rear:
            raise GeometryError(
                "Внутренний диаметр задней секции должен быть меньше наружного"
            )

        # Ограничение диаметра штока
        max_rod_diameter = min(self.D_in_front, self.D_in_rear) * 0.8  # 20% зазор
        if self.D_rod >= max_rod_diameter:
            raise GeometryError(
                f"Диаметр штока {self.D_rod} превышает допустимое значение"
            )

        # Допустимая доля остаточного объёма
        if not (0.001 <= self.residual_frac_min <= 0.1):
            raise GeometryError(
                "Минимальная доля остаточного объёма должна лежать в диапазоне"
                f" 0.001…0.1, получено {self.residual_frac_min}"
            )

        # Проверка доступного хода
        L_travel_max = self.L_inner - (
            self.L_dead_head + self.L_dead_rod + self.t_piston
        )
        if L_travel_max <= 0:
            raise GeometryError(
                "Полезный ход отсутствует: L_inner="
                f"{self.L_inner}, сумма мёртвых зон и поршня="
                f"{self.L_dead_head + self.L_dead_rod + self.t_piston}"
            )

    @property
    def L_travel_max(self) -> float:
        """Максимальный ход поршня."""
        return self.L_inner - (self.L_dead_head + self.L_dead_rod + self.t_piston)

    def area_head(self, is_front: bool) -> float:
        """Вычислить площадь головной камеры."""
        diameter = self.D_in_front if is_front else self.D_in_rear
        return math.pi * (diameter / 2.0) ** 2

    def area_rod(self, is_front: bool) -> float:
        """Вычислить эффективную площадь штоковой камеры."""
        area_head = self.area_head(is_front)
        area_rod_steel = math.pi * (self.D_rod / 2.0) ** 2
        return area_head - area_rod_steel

    def min_volume_head(self, is_front: bool) -> float:
        """Минимально допустимый объём головной камеры."""
        return self.residual_frac_min * (self.area_head(is_front) * self.L_inner)

    def min_volume_rod(self, is_front: bool) -> float:
        """Минимально допустимый объём штоковой камеры."""
        return self.residual_frac_min * (self.area_rod(is_front) * self.L_inner)

    def project_to_cyl_axis(
        self,
        tail_point: tuple[float, float, float],
        joint_point: tuple[float, float, float],
    ) -> float:
        """Проецировать смещение на ось цилиндра и вернуть длину отрезка."""
        dx = joint_point[0] - tail_point[0]
        dy = joint_point[1] - tail_point[1]
        dz = joint_point[2] - tail_point[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def validate_invariants(self) -> ValidationResult:
        """Проверить инварианты геометрии цилиндра."""
        errors: list[str] = []
        warnings: list[str] = []

        try:
            self._validate_parameters()
        except GeometryError as e:
            errors.append(str(e))
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Контроль объёмов при крайних положениях поршня
        half_travel = self.L_travel_max / 2.0

        for is_front in [True, False]:
            label = "передней" if is_front else "задней"

            # Объёмы при максимальном растяжении (x = +half_travel)
            vol_head_max = self.area_head(is_front) * (
                self.L_inner / 2.0 - half_travel - self.L_dead_head
            )
            vol_rod_max = self.area_rod(is_front) * (
                self.L_inner / 2.0 + half_travel - self.L_dead_rod
            )

            # Объёмы при максимальном сжатии (x = -half_travel)
            vol_head_min = self.area_head(is_front) * (
                self.L_inner / 2.0 + half_travel - self.L_dead_head
            )
            vol_rod_min = self.area_rod(is_front) * (
                self.L_inner / 2.0 - half_travel - self.L_dead_rod
            )

            min_vol_head = self.min_volume_head(is_front)
            min_vol_rod = self.min_volume_rod(is_front)

            if vol_head_max < min_vol_head:
                errors.append(
                    f"Объём {label} головной камеры при растяжении меньше допуска:"
                    f" {vol_head_max:.6f} < {min_vol_head:.6f}"
                )
            if vol_head_min < min_vol_head:
                errors.append(
                    f"Объём {label} головной камеры при сжатии меньше допуска:"
                    f" {vol_head_min:.6f} < {min_vol_head:.6f}"
                )
            if vol_rod_max < min_vol_rod:
                errors.append(
                    f"Объём {label} штоковой камеры при растяжении меньше допуска:"
                    f" {vol_rod_max:.6f} < {min_vol_rod:.6f}"
                )
            if vol_rod_min < min_vol_rod:
                errors.append(
                    f"Объём {label} штоковой камеры при сжатии меньше допуска:"
                    f" {vol_rod_min:.6f} < {min_vol_rod:.6f}"
                )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
