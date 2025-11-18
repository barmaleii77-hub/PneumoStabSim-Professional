from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "settings" / "app_settings.schema.json"
SETTINGS_PATH = REPO_ROOT / "config" / "app_settings.json"


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


@pytest.fixture()
def settings_payload() -> dict[str, object]:
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def test_pneumatic_receiver_volume_requires_positive(
    settings_payload: dict[str, object], validator: Draft202012Validator
) -> None:
    payload = deepcopy(settings_payload)
    payload["current"]["pneumatic"]["receiver_volume"] = -0.5  # type: ignore[index]

    with pytest.raises(ValidationError):
        validator.validate(payload)


def test_valve_diameter_has_upper_bound(
    settings_payload: dict[str, object], validator: Draft202012Validator
) -> None:
    payload = deepcopy(settings_payload)
    payload["current"]["constants"]["pneumo"]["valves"]["equivalent_diameter_m"] = 1.0  # type: ignore[index]

    with pytest.raises(ValidationError):
        validator.validate(payload)


def test_receiver_constants_disallow_zero_volumes(
    settings_payload: dict[str, object], validator: Draft202012Validator
) -> None:
    payload = deepcopy(settings_payload)
    payload["current"]["constants"]["pneumo"]["receiver"]["volume_min_m3"] = 0.0  # type: ignore[index]

    with pytest.raises(ValidationError):
        validator.validate(payload)


def test_simulation_dt_must_be_positive(
    settings_payload: dict[str, object], validator: Draft202012Validator
) -> None:
    payload = deepcopy(settings_payload)
    payload["current"]["simulation"]["physics_dt"] = 0  # type: ignore[index]

    with pytest.raises(ValidationError):
        validator.validate(payload)
