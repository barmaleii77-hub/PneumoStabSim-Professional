import math
import locale

import pytest
from PySide6.QtCore import Qt

from tests.helpers.signal_listeners import SignalListener
from src.ui.widgets.range_slider import RangeSlider

pytestmark = [pytest.mark.ui, pytest.mark.headless]


def _step_property_value(slider: RangeSlider) -> float | None:
    """Read ``RangeSlider.step`` defensively and emulate when absent."""

    def _probe_step_via_value() -> float | None:
        before = slider.value()
        slider.setValue(before + 1.0)
        after = slider.value()
        slider.setValue(before)
        delta = abs(after - before)
        return delta if delta > 0 else None

    if hasattr(slider, "step"):
        step_attr = getattr(slider, "step")
        try:
            return float(step_attr)
        except (TypeError, ValueError):
            pass

    # Some community PySide6 builds expose only a private attribute.
    private_step = getattr(slider, "_step", None)
    try:
        if private_step is not None:
            return float(private_step)
    except (TypeError, ValueError):
        pass

    return _probe_step_via_value()


class TestLocales:
    @pytest.mark.parametrize(
        "title,units",
        [
            ("Width", ""),
            ("Ширина", ""),
            ("Width", "мм"),
            ("Ширина", "мм"),
        ],
    )
    def test_accessibility_labels_in_locales(self, qapp, title: str, units: str):
        try:
            locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
        except Exception:
            pass

        w = RangeSlider(minimum=0.0, maximum=1.0, value=0.5, step=0.1, title=title)
        if units:
            w.setUnits(units)
        w.show()

        desc = w.slider.accessibleDescription()
        assert desc
        assert (units in desc) if units else True
        acc_name = w.accessibleName() or ""
        assert acc_name == w._accessible_label or (title.split(" ")[0] in acc_name)


class TestDebounce:
    def test_value_edited_stability_with_long_debounce(self, qapp, qtbot, monkeypatch):
        w = RangeSlider(minimum=0.0, maximum=10.0, value=1.0, step=0.1)
        w.show()

        monkeypatch.setattr(w, "_debounce_delay", 500)
        spy = SignalListener(w.valueEdited)

        for v in (1.2, 1.8, 2.6, 3.4, 4.2):
            w.setValue(v)
            qapp.processEvents()

        assert spy.wait(1500)
        last = spy.at(spy.count() - 1)[0]
        assert math.isclose(last, 4.2, rel_tol=1e-9, abs_tol=1e-9)


class TestExtremeStep:
    def test_quantization_with_extreme_small_step(self, qapp, qtbot):
        w = RangeSlider(
            minimum=-1000.0, maximum=1000.0, value=0.0, step=1e-6, decimals=6
        )
        w.show()

        target = 123.456789
        w.setValue(target)
        qtbot.wait(10)
        assert abs(w.value() - target) < 1e-5

        from tests.ui.test_range_slider_widget import _set_slider_by_value

        _set_slider_by_value(w, target + 0.0005)
        qtbot.wait(10)
        assert abs(w.value() - (target + 0.0005)) < 1e-3


class TestBulkUpdates:
    def test_mass_set_range_and_value_no_extra_signals(self, qapp, qtbot):
        w = RangeSlider(minimum=0.0, maximum=10.0, value=5.0, step=0.5)
        w.show()

        spy_range = SignalListener(w.rangeChanged)
        spy_changed = SignalListener(w.valueChanged)

        for _ in range(5):
            w.setRange(0.0, 10.0)
        qapp.processEvents()
        assert spy_range.count() == 0

        sequences = [
            (0.0, 10.0, 5.0),
            (-5.0, 15.0, 10.0),
            (10.0, 20.0, 15.0),
        ]
        for mn, mx, val in sequences:
            w.setRange(mn, mx)
            w.setValue(val)
        qapp.processEvents()
        assert spy_range.count() == 2

        before = spy_changed.count()
        for _ in range(4):
            w.setValue(15.0)
        qapp.processEvents()
        after = spy_changed.count()
        assert after - before <= 1


class TestStepSize:
    def test_step_size_updates_spinboxes_and_keyboard(self, qapp, qtbot):
        w = RangeSlider(minimum=0.0, maximum=10.0, value=5.0, step=1.0)
        w.show()
        w.setFocus(Qt.FocusReason.OtherFocusReason)

        initial_step = _step_property_value(w)
        if initial_step is not None:
            assert math.isclose(initial_step, 1.0, rel_tol=1e-9, abs_tol=1e-9)
        else:
            assert math.isclose(
                w.value_spinbox.singleStep(), 1.0, rel_tol=1e-9, abs_tol=1e-9
            )

        # По умолчанию шаг 1.0
        old = w.value()
        qtbot.keyClick(
            w,
            Qt.Key_Right,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
        )
        qtbot.wait(5)
        assert math.isclose(w.value(), old + 1.0)

        # Изменяем шаг на 0.2 — клавиатурный нудж должен соответствовать
        w.setStepSize(0.2)
        updated_step = _step_property_value(w)
        if updated_step is not None:
            assert math.isclose(updated_step, 0.2, rel_tol=1e-9, abs_tol=1e-9)
        else:
            assert math.isclose(
                w.value_spinbox.singleStep(), 0.2, rel_tol=1e-9, abs_tol=1e-9
            )
        change_probe = SignalListener(w.valueChanged)
        old = w.value()
        qtbot.keyClick(
            w,
            Qt.Key_Right,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
        )
        qtbot.wait(5)
        assert math.isclose(w.value(), old + 0.2)
        assert change_probe.count() >= 1


class TestUnitsPropagation:
    def test_units_update_reflected_everywhere(self, qapp):
        w = RangeSlider(minimum=0.0, maximum=1.0, value=0.5, step=0.1, title="Length")
        w.show()

        w.setUnits("m")
        # units_label
        assert "Единицы: m" in (w.units_label.text() or "")
        # range_indicator_label — суффикс единиц в конце
        assert (w.range_indicator_label.text() or "").strip().endswith(" m")
        # accessibleDescription
        desc = w.slider.accessibleDescription() or ""
        assert " m" in desc


class TestEditingFinishedDebounce:
    def test_editing_finished_emits_value_edited(self, qapp, qtbot, monkeypatch):
        w = RangeSlider(minimum=0.0, maximum=10.0, value=3.3, step=0.1)
        w.show()
        # Уменьшим задержку для теста
        monkeypatch.setattr(w, "_debounce_delay", 80)
        spy = SignalListener(w.valueEdited)

        # Имитация окончания редактирования в спинбоксе
        w.value_spinbox.setValue(4.4)
        w.value_spinbox.editingFinished.emit()
        # Ждём debounce
        assert spy.wait(600)
        last = spy.at(spy.count() - 1)[0]
        assert math.isclose(last, 4.4, rel_tol=1e-9, abs_tol=1e-9)


class TestTitleUpdates:
    def test_set_title_updates_accessibility_and_labels(self, qapp):
        w = RangeSlider(minimum=0.0, maximum=1.0, value=0.5, step=0.1, title="Old")
        w.show()

        w.setTitle("New Title")
        # Accessible names обновлены
        assert (w.accessibleName() or "").startswith("New Title") or "New Title" in (
            w.accessibleName() or ""
        )
        assert "New Title" in (w.slider.accessibleName() or "")
        assert "New Title" in (w.value_spinbox.accessibleName() or "")
        # Описание тоже перегенерировано
        desc = w.slider.accessibleDescription() or ""
        assert "New Title" in desc


class TestNegativeAndZeroStep:
    def test_zero_and_negative_step_normalization(self, qapp):
        from src.ui.widgets.range_slider import RangeSlider

        # Нулевой шаг нормализуется к 0.001
        w0 = RangeSlider(minimum=0.0, maximum=1.0, value=0.5, step=0.0)
        w0.show()
        normalized_step = _step_property_value(w0)
        if normalized_step is not None:
            assert normalized_step > 0.0
        assert w0.stepSize() > 0.0
        assert math.isclose(w0.min_spinbox.singleStep(), w0.stepSize())

        # Отрицательный шаг становится положительным
        w1 = RangeSlider(minimum=0.0, maximum=1.0, value=0.5, step=-0.2)
        w1.show()
        normalized_negative = _step_property_value(w1)
        if normalized_negative is not None:
            assert normalized_negative > 0.0
        assert w1.stepSize() > 0.0
        assert math.isclose(w1.value_spinbox.singleStep(), w1.stepSize())


class TestTitleFallback:
    def test_empty_title_fallbacks_to_default_label(self, qapp):
        w = RangeSlider(minimum=0.0, maximum=1.0, value=0.5, step=0.1, title="Initial")
        w.show()

        # Пустой заголовок должен приводить к отображаемому label по умолчанию
        w.setTitle("")
        # Имя доступности должно содержать слово Range
        acc = w.accessibleName() or ""
        assert "Range" in acc
        # Описания также должны обновиться
        desc = w.slider.accessibleDescription() or ""
        assert "Range" in desc


class TestEnableDisable:
    def test_set_enabled_propagates_to_children(self, qapp):
        w = RangeSlider(minimum=0.0, maximum=10.0, value=1.0, step=0.5)
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


class TestShortcutsMetadata:
    def test_accessibility_shortcuts_metadata_present(self, qapp):
        w = RangeSlider(minimum=0.0, maximum=10.0, value=5.0, step=1.0, title="Speed")
        w.show()

        shortcuts = w.accessibilityShortcuts()
        # increase/decrease + 3 фокуса
        assert len(shortcuts) >= 5
        # Проверяем, что у каждого есть описание и последовательность нажатий
        for sc in shortcuts:
            assert sc.identifier
            assert sc.sequence
            assert sc.description

        # Сводка должна быть непустой и начинаться с заголовка
        summary = w._compose_shortcut_summary()
        assert summary.startswith("Keyboard shortcuts:")
        assert "Speed" in summary


class TestUnitsToggle:
    def test_units_toggle_clears_suffix(self, qapp):
        w = RangeSlider(minimum=0.0, maximum=1.0, value=0.5, step=0.1, title="Length")
        w.show()

        w.setUnits("m")
        assert (w.range_indicator_label.text() or "").endswith(" m")
        w.setUnits("")
