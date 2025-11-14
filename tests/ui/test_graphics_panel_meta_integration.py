"""Интеграционный тест: проверяет что GraphicsPanel сохраняет состояние
и не конфликтует с добавленным разделом geometry.meta при сборе состояния
в одном цикле сохранения.

Задача: гарантировать что наличие 'current.geometry.meta' не ломает
collect_state() и что настройки графики остаются валидными.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.ui, pytest.mark.headless]


def test_graphics_panel_collect_state_with_geometry_meta(qapp):  # noqa: D401
    from src.ui.panels.panel_graphics import GraphicsPanel
    from src.ui.panels.panel_geometry import GeometryPanel
    from src.common.settings_manager import get_settings_manager

    settings = get_settings_manager()
    geometry_panel = GeometryPanel()
    graphics_panel = GraphicsPanel()
    geometry_panel.show()
    graphics_panel.show()

    # Модифицируем мета у одного ползунка геометрии
    geometry_panel.wheelbase_slider.setStepSize(0.002)
    geometry_panel.wheelbase_slider.setDecimals(5)
    geometry_panel.wheelbase_slider.setUnits("м")
    qapp.processEvents()

    # Собираем состояния
    geom_state = geometry_panel.collect_state()
    gfx_state = graphics_panel.collect_state()

    # Геометрия содержит meta
    assert "meta" in geom_state
    assert "wheelbase" in geom_state["meta"]
    assert geom_state["meta"]["wheelbase"]["step"] == pytest.approx(0.002)

    # Графика возвращает валидный словарь с секциями lighting/effects/materials etc.
    assert isinstance(gfx_state, dict)
    for key in [
        "lighting",
        "environment",
        "quality",
        "scene",
        "camera",
        "materials",
        "effects",
    ]:
        assert key in gfx_state

    # Сохранение обеих категорий не вызывает исключений
    settings.set_category("geometry", geom_state, auto_save=False)
    settings.set_category("graphics", gfx_state, auto_save=False)

    # Проверяем что meta остался после записи
    saved_meta = settings.get("current.geometry.meta")
    assert isinstance(saved_meta, dict)
    assert "wheelbase" in saved_meta
    assert saved_meta["wheelbase"]["decimals"] == 5
