# -*- coding: utf-8 -*-
"""
Diagnostic: Check if simulation is actually running and emitting states
"""
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import sys
import time

# Import simulation components
from src.runtime.sim_loop import SimulationManager
from src.runtime.state import StateSnapshot

app = QApplication(sys.argv)

# Create simulation manager
sim_manager = SimulationManager()

# Counter for received states
state_counter = 0
last_state_time = 0

def on_state_received(snapshot: StateSnapshot):
    global state_counter, last_state_time
    state_counter += 1
    last_state_time = time.time()
    
    if state_counter % 10 == 0:  # Every 10 states
        print(f"\n{'='*60}")
        print(f"State #{state_counter}")
        print(f"  Sim time: {snapshot.simulation_time:.3f}s")
        print(f"  Step: {snapshot.step_number}")
        print(f"  Frame heave: {snapshot.frame.heave:.6f}m")
        print(f"  Frame roll: {snapshot.frame.roll:.6f}rad")
        print(f"  Frame pitch: {snapshot.frame.pitch:.6f}rad")
        
        # Check line pressures
        for line_name, line_state in snapshot.lines.items():
            print(f"  {line_name.value} pressure: {line_state.pressure:.1f}Pa")
        
        print(f"  Tank pressure: {snapshot.tank.pressure:.1f}Pa")
        print(f"{'='*60}")

# Connect signal
sim_manager.state_bus.state_ready.connect(on_state_received)

# Start simulation
print("Starting simulation manager...")
sim_manager.start()

print("Starting physics simulation...")
sim_manager.state_bus.start_simulation.emit()

# Create timer to check if states are being received
check_timer = QTimer()
def check_states():
    global state_counter, last_state_time
    current_time = time.time()
    
    if state_counter == 0:
        print(f"??  WARNING: No states received yet!")
    else:
        time_since_last = current_time - last_state_time
        print(f"? Received {state_counter} states, last {time_since_last:.1f}s ago")

check_timer.timeout.connect(check_states)
check_timer.start(2000)  # Check every 2 seconds

# Run for 10 seconds then exit
exit_timer = QTimer()
def exit_app():
    print(f"\n{'='*60}")
    print(f"DIAGNOSTIC COMPLETE")
    print(f"Total states received: {state_counter}")
    print(f"{'='*60}")
    
    sim_manager.stop()
    app.quit()

exit_timer.singleShot(10000, exit_app)  # Exit after 10 seconds

print("\nRunning diagnostic for 10 seconds...")
print("Waiting for state snapshots...\n")

sys.exit(app.exec())
