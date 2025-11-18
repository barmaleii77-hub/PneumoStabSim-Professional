from __future__ import annotations

from pathlib import Path

import pytest

SCENE_PATH = Path("qml/ThreeDScene.qml")


def _scene_text() -> str:
    return SCENE_PATH.read_text(encoding="utf-8")


def test_scene_contains_phase3_primitives_and_lights():
    text = _scene_text()

    for marker in ("#Cube", "#Sphere", "#Cylinder"):
        assert marker in text, f"Отсутствует примитив {marker}"

    for marker in ("DirectionalLight", "PointLight", "SceneEnvironment"):
        assert marker in text, f"Отсутствует блок освещения/окружения: {marker}"

    for marker in ("helperGrid", "AxisHelper"):
        assert marker in text, f"Отсутствуют вспомогательные элементы {marker}"


def test_scene_exposes_interaction_handlers_and_materials():
    text = _scene_text()

    for marker in ("DragHandler", "WheelHandler", "PinchHandler"):
        assert marker in text, f"Не найдена обработка ввода: {marker}"

    for marker in (
        "applyInteractionOverrides",
        "applyEnvironmentOverrides",
        "applyHelperOverrides",
    ):
        assert marker in text, f"Не найдена функция синхронизации: {marker}"

    for marker in (
        "roughness: boxRoughness",
        "metalness: sphereMetalness",
        "roughness: cylinderRoughness",
    ):
        assert marker in text, "Материалы примитивов не настраиваются"


def test_scene_has_phase3_camera_properties():
    text = _scene_text()

    for marker in ("orbitAzimuthDeg", "orbitElevationDeg", "orbitDistance"):
        assert marker in text, f"Не найдено поле камеры: {marker}"

    for marker in (
        "orbitMinDistance",
        "orbitMaxDistance",
        "minElevationDeg",
        "maxElevationDeg",
    ):
        assert marker in text, f"Не найдены ограничения камеры: {marker}"
    assert "fieldOfViewDeg" in text

    assert "frameRendered" in text
    assert "telemetry" in text


@pytest.mark.parametrize(
    "expected_token",
    [
        "helpersVisible",
        "gridSpacing",
        "environmentAaMode",
        "environmentAaQuality",
        "keyLightShadowBias",
    ],
)
def test_scene_environment_tokens(expected_token: str):
    assert expected_token in _scene_text()
