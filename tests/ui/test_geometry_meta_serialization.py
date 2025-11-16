"""Тесты сериализации мета-параметров RangeSlider в GeometryPanel.

Проверяется что:
- Сигналы stepChanged/decimalsChanged/unitsChanged приводят к обновлению current.geometry.meta.* в SettingsManager
- collect_state() включает раздел 'meta' со всеми модифицированными полями
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.ui, pytest.mark.headless]


def test_geometry_meta_capture_and_collect(qapp):  # noqa: D401
    from src.ui.panels.panel_geometry import GeometryPanel
    from src.common.settings_manager import get_settings_manager

    settings = get_settings_manager()
    panel = GeometryPanel()
    panel.show()

    # Берём один параметр и меняем мета-поля
    slider = panel.wheelbase_slider

    # Изменяем шаг
    slider.setStepSize(0.005)
    # Изменяем точность
    slider.setDecimals(4)
    # Изменяем единицы
    slider.setUnits("м")
    qapp.processEvents()

    # Проверяем что значения попали в settings_manager
    step_val = settings.get("current.geometry.meta.wheelbase.step")
    dec_val = settings.get("current.geometry.meta.wheelbase.decimals")
    units_val = settings.get("current.geometry.meta.wheelbase.units")

    assert step_val == pytest.approx(0.005)
    assert dec_val == 4
    assert units_val == "м"

    state = panel.collect_state()
    assert "meta" in state
    meta = state["meta"]
    assert isinstance(meta, dict)
    assert "wheelbase" in meta
    assert meta["wheelbase"]["step"] == pytest.approx(0.005)
    assert meta["wheelbase"]["decimals"] == 4
    assert meta["wheelbase"]["units"] == "м"
