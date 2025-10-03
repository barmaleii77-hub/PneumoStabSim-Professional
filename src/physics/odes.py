"""
3-DOF rigid body dynamics for vehicle frame
Handles heave (Y), roll (phi_z), and pitch (theta_x) motion with suspension forces
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any
import logging

# Coordinate system: X-lateral (left/right), Y-vertical (down positive), Z-longitudinal


@dataclass
class RigidBody3DOF:
    """3-DOF rigid body parameters and geometry"""
    M: float                    # Total mass (kg)
    Ix: float                   # Moment of inertia around X-axis (pitch) (kg*m^2)
    Iz: float                   # Moment of inertia around Z-axis (roll) (kg*m^2)
    g: float = 9.81            # Gravitational acceleration (m/s^2)
    
    # Suspension attachment points in body frame (x_i, z_i)
    # y-coordinate taken as current heave
    attachment_points: Dict[str, Tuple[float, float]] = None  # wheel_name -> (x, z)
    
    # Vehicle dimensions for reference
    track: float = 1.6         # Track width (m)
    wheelbase: float = 3.2     # Wheelbase (m)
    
    # Numerical stability
    angle_limit: float = 0.5   # Maximum angle in radians (~28.6 degrees)
    damping_coefficient: float = 0.1  # Viscous damping on angles
    
    def __post_init__(self):
        """Initialize default attachment points if not provided"""
        if self.attachment_points is None:
            # Standard 4-wheel layout: front/rear x half track, +/- half wheelbase
            half_track = self.track / 2.0
            half_wheelbase = self.wheelbase / 2.0
            
            self.attachment_points = {
                'LP': (-half_track, -half_wheelbase),  # Left front (negative X, negative Z)
                'PP': (+half_track, -half_wheelbase),  # Right front
                'LZ': (-half_track, +half_wheelbase),  # Left rear
                'PZ': (+half_track, +half_wheelbase)   # Right rear
            }


@dataclass
class SuspensionPointState:
    """State of a single suspension point"""
    wheel_name: str                    # Wheel identifier
    axis_unit_world: np.ndarray        # Unit vector of cylinder axis in world coords (3,)
    F_cyl_axis: float                  # Pneumatic cylinder force along axis (N)
    Fs_axis: float                     # Spring force along axis (N)
    Fd_axis: float                     # Damper force along axis (N)
    lever_arm_local: np.ndarray        # Position vector in body frame (3,) -> (x, 0, z)
    
    def __post_init__(self):
        """Validate arrays"""
        self.axis_unit_world = np.asarray(self.axis_unit_world, dtype=float)
        self.lever_arm_local = np.asarray(self.lever_arm_local, dtype=float)
        
        if self.axis_unit_world.shape != (3,):
            raise ValueError(f"axis_unit_world must be shape (3,), got {self.axis_unit_world.shape}")
        if self.lever_arm_local.shape != (3,):
            raise ValueError(f"lever_arm_local must be shape (3,), got {self.lever_arm_local.shape}")


def axis_vertical_projection(F_axis: float, axis_unit_world: np.ndarray) -> float:
    """Calculate vertical component of axial force
    
    Args:
        F_axis: Force magnitude along cylinder axis (N) 
        axis_unit_world: Unit vector of axis in world coordinates
        
    Returns:
        Vertical force component (N, positive downward)
    """
    eY = np.array([0.0, 1.0, 0.0])  # Vertical axis (down positive)
    return np.dot(axis_unit_world, eY) * F_axis


def assemble_forces(system: Any, gas: Any, y: np.ndarray, 
                   params: RigidBody3DOF) -> Tuple[np.ndarray, float, float]:
    """Assemble forces and moments from suspension system
    
    Args:
        system: Pneumatic system (provides geometry, cylinder states)
        gas: Gas network (provides pressures)
        y: State vector [Y, phi_z, theta_x, dY, dphi_z, dtheta_x]
        params: Rigid body parameters
        
    Returns:
        Tuple of (vertical_forces[4], tau_x, tau_z)
        vertical_forces: Force at each wheel (N, positive down)
        tau_x: Moment around X-axis (pitch) (N*m)
        tau_z: Moment around Z-axis (roll) (N*m)
    """
    Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y
    
    # TODO: Get cylinder pressures from gas network
    # For now, use placeholder values
    wheel_names = ['LP', 'PP', 'LZ', 'PZ']  # Left Front, Right Front, Left Rear, Right Rear
    vertical_forces = np.zeros(4)
    
    # Placeholder: Calculate forces at each wheel
    for i, wheel_name in enumerate(wheel_names):
        # Get attachment point
        if wheel_name in params.attachment_points:
            x_i, z_i = params.attachment_points[wheel_name]
        else:
            # Default positions if not specified
            x_i = (-1.0 if 'L' in wheel_name else 1.0) * params.track / 2.0
            z_i = (-1.0 if 'P' in wheel_name else 1.0) * params.wheelbase / 2.0
        
        # TODO: Get actual cylinder axis from system geometry
        # Placeholder: vertical axis for now
        axis_unit = np.array([0.0, 1.0, 0.0])
        
        # TODO: Calculate pneumatic cylinder force
        # F_cyl = (p_head * A_head) - (p_rod * (A_head - A_rod))
        F_cyl_axis = 0.0  # Placeholder
        
        # TODO: Calculate spring force (one-sided compression)
        # F_spring = k * max(0, x0 - x)
        F_spring_axis = 0.0  # Placeholder
        
        # TODO: Calculate damper force (linear with velocity)
        # F_damper = c * v_axis
        F_damper_axis = 0.0  # Placeholder
        
        # Total axial force
        F_total_axis = F_cyl_axis + F_spring_axis + F_damper_axis
        
        # Project to vertical component
        F_vertical = axis_vertical_projection(F_total_axis, axis_unit)
        vertical_forces[i] = F_vertical
    
    # Calculate moments about center of mass
    tau_x = 0.0  # Pitch moment
    tau_z = 0.0  # Roll moment
    
    for i, wheel_name in enumerate(wheel_names):
        if wheel_name in params.attachment_points:
            x_i, z_i = params.attachment_points[wheel_name]
            
            # Moment arms for pitch (about X-axis) and roll (about Z-axis)
            tau_x += vertical_forces[i] * z_i  # Pitch: force x longitudinal arm
            tau_z += vertical_forces[i] * x_i  # Roll: force x lateral arm
    
    return vertical_forces, tau_x, tau_z


def f_rhs(t: float, y: np.ndarray, params: RigidBody3DOF, 
          system: Any, gas: Any) -> np.ndarray:
    """Right-hand side of 3-DOF ODE system
    
    State vector: y = [Y, phi_z, theta_x, dY, dphi_z, dtheta_x]
    
    Args:
        t: Time (s)
        y: State vector [position; velocity]
        params: Rigid body parameters
        system: Pneumatic system
        gas: Gas network
        
    Returns:
        Derivative vector dy/dt
    """
    # Unpack state
    Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y
    
    # Clamp angles to prevent numerical issues
    phi_z = np.clip(phi_z, -params.angle_limit, params.angle_limit)
    theta_x = np.clip(theta_x, -params.angle_limit, params.angle_limit)
    
    # Get suspension forces
    vertical_forces, tau_x, tau_z = assemble_forces(system, gas, y, params)
    
    # Gravitational force (positive downward)
    F_gravity = params.M * params.g
    
    # Sum of vertical forces from suspension
    F_suspension_total = np.sum(vertical_forces)
    
    # Equations of motion
    # Heave: vertical acceleration
    d2Y = (F_gravity + F_suspension_total) / params.M
    
    # Roll: angular acceleration about Z-axis
    d2phi_z = tau_z / params.Iz - params.damping_coefficient * dphi_z
    
    # Pitch: angular acceleration about X-axis  
    d2theta_x = tau_x / params.Ix - params.damping_coefficient * dtheta_x
    
    # Return derivative vector [velocity; acceleration]
    return np.array([dY, dphi_z, dtheta_x, d2Y, d2phi_z, d2theta_x])


def create_initial_conditions(heave: float = 0.0, roll: float = 0.0, pitch: float = 0.0,
                             heave_rate: float = 0.0, roll_rate: float = 0.0, 
                             pitch_rate: float = 0.0) -> np.ndarray:
    """Create initial condition vector
    
    Args:
        heave: Initial vertical position (m, positive down)
        roll: Initial roll angle (rad)
        pitch: Initial pitch angle (rad)
        heave_rate: Initial vertical velocity (m/s)
        roll_rate: Initial roll rate (rad/s)
        pitch_rate: Initial pitch rate (rad/s)
        
    Returns:
        Initial state vector y0
    """
    return np.array([heave, roll, pitch, heave_rate, roll_rate, pitch_rate])


def validate_state(y: np.ndarray, params: RigidBody3DOF) -> Tuple[bool, str]:
    """Validate state vector for physical reasonableness
    
    Args:
        y: State vector
        params: System parameters
        
    Returns:
        (is_valid, error_message)
    """
    if len(y) != 6:
        return False, f"State vector must have 6 elements, got {len(y)}"
    
    Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y
    
    # Check for NaN/inf
    if not np.all(np.isfinite(y)):
        return False, "State contains NaN or infinite values"
    
    # Check angle limits
    if abs(phi_z) > params.angle_limit:
        return False, f"Roll angle {phi_z:.3f} exceeds limit +/-{params.angle_limit:.3f}"
    
    if abs(theta_x) > params.angle_limit:
        return False, f"Pitch angle {theta_x:.3f} exceeds limit +/-{params.angle_limit:.3f}"
    
    # Check reasonable velocity limits (100 m/s, 50 rad/s)
    if abs(dY) > 100.0:
        return False, f"Heave velocity {dY:.3f} m/s is unreasonable"
    
    if abs(dphi_z) > 50.0:
        return False, f"Roll rate {dphi_z:.3f} rad/s is unreasonable"
    
    if abs(dtheta_x) > 50.0:
        return False, f"Pitch rate {dtheta_x:.3f} rad/s is unreasonable"
    
    return True, ""


# Legacy API compatibility
def rigid_body_3dof_ode(t: float, y: np.ndarray, params: RigidBody3DOF,
                       system: Any = None, gas: Any = None) -> np.ndarray:
    """Legacy wrapper for f_rhs
    
    This function provides backward compatibility with tests that use the old API.
    
    Args:
        t: Time (s)
        y: State vector [Y, phi_z, theta_x, dY, dphi_z, dtheta_x]
        params: Rigid body parameters
        system: Pneumatic system (optional)
        gas: Gas network (optional)
        
    Returns:
        Derivative vector dy/dt
    """
    return f_rhs(t, y, params, system, gas)


__all__ = [
    'RigidBody3DOF',
    'SuspensionPointState',
    'axis_vertical_projection',
    'assemble_forces',
    'f_rhs',
    'rigid_body_3dof_ode',  # Legacy API
    'create_initial_conditions',
    'validate_state',
]