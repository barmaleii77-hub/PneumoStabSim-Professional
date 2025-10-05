# GeometryBridge Module

## ?? Overview

**Module:** `src/ui/geometry_bridge.py`

**Purpose:** Convert 2D mechanical kinematics to 3D visualization coordinates

**Status:** ? Fully Functional

---

## ?? Responsibilities

1. **2D ? 3D Coordinate Conversion**
   - Lever pivot points
   - Lever tip (rod attachment)
   - Piston position inside cylinder
   
2. **Kinematic Calculations**
   - Distance from pivot to cylinder tail
   - Piston position from lever angle
   - Volume calculations (head/rod chambers)

3. **Constraint Enforcement**
   - Rod length constant
   - Piston within cylinder bounds (10%-90%)
   - Physical limits checking

---

## ?? Class Diagram

```
???????????????????????????????????????????????
?          GeometryBridge                     ?
???????????????????????????????????????????????
? - _frame_config: FrameConfig                ?
? - _cylinder_body_length: float              ?
? - _lever_length: float                      ?
? - _rod_attachment_fraction: float           ?
???????????????????????????????????????????????
? + get_corner_3d_coords(corner, angle, cyl) ?
? + _calculate_piston_position(...)           ?
? + _calculate_volumes(...)                   ?
???????????????????????????????????????????????
```

---

## ?? API Reference

### **Main Method: `get_corner_3d_coords()`**

```python
def get_corner_3d_coords(
    self,
    corner: str,
    lever_angle: float,
    cylinder_state: Optional[CylinderState] = None
) -> Dict[str, Any]
```

**Parameters:**
- `corner` (str): Corner identifier ('fl', 'fr', 'rl', 'rr')
- `lever_angle` (float): Lever rotation angle in degrees
- `cylinder_state` (Optional[CylinderState]): Physics state (if available)

**Returns:**
```python
{
    'j_arm': [x, y, z],              # Lever pivot (mm)
    'j_tail': [x, y, z],             # Cylinder tail joint (mm)
    'j_rod': [x, y, z],              # Rod attachment point (mm)
    'pistonPositionMm': float,       # Piston position from cylinder start (mm)
    'headVolumeCm3': float,          # Head chamber volume (cm?)
    'rodVolumeCm3': float,           # Rod chamber volume (cm?)
}
```

---

## ?? Coordinate System

```
Y (vertical, up)
?
?     ???????????? U-Frame (red)
?     ?
?     ? j_arm (pivot)
?    /?\
?   / ? \ lever
?  /  ?  \
? /   ?   \
???????????????? Z (longitudinal)
j_tail  j_rod
```

**Origin:** Frame center, bottom beam

**Axes:**
- **X:** Transverse (left -150, right +150)
- **Y:** Vertical (0 = bottom beam, 650 = top beam)
- **Z:** Longitudinal (0 = front, 2000 = rear)

---

## ?? Key Calculations

### **1. Rod Attachment Point (j_rod)**

```python
# Lever length scaled by rod_attachment_fraction
rod_length = lever_length * rod_attachment_fraction

# Base angle depends on side (left=180°, right=0°)
base_angle = 180 if corner in ['fl', 'rl'] else 0
total_angle = base_angle + lever_angle

# Calculate j_rod position
j_rod = [
    j_arm[0] + rod_length * cos(total_angle),
    j_arm[1] + rod_length * sin(total_angle),
    j_arm[2]  # Same Z as j_arm
]
```

### **2. Piston Position (CRITICAL!)**

```python
# Distance from cylinder tail to rod attachment
tail_to_rod = distance(j_tail, j_rod)

# Baseline distance when lever is horizontal
base_dist = calculate_baseline_distance(corner)

# Change in distance
delta_dist = tail_to_rod - base_dist

# Piston position (center + delta)
# CORRECTED: Use PLUS (not minus!) for correct direction
piston_position = (cylinder_body_length / 2.0) + delta_dist

# Clip to safe range
piston_position = clip(piston_position, 
                       cylinder_body_length * 0.1,  # 10% minimum
                       cylinder_body_length * 0.9)  # 90% maximum
```

**WHY PLUS?**
- Lever rotates ? distance increases ? rod extends
- Rod extends ? piston moves TOWARD rod end (position increases)
- Same direction! Use `+` not `-`

### **3. Volume Calculations**

```python
# Piston splits cylinder into two chambers
head_volume = piston_position * bore_head_area * 1e-3  # mm? ? cm?
rod_volume = (cylinder_length - piston_position) * bore_rod_area * 1e-3
```

---

## ?? Example Usage

```python
from src.ui.geometry_bridge import create_geometry_converter

# Create converter with default geometry
bridge = create_geometry_converter()

# Get 3D coordinates for front-left corner
coords = bridge.get_corner_3d_coords(
    corner='fl',
    lever_angle=5.0,  # degrees
    cylinder_state=None  # Pure geometry, no physics
)

print(f"Piston position: {coords['pistonPositionMm']:.1f} mm")
print(f"Head volume: {coords['headVolumeCm3']:.1f} cm?")
```

**Output:**
```
Piston position: 143.5 mm
Head volume: 72.3 cm?
```

---

## ?? Known Issues & Fixes

### **Issue 1: Piston moved in OPPOSITE direction**
**Problem:** Used `piston = center - delta` (wrong sign!)

**Fix:** Changed to `piston = center + delta`

**Commit:** `34675d1` (2025-01-05)

### **Issue 2: Rod length changed during animation**
**Problem:** j_rod calculated OUTSIDE SuspensionCorner, duplicated angle application

**Fix:** Moved j_rod calculation INSIDE QML component

**Commit:** `4f12ab3` (2025-01-05)

---

## ?? Test Coverage

**Test File:** `test_geometry_bridge.py`

**Test Cases:**
1. ? Corner coordinate calculation
2. ? Piston position from lever angle
3. ? Volume calculations
4. ? Constraint enforcement
5. ? Baseline distance calculation

**Coverage:** ~85%

---

## ?? Dependencies

```python
import numpy as np
from typing import Dict, Optional, Any
from ..core.geometry import FrameConfig
from ..mechanics.kinematics import CylinderState
```

---

## ?? Configuration

```python
# Default geometry (SI units)
DEFAULT_GEOMETRY = {
    'wheelbase': 2.5,           # m
    'track_width': 0.3,         # m
    'lever_length': 0.4,        # m
    'cylinder_body_length': 0.25,  # m
    'rod_attachment': 0.6,      # fraction (0-1)
}
```

---

## ?? Future Enhancements

1. **Support for asymmetric geometry** (different left/right)
2. **Non-linear lever kinematics** (cam profiles)
3. **Multi-stage cylinders**
4. **Cached calculations** for performance

---

## ?? References

- **Lever Mechanics:** Classical mechanics (torque balance)
- **Pneumatic Cylinders:** ISO 6432 standard
- **Coordinate Systems:** Right-handed Cartesian

---

**Last Updated:** 2025-01-05
**Module Version:** 2.0.0
**Status:** Production Ready ?
