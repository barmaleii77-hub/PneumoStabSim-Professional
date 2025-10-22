# Исправление кодировки UTF-8
# Удаляем некорректные символы и заменяем их на корректные строки
# Пример:
# "�" -> "-"

# -*- coding: utf-8 -*-
"""
UI Layout Tests - PROMPT #1 Validation
Tests for main window restructure and panel russification
Тесты раскладки UI и русификации панелей
"""

import pytest
from PySide6.QtWidgets import QApplication, QTabWidget, QSplitter, QComboBox
from PySide6.QtCore import Qt
import sys

# Import UI components
from src.ui.main_window import MainWindow
from src.ui.panels.panel_geometry import GeometryPanel
from src.ui.panels.panel_pneumo import PneumoPanel


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't quit - other tests may need it


@pytest.fixture
def main_window(qapp):
    """Create MainWindow instance for testing"""
    window = MainWindow(use_qml_3d=False)  # Disable QML for faster tests
    yield window
    window.close()


@pytest.fixture
def geometry_panel(qapp):
    """Create standalone GeometryPanel for testing"""
    panel = GeometryPanel()
    yield panel


@pytest.fixture
def pneumo_panel(qapp):
    """Create standalone PneumoPanel for testing"""
    panel = PneumoPanel()
    yield panel


# ============================================================================
# MAIN WINDOW STRUCTURE TESTS
# ============================================================================


class TestMainWindowStructure:
    """Test main window layout restructure (PROMPT #1 Step 1)"""

    def test_main_window_title_russian(self, main_window):
        """Verify window title is in Russian"""
        title = main_window.windowTitle()
        assert "PneumoStabSim" in title
        assert (
            "U-Рама" in title or "Рама" in title.lower()
        ), f"Expected Russian text in title, got: {title}"

    def test_vertical_splitter_exists(self, main_window):
        """Verify vertical splitter is created"""
        assert main_window.main_splitter is not None, "Main splitter should exist"
        assert isinstance(
            main_window.main_splitter, QSplitter
        ), "main_splitter should be QSplitter instance"
        assert (
            main_window.main_splitter.orientation() == Qt.Orientation.Vertical
        ), "Splitter should be vertical"

    def test_splitter_has_two_sections(self, main_window):
        """Verify splitter has 3D scene + charts"""
        splitter = main_window.main_splitter
        assert (
            splitter.count() == 2
        ), f"Splitter should have 2 widgets (scene + charts), got {splitter.count()}"

    def test_charts_widget_exists(self, main_window):
        """Verify charts widget is in splitter"""
        assert main_window.chart_widget is not None, "ChartWidget should exist"
        # Check it's in the splitter
        splitter = main_window.main_splitter
        widgets = [splitter.widget(i) for i in range(splitter.count())]
        assert (
            main_window.chart_widget in widgets
        ), "ChartWidget should be in main splitter"

    def test_tab_widget_exists(self, main_window):
        """Verify tab widget is created"""
        assert main_window.tab_widget is not None, "Tab widget should exist"
        assert isinstance(
            main_window.tab_widget, QTabWidget
        ), "tab_widget should be QTabWidget instance"

    def test_tab_widget_has_five_tabs(self, main_window):
        """Verify tab widget has 5 tabs"""
        tabs = main_window.tab_widget
        assert tabs.count() == 5, f"Expected 5 tabs, got {tabs.count()}"

    def test_tab_titles_russian(self, main_window):
        """Verify all tab titles are in Russian"""
        tabs = main_window.tab_widget
        expected_titles = [
            "Геометрия",
            "Пневмосистема",
            "Режимы стабилизатора",
            "Визуализация",
            "Динамика движения",
        ]

        for i, expected in enumerate(expected_titles):
            actual = tabs.tabText(i)
            assert (
                actual == expected
            ), f"Tab {i} title mismatch: expected '{expected}', got '{actual}'"

    def test_panels_exist_in_tabs(self, main_window):
        """Verify panels are created in tabs"""
        assert main_window.geometry_panel is not None, "GeometryPanel should exist"
        assert main_window.pneumo_panel is not None, "PneumoPanel should exist"
        assert main_window.modes_panel is not None, "ModesPanel should exist"


# ============================================================================
# MENU & TOOLBAR TESTS
# ============================================================================


class TestMenusAndToolbars:
    """Test menu and toolbar russification"""

    def test_file_menu_russian(self, main_window):
        """Verify File menu is in Russian"""
        menubar = main_window.menuBar()
        menus = [
            menubar.actions()[i].text() for i in range(menubar.actions().__len__())
        ]
        assert "Файл" in menus, f"Expected 'Файл' menu, got: {menus}"

    def test_parameters_menu_russian(self, main_window):
        """Verify Parameters menu is in Russian"""
        menubar = main_window.menuBar()
        menus = [
            menubar.actions()[i].text() for i in range(menubar.actions().__len__())
        ]
        assert "Параметры" in menus, f"Expected 'Параметры' menu, got: {menus}"

    def test_view_menu_russian(self, main_window):
        """Verify View menu is in Russian"""
        menubar = main_window.menuBar()
        menus = [
            menubar.actions()[i].text() for i in range(menubar.actions().__len__())
        ]
        assert "Вид" in menus, f"Expected 'Вид' menu, got: {menus}"

    def test_toolbar_buttons_russian(self, main_window):
        """Verify toolbar buttons are in Russian"""
        toolbar = None
        for child in main_window.children():
            if hasattr(child, "objectName") and child.objectName() == "MainToolbar":
                toolbar = child
                break

        assert toolbar is not None, "MainToolbar should exist"

        # Check action texts
        actions = toolbar.actions()
        action_texts = [a.text() for a in actions if a.text()]

        assert any(
            "Старт" in text for text in action_texts
        ), f"Expected 'Старт' button, got: {action_texts}"
        assert any(
            "Стоп" in text for text in action_texts
        ), f"Expected 'Стоп' button, got: {action_texts}"


# ============================================================================
# STATUS BAR TESTS
# ============================================================================


class TestStatusBar:
    """Test status bar russification"""

    def test_status_bar_exists(self, main_window):
        """Verify status bar is created"""
        assert main_window.status_bar is not None, "Status bar should exist"

    def test_status_bar_labels_russian(self, main_window):
        """Verify status bar labels are in Russian"""
        # Check time label
        assert (
            "Время:" in main_window.sim_time_label.text()
        ), f"Expected 'Время:' in sim_time_label, got: {main_window.sim_time_label.text()}"

        # Check steps label
        assert (
            "Шаги:" in main_window.step_count_label.text()
        ), f"Expected 'Шаги:' in step_count_label, got: {main_window.step_count_label.text()}"

        # Check FPS label
        assert (
            "FPS физики:" in main_window.fps_label.text()
        ), f"Expected 'FPS физики:' in fps_label, got: {main_window.fps_label.text()}"

    def test_status_bar_units_russian(self, main_window):
        """Verify status bar uses Russian units"""
        kinematics_text = main_window.kinematics_label.text()

        # Check for Russian unit markers
        assert (
            "угол:" in kinematics_text or "°" in kinematics_text
        ), f"Expected Russian kinematics labels, got: {kinematics_text}"
        assert (
            "мм" in kinematics_text or "ход:" in kinematics_text
        ), f"Expected Russian units (мм), got: {kinematics_text}"


# ============================================================================
# GEOMETRY PANEL TESTS
# ============================================================================


class TestGeometryPanel:
    """Test GeometryPanel russification and features"""

    def test_panel_title_russian(self, geometry_panel):
        """Verify panel title is in Russian"""
        # Find title label
        title_labels = [
            w
            for w in geometry_panel.children()
            if hasattr(w, "text") and hasattr(w, "font")
        ]

        title_found = False
        for label in title_labels:
            if hasattr(label, "font") and label.font().bold():
                text = label.text()
                if "Геометрия" in text:
                    title_found = True
                    break

        assert title_found, "Expected 'Геометрия автомобиля' title"

    def test_preset_combobox_exists(self, geometry_panel):
        """Verify preset QComboBox is created"""
        assert hasattr(
            geometry_panel, "preset_combo"
        ), "GeometryPanel should have preset_combo attribute"
        assert isinstance(
            geometry_panel.preset_combo, QComboBox
        ), "preset_combo should be QComboBox instance"

    def test_preset_combobox_options_russian(self, geometry_panel):
        """Verify preset QComboBox has Russian options"""
        combo = geometry_panel.preset_combo
        expected_items = [
            "Стандартный грузовик",
            "Лёгкий коммерческий",
            "Тяжёлый грузовик",
            "Пользовательский",
        ]

        assert combo.count() == len(
            expected_items
        ), f"Expected {len(expected_items)} preset items, got {combo.count()}"

        for i, expected in enumerate(expected_items):
            actual = combo.itemText(i)
            assert (
                actual == expected
            ), f"Preset {i} mismatch: expected '{expected}', got '{actual}'"

    def test_group_boxes_russian(self, geometry_panel):
        """Verify group box titles are in Russian"""
        from PySide6.QtWidgets import QGroupBox

        group_boxes = geometry_panel.findChildren(QGroupBox)
        group_titles = [gb.title() for gb in group_boxes]

        expected_titles = [
            "Размеры рамы",
            "Геометрия подвески",
            "Размеры цилиндра",
            "Опции",
        ]

        for expected in expected_titles:
            assert (
                expected in group_titles
            ), f"Expected group '{expected}', got: {group_titles}"

    def test_slider_units_russian(self, geometry_panel):
        """Verify slider units are in Russian (м, мм)"""
        # Check wheelbase slider
        assert hasattr(
            geometry_panel, "wheelbase_slider"
        ), "GeometryPanel should have wheelbase_slider"

        wheelbase_units = geometry_panel.wheelbase_slider.units
        assert (
            wheelbase_units == "м"
        ), f"Expected wheelbase units 'м', got '{wheelbase_units}'"

        # Check bore head slider
        assert hasattr(
            geometry_panel, "bore_head_slider"
        ), "GeometryPanel should have bore_head_slider"

        bore_units = geometry_panel.bore_head_slider.units
        assert bore_units == "мм", f"Expected bore units 'мм', got '{bore_units}'"

    def test_buttons_russian(self, geometry_panel):
        """Verify buttons are in Russian"""
        from PySide6.QtWidgets import QPushButton

        buttons = geometry_panel.findChildren(QPushButton)
        button_texts = [b.text() for b in buttons]

        assert (
            "Сбросить" in button_texts
        ), f"Expected 'Сбросить' button, got: {button_texts}"
        assert (
            "Проверить" in button_texts
        ), f"Expected 'Проверить' button, got: {button_texts}"


# ============================================================================
# PNEUMO PANEL TESTS
# ============================================================================


class TestPneumoPanel:
    """Test PneumoPanel russification and features"""

    def test_panel_title_russian(self, pneumo_panel):
        """Verify panel title is in Russian"""
        # Find title label
        title_labels = [
            w
            for w in pneumo_panel.children()
            if hasattr(w, "text") and hasattr(w, "font")
        ]

        title_found = False
        for label in title_labels:
            if hasattr(label, "font") and label.font().bold():
                text = label.text()
                if "Пневматическая" in text:
                    title_found = True
                    break

        assert title_found, "Expected 'Пневматическая система' title"

    def test_pressure_units_combobox_exists(self, pneumo_panel):
        """Verify pressure units QComboBox is created"""
        assert hasattr(
            pneumo_panel, "pressure_units_combo"
        ), "PneumoPanel should have pressure_units_combo attribute"
        assert isinstance(
            pneumo_panel.pressure_units_combo, QComboBox
        ), "pressure_units_combo should be QComboBox instance"

    def test_pressure_units_options_russian(self, pneumo_panel):
        """Verify pressure units QComboBox has Russian options"""
        combo = pneumo_panel.pressure_units_combo
        expected_items = ["бар (bar)", "Па (Pa)", "кПа (kPa)", "МПа (MPa)"]

        assert combo.count() == len(
            expected_items
        ), f"Expected {len(expected_items)} unit items, got {combo.count()}"

        for i, expected in enumerate(expected_items):
            actual = combo.itemText(i)
            assert (
                actual == expected
            ), f"Unit {i} mismatch: expected '{expected}', got '{actual}'"

    def test_group_boxes_russian(self, pneumo_panel):
        """Verify group box titles are in Russian"""
        from PySide6.QtWidgets import QGroupBox

        group_boxes = pneumo_panel.findChildren(QGroupBox)
        group_titles = [gb.title() for gb in group_boxes]

        expected_titles = [
            "Обратные клапаны",
            "Предохранительные клапаны",
            "Окружающая среда",
            "Системные опции",
        ]

        for expected in expected_titles:
            assert (
                expected in group_titles
            ), f"Expected group '{expected}', got: {group_titles}"

    def test_radio_buttons_russian(self, pneumo_panel):
        """Verify radio buttons are in Russian"""
        from PySide6.QtWidgets import QRadioButton

        radios = pneumo_panel.findChildren(QRadioButton)
        radio_texts = [r.text() for r in radios]

        assert (
            "Изотермический" in radio_texts
        ), f"Expected 'Изотермический' radio, got: {radio_texts}"
        assert (
            "Адиабатический" in radio_texts
        ), f"Expected 'Адиабатический' radio, got: {radio_texts}"

    def test_checkboxes_russian(self, pneumo_panel):
        """Verify checkboxes are in Russian"""
        from PySide6.QtWidgets import QCheckBox

        checkboxes = pneumo_panel.findChildren(QCheckBox)
        checkbox_texts = [cb.text() for cb in checkboxes]

        assert any(
            "изоляция" in text.lower() for text in checkbox_texts
        ), f"Expected 'изоляция' checkbox, got: {checkbox_texts}"


# ============================================================================
# REQUIREMENTS COMPLIANCE TESTS
# ============================================================================


class TestRequirementsCompliance:
    """Test compliance with PROMPT #1 requirements"""

    def test_no_docks_used(self, main_window):
        """Verify no QDockWidget is used (replaced with tabs)"""
        from PySide6.QtWidgets import QDockWidget

        docks = main_window.findChildren(QDockWidget)
        assert len(docks) == 0, f"Expected no QDockWidget, found {len(docks)}"

    def test_no_accordions_used(self, main_window):
        """Verify no QToolBox (accordions) are used"""
        from PySide6.QtWidgets import QToolBox

        toolboxes = main_window.findChildren(QToolBox)
        assert (
            len(toolboxes) == 0
        ), f"Expected no QToolBox (accordions), found {len(toolboxes)}"

    def test_scrollareas_exist(self, main_window):
        """Verify QScrollArea is used in tabs"""
        from PySide6.QtWidgets import QScrollArea

        scrolls = main_window.findChildren(QScrollArea)
        assert (
            len(scrolls) >= 3
        ), f"Expected at least 3 QScrollArea (for tabs), found {len(scrolls)}"

    def test_qcombobox_added(self, main_window):
        """Verify QComboBox widgets are added (presets, units)"""
        # Check in GeometryPanel
        assert (
            main_window.geometry_panel.preset_combo is not None
        ), "GeometryPanel should have preset QComboBox"

        # Check in PneumoPanel
        assert (
            main_window.pneumo_panel.pressure_units_combo is not None
        ), "PneumoPanel should have pressure units QComboBox"

    def test_charts_full_width_at_bottom(self, main_window):
        """Verify charts are at bottom with full width"""
        # Charts should be in vertical splitter (bottom section)
        splitter = main_window.main_splitter
        chart_widget = main_window.chart_widget

        # Check chart is in splitter
        chart_index = -1
        for i in range(splitter.count()):
            if splitter.widget(i) == chart_widget:
                chart_index = i
                break

        assert chart_index >= 0, "ChartWidget should be in main splitter"

        # Charts should be in bottom section (index 1 for vertical splitter)
        assert (
            chart_index == 1
        ), f"Charts should be at index 1 (bottom), got {chart_index}"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short", "-s"])
