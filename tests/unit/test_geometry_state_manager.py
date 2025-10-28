import pytest

from src.ui.panels.geometry.state_manager import GeometryStateManager


class DummySettingsManager:
    def __init__(self, payload):
        self._payload = payload
        self.saved = None

    def get(self, path, default=None):
        if path == "current.geometry":
            return dict(self._payload)
        return default

    def set(self, path, value, auto_save=True):
        self.saved = (path, value, auto_save)


def test_set_parameter_rejects_unknown_key():
    manager = GeometryStateManager()
    with pytest.raises(KeyError):
        manager.set_parameter("nonexistent", 0)


def test_update_parameters_rejects_unknown_keys():
    manager = GeometryStateManager()
    with pytest.raises(KeyError):
        manager.update_parameters({"wheelbase": 3.2, "extra": 1})


def test_load_state_filters_unknown_keys():
    dummy = DummySettingsManager({"wheelbase": 3.2, "unknown": 1.0})
    manager = GeometryStateManager(settings_manager=dummy)
    assert "unknown" not in manager.state


def test_save_state_persists_only_allowed_keys():
    dummy = DummySettingsManager({"wheelbase": 3.2, "unknown": 1.0})
    manager = GeometryStateManager(settings_manager=dummy)
    manager.state["wheelbase"] = 3.4
    manager.state["unknown"] = 99
    manager.save_state()
    assert dummy.saved is not None
    _, persisted, _ = dummy.saved
    assert "unknown" not in persisted
    assert "wheelbase" in persisted


def test_load_state_uses_persisted_values():
    dummy = DummySettingsManager({"wheelbase": 2.0, "track": 1.1})
    manager = GeometryStateManager(settings_manager=dummy)
    assert manager.get_parameter("wheelbase") == pytest.approx(2.0)
    assert manager.get_parameter("track") == pytest.approx(1.1)
