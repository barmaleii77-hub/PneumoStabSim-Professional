from copy import deepcopy

import pytest
from PySide6.QtCore import Qt

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for MaterialsTab tests",
    exc_type=ImportError,
)

import src.ui.panels.graphics.materials_tab as materials_tab_module
from src.common.settings_manager import get_settings_manager
from src.ui.panels.graphics.materials_tab import MaterialsTab


@pytest.fixture
def materials_payload():
    base_frame = {
        "base_color": "#7dff69",
        "metalness": 1.0,
        "roughness": 0.3,
        "specular": 0.0,
        "specular_tint": 0.0,
        "opacity": 1.0,
        "clearcoat": 0.0,
        "clearcoat_roughness": 0.0,
        "transmission": 0.0,
        "ior": 1.5,
        "thickness": 0.0,
        "attenuation_distance": 0.0,
        "attenuation_color": "#ffffff",
        "emissive_color": "#000000",
        "emissive_intensity": 0.0,
        "normal_strength": 1.0,
        "occlusion_amount": 1.0,
        "alpha_mode": "default",
        "alpha_cutoff": 0.5,
    }
    base_lever = {
        **base_frame,
        "base_color": "#ff9933",
        "roughness": 0.55,
        "emissive_intensity": 1.0,
    }
    return {
        "frame": base_frame,
        "lever": base_lever,
    }


def _select_material(tab: MaterialsTab, index: int) -> None:
    selector = tab._material_selector  # noqa: SLF001 - test helper
    selector.setCurrentIndex(index)


def test_switching_materials_preserves_cached_values(qapp, materials_payload):
    tab = MaterialsTab()
    tab.set_state(materials_payload)

    assert tab.get_current_material_key() == "frame"

    new_roughness = 0.42
    tab._controls["roughness"].set_value(new_roughness)  # noqa: SLF001
    tab._on_control_changed("roughness", new_roughness)  # noqa: SLF001

    _select_material(tab, 1)
    assert tab.get_current_material_key() == "lever"

    lever_state = tab.get_current_material_state()
    assert lever_state["roughness"] == pytest.approx(
        materials_payload["lever"]["roughness"]
    )
    assert lever_state["base_color"] == materials_payload["lever"]["base_color"]

    _select_material(tab, 0)
    assert tab.get_current_material_key() == "frame"

    frame_state = tab.get_current_material_state()
    assert frame_state["roughness"] == pytest.approx(new_roughness)
    assert frame_state["base_color"] == materials_payload["frame"]["base_color"]

    cached = tab.get_all_state()
    assert cached["frame"]["roughness"] == pytest.approx(new_roughness)
    assert cached["lever"]["roughness"] == pytest.approx(
        materials_payload["lever"]["roughness"]
    )


def test_coerce_color_accepts_normalised_tuple(qapp):
    tab = MaterialsTab()

    rgb = (0.25, 0.5, 1.0)
    coerced = tab._coerce_color(rgb)  # noqa: SLF001 - test helper

    assert coerced == "#3f80ff"

    rgb_255 = (64, 128, 255)
    coerced_255 = tab._coerce_color(rgb_255)  # noqa: SLF001 - test helper

    assert coerced_255 == "#4080ff"


def test_materials_tab_accepts_color_alias(qapp):
    tab = MaterialsTab()

    tab.set_state({"frame": {"color": "#112233"}})

    cached = tab.get_all_state()
    assert cached["frame"]["base_color"] == "#112233"


@pytest.mark.gui
def test_materials_tab_preserves_missing_texture_until_user_confirms(
    qapp,
    qtbot,
    materials_payload,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tab = MaterialsTab()
    qtbot.addWidget(tab)

    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.warning",
        lambda *args, **kwargs: None,
    )

    textures = [("One", "one.png"), ("Two", "two.png")]
    texture_widget = tab.get_controls()["texture_path"]

    # Мокаем проверку существования: one.png и two.png существуют, missing.png нет
    def mock_probe(path: str) -> bool:
        return path in {"one.png", "two.png"}

    monkeypatch.setattr(texture_widget, "_probe_path_exists", mock_probe)

    texture_widget.set_items(textures)

    payload = deepcopy(materials_payload)
    payload["frame"]["texture_path"] = "missing.png"
    tab.set_state(payload)

    tab.show()
    # Ждём полной инициализации UI перед обработкой событий
    qtbot.waitExposed(tab)
    qapp.processEvents()

    assert texture_widget.current_path() == "missing.png"
    assert texture_widget.is_missing()

    cached = tab.get_all_state()
    assert cached["frame"]["texture_path"] == "missing.png"

    # Гарантируем что виджет всё ещё живой перед кликом
    assert texture_widget._next_btn is not None  # type: ignore[attr-defined]
    qtbot.mouseClick(texture_widget._next_btn, Qt.LeftButton)  # type: ignore[attr-defined]
    qapp.processEvents()

    assert texture_widget.current_path() == "one.png"
    assert not texture_widget.is_missing()

    updated = tab.get_all_state()
    assert updated["frame"]["texture_path"] == "one.png"


@pytest.mark.gui
def test_materials_tab_empty_texture_does_not_autoselect(
    qapp,
    qtbot,
    materials_payload,
) -> None:
    tab = MaterialsTab()
    qtbot.addWidget(tab)

    textures = [("One", "one.png"), ("Two", "two.png")]
    texture_widget = tab.get_controls()["texture_path"]
    texture_widget.set_items(textures)

    payload = deepcopy(materials_payload)
    payload["frame"]["texture_path"] = ""
    tab.set_state(payload)

    assert texture_widget.current_path() == ""

    cached = tab.get_all_state()
    assert cached["frame"]["texture_path"] == ""


@pytest.mark.gui
def test_materials_tab_restores_texture_from_settings_on_init(
    qapp,
    qtbot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_manager = get_settings_manager()
    saved_path = "custom_texture.png"

    class _StubManager:
        def __init__(self, base):
            self._base = base

        def get(self, path, default=None):
            if path == "current.graphics.materials":
                return {"frame": {"texture_path": saved_path}}
            return self._base.get(path, default)

    monkeypatch.setattr(
        materials_tab_module,
        "get_settings_manager",
        lambda: _StubManager(base_manager),
    )
    monkeypatch.setattr(
        materials_tab_module,
        "discover_texture_files",
        lambda *args, **kwargs: [("First", "first.png"), ("Second", "second.png")],
    )

    warnings: list[str] = []

    def _capture_warning(parent, title, text):
        warnings.append(text)
        return None

    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.warning",
        _capture_warning,
    )

    tab = MaterialsTab()
    qtbot.addWidget(tab)

    texture_widget = tab.get_controls()["texture_path"]

    assert texture_widget.current_path() == saved_path
    assert texture_widget.is_missing()

    tab.show()
    qapp.processEvents()

    assert warnings, "Expected warning for missing initial texture path"
    assert saved_path in warnings[0]

    cached = tab.get_all_state()
    assert cached["frame"]["texture_path"] == saved_path
