# Road System Module

## ?? Overview

**Modules:**
- `src/road/engine.py` - Road input generator
- `src/road/generators.py` - Signal generators
- `src/road/csv_io.py` - CSV file loading
- `src/road/scenarios.py` - Predefined scenarios

**Purpose:** Generate road excitation inputs for suspension simulation

**Status:** ? Fully Functional

---

## ?? Module Responsibilities

### **RoadInput (`engine.py`)**
- Generate time-varying road elevation
- Support multiple signal types
- Per-wheel independent inputs
- CSV profile playback

### **Generators (`generators.py`)**
- Sine wave generator
- Step input generator
- Ramp generator
- Random noise generator
- Swept sine generator

### **CSV IO (`csv_io.py`)**
- Load road profiles from CSV
- Interpolation
- Validation
- Caching

### **Scenarios (`scenarios.py`)**
- Belgian paving
- Pothole
- Speed bump
- Smooth road
- Custom scenarios

---

## Settings & UI integration

- Road profile selection is exposed in `qml/SimulationPanel.qml` via a drop-down backed by
  `current.modes.road_profile` with presets (`smooth_highway`, `city_streets`, `off_road`,
  `mountain_serpentine`) and a dedicated **Custom** option.
- When **Custom** is chosen, the adjacent path field writes to
  `current.modes.custom_profile_path` through `SettingsManager`, keeping presets and user
  inputs in sync across sessions.
- Interference checks and kinematic spring/damper toggles from the same panel persist under
  `current.modes.check_interference` and `current.modes.physics.*`, allowing the road profile
  selector to reflect the full simulation context when a session is restored.


## ?? Class Diagram

```
???????????????????????????????????????????
?           RoadInput                     ?
???????????????????????????????????????????
? - profiles: Dict[Wheel, RoadProfile]    ?
? - mode: str ('sine', 'csv', 'scenario') ?
? - parameters: dict                      ?
???????????????????????????????????????????
? + get_wheel_excitation(t) ? dict       ?
? + set_sine_profile(params)             ?
? + load_csv_profile(path, wheel)        ?
? + set_scenario(name)                   ?
? + reset()                              ?
???????????????????????????????????????????
         ?
         ? uses
         ?
???????????????????????????????????????????
?         SignalGenerator                 ?
???????????????????????????????????????????
? + sine(t, A, f, phi) ? float           ?
? + step(t, t_step, amplitude) ? float   ?
? + ramp(t, slope) ? float               ?
? + noise(t, amplitude, seed) ? float    ?
? + swept_sine(t, f0, f1, T) ? float     ?
???????????????????????????????????????????
```

---

## ?? API Reference

### **RoadInput**

```python
class RoadInput:
    """Road elevation input generator"""

    def __init__(self):
        """Initialize road input system"""
        self.profiles = {
            Wheel.FL: None,
            Wheel.FR: None,
            Wheel.RL: None,
            Wheel.RR: None
        }
        self.mode = 'sine'
        self.parameters = {}

    def get_wheel_excitation(self, t: float) -> dict:
        """Get road elevation for all wheels at time t

        Args:
            t: Time in seconds

        Returns:
            Dictionary with elevations:
            {
                'fl': 0.05,  # m
                'fr': 0.03,
                'rl': 0.02,
                'rr': 0.04
            }
        """
        excitations = {}

        for wheel in [Wheel.FL, Wheel.FR, Wheel.RL, Wheel.RR]:
            if self.profiles[wheel]:
                excitations[wheel.name.lower()] = self.profiles[wheel].get_elevation(t)
            else:
                excitations[wheel.name.lower()] = 0.0

        return excitations

    def set_sine_profile(
        self,
        amplitude: float = 0.05,
        frequency: float = 1.0,
        phase: float = 0.0,
        wheels: List[Wheel] = None
    ):
        """Set sine wave profile for wheels

        Args:
            amplitude: Amplitude in meters
            frequency: Frequency in Hz
            phase: Phase offset in degrees
            wheels: List of wheels (None = all wheels)
        """
        if wheels is None:
            wheels = list(Wheel)

        for wheel in wheels:
            self.profiles[wheel] = SineProfile(
                amplitude, frequency, phase
            )

    def load_csv_profile(
        self,
        file_path: str,
        wheels: List[Wheel] = None
    ):
        """Load road profile from CSV file

        Args:
            file_path: Path to CSV file
            wheels: List of wheels to apply to

        CSV Format:
            time,elevation
            0.0,0.0
            0.1,0.005
            0.2,0.010
            ...
        """
        if wheels is None:
            wheels = list(Wheel)

        # Load CSV data
        data = load_csv_road_profile(file_path)

        for wheel in wheels:
            self.profiles[wheel] = CSVProfile(data)

    def set_scenario(self, scenario_name: str):
        """Load predefined scenario

        Args:
            scenario_name: 'belgian_paving', 'pothole',
                          'speed_bump', 'smooth'
        """
        scenario = SCENARIOS[scenario_name]

        if scenario['type'] == 'csv':
            self.load_csv_profile(scenario['file'])
        elif scenario['type'] == 'sine':
            self.set_sine_profile(**scenario['params'])
        elif scenario['type'] == 'step':
            self.set_step_profile(**scenario['params'])
```

### **Signal Generators**

```python
class SignalGenerator:
    """Collection of signal generation functions"""

    @staticmethod
    def sine(
        t: float,
        amplitude: float,
        frequency: float,
        phase: float = 0.0
    ) -> float:
        """Generate sine wave

        Args:
            t: Time (s)
            amplitude: Amplitude (m)
            frequency: Frequency (Hz)
            phase: Phase offset (degrees)

        Returns:
            Elevation (m)
        """
        omega = 2 * np.pi * frequency
        phi = np.deg2rad(phase)
        return amplitude * np.sin(omega * t + phi)

    @staticmethod
    def step(
        t: float,
        t_step: float,
        amplitude: float
    ) -> float:
        """Generate step input

        Args:
            t: Time (s)
            t_step: Step time (s)
            amplitude: Step height (m)

        Returns:
            Elevation (m)
        """
        return amplitude if t >= t_step else 0.0

    @staticmethod
    def ramp(
        t: float,
        slope: float
    ) -> float:
        """Generate ramp input

        Args:
            t: Time (s)
            slope: Ramp slope (m/s)

        Returns:
            Elevation (m)
        """
        return slope * t

    @staticmethod
    def noise(
        t: float,
        amplitude: float,
        seed: int = 42
    ) -> float:
        """Generate random noise

        Args:
            t: Time (s)
            amplitude: Noise amplitude (m)
            seed: Random seed

        Returns:
            Elevation (m)
        """
        np.random.seed(int(t * 1000 + seed))
        return amplitude * (2 * np.random.random() - 1)

    @staticmethod
    def swept_sine(
        t: float,
        f0: float,
        f1: float,
        T: float,
        amplitude: float
    ) -> float:
        """Generate swept sine (chirp)

        Args:
            t: Time (s)
            f0: Start frequency (Hz)
            f1: End frequency (Hz)
            T: Sweep duration (s)
            amplitude: Amplitude (m)

        Returns:
            Elevation (m)
        """
        if t > T:
            freq = f1
        else:
            freq = f0 + (f1 - f0) * (t / T)

        omega = 2 * np.pi * freq
        return amplitude * np.sin(omega * t)
```

### **CSV Loading**

```python
def load_csv_road_profile(file_path: str) -> np.ndarray:
    """Load road profile from CSV

    Args:
        file_path: Path to CSV file

    Returns:
        2D array: [[time0, elev0], [time1, elev1], ...]

    CSV Format:
        time,elevation
        0.0,0.000
        0.1,0.005
        0.2,0.010
        ...
    """
    import csv

    data = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = float(row['time'])
            z = float(row['elevation'])
            data.append([t, z])

    return np.array(data)

class CSVProfile:
    """Road profile from CSV data"""

    def __init__(self, data: np.ndarray):
        """Initialize from CSV data

        Args:
            data: 2D array [[time, elevation], ...]
        """
        self.time = data[:, 0]
        self.elevation = data[:, 1]

    def get_elevation(self, t: float) -> float:
        """Get elevation at time t (with interpolation)

        Args:
            t: Time (s)

        Returns:
            Elevation (m)
        """
        # Linear interpolation
        return np.interp(t, self.time, self.elevation)
```

---

## ?? Predefined Scenarios

```python
SCENARIOS = {
    'smooth': {
        'type': 'sine',
        'params': {
            'amplitude': 0.01,  # 10mm
            'frequency': 0.5,   # Hz
            'phase': 0.0
        }
    },

    'rough': {
        'type': 'sine',
        'params': {
            'amplitude': 0.05,  # 50mm
            'frequency': 2.0,
            'phase': 0.0
        }
    },

    'pothole': {
        'type': 'step',
        'params': {
            't_step': 2.0,
            'amplitude': -0.1,  # -100mm (downward)
            'duration': 0.2     # 200ms
        }
    },

    'speed_bump': {
        'type': 'step',
        'params': {
            't_step': 1.5,
            'amplitude': 0.08,  # 80mm (upward)
            'duration': 0.3
        }
    },

    'belgian_paving': {
        'type': 'csv',
        'file': 'assets/road/belgian_paving.csv'
    },

    'swept_sine_test': {
        'type': 'swept',
        'params': {
            'f0': 0.5,    # Start: 0.5 Hz
            'f1': 10.0,   # End: 10 Hz
            'T': 20.0,    # Duration: 20s
            'amplitude': 0.03
        }
    }
}
```

---

## ?? Example Usage

### **Simple Sine Wave**

```python
from src.road.engine import RoadInput
from src.pneumo.enums import Wheel

# Create road input
road = RoadInput()

# Set sine wave (all wheels)
road.set_sine_profile(
    amplitude=0.05,   # 50mm
    frequency=1.0,    # 1 Hz
    phase=0.0         # 0 degrees
)

# Get excitation at t=2.5s
excitations = road.get_wheel_excitation(2.5)
print(f"FL elevation: {excitations['fl']*1000:.1f} mm")
```

### **Per-Wheel Phase Offsets**

```python
# Front wheels in phase
road.set_sine_profile(
    amplitude=0.05,
    frequency=1.0,
    phase=0.0,
    wheels=[Wheel.FL, Wheel.FR]
)

# Rear wheels 180 out of phase
road.set_sine_profile(
    amplitude=0.05,
    frequency=1.0,
    phase=180.0,
    wheels=[Wheel.RL, Wheel.RR]
)
```

### **CSV Profile**

```python
# Load Belgian paving profile
road.load_csv_profile(
    'assets/road/belgian_paving.csv',
    wheels=[Wheel.FL, Wheel.FR, Wheel.RL, Wheel.RR]
)

# Simulate
for t in np.linspace(0, 10, 1000):
    excitations = road.get_wheel_excitation(t)
    # ... apply to suspension
```

### **Scenario**

```python
# Load predefined scenario
road.set_scenario('pothole')

# Simulate pothole impact
for t in np.linspace(0, 5, 500):
    excitations = road.get_wheel_excitation(t)
    print(f"t={t:.2f}s: FL={excitations['fl']*1000:.1f}mm")
```

---

## ?? Configuration

```python
DEFAULT_ROAD_CONFIG = {
    'default_amplitude': 0.05,    # m
    'default_frequency': 1.0,     # Hz
    'default_phase': 0.0,         # degrees
    'csv_cache_size': 10,         # Max cached CSV files
    'interpolation': 'linear',    # or 'cubic'
}
```

---

## ?? CSV File Format

```csv
time,elevation
0.0,0.000
0.1,0.005
0.2,0.010
0.3,0.012
0.4,0.008
0.5,0.003
0.6,-0.002
0.7,-0.005
0.8,-0.004
0.9,0.000
1.0,0.005
```

**Requirements:**
- Header row: `time,elevation`
- Time in seconds (ascending order)
- Elevation in meters
- UTF-8 encoding

---

## ?? Test Coverage

**Test Files:**
- `tests/test_road_engine.py`
- `tests/test_generators.py`
- `tests/test_csv_io.py`

**Test Cases:**
1. ? Sine wave generation
2. ? Step input
3. ? Ramp input
4. ? Noise generation
5. ? CSV loading
6. ? Interpolation
7. ? Scenario loading

**Coverage:** ~85%

---

## ?? References

- **Signal Processing:** [NumPy Signal Generation](https://numpy.org/doc/stable/reference/routines.fft.html)
- **Interpolation:** [SciPy Interpolate](https://docs.scipy.org/doc/scipy/reference/interpolate.html)
- **Road Profiles:** ISO 8608 standard

---

**Last Updated:** 2025-01-05
**Module Version:** 2.0.0
**Status:** Production Ready ?
