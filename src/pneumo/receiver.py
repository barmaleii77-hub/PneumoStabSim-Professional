"""Receiver specification and state
Handles volume changes with thermodynamic recalculation modes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from .enums import ReceiverVolumeMode
from .types import ValidationResult
from ..common.errors import ModelConfigError, ThermoError


class ReceiverVolumeUpdate(NamedTuple):
    """Summary of a receiver volume update."""

    volume: float
    pressure: float
    temperature: float
    mode: ReceiverVolumeMode


@dataclass
class ReceiverSpec:
    """Receiver tank specification"""

    V_min: float  # Minimum volume (m3)
    V_max: float  # Maximum volume (m3)

    def __post_init__(self) -> None:
        if self.V_min <= 0:
            raise ModelConfigError(f"Minimum volume must be positive, got {self.V_min}")
        if self.V_max <= self.V_min:
            raise ModelConfigError(
                f"Maximum volume {self.V_max} must be greater than minimum {self.V_min}"
            )

    def validate_invariants(self) -> ValidationResult:
        """Validate receiver specification"""
        errors: list[str] = []
        warnings: list[str] = []

        try:
            self.__post_init__()
        except ModelConfigError as e:
            errors.append(str(e))

        # Check for reasonable sizes
        if self.V_min < 1e-6:  # <1 cm3
            warnings.append(f"Very small minimum volume: {self.V_min} m3")
        if self.V_max > 1.0:  # >1000 L
            warnings.append(f"Very large maximum volume: {self.V_max} m3")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )


@dataclass
class ReceiverState:
    """Receiver state with thermodynamic properties"""

    spec: ReceiverSpec
    V: float  # Current volume (m3)
    p: float  # Current pressure (Pa)
    T: float  # Current temperature (K)
    mode: ReceiverVolumeMode  # Volume change handling mode

    # Thermodynamic constants for adiabatic processes
    _gamma: float = 1.4  # Heat capacity ratio for air

    def __post_init__(self) -> None:
        self._validate_state()

    def _validate_state(self) -> None:
        """Validate current state parameters"""
        if not (self.spec.V_min <= self.V <= self.spec.V_max):
            raise ModelConfigError(
                f"Volume {self.V} outside valid range [{self.spec.V_min}, {self.spec.V_max}]"
            )
        if self.p <= 0:
            raise ModelConfigError(f"Pressure must be positive, got {self.p}")
        if self.T <= 0:
            raise ModelConfigError(f"Temperature must be positive, got {self.T}")

    def apply_instant_volume_change(self, new_V: float) -> None:
        """Apply instantaneous volume change with appropriate thermodynamic recalculation

        Args:
            new_V: New volume (m3)
        """
        if not (self.spec.V_min <= new_V <= self.spec.V_max):
            raise ThermoError(
                f"New volume {new_V} outside valid range [{self.spec.V_min}, {self.spec.V_max}]"
            )

        old_V = self.V

        if self.mode == ReceiverVolumeMode.NO_RECALC:
            # Simply change volume, keep p and T constant
            self.V = new_V

        elif self.mode == ReceiverVolumeMode.ADIABATIC_RECALC:
            # Adiabatic process: p*V^gamma = const, T*V^(gamma-1) = const
            if abs(old_V) < 1e-12:
                raise ThermoError(
                    "Cannot perform adiabatic recalculation from zero volume"
                )

            # Calculate new pressure and temperature
            volume_ratio = new_V / old_V
            gamma = self._gamma

            # Adiabatic relations
            new_p = self.p * (volume_ratio ** (-gamma))
            new_T = self.T * (volume_ratio ** (-(gamma - 1)))

            # Update state
            self.V = new_V
            self.p = new_p
            self.T = new_T

        else:
            raise ThermoError(f"Unknown receiver volume mode: {self.mode}")

    def set_volume(
        self,
        new_volume: float,
        mode: ReceiverVolumeMode | str | None = None,
        recompute: bool = True,
    ) -> ReceiverVolumeUpdate:
        """Set the receiver volume with optional mode switching.

        Args:
            new_volume: Target receiver volume in cubic metres.
            mode: Optional new recalculation mode. Either ``ReceiverVolumeMode`` or
                a case-insensitive string token.
            recompute: When ``True`` the state is recalculated using the configured
                thermodynamic mode. When ``False`` only the volume is updated.
        Returns:
            ReceiverVolumeUpdate: A tuple describing the resulting receiver
                state after the update.
        """

        resolved_mode: ReceiverVolumeMode
        if mode is None:
            resolved_mode = self.mode
        elif isinstance(mode, ReceiverVolumeMode):
            resolved_mode = mode
        else:
            token = str(mode).strip().upper()
            alias_map = {
                "MANUAL": ReceiverVolumeMode.NO_RECALC,
                "GEOMETRIC": ReceiverVolumeMode.ADIABATIC_RECALC,
                ReceiverVolumeMode.NO_RECALC.name: ReceiverVolumeMode.NO_RECALC,
                ReceiverVolumeMode.ADIABATIC_RECALC.name: ReceiverVolumeMode.ADIABATIC_RECALC,
                ReceiverVolumeMode.NO_RECALC.value: ReceiverVolumeMode.NO_RECALC,
                ReceiverVolumeMode.ADIABATIC_RECALC.value: ReceiverVolumeMode.ADIABATIC_RECALC,
            }
            try:
                resolved_mode = alias_map[token]
            except KeyError as exc:  # pragma: no cover - defensive guard
                raise ThermoError(f"Unknown receiver volume mode: {mode}") from exc

        self.mode = resolved_mode

        if recompute:
            self.apply_instant_volume_change(new_volume)
        else:
            if not (self.spec.V_min <= new_volume <= self.spec.V_max):
                raise ModelConfigError(
                    "Volume {0} outside valid range [{1}, {2}]".format(
                        new_volume, self.spec.V_min, self.spec.V_max
                    )
                )
            self.V = new_volume

        return ReceiverVolumeUpdate(
            volume=self.V,
            pressure=self.p,
            temperature=self.T,
            mode=self.mode,
        )

    def validate_invariants(self) -> ValidationResult:
        """Validate receiver state invariants"""
        errors: list[str] = []
        warnings: list[str] = []

        # Validate specification
        spec_result = self.spec.validate_invariants()
        errors.extend(spec_result["errors"])
        warnings.extend(spec_result["warnings"])

        # Validate current state
        try:
            self._validate_state()
        except ModelConfigError as e:
            errors.append(str(e))

        # Physical reasonableness checks
        if self.p > 1e7:  # >100 bar
            warnings.append(f"Very high pressure: {self.p} Pa")
        if self.T < 200 or self.T > 400:  # Rough operational temperature range
            warnings.append(f"Temperature outside normal range: {self.T} K")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
