# Pneumatic System Modules

## ?? Overview

**Modules:** 
- `src/pneumo/network.py` - Gas network simulation
- `src/pneumo/cylinder.py` - Cylinder gas chambers
- `src/pneumo/flow.py` - Valve flow calculations
- `src/pneumo/enums.py` - System enumerations

**Purpose:** Simulate pneumatic gas flow and pressure dynamics

**Status:** ? Fully Functional

---

## ?? Module Responsibilities

### **GasNetwork (`network.py`)**
- Manage 4 cylinders + 1 receiver tank
- Calculate pressure changes
- Apply valve flows
- Thermodynamic mode (isothermal/adiabatic)

### **Cylinder (`cylinder.py`)**
- Head/rod chamber pressures
- Volume from piston position
- Mass flow integration
- Temperature calculations

### **Flow (`flow.py`)**
- Valve mass flow rate
- Choked/unchoked flow
- Pressure ratio calculations
- ISO 6358 flow standard

### **Enums (`enums.py`)**
- `Wheel` - FL, FR, RL, RR
- `Line` - Supply, exhaust, cross-connect
- `ThermoMode` - ISOTHERMAL, ADIABATIC

---

## ?? Class Diagrams

### **GasNetwork**

```
???????????????????????????????????????????
?           GasNetwork                    ?
???????????????????????????????????????????
? - cylinders: Dict[Wheel, Cylinder]      ?
? - receiver: Receiver                    ?
? - valves: Dict[Line, Valve]            ?
? - thermo_mode: ThermoMode               ?
? - ambient_pressure: float               ?
? - ambient_temp: float                   ?
???????????????????????????????????????????
? + get_pressure(wheel, chamber) ? float ?
? + set_valve_position(line, pos)        ?
? + apply_flows(dt: float)               ?
? + get_state() ? dict                   ?
???????????????????????????????????????????
```

### **Cylinder**

```
???????????????????????????????????????????
?           Cylinder                      ?
???????????????????????????????????????????
? - head_pressure: float  # Pa            ?
? - rod_pressure: float   # Pa            ?
? - head_mass: float      # kg            ?
? - rod_mass: float       # kg            ?
? - piston_position: float # m            ?
? - bore_head: float      # m             ?
? - bore_rod: float       # m             ?
? - rod_diameter: float   # m             ?
? - stroke: float         # m             ?
???????????????????????????????????????????
? + get_head_volume() ? float            ?
? + get_rod_volume() ? float             ?
? + apply_mass_flow(dm_head, dm_rod, dt) ?
? + get_force() ? float                  ?
???????????????????????????????????????????
```

---

## ?? API Reference

### **GasNetwork**

```python
class GasNetwork:
    """Pneumatic gas network with 4 cylinders + receiver"""
    
    def __init__(self, config: dict):
        """Initialize gas network
        
        Args:
            config: Configuration dictionary
                {
                    'bore_head': 0.08,      # m
                    'bore_rod': 0.08,       # m
                    'rod_diameter': 0.035,  # m
                    'stroke': 0.25,         # m
                    'receiver_volume': 0.01, # m?
                    'initial_pressure': 600000, # Pa
                }
        """
        self.cylinders = {
            Wheel.FL: Cylinder(config),
            Wheel.FR: Cylinder(config),
            Wheel.RL: Cylinder(config),
            Wheel.RR: Cylinder(config)
        }
        self.receiver = Receiver(config['receiver_volume'])
        self.valves = self._create_valves()
    
    def get_pressure(
        self, 
        wheel: Wheel, 
        chamber: str
    ) -> float:
        """Get chamber pressure
        
        Args:
            wheel: Wheel identifier (FL, FR, RL, RR)
            chamber: 'head' or 'rod'
            
        Returns:
            Pressure in Pa
        """
        cylinder = self.cylinders[wheel]
        if chamber == 'head':
            return cylinder.head_pressure
        else:
            return cylinder.rod_pressure
    
    def set_valve_position(
        self,
        line: Line,
        position: float
    ):
        """Set valve opening position
        
        Args:
            line: Line identifier (SUPPLY, EXHAUST, etc.)
            position: 0.0 (closed) to 1.0 (fully open)
        """
        self.valves[line].position = np.clip(position, 0.0, 1.0)
    
    def apply_flows(self, dt: float):
        """Apply valve flows for one timestep
        
        Args:
            dt: Timestep in seconds
        """
        # Calculate all mass flows
        flows = self._calculate_all_flows()
        
        # Apply to each cylinder
        for wheel, cylinder in self.cylinders.items():
            dm_head = flows[wheel]['head']
            dm_rod = flows[wheel]['rod']
            cylinder.apply_mass_flow(dm_head, dm_rod, dt)
        
        # Apply to receiver
        dm_receiver = flows['receiver']
        self.receiver.apply_mass_flow(dm_receiver, dt)
```

### **Cylinder**

```python
class Cylinder:
    """Single pneumatic cylinder with head/rod chambers"""
    
    def __init__(self, config: dict):
        """Initialize cylinder
        
        Args:
            config: Cylinder configuration
        """
        self.bore_head = config['bore_head']
        self.bore_rod = config['bore_rod']
        self.rod_diameter = config['rod_diameter']
        self.stroke = config['stroke']
        
        # Initial state
        self.piston_position = self.stroke / 2.0  # Center
        self.head_pressure = config['initial_pressure']
        self.rod_pressure = config['initial_pressure']
        self.head_mass = self._calc_mass(
            self.head_pressure,
            self.get_head_volume()
        )
        self.rod_mass = self._calc_mass(
            self.rod_pressure,
            self.get_rod_volume()
        )
    
    def get_head_volume(self) -> float:
        """Calculate head chamber volume
        
        Returns:
            Volume in m?
        """
        area = np.pi * (self.bore_head / 2.0) ** 2
        return area * self.piston_position
    
    def get_rod_volume(self) -> float:
        """Calculate rod chamber volume
        
        Returns:
            Volume in m?
        """
        bore_area = np.pi * (self.bore_rod / 2.0) ** 2
        rod_area = np.pi * (self.rod_diameter / 2.0) ** 2
        effective_area = bore_area - rod_area
        return effective_area * (self.stroke - self.piston_position)
    
    def apply_mass_flow(
        self,
        dm_head: float,
        dm_rod: float,
        dt: float
    ):
        """Apply mass flows to chambers
        
        Args:
            dm_head: Mass flow to head (kg/s)
            dm_rod: Mass flow to rod (kg/s)
            dt: Timestep (s)
        """
        # Update masses
        self.head_mass += dm_head * dt
        self.rod_mass += dm_rod * dt
        
        # Recalculate pressures (ideal gas law)
        self.head_pressure = self._calc_pressure(
            self.head_mass,
            self.get_head_volume()
        )
        self.rod_pressure = self._calc_pressure(
            self.rod_mass,
            self.get_rod_volume()
        )
    
    def get_force(self) -> float:
        """Calculate net force on piston
        
        Returns:
            Force in N (positive = extension)
        """
        head_area = np.pi * (self.bore_head / 2.0) ** 2
        rod_area = np.pi * (self.rod_diameter / 2.0) ** 2
        rod_bore_area = np.pi * (self.bore_rod / 2.0) ** 2
        
        F_head = self.head_pressure * head_area
        F_rod = self.rod_pressure * (rod_bore_area - rod_area)
        
        return F_head - F_rod
```

### **Flow Calculations**

```python
def calculate_mass_flow(
    p_upstream: float,
    p_downstream: float,
    temp: float,
    Cv: float,
    position: float
) -> float:
    """Calculate mass flow through valve (ISO 6358)
    
    Args:
        p_upstream: Upstream pressure (Pa)
        p_downstream: Downstream pressure (Pa)
        temp: Temperature (K)
        Cv: Flow coefficient (m?/(s·bar))
        position: Valve position (0-1)
        
    Returns:
        Mass flow rate (kg/s)
    """
    if position <= 0.0:
        return 0.0
    
    # Pressure ratio
    ratio = p_downstream / p_upstream
    
    # Critical pressure ratio (for air, ~0.528)
    b = 0.528
    
    # Choked flow
    if ratio < b:
        # Sonic flow
        rho_ref = 1.185  # kg/m? at STP
        p_ref = 101325   # Pa
        T_ref = 293.15   # K
        
        rho = rho_ref * (p_upstream / p_ref) * (T_ref / temp)
        
        # ISO 6358 formula
        dm = 0.0404 * Cv * position * p_upstream * rho
        
    else:
        # Subsonic flow
        rho_ref = 1.185
        p_ref = 101325
        T_ref = 293.15
        
        rho = rho_ref * (p_upstream / p_ref) * (T_ref / temp)
        
        # ISO 6358 formula (subsonic)
        dm = 0.0404 * Cv * position * p_upstream * rho * np.sqrt(
            1 - ((ratio - b) / (1 - b)) ** 2
        )
    
    return dm
```

---

## ?? Thermodynamic Modes

### **Isothermal (Temperature Constant)**

```python
# Isothermal: PV = mRT (T constant)
def _calc_pressure_isothermal(self, mass: float, volume: float) -> float:
    """Calculate pressure (isothermal)"""
    R = 287.05  # J/(kg·K) for air
    T = self.ambient_temp  # K
    
    if volume < 1e-9:
        return self.ambient_pressure
    
    return (mass * R * T) / volume
```

### **Adiabatic (No Heat Transfer)**

```python
# Adiabatic: PV^? = const (? = 1.4 for air)
def _calc_pressure_adiabatic(
    self,
    mass: float,
    volume: float,
    prev_pressure: float,
    prev_volume: float
) -> float:
    """Calculate pressure (adiabatic)"""
    gamma = 1.4  # Heat capacity ratio
    
    if volume < 1e-9:
        return self.ambient_pressure
    
    # PV^? = const
    # P2 = P1 * (V1/V2)^?
    return prev_pressure * (prev_volume / volume) ** gamma
```

---

## ?? System Configuration

```python
DEFAULT_PNEUMATIC_CONFIG = {
    # Cylinder geometry
    'bore_head': 0.08,          # m (80mm)
    'bore_rod': 0.08,           # m (80mm)
    'rod_diameter': 0.035,      # m (35mm)
    'stroke': 0.25,             # m (250mm)
    
    # Gas properties
    'initial_pressure': 600000,  # Pa (6 bar)
    'ambient_pressure': 101325,  # Pa (1 bar)
    'ambient_temp': 293.15,      # K (20°C)
    
    # Receiver tank
    'receiver_volume': 0.01,     # m? (10 liters)
    
    # Valves (ISO 6358)
    'Cv_supply': 0.5,            # Flow coefficient
    'Cv_exhaust': 0.5,
    'Cv_cross': 0.3,
    
    # Thermodynamic mode
    'thermo_mode': ThermoMode.ISOTHERMAL
}
```

---

## ?? Example Usage

```python
from src.pneumo.network import GasNetwork
from src.pneumo.enums import Wheel, Line, ThermoMode

# Create gas network
config = {
    'bore_head': 0.08,
    'bore_rod': 0.08,
    'rod_diameter': 0.035,
    'stroke': 0.25,
    'receiver_volume': 0.01,
    'initial_pressure': 600000
}
network = GasNetwork(config)

# Set thermodynamic mode
network.set_thermo_mode(ThermoMode.ISOTHERMAL)

# Open supply valve to FL head
network.set_valve_position(Line.SUPPLY_FL_HEAD, 0.5)  # 50% open

# Simulate 1 second
dt = 0.001  # 1ms
for i in range(1000):
    network.apply_flows(dt)

# Get final pressure
p_head = network.get_pressure(Wheel.FL, 'head')
print(f"FL head pressure: {p_head / 1e5:.2f} bar")

# Get force
force = network.cylinders[Wheel.FL].get_force()
print(f"FL force: {force:.1f} N")
```

---

## ?? Valve Control Strategies

### **Simple On/Off**
```python
# Raise front
network.set_valve_position(Line.SUPPLY_FL_HEAD, 1.0)  # Open
network.set_valve_position(Line.EXHAUST_FL_ROD, 1.0)  # Open
```

### **Proportional Control**
```python
# Smooth leveling
error = target_height - current_height
position = pid_controller.update(error, dt)
network.set_valve_position(Line.SUPPLY_FL_HEAD, position)
```

### **Bang-Bang Control**
```python
if current_height < target_height:
    network.set_valve_position(Line.SUPPLY_FL_HEAD, 1.0)
else:
    network.set_valve_position(Line.EXHAUST_FL_HEAD, 1.0)
```

---

## ?? Test Coverage

**Test Files:**
- `tests/test_gas_network.py`
- `tests/test_cylinder.py`
- `tests/test_flow.py`

**Test Cases:**
1. ? Pressure calculations (isothermal)
2. ? Pressure calculations (adiabatic)
3. ? Mass flow (choked)
4. ? Mass flow (unchoked)
5. ? Force calculation
6. ? Volume calculations
7. ? Integration over time

**Coverage:** ~80%

---

## ?? References

- **ISO 6358:** Pneumatic fluid power — Flow coefficient
- **Ideal Gas Law:** PV = mRT
- **Adiabatic Process:** PV^? = constant
- **Choked Flow:** Sonic velocity limit

---

**Last Updated:** 2025-01-05  
**Module Version:** 2.0.0  
**Status:** Production Ready ?
