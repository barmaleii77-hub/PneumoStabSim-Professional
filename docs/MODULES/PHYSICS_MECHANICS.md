# Physics & Mechanics Modules

## ?? Overview

**Modules:**
- `src/mechanics/kinematics.py` - Cylinder kinematics
- `src/physics/odes.py` - ODE right-hand sides
- `src/physics/integrator.py` - Numerical integration
- `src/physics/forces.py` - Force calculations

**Purpose:** Calculate mechanical motion and integrate equations of motion

**Status:** ? Fully Functional

---

## ?? Module Responsibilities

### **CylinderKinematics (`kinematics.py`)**
- Calculate piston position from lever angle
- Calculate lever angle from piston position
- Constraint enforcement (stroke limits)
- Velocity/acceleration calculations

### **ODE System (`odes.py`)**
- Define f_rhs (right-hand side) for ODE
- State vector management
- Constraint forces
- System matrices

### **ODEIntegrator (`integrator.py`)**
- Wrap SciPy solve_ivp
- Adaptive timestep control
- Event detection
- Error handling

### **Forces (`forces.py`)**
- Pneumatic forces
- Spring forces
- Damper forces
- Gravity/inertia

---

## ?? Class Diagrams

### **CylinderKinematics**

```
???????????????????????????????????????????
?       CylinderKinematics                ?
???????????????????????????????????????????
? - lever_length: float                   ?
? - cylinder_length: float                ?
? - pivot_to_tail: float                  ?
? - stroke_min: float                     ?
? - stroke_max: float                     ?
???????????????????????????????????????????
? + angle_to_stroke(angle) ? float       ?
? + stroke_to_angle(stroke) ? float      ?
? + get_velocity(angle, omega) ? float   ?
? + enforce_limits(stroke) ? float       ?
???????????????????????????????????????????
```

### **ODEIntegrator**

```
???????????????????????????????????????????
?         ODEIntegrator                   ?
???????????????????????????????????????????
? - method: str ('Radau', 'RK45', 'BDF') ?
? - rtol: float (relative tolerance)     ?
? - atol: float (absolute tolerance)     ?
? - max_step: float                      ?
???????????????????????????????????????????
? + integrate(f_rhs, y0, t_span) ? sol  ?
? + step(dt) ? y_new                     ?
? + reset()                              ?
???????????????????????????????????????????
```

---

## ?? API Reference

### **CylinderKinematics**

```python
class CylinderKinematics:
    """Cylinder linkage kinematics calculations"""

    def __init__(
        self,
        lever_length: float,
        cylinder_length: float,
        pivot_to_tail: float
    ):
        """Initialize kinematics

        Args:
            lever_length: Lever arm length (m)
            cylinder_length: Cylinder body length (m)
            pivot_to_tail: Distance pivot to cylinder tail (m)
        """
        self.lever_length = lever_length
        self.cylinder_length = cylinder_length
        self.pivot_to_tail = pivot_to_tail

        # Calculate stroke limits
        self.stroke_max = self._calc_max_stroke()
        self.stroke_min = 0.0

    def angle_to_stroke(self, angle: float) -> float:
        """Calculate stroke from lever angle

        Args:
            angle: Lever angle in radians

        Returns:
            Piston stroke in meters
        """
        # Rod attachment point
        rod_x = self.lever_length * np.cos(angle)
        rod_y = self.lever_length * np.sin(angle)

        # Distance from tail to rod
        # (assuming pivot and tail on same horizontal)
        dx = rod_x - (-self.pivot_to_tail)
        dy = rod_y
        distance = np.sqrt(dx**2 + dy**2)

        # Baseline distance (angle = 0)
        baseline = self.lever_length + self.pivot_to_tail

        # Stroke is change in distance
        stroke = distance - baseline

        # Enforce limits
        return self.enforce_limits(stroke)

    def stroke_to_angle(self, stroke: float) -> float:
        """Calculate lever angle from stroke (inverse kinematics)

        Args:
            stroke: Piston stroke in meters

        Returns:
            Lever angle in radians
        """
        # Target distance
        baseline = self.lever_length + self.pivot_to_tail
        target_distance = baseline + stroke

        # Solve for angle (using law of cosines)
        # d? = L? + T? - 2LT·cos(?)
        # where d = target_distance, L = lever_length, T = pivot_to_tail

        L = self.lever_length
        T = self.pivot_to_tail
        d = target_distance

        cos_theta = (L**2 + T**2 - d**2) / (2 * L * T)
        cos_theta = np.clip(cos_theta, -1.0, 1.0)

        angle = np.arccos(cos_theta)
        return angle

    def get_velocity(
        self,
        angle: float,
        omega: float
    ) -> float:
        """Calculate piston velocity from lever angular velocity

        Args:
            angle: Lever angle (rad)
            omega: Angular velocity (rad/s)

        Returns:
            Piston velocity (m/s)
        """
        # Jacobian: ds/d?
        delta = 1e-6
        s1 = self.angle_to_stroke(angle)
        s2 = self.angle_to_stroke(angle + delta)
        jacobian = (s2 - s1) / delta

        # v = (ds/d?) * ?
        return jacobian * omega

    def enforce_limits(self, stroke: float) -> float:
        """Enforce stroke limits

        Args:
            stroke: Desired stroke (m)

        Returns:
            Limited stroke (m)
        """
        return np.clip(stroke, self.stroke_min, self.stroke_max)
```

### **ODE System**

```python
def f_rhs(t: float, y: np.ndarray, params: dict) -> np.ndarray:
    """Right-hand side of ODE system

    State vector y = [angles, angular_velocities]
    where:
        angles = [theta_fl, theta_fr, theta_rl, theta_rr]
        angular_velocities = [omega_fl, omega_fr, omega_rl, omega_rr]

    Args:
        t: Time (s)
        y: State vector (8 elements)
        params: System parameters

    Returns:
        dy/dt: State derivative vector
    """
    # Extract state
    angles = y[0:4]  # [fl, fr, rl, rr]
    omegas = y[4:8]

    # Get forces
    forces = calculate_forces(angles, omegas, params)

    # Calculate accelerations (? = I·?)
    alphas = forces / params['inertia']

    # Construct derivative
    dy = np.zeros(8)
    dy[0:4] = omegas  # d?/dt = ?
    dy[4:8] = alphas  # d?/dt = ?

    return dy

def calculate_forces(
    angles: np.ndarray,
    omegas: np.ndarray,
    params: dict
) -> np.ndarray:
    """Calculate torques on each lever

    Args:
        angles: Lever angles (rad)
        omegas: Angular velocities (rad/s)
        params: System parameters

    Returns:
        Torques (N·m) for each corner
    """
    torques = np.zeros(4)

    for i, (angle, omega) in enumerate(zip(angles, omegas)):
        # Pneumatic force
        F_pneumatic = get_pneumatic_force(i, angle, params)

        # Spring force
        F_spring = -params['k_spring'] * angle

        # Damper force
        F_damper = -params['c_damper'] * omega

        # Total force at rod attachment
        F_total = F_pneumatic + F_spring + F_damper

        # Torque = F ? r
        torques[i] = F_total * params['lever_length']

    return torques
```

### **ODEIntegrator**

```python
class ODEIntegrator:
    """Wrapper for SciPy ODE integration"""

    def __init__(
        self,
        method: str = 'Radau',
        rtol: float = 1e-6,
        atol: float = 1e-9
    ):
        """Initialize integrator

        Args:
            method: Integration method ('Radau', 'RK45', 'BDF')
            rtol: Relative tolerance
            atol: Absolute tolerance
        """
        self.method = method
        self.rtol = rtol
        self.atol = atol
        self.max_step = 0.01  # 10ms max step

        # Current state
        self.t = 0.0
        self.y = None

    def integrate(
        self,
        f_rhs: callable,
        y0: np.ndarray,
        t_span: tuple,
        params: dict
    ):
        """Integrate ODE system

        Args:
            f_rhs: Right-hand side function
            y0: Initial state vector
            t_span: (t_start, t_end)
            params: Parameters for f_rhs

        Returns:
            Solution object from solve_ivp
        """
        from scipy.integrate import solve_ivp

        sol = solve_ivp(
            fun=lambda t, y: f_rhs(t, y, params),
            t_span=t_span,
            y0=y0,
            method=self.method,
            rtol=self.rtol,
            atol=self.atol,
            max_step=self.max_step,
            dense_output=True
        )

        if not sol.success:
            raise RuntimeError(f"Integration failed: {sol.message}")

        return sol

    def step(
        self,
        f_rhs: callable,
        dt: float,
        params: dict
    ) -> np.ndarray:
        """Take single integration step

        Args:
            f_rhs: Right-hand side function
            dt: Timestep (s)
            params: Parameters

        Returns:
            New state vector
        """
        if self.y is None:
            raise RuntimeError("State not initialized")

        sol = self.integrate(
            f_rhs,
            self.y,
            (self.t, self.t + dt),
            params
        )

        # Update state
        self.t += dt
        self.y = sol.y[:, -1]

        return self.y
```

---

## ?? Integration Flow

```
Initial State y0 = [angles, omegas]
      ?
      ?
????????????????????????
?  ODEIntegrator.step  ?
?  (dt = 1ms)          ?
????????????????????????
           ?
           ?
????????????????????????
?   f_rhs(t, y)        ?
?   - Extract angles   ?
?   - Extract omegas   ?
????????????????????????
           ?
           ?
????????????????????????
?  calculate_forces()  ?
?  - Pneumatic         ?
?  - Spring            ?
?  - Damper            ?
????????????????????????
           ?
           ?
????????????????????????
?  Compute dy/dt       ?
?  d?/dt = ?           ?
?  d?/dt = ?/I         ?
????????????????????????
           ?
           ?
????????????????????????
?  solve_ivp           ?
?  (Radau method)      ?
????????????????????????
           ?
           ?
      y_new = y + dy·dt
```

---

## ?? Example Usage

```python
from src.mechanics.kinematics import CylinderKinematics
from src.physics.integrator import ODEIntegrator
from src.physics.odes import f_rhs
import numpy as np

# Create kinematics
kinematics = CylinderKinematics(
    lever_length=0.4,
    cylinder_length=0.25,
    pivot_to_tail=0.15
)

# Test angle ? stroke
angle = np.deg2rad(5.0)  # 5 degrees
stroke = kinematics.angle_to_stroke(angle)
print(f"Angle {np.rad2deg(angle)}° ? Stroke {stroke*1000:.1f}mm")

# Test stroke ? angle
angle_back = kinematics.stroke_to_angle(stroke)
print(f"Stroke {stroke*1000:.1f}mm ? Angle {np.rad2deg(angle_back):.1f}°")

# Create integrator
integrator = ODEIntegrator(method='Radau')

# Initial state (all at rest)
y0 = np.zeros(8)  # [angles, omegas]

# Parameters
params = {
    'lever_length': 0.4,
    'inertia': 0.01,
    'k_spring': 1000.0,
    'c_damper': 50.0
}

# Integrate 1 second
sol = integrator.integrate(
    f_rhs,
    y0,
    (0.0, 1.0),
    params
)

# Plot results
import matplotlib.pyplot as plt
plt.plot(sol.t, np.rad2deg(sol.y[0, :]))
plt.xlabel('Time (s)')
plt.ylabel('FL Angle (deg)')
plt.show()
```

---

## ?? Configuration

```python
DEFAULT_MECHANICS_CONFIG = {
    # Geometry
    'lever_length': 0.4,        # m
    'cylinder_length': 0.25,    # m
    'pivot_to_tail': 0.15,      # m

    # Inertia
    'lever_inertia': 0.01,      # kg·m?
    'mass_at_tip': 5.0,         # kg

    # Springs (optional)
    'k_spring': 0.0,            # N·m/rad (0 = disabled)
    'c_damper': 0.0,            # N·m·s/rad (0 = disabled)
}

DEFAULT_INTEGRATION_CONFIG = {
    'method': 'Radau',          # Stiff ODE solver
    'rtol': 1e-6,               # Relative tolerance
    'atol': 1e-9,               # Absolute tolerance
    'max_step': 0.01,           # 10ms max
}
```

---

## ?? Test Coverage

**Test Files:**
- `tests/test_kinematics.py`
- `tests/test_odes.py`
- `tests/test_integrator.py`

**Coverage:** ~85%

---

## ?? References

- **Kinematics:** Classical mechanics
- **ODE Integration:** [SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)
- **Radau Method:** Implicit Runge-Kutta for stiff systems

---

**Last Updated:** 2025-01-05
**Module Version:** 2.0.0
**Status:** Production Ready ?
