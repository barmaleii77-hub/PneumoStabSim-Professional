"""UI-level tests using pytest-qt to validate parameter workflows."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.ui.geometry_schema import GeometryValidationError, validate_geometry_settings


VALID_PAYLOAD = {
    "wheelbase": 2.5,
    "track": 1.6,
    "frame_to_pivot": 0.45,
    "lever_length": 0.75,
    "rod_position": 0.42,
    "cylinder_length": 0.5,
    "cyl_diam_m": 0.12,
    "stroke_m": 0.18,
    "rod_diameter_m": 0.035,
    "rod_diameter_rear_m": 0.035,
    "piston_rod_length_m": 0.12,
    "piston_thickness_m": 0.025,
    "frame_height_m": 0.55,
    "frame_beam_size_m": 0.12,
    "tail_rod_length_m": 0.34,
    "dead_gap_m": 0.005,
    "interference_check": True,
    "link_rod_diameters": True,
}


def test_geometry_validation_success():
    result = validate_geometry_settings(VALID_PAYLOAD)
    assert result.values["wheelbase"] == pytest.approx(2.5)
    assert result.to_config_dict()["lever_length"] == pytest.approx(0.75)


def test_geometry_validation_accepts_decimal_payload():
    payload = {
        key: (Decimal(str(value)) if isinstance(value, float) else value)
        for key, value in VALID_PAYLOAD.items()
    }

    result = validate_geometry_settings(payload)
    assert result.values["wheelbase"] == pytest.approx(
        float(VALID_PAYLOAD["wheelbase"])
    )


def test_geometry_validation_failure():
    invalid = dict(VALID_PAYLOAD)
    invalid["wheelbase"] = 0.0
    with pytest.raises(GeometryValidationError):
        validate_geometry_settings(invalid)


@pytest.mark.usefixtures("qapp")
def test_indicator_updates_with_pytest_qt(qtbot):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QLabel, QLineEdit

    field = QLineEdit()
    indicator = QLabel("OK")
    qtbot.addWidget(field)
    qtbot.addWidget(indicator)

    def update_indicator(text: str) -> None:
        if not text or float(text) <= 0:
            indicator.setText("⚠️")
            indicator.setProperty("state", "invalid")
        else:
            indicator.setText("✅")
            indicator.setProperty("state", "valid")

    field.textChanged.connect(update_indicator)

    field.setText("0")
    assert indicator.text() == "⚠️"
    assert indicator.property("state") == "invalid"

    field.setText("2.5")
    assert indicator.text() == "✅"
    assert indicator.property("state") == "valid"


@pytest.mark.usefixtures("qapp")
def test_user_flow_simulation(qtbot):
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QPushButton, QLineEdit

    field = QLineEdit()
    button = QPushButton("Apply")
    qtbot.addWidget(field)
    qtbot.addWidget(button)

    collected: list[str] = []

    def on_clicked() -> None:
        collected.append(field.text())

    button.clicked.connect(on_clicked)

    qtbot.keyClicks(field, "2.50")
    qtbot.mouseClick(button, Qt.LeftButton)

    assert collected == ["2.50"]
