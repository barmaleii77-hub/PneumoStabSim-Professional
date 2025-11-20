import pytest
from src.common.settings_manager import get_settings_manager

@pytest.mark.qt
def test_shader_warning_lifecycle(qtbot):
    # Имитация QML root объекта с минимальным интерфейсом
    class DummyRoot:
        def __init__(self):
            self.warnings = {}
        def registerShaderWarning(self, effectId, message):
            self.warnings[effectId] = message
        def clearShaderWarning(self, effectId):
            if effectId in self.warnings:
                del self.warnings[effectId]
    root = DummyRoot()
    # Эмуляция предупреждений
    root.registerShaderWarning("bloom", "Fallback shader engaged")
    root.registerShaderWarning("bloom", "Updated")
    assert root.warnings["bloom"] == "Updated"
    root.clearShaderWarning("bloom")
    assert "bloom" not in root.warnings
