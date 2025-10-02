"""
Physics module for 3-DOF vehicle dynamics
"""

from .odes import RigidBody3DOF, f_rhs, create_initial_conditions, validate_state
from .forces import (
    compute_cylinder_force, compute_spring_force, compute_damper_force,
    project_forces_to_vertical_and_moments, compute_point_velocity_world
)
from .integrator import (
    step_dynamics, PhysicsLoop, PhysicsLoopConfig, 
    create_default_rigid_body, IntegrationResult
)

__all__ = [
    'RigidBody3DOF', 'f_rhs', 'create_initial_conditions', 'validate_state',
    'compute_cylinder_force', 'compute_spring_force', 'compute_damper_force',
    'project_forces_to_vertical_and_moments', 'compute_point_velocity_world',
    'step_dynamics', 'PhysicsLoop', 'PhysicsLoopConfig', 
    'create_default_rigid_body', 'IntegrationResult'
]