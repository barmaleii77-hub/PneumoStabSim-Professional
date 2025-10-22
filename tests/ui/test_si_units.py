# -*- coding: utf-8 -*-
"""
МШ-2: Тесты для единиц СИ + шаг 0.001м
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
# МШ-2: Тесты наличия новых слайдеров (в метрах)
# ============================================================================

def test_rod_diameter_m_slider_exists(geometry_panel):
    """Проверить наличие слайдера rod_diameter_m"""
    assert hasattr(geometry_panel, 'rod_diameter_m_slider'), \
        "GeometryPanel должна иметь атрибут rod_diameter_m_slider"


def test_piston_rod_length_m_slider_exists(geometry_panel):
    """Проверить наличие слайдера piston_rod_length_m"""
    assert hasattr(geometry_panel, 'piston_rod_length_m_slider'), \
        "GeometryPanel должна иметь атрибут piston_rod_length_m_slider"


def test_piston_thickness_m_slider_exists(geometry_panel):
    """Проверить наличие слайдера piston_thickness_m"""
    assert hasattr(geometry_panel, 'piston_thickness_m_slider'), \
        "GeometryPanel должна иметь атрибут piston_thickness_m_slider"


# ============================================================================
# МШ-2: Тесты отсутствия старых слайдеров (в мм)
# ============================================================================

def test_rod_diameter_slider_removed(geometry_panel):
    """Проверить ОТСУТСТВИЕ rod_diameter_slider (в мм)"""
    assert not hasattr(geometry_panel, 'rod_diameter_slider'), \
        "rod_diameter_slider должен быть удалён (заменён на rod_diameter_m_slider)"


def test_piston_rod_length_slider_removed(geometry_panel):
    """Проверить ОТСУТСТВИЕ piston_rod_length_slider (в мм)"""
    assert not hasattr(geometry_panel, 'piston_rod_length_slider'), \
        "piston_rod_length_slider должен быть удалён (заменён на piston_rod_length_m_slider)"


def test_piston_thickness_slider_removed(geometry_panel):
    """Проверить ОТСУТСТВИЕ piston_thickness_slider (в мм)"""
    assert not hasattr(geometry_panel, 'piston_thickness_slider'), \
        "piston_thickness_slider должен быть удалён (заменён на piston_thickness_m_slider)"


# ============================================================================
# МШ-2: Тесты параметров rod_diameter_m_slider
# ============================================================================

def test_rod_diameter_m_minimum(geometry_panel):
    """Проверить минимум rod_diameter_m_slider = 0.020 м"""
    assert geometry_panel.rod_diameter_m_slider.minimum() == 0.020, \
        f"rod_diameter_m minimum должен быть 0.020, получено {geometry_panel.rod_diameter_m_slider.minimum()}"


def test_rod_diameter_m_maximum(geometry_panel):
    """Проверить максимум rod_diameter_m_slider = 0.060 м"""
    assert geometry_panel.rod_diameter_m_slider.maximum() == 0.060, \
        f"rod_diameter_m maximum должен быть 0.060, получено {geometry_panel.rod_diameter_m_slider.maximum()}"


def test_rod_diameter_m_default_value(geometry_panel):
    """Проверить значение по умолчанию rod_diameter_m_slider = 0.035 м"""
    assert geometry_panel.rod_diameter_m_slider.value() == 0.035, \
        f"rod_diameter_m default должен быть 0.035, получено {geometry_panel.rod_diameter_m_slider.value()}"


def test_rod_diameter_m_step(geometry_panel):
    """Проверить шаг rod_diameter_m_slider = 0.001 м"""
    assert geometry_panel.rod_diameter_m_slider.step() == 0.001, \
        f"rod_diameter_m step должен быть 0.001, получено {geometry_panel.rod_diameter_m_slider.step()}"


def test_rod_diameter_m_decimals(geometry_panel):
    """Проверить decimals rod_diameter_m_slider = 3"""
    assert geometry_panel.rod_diameter_m_slider.decimals() == 3, \
        f"rod_diameter_m decimals должен быть 3, получено {geometry_panel.rod_diameter_m_slider.decimals()}"


def test_rod_diameter_m_units(geometry_panel):
    """Проверить единицы rod_diameter_m_slider = 'м'"""
    assert geometry_panel.rod_diameter_m_slider.units() == "м", \
        f"rod_diameter_m units должны быть 'м', получено '{geometry_panel.rod_diameter_m_slider.units()}'"


# ============================================================================
# МШ-2: Тесты параметров piston_rod_length_m_slider
# ============================================================================

def test_piston_rod_length_m_minimum(geometry_panel):
    """Проверить минимум piston_rod_length_m_slider = 0.100 м"""
    assert geometry_panel.piston_rod_length_m_slider.minimum() == 0.100, \
        f"piston_rod_length_m minimum должен быть 0.100, получено {geometry_panel.piston_rod_length_m_slider.minimum()}"


def test_piston_rod_length_m_maximum(geometry_panel):
    """Проверить максимум piston_rod_length_m_slider = 0.500 м"""
    assert geometry_panel.piston_rod_length_m_slider.maximum() == 0.500, \
        f"piston_rod_length_m maximum должен быть 0.500, получено {geometry_panel.piston_rod_length_m_slider.maximum()}"


def test_piston_rod_length_m_default_value(geometry_panel):
    """Проверить значение по умолчанию piston_rod_length_m_slider = 0.200 м"""
    assert geometry_panel.piston_rod_length_m_slider.value() == 0.200, \
        f"piston_rod_length_m default должен быть 0.200, получено {geometry_panel.piston_rod_length_m_slider.value()}"


def test_piston_rod_length_m_step(geometry_panel):
    """Проверить шаг piston_rod_length_m_slider = 0.001 м"""
    assert geometry_panel.piston_rod_length_m_slider.step() == 0.001, \
        f"piston_rod_length_m step должен быть 0.001, получено {geometry_panel.piston_rod_length_m_slider.step()}"


def test_piston_rod_length_m_decimals(geometry_panel):
    """Проверить decimals piston_rod_length_m_slider = 3"""
    assert geometry_panel.piston_rod_length_m_slider.decimals() == 3, \
        f"piston_rod_length_m decimals должен быть 3, получено {geometry_panel.piston_rod_length_m_slider.decimals()}"


def test_piston_rod_length_m_units(geometry_panel):
    """Проверить единицы piston_rod_length_m_slider = 'м'"""
    assert geometry_panel.piston_rod_length_m_slider.units() == "м", \
        f"piston_rod_length_m units должны быть 'м', получено '{geometry_panel.piston_rod_length_m_slider.units()}'"


# ============================================================================
# МШ-2: Тесты параметров piston_thickness_m_slider
# ============================================================================

def test_piston_thickness_m_minimum(geometry_panel):
    """Проверить минимум piston_thickness_m_slider = 0.010 м"""
    assert geometry_panel.piston_thickness_m_slider.minimum() == 0.010, \
        f"piston_thickness_m minimum должен быть 0.010, получено {geometry_panel.piston_thickness_m_slider.minimum()}"


def test_piston_thickness_m_maximum(geometry_panel):
    """Проверить максимум piston_thickness_m_slider = 0.050 м"""
    assert geometry_panel.piston_thickness_m_slider.maximum() == 0.050, \
        f"piston_thickness_m maximum должен быть 0.050, получено {geometry_panel.piston_thickness_m_slider.maximum()}"


def test_piston_thickness_m_default_value(geometry_panel):
    """Проверить значение по умолчанию piston_thickness_m_slider = 0.025 м"""
    assert geometry_panel.piston_thickness_m_slider.value() == 0.025, \
        f"piston_thickness_m default должен быть 0.025, получено {geometry_panel.piston_thickness_m_slider.value()}"


def test_piston_thickness_m_step(geometry_panel):
    """Проверить шаг piston_thickness_m_slider = 0.001 м"""
    assert geometry_panel.piston_thickness_m_slider.step() == 0.001, \
        f"piston_thickness_m step должен быть 0.001, получено {geometry_panel.piston_thickness_m_slider.step()}"


def test_piston_thickness_m_decimals(geometry_panel):
    """Проверить decimals piston_thickness_m_slider = 3"""
    assert geometry_panel.piston_thickness_m_slider.decimals() == 3, \
        f"piston_thickness_m decimals должен быть 3, получено {geometry_panel.piston_thickness_m_slider.decimals()}"


def test_piston_thickness_m_units(geometry_panel):
    """Проверить единицы piston_thickness_m_slider = 'м'"""
    assert geometry_panel.piston_thickness_m_slider.units() == "м", \
        f"piston_thickness_m units должны быть 'м', получено '{geometry_panel.piston_thickness_m_slider.units()}'"


# ============================================================================
# МШ-2: Тесты параметров в словаре parameters
# ============================================================================

def test_parameters_has_rod_diameter_m(geometry_panel):
    """Проверить наличие rod_diameter_m в parameters"""
    params = geometry_panel.get_parameters()
    assert 'rod_diameter_m' in params, \
        "parameters должен содержать ключ 'rod_diameter_m'"
    assert params['rod_diameter_m'] == 0.035, \
        f"rod_diameter_m должен быть 0.035, получено {params['rod_diameter_m']}"


def test_parameters_has_piston_rod_length_m(geometry_panel):
    """Проверить наличие piston_rod_length_m в parameters"""
    params = geometry_panel.get_parameters()
    assert 'piston_rod_length_m' in params, \
        "parameters должен содержать ключ 'piston_rod_length_m'"
    assert params['piston_rod_length_m'] == 0.200, \
        f"piston_rod_length_m должен быть 0.200, получено {params['piston_rod_length_m']}"


def test_parameters_has_piston_thickness_m(geometry_panel):
    """Проверить наличие piston_thickness_m в parameters"""
    params = geometry_panel.get_parameters()
    assert 'piston_thickness_m' in params, \
        "parameters должен содержать ключ 'piston_thickness_m'"
    assert params['piston_thickness_m'] == 0.025, \
        f"piston_thickness_m должен быть 0.025, получено {params['piston_thickness_m']}"


def test_parameters_no_rod_diameter(geometry_panel):
    """Проверить ОТСУТСТВИЕ rod_diameter в parameters"""
    params = geometry_panel.get_parameters()
    assert 'rod_diameter' not in params, \
        "parameters НЕ должен содержать ключ 'rod_diameter' (заменён на rod_diameter_m)"


def test_parameters_no_piston_rod_length(geometry_panel):
    """Проверить ОТСУТСТВИЕ piston_rod_length в parameters"""
    params = geometry_panel.get_parameters()
    assert 'piston_rod_length' not in params, \
        "parameters НЕ должен содержать ключ 'piston_rod_length' (заменён на piston_rod_length_m)"


def test_parameters_no_piston_thickness(geometry_panel):
    """Проверить ОТСУТСТВИЕ piston_thickness в parameters"""
    params = geometry_panel.get_parameters()
    assert 'piston_thickness' not in params, \
        "parameters НЕ должен содержать ключ 'piston_thickness' (заменён на piston_thickness_m)"


# ============================================================================
# МШ-2: Функциональные тесты (сигналы, валидация)
# ============================================================================

def test_rod_diameter_m_signal_emission(geometry_panel, qtbot):
    """Проверить emission сигнала parameter_changed при изменении rod_diameter_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.rod_diameter_m_slider.setValue(0.040)

    # Проверить параметры сигнала
    assert blocker.args == ['rod_diameter_m', 0.040], \
        f"Сигнал должен быть ('rod_diameter_m', 0.040), получено {blocker.args}"


def test_piston_rod_length_m_signal_emission(geometry_panel, qtbot):
    """Проверить emission сигнала parameter_changed при изменении piston_rod_length_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.piston_rod_length_m_slider.setValue(0.300)

    assert blocker.args == ['piston_rod_length_m', 0.300], \
        f"Сигнал должен быть ('piston_rod_length_m', 0.300), получено {blocker.args}"


def test_piston_thickness_m_signal_emission(geometry_panel, qtbot):
    """Проверить emission сигнала parameter_changed при изменении piston_thickness_m"""
    with qtbot.waitSignal(geometry_panel.parameter_changed, timeout=1000) as blocker:
        geometry_panel.piston_thickness_m_slider.setValue(0.030)

    assert blocker.args == ['piston_thickness_m', 0.030], \
        f"Сигнал должен быть ('piston_thickness_m', 0.030), получено {blocker.args}"


def test_geometry_updated_signal_with_m_params(geometry_panel, qtbot):
    """Проверить emission сигнала geometry_updated с новыми параметрами в метрах"""
    with qtbot.waitSignal(geometry_panel.geometry_updated, timeout=1000) as blocker:
        geometry_panel.rod_diameter_m_slider.setValue(0.045)

    # Проверить, что словарь содержит новые параметры
    params = blocker.args[0]
    assert 'rod_diameter_m' in params
    assert params['rod_diameter_m'] == 0.045


def test_rod_diameter_m_validation_updated(geometry_panel):
    """Проверить валидацию: rod_diameter_m < 80% cyl_diam_m (оба в метрах)"""
    # Установить диаметр цилиндра 0.080 м
    geometry_panel.cyl_diam_m_slider.setValue(0.080)

    # Установить диаметр штока 0.035 м (< 80% от 0.080 м = 0.064 м) - OK
    geometry_panel.rod_diameter_m_slider.setValue(0.035)
    params = geometry_panel.get_parameters()
    assert params['rod_diameter_m'] == 0.035


def test_reset_to_defaults_sets_m_params(geometry_panel):
    """Проверить, что сброс к умолчаниям устанавливает параметры в метрах"""
    # Изменить значения
    geometry_panel.rod_diameter_m_slider.setValue(0.050)
    geometry_panel.piston_rod_length_m_slider.setValue(0.400)
    geometry_panel.piston_thickness_m_slider.setValue(0.040)

    # Сбросить
    geometry_panel._reset_to_defaults()

    # Проверить значения
    assert geometry_panel.rod_diameter_m_slider.value() == 0.035
    assert geometry_panel.piston_rod_length_m_slider.value() == 0.200
    assert geometry_panel.piston_thickness_m_slider.value() == 0.025


def test_set_parameters_accepts_m_params(geometry_panel):
    """Проверить, что set_parameters принимает параметры в метрах"""
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
    """Проверить, что пресеты используют параметры в метрах"""
    # Установить пресет "Лёгкий коммерческий"
    geometry_panel._on_preset_changed(1)

    params = geometry_panel.get_parameters()
    assert 'rod_diameter_m' in params
    assert params['rod_diameter_m'] == 0.028  # 28 мм -> 0.028 м

    # Установить пресет "Тяжёлый грузовик"
    geometry_panel._on_preset_changed(2)

    params = geometry_panel.get_parameters()
    assert params['rod_diameter_m'] == 0.045  # 45 мм -> 0.045 м


# ============================================================================
# МШ-2: Проверка конвертации в geometry_changed
# ============================================================================

def test_geometry_changed_uses_m_params(geometry_panel, qtbot):
    """Проверить, что geometry_changed использует параметры в метрах с правильной конвертацией"""
    with qtbot.waitSignal(geometry_panel.geometry_changed, timeout=1000) as blocker:
        geometry_panel.rod_diameter_m_slider.setValue(0.040)  # 0.040 м = 40 мм

    # Проверить, что в 3D формате значение конвертировано правильно
    geometry_3d = blocker.args[0]
    assert 'rodDiameterM' in geometry_3d
    assert geometry_3d['rodDiameterM'] == 40.0  # 0.040 м * 1000 = 40 мм


# ============================================================================
# МШ-2: Итоговый комплексный тест
# ============================================================================

def test_ms2_complete_si_units(geometry_panel):
    """МШ-2: Комплексный тест - все параметры переведены в СИ единицы"""
    # 1. Проверить наличие новых слайдеров в метрах
    assert hasattr(geometry_panel, 'rod_diameter_m_slider')
    assert hasattr(geometry_panel, 'piston_rod_length_m_slider')
    assert hasattr(geometry_panel, 'piston_thickness_m_slider')

    # 2. Проверить отсутствие старых слайдеров в мм
    assert not hasattr(geometry_panel, 'rod_diameter_slider')
    assert not hasattr(geometry_panel, 'piston_rod_length_slider')
    assert not hasattr(geometry_panel, 'piston_thickness_slider')

    # 3. Проверить параметры в словаре
    params = geometry_panel.get_parameters()
    assert 'rod_diameter_m' in params
    assert 'piston_rod_length_m' in params
    assert 'piston_thickness_m' in params
    assert 'rod_diameter' not in params
    assert 'piston_rod_length' not in params
    assert 'piston_thickness' not in params

    # 4. Проверить единицы измерения СИ
    assert geometry_panel.rod_diameter_m_slider.units() == "м"
    assert geometry_panel.piston_rod_length_m_slider.units() == "м"
    assert geometry_panel.piston_thickness_m_slider.units() == "м"

    # 5. Проверить шаг = 0.001
    assert geometry_panel.rod_diameter_m_slider.step() == 0.001
    assert geometry_panel.piston_rod_length_m_slider.step() == 0.001
    assert geometry_panel.piston_thickness_m_slider.step() == 0.001

    # 6. Проверить decimals = 3
    assert geometry_panel.rod_diameter_m_slider.decimals() == 3
    assert geometry_panel.piston_rod_length_m_slider.decimals() == 3
    assert geometry_panel.piston_thickness_m_slider.decimals() == 3

    # 7. Проверить диапазоны конвертированы правильно
    # rod_diameter: 20-60 мм -> 0.020-0.060 м
    assert geometry_panel.rod_diameter_m_slider.minimum() == 0.020
    assert geometry_panel.rod_diameter_m_slider.maximum() == 0.060

    # piston_rod_length: 100-500 мм -> 0.100-0.500 м
    assert geometry_panel.piston_rod_length_m_slider.minimum() == 0.100
    assert geometry_panel.piston_rod_length_m_slider.maximum() == 0.500

    # piston_thickness: 10-50 мм -> 0.010-0.050 м
    assert geometry_panel.piston_thickness_m_slider.minimum() == 0.010
    assert geometry_panel.piston_thickness_m_slider.maximum() == 0.050

    # 8. Проверить значения по умолчанию конвертированы правильно
    assert geometry_panel.rod_diameter_m_slider.value() == 0.035   # 35 мм -> 0.035 м
    assert geometry_panel.piston_rod_length_m_slider.value() == 0.200  # 200 мм -> 0.200 м
    assert geometry_panel.piston_thickness_m_slider.value() == 0.025   # 25 мм -> 0.025 м

    print("? МШ-2: Все критерии успеха выполнены!")


def test_all_linear_params_si_units(geometry_panel):
    """МШ-2: Проверить, что ВСЕ линейные параметры в СИ единицах (метрах)"""
    params = geometry_panel.get_parameters()

    # Собрать все линейные параметры и их единицы
    linear_params = {}

    # От МШ-0: уже в метрах
    linear_params['wheelbase'] = geometry_panel.wheelbase_slider.units()
    linear_params['track'] = geometry_panel.track_slider.units()
    linear_params['frame_to_pivot'] = geometry_panel.frame_to_pivot_slider.units()
    linear_params['lever_length'] = geometry_panel.lever_length_slider.units()
    linear_params['cylinder_length'] = geometry_panel.cylinder_length_slider.units()

    # От МШ-1: новые в метрах
    linear_params['cyl_diam_m'] = geometry_panel.cyl_diam_m_slider.units()
    linear_params['stroke_m'] = geometry_panel.stroke_m_slider.units()
    linear_params['dead_gap_m'] = geometry_panel.dead_gap_m_slider.units()

    # От МШ-2: переведённые в метры
    linear_params['rod_diameter_m'] = geometry_panel.rod_diameter_m_slider.units()
    linear_params['piston_rod_length_m'] = geometry_panel.piston_rod_length_m_slider.units()
    linear_params['piston_thickness_m'] = geometry_panel.piston_thickness_m_slider.units()

    # Проверить, что ВСЕ линейные параметры в метрах
    for param_name, units in linear_params.items():
        assert units == "м", f"Параметр {param_name} должен быть в метрах, получено '{units}'"

    print(f"? Все {len(linear_params)} линейных параметров в СИ единицах (метрах)!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
