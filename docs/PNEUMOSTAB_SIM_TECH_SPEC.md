# PneumoStabSim Symmetric Stabilizer Emulator — Technical Specification

## 1. Purpose and Scope
- Deliver a Python-based symmetric pneumatic stabilizer emulator that reproduces the mechanical, pneumatic, thermal, and control behaviour of the real hardware in real time.
- Provide deterministic offline simulation and accelerated batch analysis modes for design and tuning.
- Supply visualizations (2D schematics, 3D rendered stabilizer, time-series dashboards) to validate state evolution and control actions.
- Integrate with existing application settings (see `config/app_settings.json`) and diagnostics/logging subsystems defined in `src/diagnostics/`.

## 2. Reference Architecture Overview
```
┌─────────────────────────────┐
│ CLI / UI Front Ends         │
└────────────┬────────────────┘
             │ Settings + Commands
┌────────────▼────────────────┐           ┌────────────────────────┐
│ Simulation Orchestrator     │           │ Visualization Services │
│ (`SimulationSession`)       │──────────▶│ (`SceneRenderer`,      │
└───────┬───────────┬─────────┘  Streams │  `TelemetryDashboard`) │
        │           │                    └────────────────────────┘
        │           │
 ┌──────▼─────┐ ┌────▼─────┐
 │ Dynamics   │ │ Pneumatic│
 │ Engine     │ │ Network  │
 │ (`RigidBody│ │ Solver   │
 │  Solver`)  │ │ (`PneuNet`)│
 └──────┬─────┘ └────┬─────┘
        │            │
 ┌──────▼────────┐ ┌─▼─────────┐
 │ Control Stack │ │ Sensors & │
 │ (`Controller`, │ │ Observers │
 │  `State Est.`) │ │ (`SignalBus`)│
 └──────┬────────┘ └───────────┘
        │                ▲
        └──────┬─────────┘
               │
        ┌──────▼─────────┐
        │ Data Services  │
        │ (`Settings`,   │
        │  `Recorder`,   │
        │  `ConfigIO`)   │
        └────────────────┘
```

### 2.1 Module Responsibilities
- **SimulationSession (src/simulation/session.py)**: configures the run, manages clocks, dispatches integration steps, synchronises subsystems, and exposes lifecycle hooks.
- **RigidBodySolver (src/simulation/dynamics.py)**: computes rigid-body kinematics of symmetric stabilizer arms including rotation, translation, and damped coupling between mirrored halves.
- **PneuNet (src/simulation/pneumatics.py)**: models compressible airflow, valve dynamics, accumulator behaviour, and actuator chambers.
- **Controller (src/control/controller.py)**: implements cascaded control (pressure -> force -> orientation) plus optional predictive feedforward.
- **StateEstimator (src/control/state_estimator.py)**: fuses sensor readings (pressure, flow, IMU) with a discrete-time Kalman filter.
- **SignalBus (src/diagnostics/signal_bus.py)**: central event bus for telemetry, logging, and observer callbacks.
- **SceneRenderer (src/visualization/renderer.py)**: orchestrates QtQuick3D scene updates using simulation state snapshots.
- **TelemetryDashboard (src/visualization/dashboard.py)**: produces charts, tables, and configurable overlays in the UI.

## 3. Physical Model Definition

### 3.1 Stabilizer Geometry & Symmetry
- Model as two mirrored gimballed arms connected via central hub.
- Coordinate frames:
  - Global inertial frame `G` (z up).
  - Hub frame `H` with orientation quaternion relative to `G`.
  - Arm frames `A_L`, `A_R` mirrored about hub x-axis; enforce symmetric constraints (angles equal magnitude, opposite sign where applicable).
- Geometric parameters stored in `config/stabilizer_geometry.json`; include:
  - Arm lengths, cross-sectional area, moment of inertia tensor.
  - Pivot offsets, bearing friction coefficients.
  - Chamber volumes (neutral, min, max) per arm.
  - Mass distribution (hub, arm root, distal mass).

### 3.2 Rigid-Body Dynamics
- Governing equations from Euler’s rotation dynamics:
  - `I * dω/dt + ω × (Iω) = τ_ext`
  - `dR/dt = 0.5 * Ω(ω) * R` with quaternion integration (normalized each step).
- External torques `τ_ext` derived from pneumatic actuator forces, aerodynamic disturbances, and damping.
- Constraints ensure `θ_L = f(θ_R)` as per symmetry; design must support configurable coupling (rigid, elastic, or partial via torsional spring).
- Numerical integration: semi-implicit Runge-Kutta 4/5 with adaptive time step; clamp to `dt_min = 0.1 ms`, `dt_max = 5 ms` for stability.
- Include gravity, static friction, viscous damping, and optional Coulomb friction.

### 3.3 Pneumatic Dynamics
- Model each chamber using ideal gas law with compressibility factor `Z(T, p)` (support toggling to unity).
- State variables per chamber:
  - Mass of air `m`
  - Temperature `T`
  - Pressure `p`
  - Volume `V(θ)` dependent on mechanical angle via lookup or polynomial fit.
- Mass flow through valves computed via ISO 6358 formula with choked flow detection.
- Include supply reservoir, return manifold, relief valves, check valves.
- Thermal model: use lumped-parameter energy balance `dT/dt = (γ-1)/m * (p dV/dt - hA(T - T_env))` with convective coefficient `h`.
- Leak model: configurable laminar leak path with conductance `C_leak`.

### 3.4 Force Coupling
- Convert chamber pressures to forces using effective piston area; map to torques through lever arms and moment arms dependent on angle.
- Account for mechanical stops with penalty forces and impact damping.
- Add cross-link compliance terms to simulate structural flex (tunable stiffness & damping matrices).

### 3.5 Disturbance Models
- Support deterministic scripted disturbances (e.g., step inputs) and stochastic gust model using Ornstein-Uhlenbeck process.
- Provide API for loading recorded disturbances from CSV or JSON.

## 4. Control & Automation Logic

### 4.1 Control Layers
1. **Supervisory planner**: sets desired hub orientation `R_d(t)` and pressure targets; handles mode switching (manual, semi-auto, autonomous).
2. **Attitude controller**: calculates required torques using LQR with gain scheduling based on arm angle.
3. **Force/pressure controllers**: PID + feedforward + disturbance observer to translate torque demands into chamber pressures.
4. **Valve command mapping**: solves constrained optimisation to allocate valve states (PWM duty cycles, spool positions) given actuator demands and supply limits.

### 4.2 State Estimation
- Sensors: chamber pressure transducers, flow sensors, IMU, accelerometers, gyros, temperature probes.
- Implement Extended Kalman Filter with configurable process/measurement noise covariance loaded from `config/sensor_models.json`.
- Provide fallback complementary filter for reduced computation mode.

### 4.3 Safety & Fault Handling
- Hard limits on pressure, temperature, angular displacement.
- Fault detection rules (threshold, rate-of-change, parity checks); escalate via `SignalBus` events.
- Emergency dump procedure to vent chambers and apply brakes.
- Logging of all safety events with root-cause metadata.

## 5. Simulation Execution Modes
- **Real-time mode**: integrates at wall-clock rate, synchronised with UI frame updates (target 120 Hz). Prioritize deterministic scheduling using asyncio event loop.
- **Accelerated mode**: decouple from wall-clock, run as fast as possible while storing timeline snapshots to disk.
- **Batch mode**: headless execution for scenario sweeps; integrate with CLI `python -m src.cli.run_batch`.
- **Hardware-in-the-loop (HIL)**: optional interface streaming via UDP or shared memory; must adhere to `protocols/hil.yaml` schema.

## 6. Data & Configuration Management
- All tunable parameters reside in JSON/YAML under `config/` with JSON Schema validation in `config/schemas/`.
- Provide migration scripts for schema changes (`tools/migrate_config.py`).
- Simulation session metadata recorded in `reports/sessions/YYYYMMDD-HHMMSS/` including:
  - `config_snapshot.json`
  - `telemetry.parquet`
  - `events.jsonl`
  - `render_frames/` (if captured).
- Support plugin architecture for custom parameter loaders via entry points `pneumostabsim.plugins`.

## 7. Visualization Requirements

### 7.1 3D Scene
- Built on QtQuick3D; leverage existing asset pipeline in `assets/meshes/`.
- Render hub, arms, pneumatic lines (with dynamic color-coded pressure levels), and control surfaces.
- Animations for valves (open/close), pressure gauges, and airflow particles (GPU instancing for efficiency).
- Camera presets: orthographic, perspective tracking, exploded view.
- Provide optional VR-compatible output (OpenXR) flagged via settings.

### 7.2 2D Dashboards
- Real-time plots using PyQtGraph embedded in Qt; include pressure, flow, angles, torques, temperature, safety margin.
- Configurable layouts saved per user in `config/ui_layouts/`.
- Alarm panel with severity color coding and audible cues.

### 7.3 Reporting
- Auto-generate PDF/HTML summaries after batch runs (use `reportlab` / `weasyprint`).
- Include charts, statistics (RMS error, overshoot, settling time), and parameter tables.

## 8. Software Design Requirements

### 8.1 Coding Standards
- Follow project-wide style (PEP 8 + `ruff` configuration); zero tolerance for lint errors.
- Use type hints; enforce via `mypy` strict mode on simulation modules.
- Implement docstrings for all public classes/methods referencing governing equations and assumptions.

### 8.2 Performance Targets
- Real-time mode must sustain 120 Hz on reference hardware (8-core CPU, 32 GB RAM).
- Memory footprint per session < 1 GB; telemetry ring buffer capped at 10 minutes.
- Multi-threaded architecture: use worker pool for heavy computations (pneumatic solver) with thread-safe state handoff.
- Provide benchmarking suite under `tests/performance/` with automated comparison to baselines stored in `reports/performance/`.

### 8.3 Extensibility
- Support additional actuator pairs by extending `ActuatorConfig`; symmetrical assumption should be toggleable.
- Provide plugin hooks for custom controllers (register via entry point and config mapping).
- Ensure modular decoupling so visualization can be replaced or disabled without affecting physics core.

## 9. Validation & Testing Strategy
- **Unit tests**: coverage for dynamics equations, pneumatic flow solver, controllers, estimators.
- **Integration tests**: scenario scripts verifying closed-loop responses (step, ramp, disturbance rejection).
- **Regression tests**: compare telemetry outputs to golden datasets; use `pytest` fixtures to load baseline `.parquet` files.
- **Physical plausibility checks**: enforce conservation laws (energy, mass), bounds (pressure limits), and symmetrical invariants.
- **Visualization tests**: snapshot testing of QtQuick3D renders (use headless rendering with reference images).
- **Continuous integration**: `make check` aggregator + nightly long-run tests triggered via GitHub Actions.

## 10. Documentation & Deliverables
- Developer guide updates: `docs/RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md` and `docs/RENOVATION_PHASE_5_STABILIZATION_PLAN.md` must reflect stabilizer emulator scope.
- Publish API reference using `mkdocs` (`docs/api/` generated by `mkdocs build`).
- Provide onboarding tutorials (notebook + video) in `docs/tutorials/`.
- Maintain change log entries for new simulator releases in `docs/CHANGELOG.md`.

## 11. Implementation Timeline (Suggested)
1. Environment setup & config schema extensions (Week 1).
2. Core dynamics + pneumatic solver (Weeks 2–4).
3. Control stack integration (Weeks 4–5).
4. Visualization build-out (Weeks 5–6).
5. Testing, validation, documentation (Weeks 6–7).
6. Performance tuning & HIL support (Week 8).

## 12. Acceptance Criteria
- Simulator reproduces benchmark manoeuvres within ±2% of reference torque/angle profiles.
- Real-time UI demonstrates synchronized visualization with <10 ms latency.
- Safety subsystem triggers on injected faults and transitions to safe state within 50 ms.
- Batch mode generates full reports and archives telemetry without manual steps.
- Codebase passes `make check`, integration tests, and achieves ≥90% unit test coverage on core modules.

