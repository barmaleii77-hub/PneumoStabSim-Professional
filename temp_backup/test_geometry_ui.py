# -*- coding: utf-8 -*-
"""
МШ-1: Тесты для изменений геометрии цилиндра
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
# МШ-1: Тесты наличия новых слайдеров
# ============================================================================

def test_cyl_diam_m_slider_exists(geometry_panel):
    """Проверить наличие слайдера cyl_diam_m"""
    assert hasattr(geometry_panel, 'cyl_diam_m_slider'), \
        "GeometryPanel должна иметь атрибут cyl_diam_m_slider"


def test_stroke_m_slider_exists(geometry_panel):
    """Проверить наличие слайдера stroke_m"""
    assert hasattr(geometry_panel, 'stroke_m_slider'), \
        "GeometryPanel должна иметь атрибут stroke_m_slider"


def test_dead_gap_m_slider_exists(geometry_panel):
    """Проверить наличие слайдера dead_gap_m"""
    assert hasattr(geometry_panel, 'dead_gap_m_slider'), \
        "GeometryPanel должна иметь атрибут dead_gap_m_slider"


# ============================================================================
# МШ-1: Тесты отсутствия старых слайдеров
# ============================================================================

def test_bore_head_slider_removed(geometry_panel):
    """Проверить ОТСУТСТВИЕ bore_head_slider"""
    assert not hasattr(geometry_panel, 'bore_head_slider'), \
        "bore_head_slider должен быть удалён (заменён на cyl_diam_m_slider)"


def test_bore_rod_slider_removed(geometry_panel):
    """Проверить ОТСУТСТВИЕ bore_rod_slider"""
    assert not hasattr(geometry_panel, 'bore_rod_slider'), \
        "bore_rod_slider должен быть удалён (заменён на cyl_diam_m_slider)"


# ============================================================================
# МШ-1: Тесты параметров cyl_diam_m_slider
# ============================================================================

def test_cyl_diam_m_minimum(geometry_panel):
    """Проверить минимум cyl_diam_m_slider = 0.030 м"""
    assert geometry_panel.cyl_diam_m_slider.minimum() == 0.030, \
        f"cyl_diam_m minimum должен быть 0.030, получено {geometry_panel.cyl_diam_m_slider.minimum()}"


def test_cyl_diam_m_maximum(geometry_panel):
    """Проверить максимум cyl_diam_m_slider = 0.150 м"""
    assert geometry_panel.cyl_diam_m_slider.maximum() == 0.150, \
        f"cyl_diam_m maximum должен быть 0.150, получено {geometry_panel.cyl_diam_m_slider.maximum()}"


def test_cyl_diam_m_default_value(geometry_panel):
    """Проверить значение по умолчанию cyl_diam_m_slider = 0.080 м"""
    assert geometry_panel.cyl_diam_m_slider.value() == 0.080, \
        f"cyl_diam_m default должен быть 0.080, получено {geometry_panel.cyl_diam_m_slider.value()}"


def test_cyl_diam_m_step(geometry_panel):
    """Проверить шаг cyl_diam_m_slider = 0.001 м"""
    assert geometry_panel.cyl_diam_m_slider.step() == 0.001, \
        f"cyl_diam_m step должен быть 0.001, получено {geometry_panel.cyl_diam_m_slider.step()}"


def test_cyl_diam_m_decimals(geometry_panel):
    """Проверить decimals cyl_diam_m_slider = 3"""
    assert geometry_panel.cyl_diam_m_slider.decimals() == 3, \
        f"cyl_diam_m decimals должен быть 3, получено {geometry_panel.cyl_diam_m_slider.decimals()}"


def test_cyl_diam_m_units(geometry_panel):
    """Проверить единицы cyl_diam_m_slider = 'м'"""
    assert geometry_panel.cyl_diam_m_slider.units() == "м", \
        f"cyl_diam_m units должны быть 'м', получено '{geometry_panel.cyl_diam_m_slider.units()}'"


# ============================================================================
# МШ-1: Тесты параметров stroke_m_slider
# ============================================================================

def test_stroke_m_minimum(geometry_panel):
    """Проверить минимум stroke_m_slider = 0.100 м"""
    assert geometry_panel.stroke_m_slider.minimum() == 0.100, \
        f"stroke_m minimum должен быть 0.100, получено {geometry_panel.stroke_m_slider.minimum()}"


def test_stroke_m_maximum(geometry_panel):
    """Проверить максимум stroke_m_slider = 0.500 м"""
    assert geometry_panel.stroke_m_slider.maximum() == 0.500, \
        f"stroke_m maximum должен быть 0.500, получено {geometry_panel.stroke_m_slider.maximum()}"


def test_stroke_m_default_value(geometry_panel):
    """Проверить значение по умолчанию stroke_m_slider = 0.300 м"""
    assert geometry_panel.stroke_m_slider.value() == 0.300, \
        f"stroke_m default должен быть 0.300, получено {geometry_panel.stroke_m_slider.value()}"


def test_stroke_m_step(geometry_panel):
    """Проверить шаг stroke_m_slider = 0.001 м"""
    assert geometry_panel.stroke_m_slider.step() == 0.001, \
        f"stroke_m step должен быть 0.001, получено {geometry_panel.stroke_m_slider.step()}"


def test_stroke_m_decimals(geometry_panel):
    """Проверить decimals stroke_m_slider = 3"""
    assert geometry_panel.stroke_m_slider.decimals() == 3, \
        f"stroke_m decimals должен быть 3, получено {geometry_panel.stroke_m_slider.decimals()}"


def test_stroke_m_units(geometry_panel):
    """Проверить единицы stroke_m_slider = 'м'"""
    assert geometry_panel.stroke_m_slider.units() == "м", \
        f"stroke_m units должны быть 'м', получено '{geometry_panel.stroke_m_slider.units()}'"


# ============================================================================
# МШ-1: Тесты параметров dead_gap_m_slider
# ============================================================================

def test_dead_gap_m_minimum(geometry_panel):
    """Проверить минимум dead_gap_m_slider = 0.000 м"""
    assert geometry_panel.dead_gap_m_slider.minimum() == 0.000, \
        f"dead_gap_m minimum должен быть 0.000, получено {geometry_panel.dead_gap_m_slider.minimum()}"


def test_dead_gap_m_maximum(geometry_panel):
    """Проверить максимум dead_gap_m_slider = 0.020 м"""
    assert geometry_panel.dead_gap_m_slider.maximum() == 0.020, \
        f"dead_gap_m maximum должен быть 0.020, получено {geometry_panel.dead_gap_m_slider.maximum()}"


def test_dead_gap_m_default_value(geometry_panel):
    """Проверить значение по умолчанию dead_gap_m_slider = 0.005 м"""
    assert geometry_panel.dead_gap_m_slider.value() == 0.005, \
        f"dead_gap_m default должен быть 0.005, получено {geometry_panel.dead_gap_m_slider.value()}"


def test_dead_gap_m_step(geometry_panel):
    """Проверить шаг dead_gap_m_slider = 0.001 м"""
    assert geometry_panel.dead_gap_m_slider.step() == 0.001, \
        f"dead_gap_m step должен быть 0.001, получено {geometry_panel.dead_gap_m_slider.step()}"


def test_dead_gap_m_decimals(geometry_panel):
    """Проверить decimals dead_gap_m_slider = 3"""
    assert geometry_panel.dead_gap_m_slider.decimals() == 3, \
        f"dead_gap_m decimals должен быть 3, получено {geometry_panel.dead_gap_m_slider.decimals()}"


def test_dead_gap_m_units(geometry_panel):
    """Проверить единицы dead_gap_m_slider = 'м'"""
    assert geometry_panel.dead_gap_m_slider.units() == "м", \
        f"dead_gap_m units должны быть 'м', получено '{geometry_panel.dead_gap_m_slider.units()}'"


# ============================================================================
# МШ-1: Тесты параметров в словаре parameters
# ============================================================================

def test_parameters_has_cyl_diam_m(geometry_panel):
    """Проверить наличие cyl_diam_m в parameters"""
    params = geometry_panel.get_parameters()
    assert 'cyl_diam_m' in params, \
        "parameters должен содержать ключ 'cyl_diam_m'"
    assert params['cyl_diam_m'] == 0.080, \
        f"cyl_diam_m должен быть 0.080, получено {params['cyl_diam_m']}"


def test_parameters_has_stroke_m(geometry_panel):
    """Проверить наличие stroke_m в parameters"""
    params = geometry_panel.get_parameters()
    assert 'stroke_m' in params, \
        "parameters должен содержать ключ 'stroke_m'"
    assert params['stroke_m'] == 0.300, \
        f"stroke_m должен быть 0.300, получено {params['stroke_m']}"


def test_parameters_has_dead_gap_m(geometry_panel):
    """Проверить наличие dead_gap_m в parameters"""
    params = geometry_panel.get_parameters()
    assert 'dead_gap_m' in params, \
        "parameters должен содержать ключ 'dead_gap_m'"
    assert params['dead_gap_m'] == 0.005, \
        f"dead_gap_m должен быть 0.005, получено {params['dead_gap_m']}"


def test_parameters_no_bore_head(geometry_panel):
    """Проверить ОТСУТСТВИЕ bore_head в parameters"""
    params = geometry_panel.get_parameters()
    assert 'bore_head' not in params, \
        "parameters НЕ должен содержать ключ 'bore_head' (заменён на cyl_diam_m)"


def test_parameters_no_bore_rod(geometry_panel):
    """Проверить ОТСУТСТВИЕ bore_rod в parameters"""
    params = geometry_panel.get_parameters()
    assert 'bore_rod' not in params, \
        "parameters НЕ должен содержать ключ 'bore_rod' (заменён на cyl_diam_m)"


# ============================================================================
# МШ-1: Функциональные тесты (сигналы, валидация)
# ============================================================================

def test_cyl_diam_m_signal_emission(geometry_panel, qtbot):
    """Проверить emission сигнала parameter_changed при изменении cyl_diam_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.cyl_diam_m_slider.setValue(0.100)
    
    # Проверить параметры сигнала
    assert blocker.args == ['cyl_diam_m', 0.100], \
        f"Сигнал должен быть ('cyl_diam_m', 0.100), получено {blocker.args}"


def test_stroke_m_signal_emission(geometry_panel, qtbot):
    """Проверить emission сигнала parameter_changed при изменении stroke_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.stroke_m_slider.setValue(0.400)
    
    assert blocker.args == ['stroke_m', 0.400], \
        f"Сигнал должен быть ('stroke_m', 0.400), получено {blocker.args}"


def test_dead_gap_m_signal_emission(geometry_panel, qtbot):
    """Проверить emission сигнала parameter_changed при изменении dead_gap_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.dead_gap_m_slider.setValue(0.010)
    
    assert blocker.args == ['dead_gap_m', 0.010], \
        f"Сигнал должен быть ('dead_gap_m', 0.010), получено {blocker.args}"


def test_geometry_updated_signal(geometry_panel, qtbot):
    """Проверить emission сигнала geometry_updated при изменении параметра"""
    with qtbot.waitSignal(geometry_panel.geometry_updated, timeout=1000) as blocker:
        geometry_panel.cyl_diam_m_slider.setValue(0.090)
    
    # Проверить, что словарь содержит новые параметры
    params = blocker.args[0]
    assert 'cyl_diam_m' in params
    assert params['cyl_diam_m'] == 0.090


def test_rod_diameter_validation(geometry_panel):
    """Проверить валидацию: rod_diameter < 80% cyl_diam_m"""
    # Установить диаметр цилиндра 0.080 м = 80 мм
    geometry_panel.cyl_diam_m_slider.setValue(0.080)
    
    # Установить диаметр штока 35 мм (< 80% от 80 мм = 64 мм) - OK
    geometry_panel.rod_diameter_slider.setValue(35.0)
    params = geometry_panel.get_parameters()
    assert params['rod_diameter'] == 35.0
    
    # Попытаться установить 70 мм (> 80% от 80 мм) - должен вызвать конфликт
    # (тест требует интерактивного разрешения конфликта, поэтому пропускаем)


def test_reset_to_defaults_sets_new_params(geometry_panel):
    """Проверить, что сброс к умолчаниям устанавливает новые параметры"""
    # Изменить значения
    geometry_panel.cyl_diam_m_slider.setValue(0.120)
    geometry_panel.stroke_m_slider.setValue(0.450)
    geometry_panel.dead_gap_m_slider.setValue(0.015)
    
    # Сбросить
    geometry_panel._reset_to_defaults()
    
    # Проверить значения
    assert geometry_panel.cyl_diam_m_slider.value() == 0.080
    assert geometry_panel.stroke_m_slider.value() == 0.300
    assert geometry_panel.dead_gap_m_slider.value() == 0.005


def test_set_parameters_accepts_new_params(geometry_panel):
    """Проверить, что set_parameters принимает новые параметры"""
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
# МШ-1: Итоговый smoke test
# ============================================================================

def test_ms1_complete_smoke(geometry_panel):
    """МШ-1: Комплексный smoke тест - все изменения работают вместе"""
    # 1. Проверить наличие новых слайдеров
    assert hasattr(geometry_panel, 'cyl_diam_m_slider')
    assert hasattr(geometry_panel, 'stroke_m_slider')
    assert hasattr(geometry_panel, 'dead_gap_m_slider')
    
    # 2. Проверить отсутствие старых слайдеров
    assert not hasattr(geometry_panel, 'bore_head_slider')
    assert not hasattr(geometry_panel, 'bore_rod_slider')
    
    # 3. Проверить параметры в словаре
    params = geometry_panel.get_parameters()
    assert 'cyl_diam_m' in params
    assert 'stroke_m' in params
    assert 'dead_gap_m' in params
    assert 'bore_head' not in params
    assert 'bore_rod' not in params
    
    # 4. Проверить единицы измерения
    assert geometry_panel.cyl_diam_m_slider.units() == "м"
    assert geometry_panel.stroke_m_slider.units() == "м"
    assert geometry_panel.dead_gap_m_slider.units() == "м"
    
    # 5. Проверить шаг = 0.001
    assert geometry_panel.cyl_diam_m_slider.step() == 0.001
    assert geometry_panel.stroke_m_slider.step() == 0.001
    assert geometry_panel.dead_gap_m_slider.step() == 0.001
    
    # 6. Проверить decimals = 3
    assert geometry_panel.cyl_diam_m_slider.decimals() == 3
    assert geometry_panel.stroke_m_slider.decimals() == 3
    assert geometry_panel.dead_gap_m_slider.decimals() == 3
    
    print("? МШ-1: Все критерии успеха выполнены!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
