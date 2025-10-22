"""Signals Router Module - Signal connection and routing

Модуль подключения и роутинга сигналов между компонентами.
Управляет всеми сигнально-слотовыми соединениями главного окна.

Russian comments / English code.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from PySide6.QtCore import Qt

from ...pneumo.enums import Line, Wheel
from .qml_bridge import QMLBridge

if TYPE_CHECKING:
    from .main_window import MainWindow
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
        if payload:
            QMLBridge.queue_update(window, "simulation", payload)

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

        try:
            window._qml_root_object.batchUpdatesApplied.connect(
                window._on_qml_batch_ack, Qt.QueuedConnection
            )
            SignalsRouter.logger.info("✅ QML signals connected")
        except AttributeError:
            SignalsRouter.logger.warning("⚠️ QML batchUpdatesApplied signal not found")

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

        from .qml_bridge import QMLBridge

        if not QMLBridge.invoke_qml_function(window, "applyLightingUpdates", params):
            QMLBridge.queue_update(window, "lighting", params)
            QMLBridge._log_graphics_change(window, "lighting", params, applied=False)
        else:
            QMLBridge._log_graphics_change(window, "lighting", params, applied=True)

    @staticmethod
    def handle_material_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle material changes from GraphicsPanel"""
        if not isinstance(params, dict):
            return

        from .qml_bridge import QMLBridge

        if not QMLBridge.invoke_qml_function(window, "applyMaterialUpdates", params):
            QMLBridge.queue_update(window, "materials", params)
            QMLBridge._log_graphics_change(window, "materials", params, applied=False)
        else:
            QMLBridge._log_graphics_change(window, "materials", params, applied=True)

    @staticmethod
    def handle_environment_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle environment changes from GraphicsPanel"""
        if not isinstance(params, dict):
            return

        from .qml_bridge import QMLBridge

        if not QMLBridge.invoke_qml_function(window, "applyEnvironmentUpdates", params):
            QMLBridge.queue_update(window, "environment", params)
            QMLBridge._log_graphics_change(window, "environment", params, applied=False)
        else:
            QMLBridge._log_graphics_change(window, "environment", params, applied=True)

    @staticmethod
    def handle_quality_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle quality changes from GraphicsPanel"""
        if not isinstance(params, dict):
            return

        from .qml_bridge import QMLBridge

        if not QMLBridge.invoke_qml_function(window, "applyQualityUpdates", params):
            QMLBridge.queue_update(window, "quality", params)
            QMLBridge._log_graphics_change(window, "quality", params, applied=False)
        else:
            QMLBridge._log_graphics_change(window, "quality", params, applied=True)

    @staticmethod
    def handle_camera_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle camera changes from GraphicsPanel"""
        if not isinstance(params, dict):
            return

        from .qml_bridge import QMLBridge

        if not QMLBridge.invoke_qml_function(window, "applyCameraUpdates", params):
            QMLBridge.queue_update(window, "camera", params)
            QMLBridge._log_graphics_change(window, "camera", params, applied=False)
        else:
            QMLBridge._log_graphics_change(window, "camera", params, applied=True)

    @staticmethod
    def handle_effects_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle effects changes from GraphicsPanel"""
        if not isinstance(params, dict):
            return

        from .qml_bridge import QMLBridge

        if not QMLBridge.invoke_qml_function(window, "applyEffectsUpdates", params):
            QMLBridge.queue_update(window, "effects", params)
            QMLBridge._log_graphics_change(window, "effects", params, applied=False)
        else:
            QMLBridge._log_graphics_change(window, "effects", params, applied=True)

    @staticmethod
    def handle_preset_applied(window: MainWindow, full_state: Dict[str, Any]) -> None:
        """Handle graphics preset application

        Args:
            window: MainWindow instance
            full_state: Full graphics state
        """
        if not isinstance(full_state, dict):
            return

        from .qml_bridge import QMLBridge

        # Queue all categories as batch
        QMLBridge.queue_update(window, "environment", full_state.get("environment", {}))
        QMLBridge.queue_update(window, "lighting", full_state.get("lighting", {}))
        QMLBridge.queue_update(window, "materials", full_state.get("materials", {}))
        QMLBridge.queue_update(window, "quality", full_state.get("quality", {}))
        QMLBridge.queue_update(window, "camera", full_state.get("camera", {}))
        QMLBridge.queue_update(window, "effects", full_state.get("effects", {}))

    @staticmethod
    def handle_animation_changed(window: MainWindow, params: Dict[str, Any]) -> None:
        """Handle animation changes from ModesPanel"""
        if not isinstance(params, dict):
            return

        from .qml_bridge import QMLBridge

        if not QMLBridge.invoke_qml_function(window, "applyAnimationUpdates", params):
            QMLBridge.queue_update(window, "animation", params)
            QMLBridge._log_graphics_change(window, "animation", params, applied=False)
        else:
            QMLBridge._log_graphics_change(window, "animation", params, applied=True)

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
                window.step_count_label.setText(
                    f"Steps: {latest_snapshot.step_number}"
                )

                if latest_snapshot.aggregates.physics_step_time > 0:
                    fps = 1.0 / latest_snapshot.aggregates.physics_step_time
                    window.fps_label.setText(f"Physics FPS: {fps:.1f}")

            # Update charts
            if window.chart_widget:
                window.chart_widget.update_from_snapshot(latest_snapshot)

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

        if cmd == "start":
            window.is_simulation_running = True
        elif cmd == "pause":
            window.is_simulation_running = False
        elif cmd == "stop":
            window.is_simulation_running = False
        elif cmd == "reset":
            from .qml_bridge import QMLBridge

            QMLBridge.invoke_qml_function(window, "fullResetView")
