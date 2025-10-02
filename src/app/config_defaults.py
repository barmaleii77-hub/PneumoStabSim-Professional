"""
Default configuration for pneumatic system
All values in SI units
"""

import math
from typing import Dict
from ..common.units import PA_ATM, T_AMBIENT, MIN_VOLUME_FRACTION
from ..pneumo.geometry import FrameGeom, LeverGeom, CylinderGeom
from ..pneumo.cylinder import CylinderSpec, CylinderState
from ..pneumo.valves import CheckValve, ReliefValve
from ..pneumo.receiver import ReceiverSpec, ReceiverState
from ..pneumo.gas_state import create_line_gas_state, create_tank_gas_state
from ..pneumo.network import GasNetwork
from ..pneumo.enums import (
    Wheel, Line, Port, CheckValveKind, ReliefValveKind, ReceiverVolumeMode, ThermoMode
)


def create_default_frame_geometry() -> FrameGeom:
    """Create default frame geometry"""
    return FrameGeom(
        L_wb=3.2  # 3.2m wheelbase - typical for medium vehicle
    )


def create_default_lever_geometry() -> LeverGeom:
    """Create default lever geometry"""
    return LeverGeom(
        L_lever=0.8,  # 80cm lever length
        rod_joint_frac=0.25,  # Rod attachment at 25% from hinge
        d_frame_to_lever_hinge=0.6  # 60cm from centerline to hinge
    )


def create_default_cylinder_geometry() -> CylinderGeom:
    """Create default cylinder geometry"""
    return CylinderGeom(
        # Cylinder bore dimensions
        D_in_front=0.08,   # 80mm bore front
        D_in_rear=0.08,    # 80mm bore rear
        D_out_front=0.12,  # 120mm outer diameter
        D_out_rear=0.12,   # 120mm outer diameter
        L_inner=0.25,      # 250mm internal length
        t_piston=0.02,     # 20mm piston thickness
        
        # Rod specifications
        D_rod=0.03,        # 30mm rod diameter
        link_rod_diameters_front_rear=True,  # Same rod diameter front/rear
        
        # Dead zones
        L_dead_head=0.01,  # 10mm head dead zone
        L_dead_rod=0.01,   # 10mm rod dead zone
        
        # Safety parameters
        residual_frac_min=MIN_VOLUME_FRACTION,
        
        # Position coordinates
        Y_tail=0.5,        # 50cm from centerline to cylinder tail
        Z_axle=0.4         # 40cm axle height
    )


def create_default_check_valve(kind: CheckValveKind) -> CheckValve:
    """Create default check valve configuration"""
    # Updated parameters for gas flow
    if kind == CheckValveKind.ATMO_TO_LINE:
        return CheckValve(
            kind=kind,
            delta_open_min=5000.0,   # 5000 Pa (50 mbar) for atmosphere to line
            d_eq=2.0e-3,             # 2mm equivalent diameter
            hyst=200.0               # 200 Pa hysteresis
        )
    elif kind == CheckValveKind.LINE_TO_TANK:
        return CheckValve(
            kind=kind,
            delta_open_min=10000.0,  # 10000 Pa (100 mbar) for line to tank
            d_eq=2.0e-3,             # 2mm equivalent diameter  
            hyst=200.0               # 200 Pa hysteresis
        )
    else:
        return CheckValve(
            kind=kind,
            delta_open_min=1000.0,   # Default 1000 Pa
            d_eq=2.0e-3,             # 2mm equivalent diameter
            hyst=200.0               # 200 Pa hysteresis
        )


def create_default_receiver() -> ReceiverState:
    """Create default receiver configuration"""
    spec = ReceiverSpec(
        V_min=0.0003,  # 0.3L minimum (reduced for gas simulation)
        V_max=0.0005   # 0.5L maximum
    )
    
    return ReceiverState(
        spec=spec,
        V=0.0005,     # 0.5L initial volume
        p=PA_ATM,     # Atmospheric pressure initially
        T=T_AMBIENT,  # Ambient temperature
        mode=ReceiverVolumeMode.NO_RECALC
    )


def create_default_relief_valves() -> Dict[ReliefValveKind, dict]:
    """Create default relief valve configurations"""
    return {
        ReliefValveKind.MIN_PRESS: {
            'valve': ReliefValve(
                kind=ReliefValveKind.MIN_PRESS,
                p_set=1.05 * PA_ATM,  # 5% above atmospheric
                hyst=1000.0,          # 1000 Pa hysteresis
                d_eq=1.0e-3          # 1mm throttle diameter
            )
        },
        ReliefValveKind.STIFFNESS: {
            'valve': ReliefValve(
                kind=ReliefValveKind.STIFFNESS,
                p_set=1.5 * PA_ATM,   # 50% above atmospheric
                hyst=2000.0,          # 2000 Pa hysteresis
                d_eq=1.0e-3          # 1mm throttle diameter
            )
        },
        ReliefValveKind.SAFETY: {
            'valve': ReliefValve(
                kind=ReliefValveKind.SAFETY,
                p_set=2.0 * PA_ATM,   # 100% above atmospheric
                hyst=5000.0,          # 5000 Pa hysteresis
                d_eq=None            # No throttling (unlimited flow)
            )
        }
    }


def create_default_system_configuration():
    """Create complete default system configuration"""
    
    # Geometry components
    frame_geom = create_default_frame_geometry()
    lever_geom = create_default_lever_geometry()
    cylinder_geom = create_default_cylinder_geometry()
    
    # Create cylinder specifications for each wheel
    cylinder_specs = {}
    for wheel in [Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ]:
        is_front = wheel in [Wheel.LP, Wheel.PP]
        cylinder_specs[wheel] = CylinderSpec(
            geometry=cylinder_geom,
            is_front=is_front,
            lever_geom=lever_geom
        )
    
    # Create line configurations
    line_configs = {}
    for line in [Line.A1, Line.B1, Line.A2, Line.B2]:
        line_configs[line] = {
            'cv_atmo': create_default_check_valve(CheckValveKind.ATMO_TO_LINE),
            'cv_tank': create_default_check_valve(CheckValveKind.LINE_TO_TANK),
            'p_line': PA_ATM  # Start at atmospheric pressure
        }
    
    # Create receiver
    receiver = create_default_receiver()
    
    return {
        'frame_geom': frame_geom,
        'lever_geom': lever_geom,
        'cylinder_geom': cylinder_geom,
        'cylinder_specs': cylinder_specs,
        'line_configs': line_configs,
        'receiver': receiver,
        'relief_valves': create_default_relief_valves(),
        'master_isolation_open': False
    }


def create_default_gas_network(system) -> GasNetwork:
    """Create default gas network from system configuration
    
    Args:
        system: PneumaticSystem instance
        
    Returns:
        Configured GasNetwork
    """
    # Calculate initial line volumes
    volumes = {}
    for line_name, line in system.lines.items():
        total_volume = 0.0
        for wheel, port in line.endpoints:
            cylinder = system.cylinders[wheel]
            if port == Port.HEAD:
                volume = cylinder.vol_head()
            else:
                volume = cylinder.vol_rod()
            total_volume += volume
        volumes[line_name] = total_volume
    
    # Create line gas states
    line_states = {}
    for line_name, volume in volumes.items():
        line_states[line_name] = create_line_gas_state(
            line_name, 
            p_initial=PA_ATM,
            T_initial=T_AMBIENT,
            V_initial=volume
        )
    
    # Create tank gas state
    tank_state = create_tank_gas_state(
        V_initial=0.0005,  # 0.5L
        p_initial=PA_ATM,
        T_initial=T_AMBIENT,
        mode=ReceiverVolumeMode.NO_RECALC
    )
    
    return GasNetwork(
        lines=line_states,
        tank=tank_state,
        system_ref=system,
        master_isolation_open=False
    )


def get_default_lever_angles():
    """Get default lever angles (all horizontal)"""
    return {
        Wheel.LP: 0.0,
        Wheel.PP: 0.0,
        Wheel.LZ: 0.0,
        Wheel.PZ: 0.0
    }


def get_default_gas_parameters():
    """Get default gas simulation parameters"""
    return {
        'dt': 0.005,  # 5ms time step
        'thermo_mode': ThermoMode.ISOTHERMAL,
        'log_interval': 0.1,  # Log every 100ms
        
        # Valve parameters
        'delta_open_min_atmo_to_line': 5000.0,   # Pa
        'delta_open_min_line_to_tank': 10000.0,  # Pa
        'd_eq_atmo_valve': 2.0e-3,               # m
        'd_eq_tank_valve': 2.0e-3,               # m
        
        # Relief valve thresholds  
        'p_min_threshold': 1.05 * PA_ATM,        # Pa
        'p_stiff_threshold': 1.5 * PA_ATM,       # Pa
        'p_safety_threshold': 2.0 * PA_ATM,      # Pa
        
        # Relief valve throttles
        'd_eq_min_bleed': 1.0e-3,                # m
        'd_eq_stiff_bleed': 1.0e-3,              # m
        # Safety valve has no throttle (unlimited flow)
    }


# Export key functions
__all__ = [
    'create_default_frame_geometry',
    'create_default_lever_geometry', 
    'create_default_cylinder_geometry',
    'create_default_check_valve',
    'create_default_receiver',
    'create_default_relief_valves',
    'create_default_system_configuration',
    'create_default_gas_network',
    'get_default_lever_angles',
    'get_default_gas_parameters'
]