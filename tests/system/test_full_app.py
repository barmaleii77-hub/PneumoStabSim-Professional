"""
System test for full application
"""
import pytest
import time


@pytest.mark.system
@pytest.mark.slow
@pytest.mark.gui
class TestFullApplication:
    """Test complete application workflow"""

    def test_app_imports(self):
        """Test that app.py can be imported"""
        import app

        assert app is not None

    def test_main_window_creation(self, qapp):
        """Test creating main window"""
        from src.ui.main_window import MainWindow

        window = MainWindow()
        assert window is not None
        assert (
            window.windowTitle() == "PneumoStabSim - Pneumatic Stabilization Simulator"
        )

    @pytest.mark.skip(reason="Requires full Qt event loop")
    def test_full_startup_shutdown(self, qapp):
        """Test complete application startup and shutdown"""
        from src.ui.main_window import MainWindow

        window = MainWindow()
        window.show()

        # Let Qt process events
        qapp.processEvents()
        time.sleep(0.1)

        # Close window
        window.close()

        qapp.processEvents()

        assert True  # If we got here, app didn't crash
