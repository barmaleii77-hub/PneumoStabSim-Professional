"""Mechanical component models used by the simulation core.

The original implementation exposed a number of placeholder classes that
returned hard coded values.  The runtime now relies on the real geometric
description that lives in :mod:`src.pneumo.geometry` and
``CylinderSpec``/:class:`~src.pneumo.cylinder.CylinderState`.  This module
provides small wrappers that translate lever angles into cylinder
displacements, compute spring and damper forces and evaluate pneumatic
forces from the actual chamber pressures.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Tuple

from src.pneumo.cylinder import CylinderSpec, CylinderState
from src.pneumo.geometry import LeverGeom, CylinderGeom


@dataclass
class Lever:
    """Lever kinematics based on the validated geometry definition."""

    lever_geom: LeverGeom
    cylinder_geom: CylinderGeom
    neutral_angle: float = 0.0

    def _cylinder_length(self, angle: float) -> float:
        """Return the distance between tail and rod joint for ``angle``."""

        rod_x, rod_y = self.lever_geom.rod_joint_pos(angle)
        rod_point = (0.0, rod_x, self.cylinder_geom.Z_axle + rod_y)
        tail_point = (0.0, self.cylinder_geom.Y_tail, self.cylinder_geom.Z_axle)
        return self.cylinder_geom.project_to_cyl_axis(tail_point, rod_point)

    def joint_position(self, angle: float) -> Tuple[float, float, float]:
        """Return the 3D coordinates of the rod joint for ``angle``."""

        rod_x, rod_y = self.lever_geom.rod_joint_pos(angle)
        return (0.0, rod_x, self.cylinder_geom.Z_axle + rod_y)

    def angle_to_displacement(self, angle: float) -> float:
        """Convert lever rotation to cylinder axis displacement."""

        current_length = self._cylinder_length(angle)
        neutral_length = self._cylinder_length(self.neutral_angle)
        return current_length - neutral_length

    def mechanical_advantage(self, angle: float, delta: float = 1e-4) -> float:
        """Return the instantaneous displacement/angle ratio.

        The derivative is estimated with a small symmetric difference which
        remains stable for the ranges enforced by the geometry validators.
        """

        disp_plus = self.angle_to_displacement(angle + delta)
        disp_minus = self.angle_to_displacement(angle - delta)
        return (disp_plus - disp_minus) / (2.0 * delta)


@dataclass
class Spring:
    """Linear spring model with configurable preload."""

    k: float = 50_000.0  # Spring constant (N/m)
    rest_length: float = 0.0
    preload: float = 0.0

    def force(self, length: float) -> float:
        """Return the restoring force for the current spring length."""

        extension = length - self.rest_length
        return -self.k * extension + self.preload

    def potential_energy(self, length: float) -> float:
        """Energy stored in the spring for convenience diagnostics."""

        extension = length - self.rest_length
        return 0.5 * self.k * extension * extension


@dataclass
class Damper:
    """Viscous damper resisting relative motion."""

    c: float = 2_000.0  # Damping coefficient (N*s/m)
    threshold: float = 0.0

    def force(self, velocity: float) -> float:
        """Return the damping force opposing ``velocity``."""

        raw = -self.c * velocity
        if abs(raw) < self.threshold:
            return 0.0
        return raw


@dataclass
class PneumaticCylinder:
    """Convenience wrapper exposing force and volume helpers."""

    spec: CylinderSpec
    state: CylinderState | None = None

    def __post_init__(self) -> None:  # pragma: no cover - simple guard
        if self.state is None:
            self.state = CylinderState(spec=self.spec)

    @property
    def geometry(self) -> CylinderGeom:
        return self.spec.geometry

    def clamp_position(self, x: float) -> float:
        """Clamp piston displacement to the physical travel."""

        half_travel = self.geometry.L_travel_max / 2.0
        return max(-half_travel, min(half_travel, x))

    def set_position(self, x: float) -> None:
        assert self.state is not None
        self.state.x = self.clamp_position(x)

    def volumes(self) -> Tuple[float, float]:
        """Return head/rod chamber volumes for the current position."""

        assert self.state is not None
        return self.state.vol_head(), self.state.vol_rod()

    def force(self, p_head: float, p_rod: float) -> float:
        """Compute the net pneumatic force produced by the cylinder."""

        geom = self.geometry
        area_head = geom.area_head(self.spec.is_front)
        area_rod = geom.area_rod(self.spec.is_front)
        return p_head * area_head - p_rod * area_rod


@dataclass
class DetailedLever(Lever):
    """Lever with inertia that can integrate applied torques."""

    moment_of_inertia: float = 1.0
    angular_velocity: float = 0.0
    applied_torque: float = 0.0

    def apply_force(self, force_magnitude: float, force_angle: float) -> None:
        """Store the torque produced by ``force_magnitude``."""

        lever_arm = self.lever_geom.L_lever * math.sin(force_angle - self.neutral_angle)
        self.applied_torque = force_magnitude * lever_arm

    def integrate(self, dt: float) -> None:
        """Advance the lever state using semi-implicit Euler integration."""

        if dt <= 0.0:
            return
        angular_accel = self.applied_torque / max(self.moment_of_inertia, 1e-6)
        self.angular_velocity += angular_accel * dt
        self.neutral_angle += self.angular_velocity * dt
        self.applied_torque = 0.0

    def compute_torque(self) -> float:
        return self.applied_torque


@dataclass
class DetailedSpring(Spring):
    """Spring with first order dynamics and viscous damping."""

    damping_coefficient: float = 0.0
    mass: float = 1.0
    position: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0

    def apply_force(self, external_force: float) -> None:
        spring_force = super().force(self.position)
        damping_force = -self.damping_coefficient * self.velocity
        net_force = external_force + spring_force + damping_force
        self.acceleration = net_force / max(self.mass, 1e-6)

    def update(self, time_step: float) -> None:
        if time_step <= 0.0:
            return
        self.velocity += self.acceleration * time_step
        self.position += self.velocity * time_step
        self.acceleration = 0.0

    def damping_force(self) -> float:
        return -self.damping_coefficient * self.velocity


@dataclass
class DetailedDamper(Damper):
    """Damper with explicit state integration."""

    mass: float = 1.0
    extension: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0

    def apply_force(self, external_force: float) -> None:
        damping = self.force(self.velocity)
        net_force = external_force + damping
        self.acceleration = net_force / max(self.mass, 1e-6)

    def update(self, time_step: float) -> None:
        if time_step <= 0.0:
            return
        self.velocity += self.acceleration * time_step
        self.extension += self.velocity * time_step
        self.acceleration = 0.0


@dataclass
class DetailedPneumaticCylinder(PneumaticCylinder):
    """Pneumatic cylinder with lumped mass and viscous losses."""

    damping_coefficient: float = 0.0
    mass: float = 1.0
    velocity: float = 0.0
    acceleration: float = 0.0

    def apply_force(self, p_head: float, p_rod: float) -> None:
        pneumatic = self.force(p_head, p_rod)
        damping = -self.damping_coefficient * self.velocity
        net_force = pneumatic + damping
        self.acceleration = net_force / max(self.mass, 1e-6)

    def update(self, time_step: float) -> None:
        if time_step <= 0.0:
            return
        self.velocity += self.acceleration * time_step
        assert self.state is not None
        new_position = self.state.x + self.velocity * time_step
        self.set_position(new_position)
        self.acceleration = 0.0

    def damping_force(self) -> float:
        return -self.damping_coefficient * self.velocity
