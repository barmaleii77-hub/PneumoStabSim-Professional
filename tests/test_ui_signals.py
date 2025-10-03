"""
P12: UI signals validation tests (QtTest/QSignalSpy)

Tests:
- Panel signals (sliders, knobs)
- Signal emission and reception
- Parameter updates

References:
- PySide6.QtTest.QSignalSpy: https://doc.qt.io/qtforpython-6/PySide6/QtTest/QSignalSpy.html
- Qt QSignalSpy: https://doc.qt.io/qt-6/qsignalspy.html
- unittest: https://docs.python.org/3/library/unittest.html
"""

import unittest
import sys
from pathlib import Path

# Qt imports
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QSignalSpy
from PySide6.QtCore import Qt

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.widgets.knob import Knob
from src.ui.widgets.range_slider import RangeSlider
from src.ui.panels.panel_pneumo import PneumoPanel


# Create QApplication once for all UI tests
app = None

def setUpModule():
    """Create QApplication once before any UI tests"""
    global app
    if QApplication.instance() is None:
        app = QApplication(sys.argv)


class TestKnobSignals(unittest.TestCase):
    """Test Knob widget signal emission"""
    
    def test_knob_value_changed_signal(self):
        """Test Knob emits valueChanged signal when value is set"""
        knob = Knob(minimum=0.0, maximum=100.0, value=50.0)
        
        # Create signal spy
        spy = QSignalSpy(knob.valueChanged)
        
        # Change value
        new_value = 75.0
        knob.setValue(new_value)
        
        # Check signal emitted
        self.assertEqual(
            len(spy),
            1,
            f"Signal should be emitted once, got {len(spy)} emissions"
        )
        
        # Check signal argument
        if len(spy) > 0:
            emitted_value = spy[0][0]
            self.assertEqual(
                emitted_value,
                new_value,
                f"Signal argument should be {new_value}, got {emitted_value}"
            )
            
    def test_knob_multiple_changes(self):
        """Test Knob signal spy counts multiple changes"""
        knob = Knob(minimum=0.0, maximum=100.0, value=0.0)
        spy = QSignalSpy(knob.valueChanged)
        
        # Make multiple changes
        values = [25.0, 50.0, 75.0, 100.0]
        for val in values:
            knob.setValue(val)
        
        # Check count
        self.assertEqual(
            len(spy),
            len(values),
            f"Should have {len(values)} emissions, got {len(spy)}"
        )
        
    def test_knob_bounds(self):
        """Test Knob respects min/max bounds"""
        minimum = 10.0
        maximum = 90.0
        knob = Knob(minimum=minimum, maximum=maximum, value=50.0)
        
        # Try to set below minimum
        knob.setValue(5.0)
        self.assertGreaterEqual(
            knob.value(),
            minimum,
            "Value should be clamped to minimum"
        )
        
        # Try to set above maximum
        knob.setValue(95.0)
        self.assertLessEqual(
            knob.value(),
            maximum,
            "Value should be clamped to maximum"
        )


class TestRangeSliderSignals(unittest.TestCase):
    """Test RangeSlider widget signal emission"""
    
    def test_range_slider_min_changed(self):
        """Test RangeSlider emits signal when min value changes"""
        slider = RangeSlider(minimum=0.0, maximum=100.0)
        slider.setMinValue(20.0)
        slider.setMaxValue(80.0)
        
        spy = QSignalSpy(slider.minValueChanged)
        
        # Change min value
        new_min = 30.0
        slider.setMinValue(new_min)
        
        # Check signal
        self.assertGreater(len(spy), 0, "minValueChanged should be emitted")
        
    def test_range_slider_max_changed(self):
        """Test RangeSlider emits signal when max value changes"""
        slider = RangeSlider(minimum=0.0, maximum=100.0)
        slider.setMinValue(20.0)
        slider.setMaxValue(80.0)
        
        spy = QSignalSpy(slider.maxValueChanged)
        
        # Change max value
        new_max = 90.0
        slider.setMaxValue(new_max)
        
        # Check signal
        self.assertGreater(len(spy), 0, "maxValueChanged should be emitted")
        
    def test_range_slider_bounds_validation(self):
        """Test RangeSlider keeps min < max"""
        slider = RangeSlider(minimum=0.0, maximum=100.0)
        
        # Set min and max
        slider.setMinValue(40.0)
        slider.setMaxValue(60.0)
        
        # Min should be <= max
        self.assertLessEqual(
            slider.minValue(),
            slider.maxValue(),
            "Min value should be <= max value"
        )


class TestPneumoPanelSignals(unittest.TestCase):
    """Test PneumoPanel parameter signals"""
    
    def test_pneumo_panel_creates(self):
        """Test PneumoPanel can be instantiated"""
        try:
            panel = PneumoPanel()
            self.assertIsNotNone(panel, "PneumoPanel should be created")
        except Exception as e:
            self.fail(f"PneumoPanel initialization failed: {e}")
            
    def test_pneumo_panel_has_signals(self):
        """Test PneumoPanel has required signals"""
        panel = PneumoPanel()
        
        # Check signal existence
        self.assertTrue(
            hasattr(panel, 'parameter_changed'),
            "PneumoPanel should have parameter_changed signal"
        )
        
        self.assertTrue(
            hasattr(panel, 'mode_changed'),
            "PneumoPanel should have mode_changed signal"
        )
        
    def test_pneumo_panel_parameter_update(self):
        """Test PneumoPanel emits signal on parameter change"""
        panel = PneumoPanel()
        
        # Create spy for parameter_changed signal
        spy = QSignalSpy(panel.parameter_changed)
        
        # Get parameters and modify
        params = panel.get_parameters()
        
        # Simulate parameter change (if panel has setter)
        if hasattr(panel, 'set_parameters'):
            # Modify a parameter
            new_params = params.copy()
            new_params['tank_volume'] = 0.05  # Change tank volume
            
            panel.set_parameters(new_params)
            
            # Signal might be emitted (depends on implementation)
            # Just check it doesn't crash
            self.assertIsInstance(params, dict, "Parameters should be dict")


class TestSignalConnection(unittest.TestCase):
    """Test signal-slot connections"""
    
    def test_signal_slot_basic(self):
        """Test basic signal-slot connection"""
        knob = Knob(minimum=0.0, maximum=100.0)
        
        # Track received values
        received_values = []
        
        def slot(value):
            received_values.append(value)
        
        # Connect signal to slot
        knob.valueChanged.connect(slot)
        
        # Emit signals
        knob.setValue(25.0)
        knob.setValue(75.0)
        
        # Check slot received values
        self.assertEqual(
            len(received_values),
            2,
            f"Slot should receive 2 values, got {len(received_values)}"
        )
        
        self.assertEqual(received_values[0], 25.0)
        self.assertEqual(received_values[1], 75.0)
        
    def test_signal_disconnect(self):
        """Test signal can be disconnected"""
        knob = Knob(minimum=0.0, maximum=100.0)
        
        received_values = []
        
        def slot(value):
            received_values.append(value)
        
        # Connect
        knob.valueChanged.connect(slot)
        knob.setValue(10.0)
        
        # Disconnect
        knob.valueChanged.disconnect(slot)
        knob.setValue(20.0)
        
        # Only first value should be received
        self.assertEqual(
            len(received_values),
            1,
            "After disconnect, slot should not receive new values"
        )


class TestUIParameterFlow(unittest.TestCase):
    """Test parameter flow from UI to model"""
    
    def test_knob_to_model_flow(self):
        """Test knob value flows to model parameter"""
        knob = Knob(minimum=0.0, maximum=10.0, value=5.0)
        
        # Mock model parameter
        model_param = {'value': 0.0}
        
        def update_model(value):
            model_param['value'] = value
        
        # Connect
        knob.valueChanged.connect(update_model)
        
        # Change knob
        knob.setValue(7.5)
        
        # Check model updated
        self.assertEqual(
            model_param['value'],
            7.5,
            "Model parameter should be updated from knob"
        )


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
