"""Тесты для виджета RangeSlider.

Покрываются базовые сценарии:
- Инициализация и обновление единиц измерения
- Изменение диапазона с защитой от min>=max
- Квантизация значения по шагу при движении слайдера
- Сигналы valueChanged и valueEdited (debounce)
- Защита от инверсии через спинбоксы min/max
- Горячие клавиши увеличения/уменьшения и фокусировки полей
- Accessibility описания и смена точности decimals
- Пограничные случаи шага (step=0) и enable/disable
- Дополнительно: rangeChanged при правке min/max, точность индикатора позиции, setRange(min==max)
"""

from __future__ import annotations

import math

import pytest

pytestmark = [pytest.mark.ui, pytest.mark.headless]


def _spy_count(spy) -> int:
    try:
        return int(spy.count())
    except Exception:
        # На случай, если используется другой тип шпиона
        try:
            return len(spy)
        except Exception:
            return 0


def _spy_last(spy):
    try:
        if spy:
            return spy[-1]
    except Exception:
        pass
    try:
        return spy.at(spy.count() - 1)
    except Exception:
        return None


def _set_slider_by_value(widget, target: float) -> None:
    """Установить позицию внутреннего QSlider так, чтобы он соответствовал target.

    Делается пересчёт из значения в позицию с учётом внутреннего разрешения.
    """
    from PySide6.QtCore import Qt

    # Дублируем формулу из виджета
    vmin = widget.minimum()
    vmax = widget.maximum()
    resolution = getattr(widget, "_slider_resolution", 100000)
    if math.isclose(vmax, vmin):
        pos = 0
    else:
        ratio = (float(target) - vmin) / (vmax - vmin)
        ratio = min(max(ratio, 0.0), 1.0)
        pos = int(ratio * resolution)
    widget.slider.setValue(pos)
    # Сфокусируем на треке для корректной обработки хоткеев при необходимости
    widget.slider.setFocus(Qt.FocusReason.OtherFocusReason)


def test_initialization_and_units_label(qapp):  # noqa: D401
    from PySide6.QtTest import QSignalSpy
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=10.0, value=5.0, step=0.5, title="Тест")
    w.show()

    # Изначально units пуст
    assert w._units == ""
    assert w.units_label.text() == ""

    # Установка units должна обновлять подпись и a11y описания
    w.setUnits("мм")
    assert w._units == "мм"
    assert "Единицы: мм" in w.units_label.text()

    # Проверим, что valueChanged как минимум один раз эмитится при setValue
    spy_changed = QSignalSpy(w.valueChanged)
    w.setValue(6.0)
    qapp.processEvents()
    assert _spy_count(spy_changed) >= 1


def test_set_range_guard_and_emit(qapp):  # noqa: D401
    from PySide6.QtTest import QSignalSpy
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=5.0, value=2.0, step=0.5)
    w.show()

    spy_range = QSignalSpy(w.rangeChanged)

    # min >= max должен скорректировать max = min + step
    w.setRange(10.0, 9.0)
    qapp.processEvents()

    assert math.isclose(w.minimum(), 10.0)
    assert math.isclose(w.maximum(), 10.0 + 0.5)
    assert _spy_count(spy_range) >= 1


def test_slider_quantization_by_step(qapp, qtbot):  # noqa: D401
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=10.0, value=0.0, step=0.5)
    w.show()

    # Двигаем слайдер к значению 3.3 — оно должно заквантоваться до 3.5
    _set_slider_by_value(w, 3.3)
    qtbot.wait(10)

    expected = round(3.3 / 0.5) * 0.5
    assert math.isclose(w.value(), expected)


def test_slider_without_quantization_when_step_is_zero(qapp, qtbot):  # noqa: D401
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=10.0, value=0.0, step=0.0)
    w.show()

    # Перемещение должно сохранять точное значение без округления по шагу
    target = 3.37
    _set_slider_by_value(w, target)
    qtbot.wait(10)

    # Значение корректируется по ограничению, но не по шагу (шаг = 0)
    assert abs(w.value() - target) < 0.02  # допускаем погрешность пересчёта


def test_value_signals_with_debounce(qapp, qtbot):  # noqa: D401
    from PySide6.QtTest import QSignalSpy
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=1.0, value=0.2, step=0.1)
    w.show()

    spy_changed = QSignalSpy(w.valueChanged)
    spy_edited = QSignalSpy(w.valueEdited)

    # Несколько последовательных изменений
    w.setValue(0.3)
    w.setValue(0.4)
    w.setValue(0.5)
    qapp.processEvents()

    # valueChanged должен быть эмитирован многократно
    assert _spy_count(spy_changed) >= 3

    # valueEdited приходит после debounce ~200мс, и последнее значение соответствует 0.5
    assert spy_edited.wait(600)
    last = _spy_last(spy_edited)
    assert last is None or pytest.approx(last[0]) == pytest.approx(0.5)


def test_min_max_spinboxes_inversion_guard(qapp, qtbot):  # noqa: D401
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=10.0, value=5.0, step=1.0)
    w.show()

    # Форсируем инверсию через min_spinbox: должно скорректировать к max - step
    w.min_spinbox.setValue(12.0)
    qtbot.wait(10)
    assert math.isclose(w.minimum(), 9.0)  # 10 - 1

    # Форсируем инверсию через max_spinbox: должно скорректировать к min + step
    w.max_spinbox.setValue(-5.0)
    qtbot.wait(10)
    assert math.isclose(w.maximum(), w.minimum() + 1.0)


def test_keyboard_shortcuts_nudge_and_focus(qapp, qtbot):  # noqa: D401
    from PySide6.QtCore import Qt
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=10.0, value=5.0, step=0.5)
    w.show()
    w.setFocus(Qt.FocusReason.OtherFocusReason)

    # Увеличение по Ctrl+Alt+Right
    old = w.value()
    qtbot.keyClick(
        w,
        Qt.Key_Right,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
    )
    qtbot.wait(10)
    assert math.isclose(w.value(), old + 0.5)

    # Уменьшение по Ctrl+Alt+Left
    qtbot.keyClick(
        w,
        Qt.Key_Left,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
    )
    qtbot.wait(10)
    assert math.isclose(w.value(), old)

    # Фокус на min/value/max через 1/2/3
    qtbot.keyClick(
        w,
        Qt.Key_1,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
    )
    qtbot.wait(5)
    assert w.min_spinbox.hasFocus()

    qtbot.keyClick(
        w,
        Qt.Key_2,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
    )
    qtbot.wait(5)
    assert w.value_spinbox.hasFocus()

    qtbot.keyClick(
        w,
        Qt.Key_3,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
    )
    qtbot.wait(5)
    assert w.max_spinbox.hasFocus()


def test_accessibility_descriptions_and_decimals(qapp, qtbot):  # noqa: D401
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(
        minimum=0.0, maximum=1.0, value=0.25, step=0.05, units="мм", title="Ширина"
    )
    w.show()

    # Обновление decimals должно отражаться в лейбле диапазона
    w.setDecimals(3)
    w.setRange(0.0, 1.0)
    qtbot.wait(10)
    text = w.range_indicator_label.text()
    assert ".000" in text and ".000" in text  # 0.000 — 1.000

    # Accessibility описания не пустые и содержат границы и единицы измерения
    slider_desc = w.slider.accessibleDescription()
    assert slider_desc
    assert "Adjust" in slider_desc and "мм" in slider_desc

    # Индикатор позиции формирует описания с процентовым значением
    pos_desc = w.position_indicator_label.accessibleDescription()
    assert "percent" in pos_desc


def test_accessibility_shortcuts_metadata(qapp):  # noqa: D401
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0, maximum=10, value=5, step=1, title="Test")
    w.show()

    shortcuts = w.accessibilityShortcuts()
    # Должно быть минимум 5 шорткатов (increase, decrease, focus-min/value/max)
    assert len(shortcuts) >= 5
    # Каждый содержит осмысательное описание
    assert all(s.description and s.sequence for s in shortcuts)


def test_set_enabled_propagates_to_children(qapp):  # noqa: D401
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0, maximum=10, value=5, step=1)
    w.show()

    w.setEnabled(False)
    assert not w.slider.isEnabled()
    assert not w.min_spinbox.isEnabled()
    assert not w.value_spinbox.isEnabled()
    assert not w.max_spinbox.isEnabled()

    w.setEnabled(True)
    assert w.slider.isEnabled()
    assert w.min_spinbox.isEnabled()
    assert w.value_spinbox.isEnabled()
    assert w.max_spinbox.isEnabled()


def test_range_changed_via_spinboxes_emits_and_clamps(qapp, qtbot):  # noqa: D401
    from PySide6.QtTest import QSignalSpy
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=2.0, value=1.0, step=0.2)
    w.show()

    spy_range = QSignalSpy(w.rangeChanged)

    # 1) Поднимаем min до > max -> должно скорректироваться к max - step
    w.min_spinbox.setValue(3.0)
    qtbot.wait(10)
    assert math.isclose(w.minimum(), 1.8)
    assert _spy_count(spy_range) >= 1
    last = _spy_last(spy_range)
    if last:
        assert math.isclose(last[0], w.minimum()) and math.isclose(last[1], w.maximum())

    # 2) Опускаем max до < min -> скорректируется к min + step
    w.max_spinbox.setValue(-1.0)
    qtbot.wait(10)
    assert math.isclose(w.maximum(), w.minimum() + 0.2)
    assert _spy_count(spy_range) >= 2


def test_position_indicator_boundaries(qapp, qtbot):  # noqa: D401
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=10.0, value=0.0, step=0.5)
    w.show()

    # На минимуме 0%
    w.setValue(0.0)
    qtbot.wait(5)
    assert "0.0%" in w.position_indicator_label.text()

    # На максимуме 100%
    w.setValue(10.0)
    qtbot.wait(5)
    assert "100.0%" in w.position_indicator_label.text()


def test_decimals_affect_spinboxes_and_indicator(qapp, qtbot):  # noqa: D401
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=1.0, value=0.12345, step=0.001, decimals=2)
    w.show()

    # Меняем на 4 знака
    w.setDecimals(4)
    w.setRange(0.0, 1.0)
    qtbot.wait(10)

    assert w.min_spinbox.decimals() == 4
    assert w.value_spinbox.decimals() == 4
    assert w.max_spinbox.decimals() == 4

    text = w.range_indicator_label.text()
    assert ".0000" in text  # 4 знака для границ и ширины


def test_set_range_equal_min_max_is_corrected(qapp, qtbot):  # noqa: D401
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=10.0, value=5.0, step=0.2)
    w.show()

    w.setRange(5.0, 5.0)
    qtbot.wait(10)

    assert math.isclose(w.minimum(), 5.0)
    assert math.isclose(w.maximum(), 5.2)

    # На минимуме процент 0.0%
    w.setValue(5.0)
    qtbot.wait(5)
    assert "0.0%" in w.position_indicator_label.text()


def test_keyboard_nudge_respects_clamping(qapp, qtbot):  # noqa: D401
    from PySide6.QtCore import Qt
    from src.ui.widgets.range_slider import RangeSlider

    w = RangeSlider(minimum=0.0, maximum=1.0, value=0.95, step=0.1)
    w.show()
    w.setFocus(Qt.FocusReason.OtherFocusReason)

    # Увеличение не должно выходить за максимум
    qtbot.keyClick(
        w,
        Qt.Key_Right,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
    )
    qtbot.wait(10)
    assert w.value() <= 1.0

    # Аналогично у минимума
    w.setValue(0.0)
    qtbot.wait(5)
    qtbot.keyClick(
        w,
        Qt.Key_Left,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
    )
    qtbot.wait(10)
    assert w.value() >= 0.0
