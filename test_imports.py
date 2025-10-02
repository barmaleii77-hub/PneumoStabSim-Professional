#!/usr/bin/env python
"""Test all imports"""

import sys
sys.path.insert(0, '.')

# Core modules
from src.common import errors, units
from src.pneumo import enums, thermo, gas_state, valves, flow, network
from src.physics import odes, forces, integrator
from src.road import generators, scenarios, engine
from src.runtime import state, sync, sim_loop
from src.ui import main_window, charts, gl_view
from src.ui.widgets import Knob, RangeSlider
from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel

print('? ALL MODULES IMPORTED SUCCESSFULLY')
print(f'  - Common: 2 modules')
print(f'  - Pneumo: 6 modules')
print(f'  - Physics: 3 modules')
print(f'  - Road: 3 modules')
print(f'  - Runtime: 3 modules')
print(f'  - UI: 3 modules')
print(f'  - Widgets: 2 classes')
print(f'  - Panels: 4 classes')
