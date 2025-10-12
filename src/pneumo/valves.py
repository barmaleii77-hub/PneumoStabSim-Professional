"""
Valve components: check valves and relief valves
Boolean opening logic without flow calculations
"""

from dataclasses import dataclass
from typing import Optional
from .enums import CheckValveKind, ReliefValveKind
from .types import ValidationResult
from src.common.errors import ModelConfigError


@dataclass
class CheckValve:
    """Check valve with directional flow control"""
    kind: CheckValveKind
    delta_open_min: float  # Minimum pressure differential to open (Pa)
    d_eq: float           # Equivalent diameter for resistance (m)
    hyst: float          # Hysteresis/sensitivity (Pa)
    
    def __post_init__(self):
        if self.delta_open_min <= 0:
            raise ModelConfigError(f"Minimum opening pressure must be positive, got {self.delta_open_min}")
        if self.d_eq <= 0:
            raise ModelConfigError(f"Equivalent diameter must be positive, got {self.d_eq}")
        if self.hyst < 0:
            raise ModelConfigError(f"Hysteresis must be non-negative, got {self.hyst}")
    
    def is_open(self, p_upstream: float, p_downstream: float) -> bool:
        """Check if valve is open based on pressure differential
        
        Args:
            p_upstream: Upstream pressure (Pa)
            p_downstream: Downstream pressure (Pa)
            
        Returns:
            True if valve allows flow
        """
        delta_p = p_upstream - p_downstream
        
        if self.kind == CheckValveKind.ATMO_TO_LINE:
            # Opens when atmospheric pressure exceeds line pressure
            return delta_p >= self.delta_open_min
        elif self.kind == CheckValveKind.LINE_TO_TANK:
            # Opens when line pressure exceeds tank pressure  
            return delta_p >= self.delta_open_min
        else:
            return False
    
    def validate_invariants(self) -> ValidationResult:
        """Validate check valve parameters"""
        errors = []
        warnings = []
        
        try:
            self.__post_init__()
        except ModelConfigError as e:
            errors.append(str(e))
        
        # Warnings for unusual values
        if self.delta_open_min > 50000:  # > 0.5 bar
            warnings.append(f"Very high opening pressure: {self.delta_open_min} Pa")
        if self.d_eq > 0.1:  # > 10cm diameter  
            warnings.append(f"Very large equivalent diameter: {self.d_eq} m")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


@dataclass
class ReliefValve:
    """Relief valve for pressure control"""
    kind: ReliefValveKind
    p_set: float                    # Set pressure (Pa)
    hyst: float                     # Hysteresis (Pa)
    d_eq: Optional[float] = None    # Equivalent diameter (m), None for SAFETY valves
    
    def __post_init__(self):
        if self.p_set <= 0:
            raise ModelConfigError(f"Set pressure must be positive, got {self.p_set}")
        if self.hyst < 0:
            raise ModelConfigError(f"Hysteresis must be non-negative, got {self.hyst}")
        
        # Safety valves should not have throttling
        if self.kind == ReliefValveKind.SAFETY and self.d_eq is not None:
            raise ModelConfigError("SAFETY relief valves must not have throttling (d_eq should be None)")
        
        # Other valve types need diameter specification
        if self.kind != ReliefValveKind.SAFETY and (self.d_eq is None or self.d_eq <= 0):
            raise ModelConfigError(f"{self.kind} relief valves must have positive d_eq")
    
    def is_open(self, p_tank: float) -> bool:
        """Check if relief valve is open
        
        Args:
            p_tank: Tank/system pressure (Pa)
            
        Returns:
            True if valve is relieving pressure
        """
        if self.kind == ReliefValveKind.MIN_PRESS:
            # Opens when pressure falls below set point (to maintain minimum)
            return p_tank < (self.p_set - self.hyst)
        elif self.kind in [ReliefValveKind.STIFFNESS, ReliefValveKind.SAFETY]:
            # Opens when pressure exceeds set point
            return p_tank > (self.p_set + self.hyst)
        else:
            return False
    
    def validate_invariants(self) -> ValidationResult:
        """Validate relief valve parameters"""
        errors = []
        warnings = []
        
        try:
            self.__post_init__()
        except ModelConfigError as e:
            errors.append(str(e))
        
        # Warnings for unusual values
        if self.p_set > 2e6:  # > 20 bar
            warnings.append(f"Very high set pressure: {self.p_set} Pa")
        if self.hyst > self.p_set * 0.1:  # > 10% of set pressure
            warnings.append(f"Large hysteresis relative to set pressure: {self.hyst}/{self.p_set}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )