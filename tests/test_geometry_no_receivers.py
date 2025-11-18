import importlib
import logging
import sys
import types

import pytest


def _load_panel_geometry(monkeypatch: pytest.MonkeyPatch):
    for name in list(sys.modules):
        if name.startswith("PySide6") or name in {
            "config.constants",
            "src.common.settings_manager",
            "src.ui.geometry_schema",
            "src.ui.panels.geometry.defaults",
            "src.ui.widgets",
            "src.ui.widgets.knob",
            "src.ui.widgets.range_slider",
            "src.ui.panels.panel_geometry",
        }:
            sys.modules.pop(name)

    qtwidgets = types.ModuleType("PySide6.QtWidgets")

    class _Widget:
        def __init__(self, *args, **kwargs):
            pass

    qtwidgets.QWidget = _Widget
    qtwidgets.QVBoxLayout = qtwidgets.QHBoxLayout = qtwidgets.QGroupBox = _Widget
    qtwidgets.QCheckBox = qtwidgets.QPushButton = qtwidgets.QLabel = _Widget
    qtwidgets.QMessageBox = qtwidgets.QSizePolicy = qtwidgets.QComboBox = _Widget

    qtcore = types.ModuleType("PySide6.QtCore")

    class _QMetaMethod:
        @staticmethod
        def fromSignal(_signal):
            return _QMetaMethod()

        def isValid(self):
            return True

        def methodSignature(self):
            return b"dummy()"

    class _QObject:
        def receivers(self, _signature):
            return 0

    def _Signal(*_args, **_kwargs):  # noqa: N802 - Qt mimic
        return object()

    def _Slot(*_args, **_kwargs):  # noqa: N802 - Qt mimic
        def decorator(func):
            return func

        return decorator

    class _Qt:
        class AlignmentFlag:
            AlignCenter = 0

    qtcore.QObject = _QObject
    qtcore.QMetaMethod = _QMetaMethod
    qtcore.Signal = _Signal
    qtcore.Slot = _Slot
    qtcore.Qt = _Qt

    qtgui = types.ModuleType("PySide6.QtGui")

    class _QFont:
        def setPointSize(self, _size):
            return None

    qtgui.QFont = _QFont

    sys.modules["PySide6"] = types.ModuleType("PySide6")
    sys.modules["PySide6.QtWidgets"] = qtwidgets
    sys.modules["PySide6.QtCore"] = qtcore
    sys.modules["PySide6.QtGui"] = qtgui

    config_constants = types.ModuleType("config.constants")
    config_constants.get_geometry_presets = lambda: {}
    config_constants.get_geometry_ui_ranges = lambda: {}
    sys.modules["config.constants"] = config_constants

    settings_manager = types.ModuleType("src.common.settings_manager")
    settings_manager.get_settings_manager = lambda: object()
    sys.modules["src.common.settings_manager"] = settings_manager

    geometry_schema = types.ModuleType("src.ui.geometry_schema")

    class _GeometrySettings:
        def to_config_dict(self):
            return {}

    class _GeometryValidationError(Exception):
        pass

    geometry_schema.GeometrySettings = _GeometrySettings
    geometry_schema.GeometryValidationError = _GeometryValidationError

    def _validate_geometry_settings(payload):
        class _Validated:
            def to_config_dict(self):
                return {}

        return _Validated()

    geometry_schema.validate_geometry_settings = _validate_geometry_settings
    sys.modules["src.ui.geometry_schema"] = geometry_schema

    defaults = types.ModuleType("src.ui.panels.geometry.defaults")
    defaults.DEFAULT_GEOMETRY = {}
    sys.modules["src.ui.panels.geometry.defaults"] = defaults

    widgets = types.ModuleType("src.ui.widgets")
    knob_mod = types.ModuleType("src.ui.widgets.knob")
    range_slider_mod = types.ModuleType("src.ui.widgets.range_slider")

    class _DummyWidget:
        pass

    knob_mod.Knob = _DummyWidget
    range_slider_mod.RangeSlider = _DummyWidget
    widgets.Knob = _DummyWidget
    widgets.RangeSlider = _DummyWidget

    sys.modules["src.ui.widgets"] = widgets
    sys.modules["src.ui.widgets.knob"] = knob_mod
    sys.modules["src.ui.widgets.range_slider"] = range_slider_mod

    module = importlib.import_module("src.ui.panels.panel_geometry")
    return importlib.reload(module)


class DummySignal:
    def __init__(self) -> None:
        self.emitted_payload = None

    def emit(self, payload):
        self.emitted_payload = payload


def test_emit_skipped_and_logged_when_no_subscribers(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
    panel_geometry = _load_panel_geometry(monkeypatch)
    panel = type("Panel", (), {"logger": logging.getLogger("dummy.panel"), "_is_signal_connected": lambda self, *_: False})()
    signal = DummySignal()

    with caplog.at_level(logging.INFO):
        panel_geometry.GeometryPanel._emit_if_connected(panel, signal, {"hello": "world"}, "initial geometry")

    assert signal.emitted_payload is None
    record = next(rec for rec in caplog.records if rec.message == "geometry_emit_skipped")
    assert record.reason == "no_subscribers"
    assert record.description == "initial geometry"
    assert record.signal_signature is None


def test_emit_probe_failures_are_soft(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
    panel_geometry = _load_panel_geometry(monkeypatch)

    class FailingPanel:
        def __init__(self):
            self.logger = logging.getLogger("dummy.panel")

        def _is_signal_connected(self, *_args, **_kwargs):
            raise RuntimeError("probe failed")

    signal = DummySignal()

    with caplog.at_level(logging.DEBUG):
        panel_geometry.GeometryPanel._emit_if_connected(FailingPanel(), signal, {"hello": "world"}, "initial geometry")

    assert any(
        rec.message == "geometry_emit_connection_probe_failed" and rec.description == "initial geometry"
        for rec in caplog.records
    )
