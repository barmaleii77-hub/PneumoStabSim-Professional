"""
Physics simulation loop with fixed timestep
Runs in dedicated QThread with QTimer for precise timing
"""

import time
import logging
from dataclasses import replace
from typing import Optional, Dict, Any
import numpy as np

from PySide6.QtCore import QObject, QTimer, Signal, Slot, Qt
from PySide6.QtCore import QThread

from .state import (
    StateSnapshot,
    StateBus,
    FrameState,
    WheelState,
    LineState,
    TankState,
    SystemAggregates,
)
from .sync import (
    LatestOnlyQueue,
    PerformanceMetrics,
    StateSnapshotBuffer,
    TimingAccumulator,
    ThreadSafeCounter,
)

# Измененные импорты на абсолютные пути
from src.physics.odes import RigidBody3DOF, create_initial_conditions
from src.physics.integrator import (
    step_dynamics,
    create_default_rigid_body,
)
from src.pneumo.enums import (
    Wheel,
    Line,
    ThermoMode,
    Port,
    ReceiverVolumeMode,
)
from src.pneumo.receiver import ReceiverState, ReceiverSpec
from src.pneumo.system import create_standard_diagonal_system
from src.pneumo.gas_state import (
    create_line_gas_state,
    create_tank_gas_state,
    apply_instant_volume_change,
)
from src.pneumo.network import GasNetwork
from src.pneumo.thermo import PolytropicParameters
from src.road.engine import RoadInput, create_road_input_from_preset
from src.road.scenarios import get_preset_by_name
from src.common.units import KELVIN_0C, PA_ATM, T_AMBIENT, to_gauge_pressure
from src.app.config_defaults import create_default_system_configuration

# Settings manager (используем абсолютный импорт, т.к. общий модуль)
from src.common.settings_manager import get_settings_manager


class PhysicsWorker(QObject):
    """Physics simulation worker running in dedicated thread

    Handles fixed-timestep physics simulation with road inputs,
    pneumatic system, and3-DOF frame dynamics.
    """

    # Signals emitted to UI thread
    state_ready = Signal(object)  # StateSnapshot
    error_occurred = Signal(str)  # Error message
    performance_update = Signal(object)  # PerformanceMetrics

    def __init__(self, parent=None):
        super().__init__(parent)

        # Logging and settings access
        self.logger = logging.getLogger(__name__)
        self.settings_manager = get_settings_manager()

        # Physics configuration (loaded from settings file)
        self.dt_physics: float = 0.0
        self.vsync_render_hz: float = 0.0
        self.max_steps_per_frame: int = 1
        self.max_frame_time: float = 0.05

        # Simulation state
        self.is_running = False
        self.is_configured = False
        self.simulation_time = 0.0
        self.step_counter = 0

        # Physics objects (will be initialized in configure)
        self.rigid_body: Optional[RigidBody3DOF] = None
        self.road_input: Optional[Any] = None  # Changed type hint
        self.pneumatic_system: Optional[Any] = None
        self.gas_network: Optional[Any] = None

        # Current physics state
        self.physics_state: np.ndarray = np.zeros(6)  # [Y, φz, θx, dY, dφz, dθx]
        self._prev_frame_velocities = np.zeros(3)
        self._latest_frame_accel = np.zeros(3)

        # Simulation modes (overridden by persisted settings)
        self.thermo_mode = ThermoMode.ISOTHERMAL
        self.master_isolation_open = False

        # Receiver parameters and limits (loaded from settings)
        self.receiver_volume: float = 0.0
        self.receiver_volume_mode: str = ""
        self._volume_limits: tuple[float, float] = (0.0, 0.0)

        # Cached state for snapshot creation
        self._latest_wheel_states: Dict[Wheel, WheelState] = {
            wheel: WheelState(wheel=wheel) for wheel in Wheel
        }
        self._latest_line_states: Dict[Line, LineState] = {
            line: LineState(line=line) for line in Line
        }
        self._latest_tank_state = TankState()
        self._prev_piston_positions: Dict[Wheel, float] = {
            wheel: 0.0 for wheel in Wheel
        }
        self._last_road_inputs: Dict[str, float] = {
            k: 0.0 for k in ("LF", "RF", "LR", "RR")
        }

        # Threading objects (created in target thread)
        self.physics_timer: Optional[QTimer] = None

        # Performance monitoring
        self.performance = PerformanceMetrics()
        self.timing_accumulator: Optional[TimingAccumulator] = None
        self.step_time_samples = []

        # Thread safety
        self.error_counter = ThreadSafeCounter()

        # Load persisted configuration
        self._load_initial_settings()
        self._apply_timing_configuration()

        self.logger.info(
            "PhysicsWorker settings: dt=%.6fs, vsync=%.1fHz, max_steps=%d, max_frame_time=%.3fs, "
            "receiver=%.3fm³ (%s mode)",
            self.dt_physics,
            self.vsync_render_hz,
            self.max_steps_per_frame,
            self.max_frame_time,
            self.receiver_volume,
            self.receiver_volume_mode,
        )

    def _load_initial_settings(self) -> None:
        """Load simulation-related settings from SettingsManager"""
        defaults = self.settings_manager.get_all_defaults()

        def _current(path: str) -> Any:
            return self.settings_manager.get(path, None)

        def _default(category: str, key: str) -> Any:
            block = defaults.get(category, {})
            if isinstance(block, dict):
                return block.get(key)
            return None

        def _require_number(category: str, key: str) -> float:
            value = _current(f"{category}.{key}")
            if isinstance(value, bool):
                value = None
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
            fallback = _default(category, key)
            if isinstance(fallback, bool):
                fallback = None
            if isinstance(fallback, (int, float)) and not isinstance(fallback, bool):
                return float(fallback)
            raise RuntimeError(f"Missing numeric setting: {category}.{key}")

        def _require_bool(category: str, key: str) -> bool:
            value = _current(f"{category}.{key}")
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return bool(value)
            fallback = _default(category, key)
            if isinstance(fallback, bool):
                return fallback
            if isinstance(fallback, (int, float)) and not isinstance(fallback, bool):
                return bool(fallback)
            raise RuntimeError(f"Missing boolean setting: {category}.{key}")

        def _require_str(category: str, key: str) -> str:
            value = _current(f"{category}.{key}")
            if isinstance(value, str) and value.strip():
                return value.strip()
            fallback = _default(category, key)
            if isinstance(fallback, str) and fallback.strip():
                return fallback.strip()
            raise RuntimeError(f"Missing text setting: {category}.{key}")

        # Keys lists imported from settings_requirements if available
        try:
            from src.common.settings_requirements import (
                NUMERIC_SIMULATION_KEYS,
                NUMERIC_PNEUMATIC_KEYS,
                RECEIVER_VOLUME_LIMIT_KEYS,
                STRING_PNEUMATIC_KEYS,
                BOOL_PNEUMATIC_KEYS,
            )
        except Exception:
            NUMERIC_SIMULATION_KEYS = (
                "physics_dt",
                "render_vsync_hz",
                "max_steps_per_frame",
                "max_frame_time",
            )
            NUMERIC_PNEUMATIC_KEYS = (
                "receiver_volume",
                "polytropic_heat_transfer_coeff",
                "polytropic_exchange_area",
                "leak_coefficient",
                "leak_reference_area",
            )
            RECEIVER_VOLUME_LIMIT_KEYS = ("min_m3", "max_m3")
            STRING_PNEUMATIC_KEYS = ("volume_mode", "thermo_mode")
            BOOL_PNEUMATIC_KEYS = ("master_isolation_open",)

        try:
            sim_values = {
                key: _require_number("simulation", key)
                for key in NUMERIC_SIMULATION_KEYS
            }
            self.dt_physics = sim_values["physics_dt"]
            self.vsync_render_hz = sim_values["render_vsync_hz"]
            self.max_steps_per_frame = max(
                1, int(round(sim_values["max_steps_per_frame"]))
            )
            self.max_frame_time = sim_values["max_frame_time"]

            limits = self.settings_manager.get("pneumatic.receiver_volume_limits", None)
            if not isinstance(limits, dict) or not limits:
                limits = _default("pneumatic", "receiver_volume_limits")
            if not isinstance(limits, dict):
                raise RuntimeError("Missing pneumatic.receiver_volume_limits")
            min_limit = limits.get("min_m3")
            max_limit = limits.get("max_m3")
            if not isinstance(min_limit, (int, float)) or not isinstance(
                max_limit, (int, float)
            ):
                raise RuntimeError("Invalid receiver volume limits in settings")
            min_limit = float(min_limit)
            max_limit = float(max_limit)
            if max_limit <= min_limit or min_limit <= 0:
                raise RuntimeError("Receiver volume limits must satisfy0 < min < max")
            self._volume_limits = (min_limit, max_limit)

            for key in RECEIVER_VOLUME_LIMIT_KEYS:
                if key not in limits:
                    raise RuntimeError(
                        "Missing pneumatic.receiver_volume_limits." + key
                    )

            pneumatic_numbers = {
                key: _require_number("pneumatic", key) for key in NUMERIC_PNEUMATIC_KEYS
            }
            self.receiver_volume = pneumatic_numbers["receiver_volume"]
            if not (
                self._volume_limits[0] <= self.receiver_volume <= self._volume_limits[1]
            ):
                raise RuntimeError(
                    f"Receiver volume {self.receiver_volume} outside limits {self._volume_limits}"
                )

            pneumatic_strings = {
                key: _require_str("pneumatic", key) for key in STRING_PNEUMATIC_KEYS
            }

            mode = pneumatic_strings["volume_mode"].upper()
            if mode not in {"MANUAL", "GEOMETRIC"}:
                raise RuntimeError(f"Unsupported receiver volume mode: {mode}")
            self.receiver_volume_mode = mode

            pneumatic_bools = {
                key: _require_bool("pneumatic", key) for key in BOOL_PNEUMATIC_KEYS
            }
            self.master_isolation_open = pneumatic_bools["master_isolation_open"]

            thermo = pneumatic_strings["thermo_mode"].upper()
            try:
                self.thermo_mode = ThermoMode[thermo]
            except KeyError as exc:
                raise RuntimeError(f"Unsupported thermo_mode: {thermo}") from exc
        except Exception as exc:
            self.logger.critical(f"Failed to load physics settings: {exc}")
            raise

    def _apply_timing_configuration(self) -> None:
        """Recreate timing accumulator with current configuration"""
        self.timing_accumulator = TimingAccumulator(
            self.dt_physics,
            self.max_steps_per_frame,
            self.max_frame_time,
        )
        self.performance.target_dt = self.dt_physics

    def configure(
        self,
        dt_phys: Optional[float] = None,
        vsync_render_hz: Optional[float] = None,
        max_steps_per_frame: Optional[int] = None,
        max_frame_time: Optional[float] = None,
    ):
        """Configure physics parameters"""
        if isinstance(dt_phys, (int, float)) and not isinstance(dt_phys, bool):
            self.dt_physics = float(dt_phys)
        if isinstance(vsync_render_hz, (int, float)) and not isinstance(
            vsync_render_hz, bool
        ):
            self.vsync_render_hz = float(vsync_render_hz)
        if isinstance(max_steps_per_frame, (int, float)) and not isinstance(
            max_steps_per_frame, bool
        ):
            self.max_steps_per_frame = max(1, int(round(max_steps_per_frame)))
        if isinstance(max_frame_time, (int, float)) and not isinstance(
            max_frame_time, bool
        ):
            self.max_frame_time = float(max_frame_time)

        # Update timing accumulator
        self._apply_timing_configuration()

        # Create default physics objects
        self._initialize_physics_objects()

        self.is_configured = True
        self.logger.info(
            f"Physics configured: dt={self.dt_physics * 1000:.3f}ms, render={self.vsync_render_hz:.1f}Hz"
        )

    def _initialize_physics_objects(self):
        """Initialize physics simulation objects"""
        try:
            # Create 3-DOF rigid body
            self.rigid_body = create_default_rigid_body()

            # Initialize physics state (at rest)
            self.physics_state = create_initial_conditions()

            config_defaults = create_default_system_configuration()

            receiver_spec = ReceiverSpec(
                V_min=self._volume_limits[0],
                V_max=self._volume_limits[1],
            )
            receiver_mode = self._resolve_receiver_mode(self.receiver_volume_mode)
            pneumatic_cfg = self.settings_manager.get("pneumatic", {}) or {}
            pneumatic_defaults = (
                self.settings_manager.get("defaults_snapshot.pneumatic", {}) or {}
            )

            def _resolve_numeric(data: Dict[str, Any], key: str) -> Optional[float]:
                value = data.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    return None
                return float(value)

            def _get_pressure_setting(key: str, fallback: float) -> float:
                value = _resolve_numeric(pneumatic_cfg, key)
                if value is None:
                    value = _resolve_numeric(pneumatic_defaults, key)
                if value is None:
                    return fallback
                return value

            def _resolve_positive(key: str) -> float:
                value = _resolve_numeric(pneumatic_cfg, key)
                if value is None:
                    value = _resolve_numeric(pneumatic_defaults, key)
                if value is None:
                    return 0.0
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    return 0.0
                return max(numeric, 0.0)

            default_temp_c = 20.0
            atmo_temp_c = _resolve_numeric(pneumatic_cfg, "atmo_temp")
            if atmo_temp_c is None:
                atmo_temp_c = _resolve_numeric(pneumatic_defaults, "atmo_temp")
            if atmo_temp_c is None:
                atmo_temp_c = default_temp_c
            ambient_temperature = max(atmo_temp_c + KELVIN_0C, 1.0)

            poly_heat_transfer = _resolve_positive("polytropic_heat_transfer_coeff")
            poly_exchange_area = _resolve_positive("polytropic_exchange_area")
            leak_coefficient = _resolve_positive("leak_coefficient")
            leak_reference_area = _resolve_positive("leak_reference_area")

            relief_min_threshold = _get_pressure_setting(
                "relief_min_pressure", 1.05 * PA_ATM
            )
            relief_stiff_threshold = _get_pressure_setting(
                "relief_stiff_pressure", 1.5 * PA_ATM
            )
            relief_safety_threshold = _get_pressure_setting(
                "relief_safety_pressure", 2.0 * PA_ATM
            )

            receiver_state = ReceiverState(
                spec=receiver_spec,
                V=self.receiver_volume,
                p=PA_ATM,
                T=ambient_temperature,
                mode=receiver_mode,
            )

            self.pneumatic_system = create_standard_diagonal_system(
                cylinder_specs=config_defaults["cylinder_specs"],
                line_configs=config_defaults["line_configs"],
                receiver=receiver_state,
                master_isolation_open=self.master_isolation_open,
            )

            line_volumes = self.pneumatic_system.get_line_volumes()
            line_states: Dict[Line, Any] = {}
            for line_name, volume_info in line_volumes.items():
                if (
                    not isinstance(volume_info, dict)
                    or "total_volume" not in volume_info
                ):
                    raise RuntimeError(
                        f"Line volume information missing for {line_name.value}"
                    )
                total_volume = float(volume_info.get("total_volume"))
                if total_volume <= 0:
                    raise RuntimeError(
                        f"Line {line_name.value} has non-positive volume {total_volume}"
                    )
                line_states[line_name] = create_line_gas_state(
                    line_name,
                    PA_ATM,
                    ambient_temperature,
                    total_volume,
                )

            tank_state = create_tank_gas_state(
                V_initial=self.receiver_volume,
                p_initial=PA_ATM,
                T_initial=ambient_temperature,
                mode=receiver_mode,
            )

            self.gas_network = GasNetwork(
                lines=line_states,
                tank=tank_state,
                system_ref=self.pneumatic_system,
                master_isolation_open=self.master_isolation_open,
                ambient_temperature=ambient_temperature,
                relief_min_threshold=relief_min_threshold,
                relief_stiff_threshold=relief_stiff_threshold,
                relief_safety_threshold=relief_safety_threshold,
                polytropic_params=PolytropicParameters(
                    heat_transfer_coeff=poly_heat_transfer,
                    exchange_area=poly_exchange_area,
                    ambient_temperature=ambient_temperature,
                ),
                leak_coefficient=leak_coefficient,
                leak_reference_area=leak_reference_area,
            )

            self._latest_tank_state = TankState(
                pressure=tank_state.p,
                temperature=tank_state.T,
                mass=tank_state.m,
                volume=tank_state.V,
            )

            for wheel, cylinder in self.pneumatic_system.cylinders.items():
                self._prev_piston_positions[wheel] = cylinder.x
                wheel_state = self._latest_wheel_states[wheel]
                wheel_state.piston_position = cylinder.x
                wheel_state.lever_angle = 0.0

            preset_name = self._select_road_preset()
            road_input = create_road_input_from_preset(preset_name)
            road_input.configure(road_input.config, system=self.pneumatic_system)
            road_input.prime()
            self.road_input = road_input

            if not all([self.pneumatic_system, self.gas_network, self.road_input]):
                raise RuntimeError("Failed to initialize all physics dependencies")

            self.logger.info(
                "Physics objects initialized successfully with preset '%s'",
                preset_name,
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize physics objects: {e}")
            raise

    @Slot()
    def start_simulation(self):
        """Start physics simulation (called from UI thread)"""
        if not self.is_configured:
            self.error_occurred.emit("Physics worker not configured")
            return

        if self.is_running:
            self.logger.warning("Simulation already running")
            return

        # Create timer in this thread (will be moved to physics thread)
        if self.physics_timer is None:
            self.physics_timer = QTimer()
            self.physics_timer.timeout.connect(self._physics_step)
            self.physics_timer.setSingleShot(False)

        # Start timer with high precision
        timer_interval_ms = max(1, int(self.dt_physics * 1000))  # At least 1ms
        self.physics_timer.start(timer_interval_ms)

        self.is_running = True
        self.timing_accumulator.reset()

        self.logger.info(
            f"Physics simulation started, timer interval: {timer_interval_ms}ms"
        )

    @Slot()
    def stop_simulation(self):
        """Stop physics simulation"""
        self.logger.info("Остановка physics simulation...")

        try:
            # Сначала отмечаем, что симуляция должна остановиться
            self.is_running = False

            # Останавливаем таймер АГРЕССИВНО
            if self.physics_timer:
                try:
                    # Отключаем все сигналы
                    self.physics_timer.timeout.disconnect()
                except Exception:
                    pass  # Может быть уже отключен

                # Останавливаем таймер
                self.physics_timer.stop()

                # Удаляем таймер для полной очистки
                self.physics_timer.deleteLater()
                self.physics_timer = None
                self.logger.info("Physics timer остановлен и очищен")

            # Очищаем ссылки на объекты
            # (НЕ удаляем их полностью, так как могут быть нужны для повторного запуска)

            self.logger.info("Physics simulation остановлена")

        except Exception as e:
            self.logger.error(f"Ошибка остановки physics simulation: {e}")
            import traceback

            traceback.print_exc()

        # В любом случае помечаем как остановленную
        self.is_running = False

    def force_cleanup(self):
        """Принудительная очистка всех ресурсов"""
        try:
            self.is_running = False
            self.is_configured = False

            if self.physics_timer:
                try:
                    self.physics_timer.timeout.disconnect()
                except Exception:
                    pass
                self.physics_timer.stop()
                self.physics_timer.deleteLater()
                self.physics_timer = None

            # Очистка объектов физики
            self.rigid_body = None
            self.road_input = None
            self.pneumatic_system = None
            self.gas_network = None

            self.logger.info("Принудительная очистка PhysicsWorker завершена")

        except Exception as e:
            self.logger.error(f"Ошибка принудительной очистки: {e}")

    def __del__(self):
        """Деструктор - финальная очистка"""
        try:
            self.force_cleanup()
        except Exception:
            pass

    @Slot()
    def reset_simulation(self):
        """Reset simulation to initial state"""
        self.simulation_time = 0.0
        self.step_counter = 0

        if self.rigid_body:
            self.physics_state = create_initial_conditions()

        self.timing_accumulator.reset()
        self.performance = PerformanceMetrics()
        self.performance.target_dt = self.dt_physics

        self.logger.info("Simulation reset to initial state")

    @Slot()
    def pause_simulation(self):
        """Pause/unpause simulation"""
        if self.is_running:
            self.stop_simulation()
        else:
            self.start_simulation()

    @Slot(str)
    def set_thermo_mode(self, mode: str):
        """Set thermodynamic mode"""
        if mode == "ISOTHERMAL":
            self.thermo_mode = ThermoMode.ISOTHERMAL
        elif mode == "ADIABATIC":
            self.thermo_mode = ThermoMode.ADIABATIC
        elif mode == "POLYTROPIC":
            self.thermo_mode = ThermoMode.POLYTROPIC
        else:
            self.error_occurred.emit(f"Unknown thermo mode: {mode}")
            return

        self.logger.info(f"Thermo mode set to: {mode}")

    @Slot(bool)
    def set_master_isolation(self, open: bool):
        """Set master isolation valve state"""
        self.master_isolation_open = open
        self.logger.info(f"Master isolation: {'OPEN' if open else 'CLOSED'}")

    @Slot(float, str)
    def set_receiver_volume(self, volume: float, mode: str):
        """Set receiver volume and recalculation mode

        Args:
            volume: New receiver volume in m?
            mode: Recalculation mode ('NO_RECALC' or 'ADIABATIC_RECALC')
        """
        if volume <= 0 or volume > 1.0:  # Reasonable limits (0-1000L)
            self.error_occurred.emit(f"Invalid receiver volume: {volume} m?")
            return

        # Store volume and mode for gas network updates
        self.receiver_volume = volume
        self.receiver_volume_mode = mode

        mode_enum = self._resolve_receiver_mode(mode)

        if self.pneumatic_system is not None:
            try:
                self.pneumatic_system.receiver.mode = mode_enum
                self.pneumatic_system.receiver.apply_instant_volume_change(volume)
            except Exception as exc:
                self.logger.warning(f"Failed to update receiver state: {exc}")

        if self.gas_network is not None:
            try:
                self.gas_network.tank.mode = mode_enum
                apply_instant_volume_change(
                    self.gas_network.tank,
                    volume,
                    gamma=self.gas_network.tank.gamma,
                )
            except Exception as exc:
                self.logger.warning(f"Failed to update gas network tank volume: {exc}")

        self.logger.info(f"Receiver volume set: {volume:.3f}m? (mode: {mode})")

    @Slot(float)
    def set_physics_dt(self, dt: float):
        """Change physics timestep"""
        if dt <= 0 or dt > 0.1:  # Reasonable limits
            self.error_occurred.emit(f"Invalid physics dt: {dt}")
            return

        old_dt = self.dt_physics
        self.dt_physics = dt
        self.timing_accumulator = TimingAccumulator(dt)
        self.performance.target_dt = dt

        # Restart timer if running
        if self.is_running and self.physics_timer:
            self.physics_timer.stop()
            timer_interval_ms = max(1, int(dt * 1000))
            self.physics_timer.start(timer_interval_ms)

        self.logger.info(
            f"Physics dt changed: {old_dt * 1000:.3f}ms ? {dt * 1000:.3f}ms"
        )

    @Slot()
    def _physics_step(self):
        """Single physics simulation step (called by QTimer)"""
        if not self.is_running:
            return

        step_start_time = time.perf_counter()

        try:
            # Use timing accumulator to determine number of steps
            steps_to_take = self.timing_accumulator.update()

            for _ in range(steps_to_take):
                self._execute_physics_step()

            # Update performance metrics
            step_end_time = time.perf_counter()
            step_time = step_end_time - step_start_time
            self.performance.update_step_time(step_time)

            # Emit performance update periodically
            if self.step_counter % 100 == 0:  # Every 100 steps
                self.performance_update.emit(self.performance.get_summary())

            # Create and emit state snapshot
            snapshot = self._create_state_snapshot()
            if snapshot and snapshot.validate():
                self.state_ready.emit(snapshot)
            else:
                self.error_counter.increment()
                if self.error_counter.get() > 10:  # Too many invalid states
                    self.error_occurred.emit("Too many invalid state snapshots")
                    self.stop_simulation()

        except Exception as e:
            self.logger.error(f"Physics step failed: {e}")
            self.error_occurred.emit(f"Physics step error: {str(e)}")
            self.stop_simulation()

    def _execute_physics_step(self):
        """Execute single physics timestep"""
        if not self.pneumatic_system or not self.gas_network or not self.road_input:
            raise RuntimeError("Physics dependencies are not initialized")

        # 1. Get road inputs
        road_inputs = self._get_road_inputs()
        self._last_road_inputs = {k: float(v) for k, v in road_inputs.items()}

        # 2. Update geometry/kinematics
        lever_angles: Dict[Wheel, float] = {}
        wheel_key_map = {
            Wheel.LP: "LF",
            Wheel.PP: "RF",
            Wheel.LZ: "LR",
            Wheel.PZ: "RR",
        }

        for wheel, key in wheel_key_map.items():
            excitation = float(road_inputs.get(key, 0.0))
            cylinder = self.pneumatic_system.cylinders[wheel]
            lever = cylinder.spec.lever_geom
            lever_length = max(lever.L_lever, 1e-6)
            angle = float(np.clip(excitation / lever_length, -0.5, 0.5))
            lever_angles[wheel] = angle

        self.pneumatic_system.update_system_from_lever_angles(lever_angles)

        for wheel, angle in lever_angles.items():
            cylinder = self.pneumatic_system.cylinders[wheel]
            piston_pos = float(cylinder.x)
            prev_pos = self._prev_piston_positions.get(wheel, 0.0)
            piston_vel = (
                (piston_pos - prev_pos) / self.dt_physics
                if self.dt_physics > 0
                else 0.0
            )
            self._prev_piston_positions[wheel] = piston_pos

            geom = cylinder.spec.geometry
            rod_x, rod_y = cylinder.spec.lever_geom.rod_joint_pos(angle)
            wheel_state = self._latest_wheel_states[wheel]
            wheel_state.lever_angle = angle
            wheel_state.piston_position = piston_pos
            wheel_state.piston_velocity = piston_vel
            wheel_state.vol_head = cylinder.vol_head()
            wheel_state.vol_rod = cylinder.vol_rod()
            wheel_state.joint_x = 0.0
            wheel_state.joint_y = rod_x
            wheel_state.joint_z = geom.Z_axle + rod_y
            wheel_state.road_excitation = self._last_road_inputs.get(
                wheel_key_map[wheel], 0.0
            )

            wheel_state.stop_head_penetration = cylinder.penetration_head
            wheel_state.stop_rod_penetration = cylinder.penetration_rod
            wheel_state.stop_head_engaged = cylinder.penetration_head > 1e-9
            wheel_state.stop_rod_engaged = cylinder.penetration_rod > 1e-9

            head_pressure = self._get_line_pressure(wheel, Port.HEAD)
            rod_pressure = self._get_line_pressure(wheel, Port.ROD)
            head_pressure_gauge = to_gauge_pressure(head_pressure)
            rod_pressure_gauge = to_gauge_pressure(rod_pressure)
            area_head = geom.area_head(cylinder.spec.is_front)
            area_rod = geom.area_rod(cylinder.spec.is_front)
            wheel_state.force_pneumatic = (
                head_pressure_gauge * area_head - rod_pressure_gauge * area_rod
            )

        # 3. Update gas system
        line_volumes = self.pneumatic_system.get_line_volumes()
        corrected_volumes: Dict[Line, float] = {}
        for line_name, volume_info in line_volumes.items():
            total_volume = float(volume_info.get("total_volume"))
            penetration_volume = 0.0
            endpoints = self.pneumatic_system.lines[line_name].endpoints
            for wheel, port in endpoints:
                cylinder = self.pneumatic_system.cylinders[wheel]
                geom = cylinder.spec.geometry
                if port == Port.HEAD:
                    penetration = cylinder.penetration_head
                    if penetration > 0.0:
                        penetration_volume += (
                            geom.area_head(cylinder.spec.is_front) * penetration
                        )
                else:
                    penetration = cylinder.penetration_rod
                    if penetration > 0.0:
                        penetration_volume += (
                            geom.area_rod(cylinder.spec.is_front) * penetration
                        )

            effective_volume = max(total_volume - penetration_volume, 1e-9)
            corrected_volumes[line_name] = effective_volume

        self.gas_network.master_isolation_open = self.master_isolation_open
        self.gas_network.update_pressures_with_explicit_volumes(
            corrected_volumes, self.thermo_mode
        )

        receiver_mode = self._resolve_receiver_mode(self.receiver_volume_mode)
        self.gas_network.tank.mode = receiver_mode
        if abs(self.gas_network.tank.V - self.receiver_volume) > 1e-9:
            apply_instant_volume_change(
                self.gas_network.tank,
                self.receiver_volume,
                gamma=self.gas_network.tank.gamma,
            )

        self.gas_network.apply_valves_and_flows(self.dt_physics, self.logger)
        self.gas_network.enforce_master_isolation(self.logger)

        for line_name, gas_state in self.gas_network.lines.items():
            line_state = self._latest_line_states[line_name]
            line_state.pressure = gas_state.p
            line_state.temperature = gas_state.T
            line_state.mass = gas_state.m
            line_state.volume = gas_state.V_curr
            pneumo_line = self.pneumatic_system.lines[line_name]
            try:
                line_state.cv_atmo_open = pneumo_line.cv_atmo.is_open(
                    PA_ATM, gas_state.p
                )
            except Exception:
                line_state.cv_atmo_open = False
            try:
                line_state.cv_tank_open = pneumo_line.cv_tank.is_open(
                    gas_state.p, self.gas_network.tank.p
                )
            except Exception:
                line_state.cv_tank_open = False
            line_state.flow_atmo = 0.0
            line_state.flow_tank = 0.0

        tank_state = self.gas_network.tank
        self._latest_tank_state.pressure = tank_state.p
        self._latest_tank_state.temperature = tank_state.T
        self._latest_tank_state.mass = tank_state.m
        self._latest_tank_state.volume = tank_state.V

        # 4. Integrate 3-DOF dynamics
        if self.rigid_body:
            try:
                result = step_dynamics(
                    y0=self.physics_state,
                    t0=self.simulation_time,
                    dt=self.dt_physics,
                    params=self.rigid_body,
                    system=self.pneumatic_system,
                    gas=self.gas_network,
                    method="Radau",
                )

                if result.success:
                    prev_vel = self.physics_state[3:6].copy()
                    self.physics_state = result.y_final
                    velocities = self.physics_state[3:6]
                    if self.dt_physics > 0:
                        self._latest_frame_accel = (
                            velocities - prev_vel
                        ) / self.dt_physics
                    self._prev_frame_velocities = velocities.copy()
                else:
                    self.performance.integration_failures += 1
                    self.logger.warning(f"Integration failed: {result.message}")

            except Exception as e:
                self.performance.integration_failures += 1
                self.logger.error(f"Integration error: {e}")

        # Update simulation time and step counter
        self.simulation_time += self.dt_physics
        self.step_counter += 1

    def _get_road_inputs(self) -> Dict[str, float]:
        """Get road excitation for all wheels"""
        if self.road_input:
            try:
                return self.road_input.get_wheel_excitation(self.simulation_time)
            except Exception as e:
                self.logger.warning(f"Road input error: {e}")

        # Return zero excitation as fallback
        return {"LF": 0.0, "RF": 0.0, "LR": 0.0, "RR": 0.0}

    def _create_state_snapshot(self) -> Optional[StateSnapshot]:
        """Create current state snapshot"""
        try:
            snapshot = StateSnapshot()

            # Basic timing info
            snapshot.simulation_time = self.simulation_time
            snapshot.dt_physics = self.dt_physics
            snapshot.step_number = self.step_counter

            # Frame state from physics integration
            if len(self.physics_state) >= 6:
                Y, phi_z, theta_x, dY, dphi_z, dtheta_x = self.physics_state

                snapshot.frame = FrameState(
                    heave=float(Y),
                    roll=float(phi_z),
                    pitch=float(theta_x),
                    heave_rate=float(dY),
                    roll_rate=float(dphi_z),
                    pitch_rate=float(dtheta_x),
                    heave_accel=float(self._latest_frame_accel[0]),
                    roll_accel=float(self._latest_frame_accel[1]),
                    pitch_accel=float(self._latest_frame_accel[2]),
                )

            # Road excitations
            road_excitations = self._last_road_inputs

            # Wheel states
            for wheel in [Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ]:
                wheel_state = replace(self._latest_wheel_states[wheel])

                wheel_key = wheel.value  # LP, PP, LZ, PZ
                if wheel_key in road_excitations:
                    wheel_state.road_excitation = road_excitations[wheel_key]

                snapshot.wheels[wheel] = wheel_state

            # Line states
            for line in [Line.A1, Line.B1, Line.A2, Line.B2]:
                snapshot.lines[line] = replace(self._latest_line_states[line])

            # Tank state
            snapshot.tank = replace(self._latest_tank_state)

            # System aggregates
            snapshot.aggregates = SystemAggregates(
                physics_step_time=self.performance.avg_step_time,
                integration_steps=self.step_counter,
                integration_failures=self.performance.integration_failures,
            )

            # Configuration
            snapshot.master_isolation_open = self.master_isolation_open
            snapshot.thermo_mode = (
                self.thermo_mode.name
                if hasattr(self.thermo_mode, "name")
                else str(self.thermo_mode)
            )

            return snapshot

        except Exception as e:
            self.logger.error(f"Failed to create state snapshot: {e}")
            return None

    def _resolve_receiver_mode(self, mode: Optional[str] = None) -> ReceiverVolumeMode:
        raw_mode = (mode or self.receiver_volume_mode or "MANUAL").strip().upper()
        mapping = {
            "MANUAL": ReceiverVolumeMode.NO_RECALC,
            "GEOMETRIC": ReceiverVolumeMode.ADIABATIC_RECALC,
            ReceiverVolumeMode.NO_RECALC.name: ReceiverVolumeMode.NO_RECALC,
            ReceiverVolumeMode.ADIABATIC_RECALC.name: ReceiverVolumeMode.ADIABATIC_RECALC,
        }
        if raw_mode not in mapping:
            raise RuntimeError(f"Unsupported receiver volume mode: {raw_mode}")
        return mapping[raw_mode]

    def _select_road_preset(self) -> str:
        preset_candidates = [
            self.settings_manager.get("simulation.road_preset", None),
            self.settings_manager.get("modes.road_preset", None),
            self.settings_manager.get("modes.mode_preset", None),
        ]

        for candidate in preset_candidates:
            if candidate:
                preset = str(candidate).strip()
                if preset:
                    break
        else:
            preset = "test_sine"

        alias_map = {
            "standard": "urban_50kmh",
            "полная динамика": "sine_sweep",
            "только кинематика": "test_sine",
            "тест пневматики": "test_sine",
        }

        lookup = alias_map.get(preset.lower(), preset)
        if get_preset_by_name(lookup) is None:
            self.logger.warning(
                "Unknown road preset '%s', falling back to 'test_sine'",
                lookup,
            )
            lookup = "test_sine"
        return lookup

    def _get_line_pressure(self, wheel: Wheel, port: Port) -> float:
        for line_name, line in self.pneumatic_system.lines.items():
            for endpoint_wheel, endpoint_port in line.endpoints:
                if endpoint_wheel == wheel and endpoint_port == port:
                    return float(self.gas_network.lines[line_name].p)
        return float(self.gas_network.tank.p)


SNAPSHOT_BUFFER_CAPACITY = 4096


class SimulationManager(QObject):
    """High-level simulation manager

    Manages PhysicsWorker in separate thread and provides
    unified interface for UI interaction.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create physics thread and worker
        self.physics_thread = QThread()
        self.physics_worker = PhysicsWorker()

        # Move worker to physics thread
        self.physics_worker.moveToThread(self.physics_thread)

        # Create state bus for communication
        self.state_bus = StateBus()

        # Create state queue for latest-only semantics
        self.state_queue = LatestOnlyQueue()

        # Snapshot history for CSV export and diagnostics
        self._snapshot_buffer = StateSnapshotBuffer(maxlen=SNAPSHOT_BUFFER_CAPACITY)

        # Connect signals
        self._connect_signals()

        # Logging
        self.logger = logging.getLogger(__name__)

    def _connect_signals(self):
        """Connect signals between components"""
        # Physics worker signals
        self.physics_worker.state_ready.connect(
            self._on_state_ready, Qt.QueuedConnection
        )
        self.physics_worker.error_occurred.connect(
            self._on_physics_error, Qt.QueuedConnection
        )

        # State bus control signals
        self.state_bus.start_simulation.connect(
            self.physics_worker.start_simulation, Qt.QueuedConnection
        )
        self.state_bus.stop_simulation.connect(
            self.physics_worker.stop_simulation, Qt.QueuedConnection
        )
        self.state_bus.reset_simulation.connect(
            self.physics_worker.reset_simulation, Qt.QueuedConnection
        )
        self.state_bus.pause_simulation.connect(
            self.physics_worker.pause_simulation, Qt.QueuedConnection
        )

        # Local housekeeping when reset is requested
        self.state_bus.reset_simulation.connect(
            self.clear_snapshot_buffer, Qt.QueuedConnection
        )

        # Configuration signals
        self.state_bus.set_physics_dt.connect(
            self.physics_worker.set_physics_dt, Qt.QueuedConnection
        )
        self.state_bus.set_thermo_mode.connect(
            self.physics_worker.set_thermo_mode, Qt.QueuedConnection
        )
        self.state_bus.set_master_isolation.connect(
            self.physics_worker.set_master_isolation, Qt.QueuedConnection
        )
        self.state_bus.set_receiver_volume.connect(
            self.physics_worker.set_receiver_volume, Qt.QueuedConnection
        )  # NEW!

        # Thread lifecycle
        self.physics_thread.started.connect(self._on_thread_started)
        self.physics_thread.finished.connect(self._on_thread_finished)

    def start(self):
        """Start simulation manager"""
        if not self.physics_thread.isRunning():
            # Ensure previous history does not leak into a new run
            self.clear_snapshot_buffer()

            # Configure physics worker
            self.physics_worker.configure()

            # Start physics thread
            self.physics_thread.start()

            self.logger.info("Simulation manager started")

    def stop(self):
        """Stop simulation manager"""
        self.logger.info("Остановка simulation manager...")

        try:
            if self.physics_thread.isRunning():
                # 1. Сначала остановить симуляцию через worker
                if hasattr(self.physics_worker, "force_cleanup"):
                    try:
                        self.physics_worker.force_cleanup()
                    except Exception as e:
                        self.logger.warning(
                            f"Ошибка принудительной очистки worker: {e}"
                        )

                # 2. Отправить сигнал остановки
                try:
                    self.state_bus.stop_simulation.emit()
                except Exception as e:
                    self.logger.warning(f"Ошибка отправки сигнала остановки: {e}")

                # 3. Дать короткое время на корректную остановку (50мс)
                import time

                time.sleep(0.05)

                # 4. Попытаться корректно завершить поток
                self.logger.info("Корректное завершение physics thread...")
                self.physics_thread.quit()

                # 5. Ждать завершения максимум 2 секунды
                if not self.physics_thread.wait(2000):
                    self.logger.warning(
                        "Physics thread не завершился за 2 секунды, принудительное завершение..."
                    )
                    self.physics_thread.terminate()

                    # Дать полсекунды на принудительное завершение
                    if not self.physics_thread.wait(500):
                        self.logger.error(
                            "Physics thread не удалось завершить даже принудительно!"
                        )
                    else:
                        self.logger.info("Physics thread завершен принудительно")
                else:
                    self.logger.info("Physics thread завершен корректно")

            else:
                self.logger.info("Physics thread уже остановлен")

        except Exception as e:
            self.logger.error(f"Ошибка при остановке simulation manager: {e}")
            import traceback

            traceback.print_exc()

            # В случае ошибки все равно пытаемся принудительно завершить
            try:
                if hasattr(self, "physics_thread") and self.physics_thread.isRunning():
                    self.physics_thread.terminate()
                    self.physics_thread.wait(500)
            except Exception:
                pass

        # Финальная очистка ссылок
        try:
            self.physics_worker = None
        except Exception:
            pass

        self.logger.info("Simulation manager остановлен")

    def force_shutdown(self):
        """Принудительное завершение для критических случаев"""
        try:
            if hasattr(self, "physics_worker") and self.physics_worker:
                self.physics_worker.force_cleanup()

            if hasattr(self, "physics_thread") and self.physics_thread.isRunning():
                self.physics_thread.terminate()
                self.physics_thread.wait(1000)

            self.logger.info("Принудительное завершение SimulationManager выполнено")
        except Exception as e:
            self.logger.error(f"Ошибка принудительного завершения: {e}")

    def cleanup(self):
        """Очистка ресурсов симуляции (вызывается при закрытии приложения)

        Корректно останавливает физический поток и освобождает ресурсы.
        """
        self.logger.info("Начинаем очистку SimulationManager...")

        try:
            # Используем существующий метод stop() для корректной остановки
            self.stop()

            # Дополнительная очистка ссылок
            self.state_bus = None
            self.state_queue = None

            self.logger.info("Очистка SimulationManager завершена успешно")

        except Exception as e:
            self.logger.error(f"Ошибка при очистке SimulationManager: {e}")
            # Принудительная очистка в случае ошибки
            try:
                self.force_shutdown()
            except Exception as cleanup_error:
                self.logger.error(
                    f"Критическая ошибка при принудительной очистке: {cleanup_error}"
                )

    def get_latest_state(self) -> Optional[StateSnapshot]:
        """Get latest state snapshot without blocking"""
        return self.state_queue.get_nowait()

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get state queue statistics"""
        return self.state_queue.get_stats()

    def get_snapshot_buffer(self):
        """Получить копию буфера снимков для экспорта"""

        return self._snapshot_buffer.to_list()

    @Slot()
    def clear_snapshot_buffer(self) -> None:
        """Очистить буфер снимков (используется при сбросе симуляции)."""

        self._snapshot_buffer.clear()
        self.logger.debug("Snapshot buffer cleared")

    @Slot(object)
    def _on_state_ready(self, snapshot):
        """Handle state ready from physics worker"""
        try:
            self.state_queue.put_nowait(snapshot)
        except Exception as queue_error:
            self.logger.error(f"Error handling state ready: {queue_error}")
        else:
            try:
                self.state_bus.state_ready.emit(snapshot)
            except Exception as emit_error:
                self.logger.error(f"Error re-emitting state snapshot: {emit_error}")

        # Always record the snapshot for export/diagnostics.
        self._snapshot_buffer.append(snapshot)

    @Slot(str)
    def _on_physics_error(self, error_msg):
        """Handle physics error"""
        self.logger.error(f"Physics error: {error_msg}")
        self.state_bus.physics_error.emit(error_msg)

    @Slot()
    def _on_thread_started(self):
        """Handle physics thread started"""
        self.logger.info("Physics thread started successfully")

    @Slot()
    def _on_thread_finished(self):
        """Handle physics thread finished"""
        self.logger.info("Physics thread finished")
