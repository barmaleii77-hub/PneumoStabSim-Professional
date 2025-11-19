import pytest

from src.ui.panels.panel_geometry import GeometryPanel


class DummySignal:
    def __init__(self) -> None:
        self.emitted: list[dict] = []

    def emit(self, payload):
        self.emitted.append(payload)


@pytest.mark.usefixtures("qapp")
def test_emit_if_connected_without_receivers(monkeypatch):
    panel = GeometryPanel()
    dummy_signal = DummySignal()
    monkeypatch.setattr(panel, "geometry_changed", dummy_signal)

    panel._emit_if_connected(dummy_signal, {"value": 1}, "dummy emission")

    assert dummy_signal.emitted == [{"value": 1}]


@pytest.mark.usefixtures("qapp")
def test_is_signal_connected_uses_public_guards(monkeypatch):
    panel = GeometryPanel()
    meta_method = panel._get_geometry_meta_method()

    monkeypatch.setattr(panel, "isSignalConnected", lambda _meta: False)

    assert panel._is_signal_connected(panel.geometry_changed, meta_method) is False
