"""
Mass flow calculations through orifices, valves, and throttles
Handles both incompressible and compressible flow regimes
"""

import math
from ..common.units import R_AIR, GAMMA_AIR


def rho(p: float, T: float) -> float:
    """Calculate gas density from pressure and temperature
    
    Args:
        p: Pressure (Pa)
        T: Temperature (K)
        
    Returns:
        Density (kg/m?)
    """
    if p < 0:
        raise ValueError(f"Pressure cannot be negative: {p}")
    if T <= 0:
        raise ValueError(f"Temperature must be positive: {T}")
    
    return p / (R_AIR * T)


def area(d_eq: float) -> float:
    """Calculate area from equivalent diameter
    
    Args:
        d_eq: Equivalent diameter (m)
        
    Returns:
        Area (m?)
    """
    if d_eq < 0:
        raise ValueError(f"Diameter cannot be negative: {d_eq}")
    
    return math.pi * (d_eq / 2.0) ** 2


def is_choked_flow(p_up: float, p_down: float, gamma: float = GAMMA_AIR) -> bool:
    """Check if flow is choked (sonic)
    
    Args:
        p_up: Upstream pressure (Pa)
        p_down: Downstream pressure (Pa)
        gamma: Heat capacity ratio
        
    Returns:
        True if flow is choked
    """
    if p_up <= 0:
        return False
    
    # Critical pressure ratio for choked flow
    critical_ratio = (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))
    pressure_ratio = p_down / p_up
    
    return pressure_ratio <= critical_ratio


def mass_flow_incompressible(p_up: float, T_up: float, p_down: float, 
                            d_eq: float, C_d: float = 0.7) -> float:
    """Calculate mass flow using incompressible approximation
    
    Args:
        p_up: Upstream pressure (Pa)
        T_up: Upstream temperature (K)
        p_down: Downstream pressure (Pa)
        d_eq: Equivalent diameter (m)
        C_d: Discharge coefficient
        
    Returns:
        Mass flow rate (kg/s)
    """
    delta_p = max(p_up - p_down, 0.0)
    if delta_p <= 0:
        return 0.0
    
    rho_up = rho(p_up, T_up)
    v = math.sqrt(2.0 * delta_p / rho_up)
    A = area(d_eq)
    
    return C_d * rho_up * A * v


def mass_flow_choked(p_up: float, T_up: float, d_eq: float, 
                    C_d: float = 0.7, gamma: float = GAMMA_AIR) -> float:
    """Calculate choked (sonic) mass flow rate
    
    Args:
        p_up: Upstream pressure (Pa)
        T_up: Upstream temperature (K)
        d_eq: Equivalent diameter (m)
        C_d: Discharge coefficient
        gamma: Heat capacity ratio
        
    Returns:
        Mass flow rate (kg/s)
    """
    if p_up <= 0 or T_up <= 0:
        return 0.0
    
    A = area(d_eq)
    
    # Choked flow formula for ideal gas
    # m_dot = C_d * A * p_up * sqrt(gamma/(R*T_up)) * (2/(gamma+1))^((gamma+1)/(2*(gamma-1)))
    
    sqrt_term = math.sqrt(gamma / (R_AIR * T_up))
    power_term = (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
    
    return C_d * A * p_up * sqrt_term * power_term


def mass_flow_subsonic(p_up: float, T_up: float, p_down: float, 
                      d_eq: float, C_d: float = 0.7, gamma: float = GAMMA_AIR) -> float:
    """Calculate subsonic compressible mass flow rate
    
    Args:
        p_up: Upstream pressure (Pa)
        T_up: Upstream temperature (K)
        p_down: Downstream pressure (Pa)
        d_eq: Equivalent diameter (m)
        C_d: Discharge coefficient
        gamma: Heat capacity ratio
        
    Returns:
        Mass flow rate (kg/s)
    """
    if p_up <= 0 or T_up <= 0 or p_down >= p_up:
        return 0.0
    
    A = area(d_eq)
    pressure_ratio = p_down / p_up
    
    # Isentropic flow formula for subsonic compressible flow
    # m_dot = C_d * A * p_up * sqrt((2*gamma)/(R*T_up*(gamma-1))) * 
    #         sqrt((p_down/p_up)^(2/gamma) - (p_down/p_up)^((gamma+1)/gamma))
    
    sqrt_coeff = math.sqrt((2.0 * gamma) / (R_AIR * T_up * (gamma - 1.0)))
    
    term1 = pressure_ratio ** (2.0 / gamma)
    term2 = pressure_ratio ** ((gamma + 1.0) / gamma)
    
    if term1 <= term2:  # Avoid negative square root
        return 0.0
    
    sqrt_term = math.sqrt(term1 - term2)
    
    return C_d * A * p_up * sqrt_coeff * sqrt_term


def mass_flow_orifice(p_up: float, T_up: float, p_down: float, T_down: float,
                     d_eq: float, C_d: float = 0.7, gamma: float = GAMMA_AIR) -> float:
    """Calculate mass flow through orifice (high-level function)
    
    Automatically chooses appropriate flow regime (incompressible/choked/subsonic)
    
    Args:
        p_up: Upstream pressure (Pa)
        T_up: Upstream temperature (K)
        p_down: Downstream pressure (Pa)
        T_down: Downstream temperature (K) - not used in current implementation
        d_eq: Equivalent diameter (m)
        C_d: Discharge coefficient
        gamma: Heat capacity ratio
        
    Returns:
        Mass flow rate (kg/s) - always non-negative
    """
    # Validate inputs
    if p_up < 0 or p_down < 0 or T_up <= 0 or T_down <= 0 or d_eq < 0:
        return 0.0
    
    # No flow if downstream pressure is higher
    if p_down >= p_up:
        return 0.0
    
    # Check flow regime
    if is_choked_flow(p_up, p_down, gamma):
        # Choked flow
        return mass_flow_choked(p_up, T_up, d_eq, C_d, gamma)
    else:
        # Determine if compressible effects are significant
        pressure_ratio = p_down / p_up
        
        # Use compressible flow if pressure ratio < 0.9 (significant compression)
        if pressure_ratio < 0.9:
            return mass_flow_subsonic(p_up, T_up, p_down, d_eq, C_d, gamma)
        else:
            # Use incompressible approximation for small pressure drops
            return mass_flow_incompressible(p_up, T_up, p_down, d_eq, C_d)


def mass_flow_unlimited(p_tank: float, T_tank: float) -> float:
    """Calculate unlimited mass flow (for safety valve without throttling)
    
    This represents a very large orifice that can quickly reduce pressure
    to atmospheric levels.
    
    Args:
        p_tank: Tank pressure (Pa)
        T_tank: Tank temperature (K)
        
    Returns:
        Mass flow rate (kg/s)
    """
    from ..common.units import PA_ATM
    
    if p_tank <= PA_ATM or T_tank <= 0:
        return 0.0
    
    # Use a very large equivalent diameter (50mm) for unlimited flow
    d_eq_large = 0.05  # 50mm
    
    return mass_flow_orifice(p_tank, T_tank, PA_ATM, T_tank, d_eq_large, C_d=0.9)