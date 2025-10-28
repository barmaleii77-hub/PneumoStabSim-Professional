import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for MaterialsTab tests",
    exc_type=ImportError,
)

from src.ui.panels.graphics.materials_tab import MaterialsTab


@pytest.fixture
def materials_payload():
    base_frame = {
        "base_color": "#7dff69",
        "metalness": 1.0,
        "roughness": 0.3,
        "specular": 0.0,
        "specular_tint": "#ffffff",
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
