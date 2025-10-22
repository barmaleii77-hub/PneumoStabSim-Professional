"""
Physics simulation loop with fixed timestep
Runs in dedicated QThread with QTimer for precise timing
"""

import time
import logging
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
)
from src.pneumo.receiver import ReceiverState
from src.pneumo.system import create_standard_diagonal_system
from src.pneumo.gas_state import create_line_gas_state, create_tank_gas_state
from src.pneumo.network import GasNetwork
from src.road.engine import RoadInput
from src.road.scenarios import get_preset_by_name

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

        # Simulation modes (overridden by persisted settings)
        self.thermo_mode = ThermoMode.ISOTHERMAL
        self.master_isolation_open = False

        # Receiver parameters and limits (loaded from settings)
        self.receiver_volume: float = 0.0
        self.receiver_volume_mode: str = ""
        self._volume_limits: tuple[float, float] = (0.0, 0.0)

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

        try:
            self.dt_physics = _require_number("simulation", "physics_dt")
            self.vsync_render_hz = _require_number("simulation", "render_vsync_hz")
            self.max_steps_per_frame = max(
                1, int(round(_require_number("simulation", "max_steps_per_frame")))
            )
            self.max_frame_time = _require_number("simulation", "max_frame_time")

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

            self.receiver_volume = _require_number("pneumatic", "receiver_volume")
            if not (
                self._volume_limits[0] <= self.receiver_volume <= self._volume_limits[1]
            ):
                raise RuntimeError(
                    f"Receiver volume {self.receiver_volume} outside limits {self._volume_limits}"
                )

            mode = _require_str("pneumatic", "volume_mode").upper()
            if mode not in {"MANUAL", "GEOMETRIC"}:
                raise RuntimeError(f"Unsupported receiver volume mode: {mode}")
            self.receiver_volume_mode = mode

            self.master_isolation_open = _require_bool(
                "pneumatic", "master_isolation_open"
            )

            thermo = _require_str("pneumatic", "thermo_mode").upper()
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
            f"Physics configured: dt={self.dt_physics*1000:.3f}ms, render={self.vsync_render_hz:.1f}Hz"
        )

    def _initialize_physics_objects(self):
        """Initialize physics simulation objects"""
        try:
            # Create 3-DOF rigid body
            self.rigid_body = create_default_rigid_body()

            # Initialize physics state (at rest)
            self.physics_state = create_initial_conditions()

            # TODO: Initialize pneumatic system and gas network
            # For now, create minimal stubs
            self.pneumatic_system = None  # Will be set up later
            self.gas_network = None

            # TODO: Initialize road input
            # For now, create minimal stub
            self.road_input = None

            # NEW: Initialize road input with default scenario
            road_scenario = "default_scenario"  # Заменить на нужный пресет
            road_config = get_preset_by_name(road_scenario)
            if road_config:
                self.road_input = RoadInput(config=road_config)
                self.logger.info(
                    f"Road input initialized with scenario: {road_scenario}"
                )
            else:
                self.logger.warning(f"Road scenario not found: {road_scenario}")
                self.road_input = None  # Использовать заглушку

            # NEW: Initialize pneumatic system with standard configuration
            try:
                self.pneumatic_system = create_standard_diagonal_system()
                self.logger.info(
                    "Pneumatic system initialized with standard configuration"
                )
            except Exception as e:
                self.logger.warning(f"Failed to create standard pneumatic system: {e}")
                self.pneumatic_system = None  # Использовать заглушку

            # NEW: Initialize gas network with default parameters
            try:
                self.gas_network = GasNetwork()
                self.logger.info("Gas network initialized with default parameters")
            except Exception as e:
                self.logger.warning(f"Failed to create gas network: {e}")
                self.gas_network = None  # Использовать заглушку

            self.logger.info("Physics objects initialized successfully")

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

        # TODO: Update actual ReceiverState when gas network is integrated
        # For now, just log the change
        self.logger.info(f"Receiver volume set: {volume:.3f}m? (mode: {mode})")

        print(f"?? PhysicsWorker: Receiver volume={volume*1000:.1f}L, mode={mode}")

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

        self.logger.info(f"Physics dt changed: {old_dt*1000:.3f}ms ? {dt*1000:.3f}ms")

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
        # 1. Get road inputs
        road_inputs = self._get_road_inputs()

        # 2. Update geometry/kinematics
        if self.rigid_body:
            try:
                # Update lever angles and piston positions from road inputs
                if self.pneumatic_system:
                    for wheel, input_value in road_inputs.items():
                        if wheel in {Wheel.LP.value, Wheel.PP.value}:  # Левые колеса
                            cylinder = self.pneumatic_system.left_cylinder
                            if cylinder:
                                # Применяем возбуждение к позиции поршня
                                cylinder.piston_position += input_value

                        elif wheel in {Wheel.LZ.value, Wheel.PZ.value}:  # Правые колеса
                            cylinder = self.pneumatic_system.right_cylinder
                            if cylinder:
                                # Применяем возбуждение к позиции поршня
                                cylinder.piston_position += input_value

            except Exception as e:
                self.logger.warning(f"Failed to update kinematics: {e}")

        # 3. Update gas system
        if self.gas_network:
            try:
                # Получаем текущее состояние газа в трубопроводах и резервуарах
                line_gas_states = create_line_gas_state(self.gas_network)
                tank_gas_states = create_tank_gas_state(self.gas_network)

                # Обновляем состояния резервуаров в системе
                for state in tank_gas_states:
                    if state.receiver_id == "default_receiver":
                        # Применяем новое состояние газа к резервуару
                        receiver_state = ReceiverState(
                            pressure=state.pressure,
                            temperature=state.temperature,
                            volume=self.receiver_volume,
                        )
                        self.gas_network.update_receiver_state(receiver_state)

            except Exception as e:
                self.logger.warning(f"Failed to update gas network: {e}")

        # 4. Integrate 3-DOF dynamics
        if self.rigid_body:
            try:
                # Use placeholder system/gas for now
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
                    self.physics_state = result.y_final
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
        return {"LP": 0.0, "PP": 0.0, "LZ": 0.0, "PZ": 0.0}

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
                )

            # Road excitations
            road_excitations = self._get_road_inputs()

            # Wheel states
            for wheel in [Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ]:
                wheel_state = WheelState(wheel=wheel)

                # Add road excitation
                wheel_key = wheel.value  # LP, PP, LZ, PZ
                if wheel_key in road_excitations:
                    wheel_state.road_excitation = road_excitations[wheel_key]

                # TODO: Add actual wheel state from pneumatic system

                snapshot.wheels[wheel] = wheel_state

            # Line states (placeholder)
            for line in [Line.A1, Line.B1, Line.A2, Line.B2]:
                line_state = LineState(line=line)
                # TODO: Get actual line state from gas network
                snapshot.lines[line] = line_state

            # Tank state (placeholder)
            snapshot.tank = TankState()

            # NEW: Update tank volume from receiver settings
            snapshot.tank.volume = self.receiver_volume

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
        """Получить буфер снимков для экспорта (заглушка)"""
        # TODO: Реализовать буфер снимков
        return []

    @Slot(object)
    def _on_state_ready(self, snapshot):
        """Handle state ready from physics worker"""
        try:
            # Put in latest-only queue
            self.state_queue.put_nowait(snapshot)

            # Re-emit through state bus
            self.state_bus.state_ready.emit(snapshot)
        except Exception as e:
            self.logger.error(f"Error handling state ready: {e}")

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
