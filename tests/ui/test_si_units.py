# -*- coding: utf-8 -*-
"""
��-2: ����� ��� ������ �� + ��� 0.001�
Tests for SI units conversion - rod_diameter, piston_rod_length, piston_thickness to meters
"""

import pytest
from PySide6.QtWidgets import QApplication
from src.ui.panels.panel_geometry import GeometryPanel


@pytest.fixture(scope="module")
def app():
    """Create QApplication instance for tests"""
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication([])
    return app_instance


@pytest.fixture
def geometry_panel(app):
    """Create GeometryPanel instance for testing"""
    panel = GeometryPanel()
    return panel


# ============================================================================
# ��-2: ����� ������� ����� ��������� (� ������)
# ============================================================================

def test_rod_diameter_m_slider_exists(geometry_panel):
    """��������� ������� �������� rod_diameter_m"""
    assert hasattr(geometry_panel, 'rod_diameter_m_slider'), \
        "GeometryPanel ������ ����� ������� rod_diameter_m_slider"


def test_piston_rod_length_m_slider_exists(geometry_panel):
    """��������� ������� �������� piston_rod_length_m"""
    assert hasattr(geometry_panel, 'piston_rod_length_m_slider'), \
        "GeometryPanel ������ ����� ������� piston_rod_length_m_slider"


def test_piston_thickness_m_slider_exists(geometry_panel):
    """��������� ������� �������� piston_thickness_m"""
    assert hasattr(geometry_panel, 'piston_thickness_m_slider'), \
        "GeometryPanel ������ ����� ������� piston_thickness_m_slider"


# ============================================================================
# ��-2: ����� ���������� ������ ��������� (� ��)
# ============================================================================

def test_rod_diameter_slider_removed(geometry_panel):
    """��������� ���������� rod_diameter_slider (� ��)"""
    assert not hasattr(geometry_panel, 'rod_diameter_slider'), \
        "rod_diameter_slider ������ ���� ����� (������ �� rod_diameter_m_slider)"


def test_piston_rod_length_slider_removed(geometry_panel):
    """��������� ���������� piston_rod_length_slider (� ��)"""
    assert not hasattr(geometry_panel, 'piston_rod_length_slider'), \
        "piston_rod_length_slider ������ ���� ����� (������ �� piston_rod_length_m_slider)"


def test_piston_thickness_slider_removed(geometry_panel):
    """��������� ���������� piston_thickness_slider (� ��)"""
    assert not hasattr(geometry_panel, 'piston_thickness_slider'), \
        "piston_thickness_slider ������ ���� ����� (������ �� piston_thickness_m_slider)"


# ============================================================================
# ��-2: ����� ���������� rod_diameter_m_slider
# ============================================================================

def test_rod_diameter_m_minimum(geometry_panel):
    """��������� ������� rod_diameter_m_slider = 0.020 �"""
    assert geometry_panel.rod_diameter_m_slider.minimum() == 0.020, \
        f"rod_diameter_m minimum ������ ���� 0.020, �������� {geometry_panel.rod_diameter_m_slider.minimum()}"


def test_rod_diameter_m_maximum(geometry_panel):
    """��������� �������� rod_diameter_m_slider = 0.060 �"""
    assert geometry_panel.rod_diameter_m_slider.maximum() == 0.060, \
        f"rod_diameter_m maximum ������ ���� 0.060, �������� {geometry_panel.rod_diameter_m_slider.maximum()}"


def test_rod_diameter_m_default_value(geometry_panel):
    """��������� �������� �� ��������� rod_diameter_m_slider = 0.035 �"""
    assert geometry_panel.rod_diameter_m_slider.value() == 0.035, \
        f"rod_diameter_m default ������ ���� 0.035, �������� {geometry_panel.rod_diameter_m_slider.value()}"


def test_rod_diameter_m_step(geometry_panel):
    """��������� ��� rod_diameter_m_slider = 0.001 �"""
    assert geometry_panel.rod_diameter_m_slider.step() == 0.001, \
        f"rod_diameter_m step ������ ���� 0.001, �������� {geometry_panel.rod_diameter_m_slider.step()}"


def test_rod_diameter_m_decimals(geometry_panel):
    """��������� decimals rod_diameter_m_slider = 3"""
    assert geometry_panel.rod_diameter_m_slider.decimals() == 3, \
        f"rod_diameter_m decimals ������ ���� 3, �������� {geometry_panel.rod_diameter_m_slider.decimals()}"


def test_rod_diameter_m_units(geometry_panel):
    """��������� ������� rod_diameter_m_slider = '�'"""
    assert geometry_panel.rod_diameter_m_slider.units() == "�", \
        f"rod_diameter_m units ������ ���� '�', �������� '{geometry_panel.rod_diameter_m_slider.units()}'"


# ============================================================================
# ��-2: ����� ���������� piston_rod_length_m_slider
# ============================================================================

def test_piston_rod_length_m_minimum(geometry_panel):
    """��������� ������� piston_rod_length_m_slider = 0.100 �"""
    assert geometry_panel.piston_rod_length_m_slider.minimum() == 0.100, \
        f"piston_rod_length_m minimum ������ ���� 0.100, �������� {geometry_panel.piston_rod_length_m_slider.minimum()}"


def test_piston_rod_length_m_maximum(geometry_panel):
    """��������� �������� piston_rod_length_m_slider = 0.500 �"""
    assert geometry_panel.piston_rod_length_m_slider.maximum() == 0.500, \
        f"piston_rod_length_m maximum ������ ���� 0.500, �������� {geometry_panel.piston_rod_length_m_slider.maximum()}"


def test_piston_rod_length_m_default_value(geometry_panel):
    """��������� �������� �� ��������� piston_rod_length_m_slider = 0.200 �"""
    assert geometry_panel.piston_rod_length_m_slider.value() == 0.200, \
        f"piston_rod_length_m default ������ ���� 0.200, �������� {geometry_panel.piston_rod_length_m_slider.value()}"


def test_piston_rod_length_m_step(geometry_panel):
    """��������� ��� piston_rod_length_m_slider = 0.001 �"""
    assert geometry_panel.piston_rod_length_m_slider.step() == 0.001, \
        f"piston_rod_length_m step ������ ���� 0.001, �������� {geometry_panel.piston_rod_length_m_slider.step()}"


def test_piston_rod_length_m_decimals(geometry_panel):
    """��������� decimals piston_rod_length_m_slider = 3"""
    assert geometry_panel.piston_rod_length_m_slider.decimals() == 3, \
        f"piston_rod_length_m decimals ������ ���� 3, �������� {geometry_panel.piston_rod_length_m_slider.decimals()}"


def test_piston_rod_length_m_units(geometry_panel):
    """��������� ������� piston_rod_length_m_slider = '�'"""
    assert geometry_panel.piston_rod_length_m_slider.units() == "�", \
        f"piston_rod_length_m units ������ ���� '�', �������� '{geometry_panel.piston_rod_length_m_slider.units()}'"


# ============================================================================
# ��-2: ����� ���������� piston_thickness_m_slider
# ============================================================================

def test_piston_thickness_m_minimum(geometry_panel):
    """��������� ������� piston_thickness_m_slider = 0.010 �"""
    assert geometry_panel.piston_thickness_m_slider.minimum() == 0.010, \
        f"piston_thickness_m minimum ������ ���� 0.010, �������� {geometry_panel.piston_thickness_m_slider.minimum()}"


def test_piston_thickness_m_maximum(geometry_panel):
    """��������� �������� piston_thickness_m_slider = 0.050 �"""
    assert geometry_panel.piston_thickness_m_slider.maximum() == 0.050, \
        f"piston_thickness_m maximum ������ ���� 0.050, �������� {geometry_panel.piston_thickness_m_slider.maximum()}"


def test_piston_thickness_m_default_value(geometry_panel):
    """��������� �������� �� ��������� piston_thickness_m_slider = 0.025 �"""
    assert geometry_panel.piston_thickness_m_slider.value() == 0.025, \
        f"piston_thickness_m default ������ ���� 0.025, �������� {geometry_panel.piston_thickness_m_slider.value()}"


def test_piston_thickness_m_step(geometry_panel):
    """��������� ��� piston_thickness_m_slider = 0.001 �"""
    assert geometry_panel.piston_thickness_m_slider.step() == 0.001, \
        f"piston_thickness_m step ������ ���� 0.001, �������� {geometry_panel.piston_thickness_m_slider.step()}"


def test_piston_thickness_m_decimals(geometry_panel):
    """��������� decimals piston_thickness_m_slider = 3"""
    assert geometry_panel.piston_thickness_m_slider.decimals() == 3, \
        f"piston_thickness_m decimals ������ ���� 3, �������� {geometry_panel.piston_thickness_m_slider.decimals()}"


def test_piston_thickness_m_units(geometry_panel):
    """��������� ������� piston_thickness_m_slider = '�'"""
    assert geometry_panel.piston_thickness_m_slider.units() == "�", \
        f"piston_thickness_m units ������ ���� '�', �������� '{geometry_panel.piston_thickness_m_slider.units()}'"


# ============================================================================
# ��-2: ����� ���������� � ������� parameters
# ============================================================================

def test_parameters_has_rod_diameter_m(geometry_panel):
    """��������� ������� rod_diameter_m � parameters"""
    params = geometry_panel.get_parameters()
    assert 'rod_diameter_m' in params, \
        "parameters ������ ��������� ���� 'rod_diameter_m'"
    assert params['rod_diameter_m'] == 0.035, \
        f"rod_diameter_m ������ ���� 0.035, �������� {params['rod_diameter_m']}"


def test_parameters_has_piston_rod_length_m(geometry_panel):
    """��������� ������� piston_rod_length_m � parameters"""
    params = geometry_panel.get_parameters()
    assert 'piston_rod_length_m' in params, \
        "parameters ������ ��������� ���� 'piston_rod_length_m'"
    assert params['piston_rod_length_m'] == 0.200, \
        f"piston_rod_length_m ������ ���� 0.200, �������� {params['piston_rod_length_m']}"


def test_parameters_has_piston_thickness_m(geometry_panel):
    """��������� ������� piston_thickness_m � parameters"""
    params = geometry_panel.get_parameters()
    assert 'piston_thickness_m' in params, \
        "parameters ������ ��������� ���� 'piston_thickness_m'"
    assert params['piston_thickness_m'] == 0.025, \
        f"piston_thickness_m ������ ���� 0.025, �������� {params['piston_thickness_m']}"


def test_parameters_no_rod_diameter(geometry_panel):
    """��������� ���������� rod_diameter � parameters"""
    params = geometry_panel.get_parameters()
    assert 'rod_diameter' not in params, \
        "parameters �� ������ ��������� ���� 'rod_diameter' (������ �� rod_diameter_m)"


def test_parameters_no_piston_rod_length(geometry_panel):
    """��������� ���������� piston_rod_length � parameters"""
    params = geometry_panel.get_parameters()
    assert 'piston_rod_length' not in params, \
        "parameters �� ������ ��������� ���� 'piston_rod_length' (������ �� piston_rod_length_m)"


def test_parameters_no_piston_thickness(geometry_panel):
    """��������� ���������� piston_thickness � parameters"""
    params = geometry_panel.get_parameters()
    assert 'piston_thickness' not in params, \
        "parameters �� ������ ��������� ���� 'piston_thickness' (������ �� piston_thickness_m)"


# ============================================================================
# ��-2: �������������� ����� (�������, ���������)
# ============================================================================

def test_rod_diameter_m_signal_emission(geometry_panel, qtbot):
    """��������� emission ������� parameter_changed ��� ��������� rod_diameter_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.rod_diameter_m_slider.setValue(0.040)

    # ��������� ��������� �������
    assert blocker.args == ['rod_diameter_m', 0.040], \
        f"������ ������ ���� ('rod_diameter_m', 0.040), �������� {blocker.args}"


def test_piston_rod_length_m_signal_emission(geometry_panel, qtbot):
    """��������� emission ������� parameter_changed ��� ��������� piston_rod_length_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.piston_rod_length_m_slider.setValue(0.300)

    assert blocker.args == ['piston_rod_length_m', 0.300], \
        f"������ ������ ���� ('piston_rod_length_m', 0.300), �������� {blocker.args}"


def test_piston_thickness_m_signal_emission(geometry_panel, qtbot):
    """��������� emission ������� parameter_changed ��� ��������� piston_thickness_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.piston_thickness_m_slider.setValue(0.030)

    assert blocker.args == ['piston_thickness_m', 0.030], \
        f"������ ������ ���� ('piston_thickness_m', 0.030), �������� {blocker.args}"


def test_geometry_updated_signal_with_m_params(geometry_panel, qtbot):
    """��������� emission ������� geometry_updated � ������ ����������� � ������"""
    with qtbot.waitSignal(geometry_panel.geometry_updated, timeout=1000) as blocker:
        geometry_panel.rod_diameter_m_slider.setValue(0.045)

    # ���������, ��� ������� �������� ����� ���������
    params = blocker.args[0]
    assert 'rod_diameter_m' in params
    assert params['rod_diameter_m'] == 0.045


def test_rod_diameter_m_validation_updated(geometry_panel):
    """��������� ���������: rod_diameter_m < 80% cyl_diam_m (��� � ������)"""
    # ���������� ������� �������� 0.080 �
    geometry_panel.cyl_diam_m_slider.setValue(0.080)

    # ���������� ������� ����� 0.035 � (< 80% �� 0.080 � = 0.064 �) - OK
    geometry_panel.rod_diameter_m_slider.setValue(0.035)
    params = geometry_panel.get_parameters()
    assert params['rod_diameter_m'] == 0.035


def test_reset_to_defaults_sets_m_params(geometry_panel):
    """���������, ��� ����� � ���������� ������������� ��������� � ������"""
    # �������� ��������
    geometry_panel.rod_diameter_m_slider.setValue(0.050)
    geometry_panel.piston_rod_length_m_slider.setValue(0.400)
    geometry_panel.piston_thickness_m_slider.setValue(0.040)

    # ��������
    geometry_panel._reset_to_defaults()

    # ��������� ��������
    assert geometry_panel.rod_diameter_m_slider.value() == 0.035
    assert geometry_panel.piston_rod_length_m_slider.value() == 0.200
    assert geometry_panel.piston_thickness_m_slider.value() == 0.025


def test_set_parameters_accepts_m_params(geometry_panel):
    """���������, ��� set_parameters ��������� ��������� � ������"""
    new_params = {
        'rod_diameter_m': 0.042,
        'piston_rod_length_m': 0.350,
        'piston_thickness_m': 0.032
    }

    geometry_panel.set_parameters(new_params)

    params = geometry_panel.get_parameters()
    assert params['rod_diameter_m'] == 0.042
    assert params['piston_rod_length_m'] == 0.350
    assert params['piston_thickness_m'] == 0.032


def test_presets_use_m_params(geometry_panel):
    """���������, ��� ������� ���������� ��������� � ������"""
    # ���������� ������ "˸���� ������������"
    geometry_panel._on_preset_changed(1)

    params = geometry_panel.get_parameters()
    assert 'rod_diameter_m' in params
    assert params['rod_diameter_m'] == 0.028  # 28 �� -> 0.028 �

    # ���������� ������ "������ ��������"
    geometry_panel._on_preset_changed(2)

    params = geometry_panel.get_parameters()
    assert params['rod_diameter_m'] == 0.045  # 45 �� -> 0.045 �


# ============================================================================
# ��-2: �������� ����������� � geometry_changed
# ============================================================================

def test_geometry_changed_uses_m_params(geometry_panel, qtbot):
    """���������, ��� geometry_changed ���������� ��������� � ������ � ���������� ������������"""
    with qtbot.waitSignal(geometry_panel.geometry_changed, timeout=1000) as blocker:
        geometry_panel.rod_diameter_m_slider.setValue(0.040)  # 0.040 � = 40 ��

    # ���������, ��� � 3D ������� �������� �������������� ���������
    geometry_3d = blocker.args[0]
    assert 'rodDiameterM' in geometry_3d
    assert geometry_3d['rodDiameterM'] == 40.0  # 0.040 � * 1000 = 40 ��


# ============================================================================
# ��-2: �������� ����������� ����
# ============================================================================

def test_ms2_complete_si_units(geometry_panel):
    """��-2: ����������� ���� - ��� ��������� ���������� � �� �������"""
    # 1. ��������� ������� ����� ��������� � ������
    assert hasattr(geometry_panel, 'rod_diameter_m_slider')
    assert hasattr(geometry_panel, 'piston_rod_length_m_slider')
    assert hasattr(geometry_panel, 'piston_thickness_m_slider')

    # 2. ��������� ���������� ������ ��������� � ��
    assert not hasattr(geometry_panel, 'rod_diameter_slider')
    assert not hasattr(geometry_panel, 'piston_rod_length_slider')
    assert not hasattr(geometry_panel, 'piston_thickness_slider')

    # 3. ��������� ��������� � �������
    params = geometry_panel.get_parameters()
    assert 'rod_diameter_m' in params
    assert 'piston_rod_length_m' in params
    assert 'piston_thickness_m' in params
    assert 'rod_diameter' not in params
    assert 'piston_rod_length' not in params
    assert 'piston_thickness' not in params

    # 4. ��������� ������� ��������� ��
    assert geometry_panel.rod_diameter_m_slider.units() == "�"
    assert geometry_panel.piston_rod_length_m_slider.units() == "�"
    assert geometry_panel.piston_thickness_m_slider.units() == "�"

    # 5. ��������� ��� = 0.001
    assert geometry_panel.rod_diameter_m_slider.step() == 0.001
    assert geometry_panel.piston_rod_length_m_slider.step() == 0.001
    assert geometry_panel.piston_thickness_m_slider.step() == 0.001

    # 6. ��������� decimals = 3
    assert geometry_panel.rod_diameter_m_slider.decimals() == 3
    assert geometry_panel.piston_rod_length_m_slider.decimals() == 3
    assert geometry_panel.piston_thickness_m_slider.decimals() == 3

    # 7. ��������� ��������� �������������� ���������
    # rod_diameter: 20-60 �� -> 0.020-0.060 �
    assert geometry_panel.rod_diameter_m_slider.minimum() == 0.020
    assert geometry_panel.rod_diameter_m_slider.maximum() == 0.060

    # piston_rod_length: 100-500 �� -> 0.100-0.500 �
    assert geometry_panel.piston_rod_length_m_slider.minimum() == 0.100
    assert geometry_panel.piston_rod_length_m_slider.maximum() == 0.500

    # piston_thickness: 10-50 �� -> 0.010-0.050 �
    assert geometry_panel.piston_thickness_m_slider.minimum() == 0.010
    assert geometry_panel.piston_thickness_m_slider.maximum() == 0.050

    # 8. ��������� �������� �� ��������� �������������� ���������
    assert geometry_panel.rod_diameter_m_slider.value() == 0.035   # 35 �� -> 0.035 �
    assert geometry_panel.piston_rod_length_m_slider.value() == 0.200  # 200 �� -> 0.200 �
    assert geometry_panel.piston_thickness_m_slider.value() == 0.025   # 25 �� -> 0.025 �

    print("? ��-2: ��� �������� ������ ���������!")


def test_all_linear_params_si_units(geometry_panel):
    """��-2: ���������, ��� ��� �������� ��������� � �� �������� (������)"""
    params = geometry_panel.get_parameters()

    # ������� ��� �������� ��������� � �� �������
    linear_params = {}

    # �� ��-0: ��� � ������
    linear_params['wheelbase'] = geometry_panel.wheelbase_slider.units()
    linear_params['track'] = geometry_panel.track_slider.units()
    linear_params['frame_to_pivot'] = geometry_panel.frame_to_pivot_slider.units()
    linear_params['lever_length'] = geometry_panel.lever_length_slider.units()
    linear_params['cylinder_length'] = geometry_panel.cylinder_length_slider.units()

    # �� ��-1: ����� � ������
    linear_params['cyl_diam_m'] = geometry_panel.cyl_diam_m_slider.units()
    linear_params['stroke_m'] = geometry_panel.stroke_m_slider.units()
    linear_params['dead_gap_m'] = geometry_panel.dead_gap_m_slider.units()

    # �� ��-2: ����������� � �����
    linear_params['rod_diameter_m'] = geometry_panel.rod_diameter_m_slider.units()
    linear_params['piston_rod_length_m'] = geometry_panel.piston_rod_length_m_slider.units()
    linear_params['piston_thickness_m'] = geometry_panel.piston_thickness_m_slider.units()

    # ���������, ��� ��� �������� ��������� � ������
    for param_name, units in linear_params.items():
        assert units == "�", f"�������� {param_name} ������ ���� � ������, �������� '{units}'"

    print(f"? ��� {len(linear_params)} �������� ���������� � �� �������� (������)!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
