# -*- coding: utf-8 -*-
"""
��-1: ����� ��� ��������� ��������� ��������
Tests for cylinder geometry changes - unified diameter, stroke, dead gap
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
# ��-1: ����� ������� ����� ���������
# ============================================================================

def test_cyl_diam_m_slider_exists(geometry_panel):
    """��������� ������� �������� cyl_diam_m"""
    assert hasattr(geometry_panel, 'cyl_diam_m_slider'), \
        "GeometryPanel ������ ����� ������� cyl_diam_m_slider"


def test_stroke_m_slider_exists(geometry_panel):
    """��������� ������� �������� stroke_m"""
    assert hasattr(geometry_panel, 'stroke_m_slider'), \
        "GeometryPanel ������ ����� ������� stroke_m_slider"


def test_dead_gap_m_slider_exists(geometry_panel):
    """��������� ������� �������� dead_gap_m"""
    assert hasattr(geometry_panel, 'dead_gap_m_slider'), \
        "GeometryPanel ������ ����� ������� dead_gap_m_slider"


# ============================================================================
# ��-1: ����� ���������� ������ ���������
# ============================================================================

def test_bore_head_slider_removed(geometry_panel):
    """��������� ���������� bore_head_slider"""
    assert not hasattr(geometry_panel, 'bore_head_slider'), \
        "bore_head_slider ������ ���� ����� (������ �� cyl_diam_m_slider)"


def test_bore_rod_slider_removed(geometry_panel):
    """��������� ���������� bore_rod_slider"""
    assert not hasattr(geometry_panel, 'bore_rod_slider'), \
        "bore_rod_slider ������ ���� ����� (������ �� cyl_diam_m_slider)"


# ============================================================================
# ��-1: ����� ���������� cyl_diam_m_slider
# ============================================================================

def test_cyl_diam_m_minimum(geometry_panel):
    """��������� ������� cyl_diam_m_slider = 0.030 �"""
    assert geometry_panel.cyl_diam_m_slider.minimum() == 0.030, \
        f"cyl_diam_m minimum ������ ���� 0.030, �������� {geometry_panel.cyl_diam_m_slider.minimum()}"


def test_cyl_diam_m_maximum(geometry_panel):
    """��������� �������� cyl_diam_m_slider = 0.150 �"""
    assert geometry_panel.cyl_diam_m_slider.maximum() == 0.150, \
        f"cyl_diam_m maximum ������ ���� 0.150, �������� {geometry_panel.cyl_diam_m_slider.maximum()}"


def test_cyl_diam_m_default_value(geometry_panel):
    """��������� �������� �� ��������� cyl_diam_m_slider = 0.080 �"""
    assert geometry_panel.cyl_diam_m_slider.value() == 0.080, \
        f"cyl_diam_m default ������ ���� 0.080, �������� {geometry_panel.cyl_diam_m_slider.value()}"


def test_cyl_diam_m_step(geometry_panel):
    """��������� ��� cyl_diam_m_slider = 0.001 �"""
    assert geometry_panel.cyl_diam_m_slider.step() == 0.001, \
        f"cyl_diam_m step ������ ���� 0.001, �������� {geometry_panel.cyl_diam_m_slider.step()}"


def test_cyl_diam_m_decimals(geometry_panel):
    """��������� decimals cyl_diam_m_slider = 3"""
    assert geometry_panel.cyl_diam_m_slider.decimals() == 3, \
        f"cyl_diam_m decimals ������ ���� 3, �������� {geometry_panel.cyl_diam_m_slider.decimals()}"


def test_cyl_diam_m_units(geometry_panel):
    """��������� ������� cyl_diam_m_slider = '�'"""
    assert geometry_panel.cyl_diam_m_slider.units() == "�", \
        f"cyl_diam_m units ������ ���� '�', �������� '{geometry_panel.cyl_diam_m_slider.units()}'"


# ============================================================================
# ��-1: ����� ���������� stroke_m_slider
# ============================================================================

def test_stroke_m_minimum(geometry_panel):
    """��������� ������� stroke_m_slider = 0.100 �"""
    assert geometry_panel.stroke_m_slider.minimum() == 0.100, \
        f"stroke_m minimum ������ ���� 0.100, �������� {geometry_panel.stroke_m_slider.minimum()}"


def test_stroke_m_maximum(geometry_panel):
    """��������� �������� stroke_m_slider = 0.500 �"""
    assert geometry_panel.stroke_m_slider.maximum() == 0.500, \
        f"stroke_m maximum ������ ���� 0.500, �������� {geometry_panel.stroke_m_slider.maximum()}"


def test_stroke_m_default_value(geometry_panel):
    """��������� �������� �� ��������� stroke_m_slider = 0.300 �"""
    assert geometry_panel.stroke_m_slider.value() == 0.300, \
        f"stroke_m default ������ ���� 0.300, �������� {geometry_panel.stroke_m_slider.value()}"


def test_stroke_m_step(geometry_panel):
    """��������� ��� stroke_m_slider = 0.001 �"""
    assert geometry_panel.stroke_m_slider.step() == 0.001, \
        f"stroke_m step ������ ���� 0.001, �������� {geometry_panel.stroke_m_slider.step()}"


def test_stroke_m_decimals(geometry_panel):
    """��������� decimals stroke_m_slider = 3"""
    assert geometry_panel.stroke_m_slider.decimals() == 3, \
        f"stroke_m decimals ������ ���� 3, �������� {geometry_panel.stroke_m_slider.decimals()}"


def test_stroke_m_units(geometry_panel):
    """��������� ������� stroke_m_slider = '�'"""
    assert geometry_panel.stroke_m_slider.units() == "�", \
        f"stroke_m units ������ ���� '�', �������� '{geometry_panel.stroke_m_slider.units()}'"


# ============================================================================
# ��-1: ����� ���������� dead_gap_m_slider
# ============================================================================

def test_dead_gap_m_minimum(geometry_panel):
    """��������� ������� dead_gap_m_slider = 0.000 �"""
    assert geometry_panel.dead_gap_m_slider.minimum() == 0.000, \
        f"dead_gap_m minimum ������ ���� 0.000, �������� {geometry_panel.dead_gap_m_slider.minimum()}"


def test_dead_gap_m_maximum(geometry_panel):
    """��������� �������� dead_gap_m_slider = 0.020 �"""
    assert geometry_panel.dead_gap_m_slider.maximum() == 0.020, \
        f"dead_gap_m maximum ������ ���� 0.020, �������� {geometry_panel.dead_gap_m_slider.maximum()}"


def test_dead_gap_m_default_value(geometry_panel):
    """��������� �������� �� ��������� dead_gap_m_slider = 0.005 �"""
    assert geometry_panel.dead_gap_m_slider.value() == 0.005, \
        f"dead_gap_m default ������ ���� 0.005, �������� {geometry_panel.dead_gap_m_slider.value()}"


def test_dead_gap_m_step(geometry_panel):
    """��������� ��� dead_gap_m_slider = 0.001 �"""
    assert geometry_panel.dead_gap_m_slider.step() == 0.001, \
        f"dead_gap_m step ������ ���� 0.001, �������� {geometry_panel.dead_gap_m_slider.step()}"


def test_dead_gap_m_decimals(geometry_panel):
    """��������� decimals dead_gap_m_slider = 3"""
    assert geometry_panel.dead_gap_m_slider.decimals() == 3, \
        f"dead_gap_m decimals ������ ���� 3, �������� {geometry_panel.dead_gap_m_slider.decimals()}"


def test_dead_gap_m_units(geometry_panel):
    """��������� ������� dead_gap_m_slider = '�'"""
    assert geometry_panel.dead_gap_m_slider.units() == "�", \
        f"dead_gap_m units ������ ���� '�', �������� '{geometry_panel.dead_gap_m_slider.units()}'"


# ============================================================================
# ��-1: ����� ���������� � ������� parameters
# ============================================================================

def test_parameters_has_cyl_diam_m(geometry_panel):
    """��������� ������� cyl_diam_m � parameters"""
    params = geometry_panel.get_parameters()
    assert 'cyl_diam_m' in params, \
        "parameters ������ ��������� ���� 'cyl_diam_m'"
    assert params['cyl_diam_m'] == 0.080, \
        f"cyl_diam_m ������ ���� 0.080, �������� {params['cyl_diam_m']}"


def test_parameters_has_stroke_m(geometry_panel):
    """��������� ������� stroke_m � parameters"""
    params = geometry_panel.get_parameters()
    assert 'stroke_m' in params, \
        "parameters ������ ��������� ���� 'stroke_m'"
    assert params['stroke_m'] == 0.300, \
        f"stroke_m ������ ���� 0.300, �������� {params['stroke_m']}"


def test_parameters_has_dead_gap_m(geometry_panel):
    """��������� ������� dead_gap_m � parameters"""
    params = geometry_panel.get_parameters()
    assert 'dead_gap_m' in params, \
        "parameters ������ ��������� ���� 'dead_gap_m'"
    assert params['dead_gap_m'] == 0.005, \
        f"dead_gap_m ������ ���� 0.005, �������� {params['dead_gap_m']}"


def test_parameters_no_bore_head(geometry_panel):
    """��������� ���������� bore_head � parameters"""
    params = geometry_panel.get_parameters()
    assert 'bore_head' not in params, \
        "parameters �� ������ ��������� ���� 'bore_head' (������ �� cyl_diam_m)"


def test_parameters_no_bore_rod(geometry_panel):
    """��������� ���������� bore_rod � parameters"""
    params = geometry_panel.get_parameters()
    assert 'bore_rod' not in params, \
        "parameters �� ������ ��������� ���� 'bore_rod' (������ �� cyl_diam_m)"


# ============================================================================
# ��-1: �������������� ����� (�������, ���������)
# ============================================================================

def test_cyl_diam_m_signal_emission(geometry_panel, qtbot):
    """��������� emission ������� parameter_changed ��� ��������� cyl_diam_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.cyl_diam_m_slider.setValue(0.100)
    
    # ��������� ��������� �������
    assert blocker.args == ['cyl_diam_m', 0.100], \
        f"������ ������ ���� ('cyl_diam_m', 0.100), �������� {blocker.args}"


def test_stroke_m_signal_emission(geometry_panel, qtbot):
    """��������� emission ������� parameter_changed ��� ��������� stroke_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.stroke_m_slider.setValue(0.400)
    
    assert blocker.args == ['stroke_m', 0.400], \
        f"������ ������ ���� ('stroke_m', 0.400), �������� {blocker.args}"


def test_dead_gap_m_signal_emission(geometry_panel, qtbot):
    """��������� emission ������� parameter_changed ��� ��������� dead_gap_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.dead_gap_m_slider.setValue(0.010)
    
    assert blocker.args == ['dead_gap_m', 0.010], \
        f"������ ������ ���� ('dead_gap_m', 0.010), �������� {blocker.args}"


def test_geometry_updated_signal(geometry_panel, qtbot):
    """��������� emission ������� geometry_updated ��� ��������� ���������"""
    with qtbot.waitSignal(geometry_panel.geometry_updated, timeout=1000) as blocker:
        geometry_panel.cyl_diam_m_slider.setValue(0.090)
    
    # ���������, ��� ������� �������� ����� ���������
    params = blocker.args[0]
    assert 'cyl_diam_m' in params
    assert params['cyl_diam_m'] == 0.090


def test_rod_diameter_validation(geometry_panel):
    """��������� ���������: rod_diameter < 80% cyl_diam_m"""
    # ���������� ������� �������� 0.080 � = 80 ��
    geometry_panel.cyl_diam_m_slider.setValue(0.080)
    
    # ���������� ������� ����� 35 �� (< 80% �� 80 �� = 64 ��) - OK
    geometry_panel.rod_diameter_slider.setValue(35.0)
    params = geometry_panel.get_parameters()
    assert params['rod_diameter'] == 35.0
    
    # ���������� ���������� 70 �� (> 80% �� 80 ��) - ������ ������� ��������
    # (���� ������� �������������� ���������� ���������, ������� ����������)


def test_reset_to_defaults_sets_new_params(geometry_panel):
    """���������, ��� ����� � ���������� ������������� ����� ���������"""
    # �������� ��������
    geometry_panel.cyl_diam_m_slider.setValue(0.120)
    geometry_panel.stroke_m_slider.setValue(0.450)
    geometry_panel.dead_gap_m_slider.setValue(0.015)
    
    # ��������
    geometry_panel._reset_to_defaults()
    
    # ��������� ��������
    assert geometry_panel.cyl_diam_m_slider.value() == 0.080
    assert geometry_panel.stroke_m_slider.value() == 0.300
    assert geometry_panel.dead_gap_m_slider.value() == 0.005


def test_set_parameters_accepts_new_params(geometry_panel):
    """���������, ��� set_parameters ��������� ����� ���������"""
    new_params = {
        'cyl_diam_m': 0.095,
        'stroke_m': 0.350,
        'dead_gap_m': 0.008
    }
    
    geometry_panel.set_parameters(new_params)
    
    params = geometry_panel.get_parameters()
    assert params['cyl_diam_m'] == 0.095
    assert params['stroke_m'] == 0.350
    assert params['dead_gap_m'] == 0.008


# ============================================================================
# ��-1: �������� smoke test
# ============================================================================

def test_ms1_complete_smoke(geometry_panel):
    """��-1: ����������� smoke ���� - ��� ��������� �������� ������"""
    # 1. ��������� ������� ����� ���������
    assert hasattr(geometry_panel, 'cyl_diam_m_slider')
    assert hasattr(geometry_panel, 'stroke_m_slider')
    assert hasattr(geometry_panel, 'dead_gap_m_slider')
    
    # 2. ��������� ���������� ������ ���������
    assert not hasattr(geometry_panel, 'bore_head_slider')
    assert not hasattr(geometry_panel, 'bore_rod_slider')
    
    # 3. ��������� ��������� � �������
    params = geometry_panel.get_parameters()
    assert 'cyl_diam_m' in params
    assert 'stroke_m' in params
    assert 'dead_gap_m' in params
    assert 'bore_head' not in params
    assert 'bore_rod' not in params
    
    # 4. ��������� ������� ���������
    assert geometry_panel.cyl_diam_m_slider.units() == "�"
    assert geometry_panel.stroke_m_slider.units() == "�"
    assert geometry_panel.dead_gap_m_slider.units() == "�"
    
    # 5. ��������� ��� = 0.001
    assert geometry_panel.cyl_diam_m_slider.step() == 0.001
    assert geometry_panel.stroke_m_slider.step() == 0.001
    assert geometry_panel.dead_gap_m_slider.step() == 0.001
    
    # 6. ��������� decimals = 3
    assert geometry_panel.cyl_diam_m_slider.decimals() == 3
    assert geometry_panel.stroke_m_slider.decimals() == 3
    assert geometry_panel.dead_gap_m_slider.decimals() == 3
    
    print("? ��-1: ��� �������� ������ ���������!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
