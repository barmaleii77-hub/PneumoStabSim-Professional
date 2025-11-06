"""Utilities for loading physics regression scenarios defined in JSON/YAML."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Optional,
)

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = REPO_ROOT / "config" / "schemas"


@dataclass(frozen=True)
class AssertionDefinition:
    """Structured representation of a single assertion."""

    kind: str
    target: str
    expected: Any
    tolerance: float
    source: Optional[str]


@dataclass(frozen=True)
class SceneDefinition:
    """In-memory representation of the YAML physics scene."""

    name: str
    attachment_points: Mapping[str, tuple[float, float]]
    axis_directions: Mapping[str, tuple[float, float, float]]
    state_vectors: Mapping[str, tuple[float, ...]]
    pneumatic: Mapping[str, Any]
    description: str | None = None
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class TestCaseDefinition:
    """Combined descriptor referencing a scene and associated assertions."""

    identifier: str
    name: str
    scene_path: Path
    scene: SceneDefinition
    assertions: tuple[AssertionDefinition, ...]
    description: str | None = None
    tags: tuple[str, ...] = ()

    def iter_assertions(self) -> Iterator[AssertionDefinition]:
        """Return an iterator over assertion definitions."""

        return iter(self.assertions)


class SchemaRegistry:
    """Lightweight cache for JSON/YAML schemas used during test loading."""

    def __init__(self) -> None:
        self._cache: MutableMapping[str, Mapping[str, Any]] = {}

    def load(self, schema_name: str) -> Mapping[str, Any]:
        """Load and cache a schema residing in :mod:`config/schemas`."""

        if schema_name in self._cache:
            return self._cache[schema_name]

        schema_path = SCHEMA_DIR / schema_name
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema {schema_name} not found in {SCHEMA_DIR}")

        if schema_path.suffix in {".yaml", ".yml"}:
            raw = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        else:
            raw = json.loads(schema_path.read_text(encoding="utf-8"))
        if not isinstance(raw, Mapping):
            raise TypeError(f"Schema {schema_name} did not evaluate to a mapping")

        self._cache[schema_name] = raw
        return raw


_SCHEMAS = SchemaRegistry()


def _validate(instance: Mapping[str, Any], schema_name: str) -> None:
    """Validate ``instance`` against the cached schema."""

    schema = _SCHEMAS.load(schema_name)
    resolver = jsonschema.validators.RefResolver.from_schema(schema)
    jsonschema.validate(instance=instance, schema=schema, resolver=resolver)


def _coerce_attachment_points(
    raw: Mapping[str, Iterable[float]],
) -> Dict[str, tuple[float, float]]:
    result: Dict[str, tuple[float, float]] = {}
    for key, values in raw.items():
        coords = tuple(float(v) for v in values)
        if len(coords) != 2:
            raise ValueError(
                f"Attachment point '{key}' must contain two values, got {coords}"
            )
        result[key] = coords  # type: ignore[assignment]
    return result


def _coerce_axis_directions(
    raw: Mapping[str, Iterable[float]],
) -> Dict[str, tuple[float, float, float]]:
    result: Dict[str, tuple[float, float, float]] = {}
    for key, values in raw.items():
        coords = tuple(float(v) for v in values)
        if len(coords) != 3:
            raise ValueError(
                f"Axis direction '{key}' must contain three values, got {coords}"
            )
        result[key] = coords  # type: ignore[assignment]
    return result


def _coerce_state_vectors(
    raw: Mapping[str, Iterable[float]],
) -> Dict[str, tuple[float, ...]]:
    result: Dict[str, tuple[float, ...]] = {}
    for name, values in raw.items():
        vector = tuple(float(v) for v in values)
        if len(vector) != 6:
            raise ValueError(
                f"State vector '{name}' must contain six values, got {vector}"
            )
        result[name] = vector
    return result


def _coerce_pneumatic_block(raw: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert pneumatic parameters to numeric heavy structures."""

    converted: Dict[str, Any] = {"pressures": {}, "springs": {}, "dampers": {}}

    pressures = raw.get("pressures", {})
    for wheel, payload in pressures.items():
        converted["pressures"][wheel] = {
            "head": float(payload["head"]),
            "rod": float(payload["rod"]),
        }

    springs = raw.get("springs", {})
    for wheel, payload in springs.items():
        converted["springs"][wheel] = {
            "rest": float(payload["rest"]),
            "current": float(payload["current"]),
        }

    dampers = raw.get("dampers", {})
    for wheel, value in dampers.items():
        converted["dampers"][wheel] = float(value)

    declared_wheels = {
        key: set(mapping.keys()) for key, mapping in converted.items() if mapping
    }
    if declared_wheels:
        reference_name, reference_set = next(iter(declared_wheels.items()))
        for block_name, wheel_set in declared_wheels.items():
            if wheel_set != reference_set:
                missing = reference_set.symmetric_difference(wheel_set)
                raise ValueError(
                    "Inconsistent pneumatic wheel definitions between"
                    f" '{reference_name}' and '{block_name}': {sorted(missing)}"
                )

    return converted


def load_scene(scene_path: Path) -> SceneDefinition:
    """Load a scene YAML file into a :class:`SceneDefinition`."""

    scene_data = yaml.safe_load(scene_path.read_text(encoding="utf-8"))
    if not isinstance(scene_data, Mapping):
        raise TypeError(f"Scene {scene_path} must evaluate to a mapping")

    _validate(scene_data, "scene.schema.yaml")

    notes = tuple(str(entry) for entry in scene_data.get("notes", []))
    return SceneDefinition(
        name=str(scene_data["name"]),
        description=scene_data.get("description"),
        attachment_points=_coerce_attachment_points(scene_data["attachment_points"]),
        axis_directions=_coerce_axis_directions(scene_data["axis_directions"]),
        state_vectors=_coerce_state_vectors(scene_data["state_vectors"]),
        pneumatic=_coerce_pneumatic_block(scene_data["pneumatic"]),
        notes=notes,
    )


def load_test_case(case_path: Path) -> TestCaseDefinition:
    """Load a ``.test.json`` descriptor and its linked scene."""

    raw_case = json.loads(case_path.read_text(encoding="utf-8"))
    if not isinstance(raw_case, Mapping):
        raise TypeError(f"Test case {case_path} must contain a mapping")

    _validate(raw_case, "test_case.schema.json")

    scene_path = case_path.parent / str(raw_case["scene"])
    if not scene_path.exists():
        raise FileNotFoundError(
            f"Scene {scene_path} referenced by {case_path} is missing"
        )

    scene = load_scene(scene_path)

    assertions: list[AssertionDefinition] = []
    for entry in raw_case.get("assertions", []):
        assertions.append(
            AssertionDefinition(
                kind=str(entry["kind"]),
                target=str(entry["target"]),
                expected=entry["expected"],
                tolerance=float(entry.get("tolerance", 1e-6)),
                source=str(entry.get("source"))
                if entry.get("source") is not None
                else None,
            )
        )

    tags = tuple(str(tag) for tag in raw_case.get("tags", []))
    return TestCaseDefinition(
        identifier=str(raw_case["id"]),
        name=str(raw_case["name"]),
        description=raw_case.get("description"),
        tags=tags,
        scene_path=scene_path,
        scene=scene,
        assertions=tuple(assertions),
    )


def discover_cases(base_dir: Path | None = None) -> tuple[TestCaseDefinition, ...]:
    """Discover all ``*.test.json`` descriptors under ``base_dir``."""

    directory = base_dir or (REPO_ROOT / "tests" / "physics" / "cases")
    pattern = "*.test.json"
    found: list[TestCaseDefinition] = []
    for path in sorted(directory.glob(pattern)):
        found.append(load_test_case(path))
    return tuple(found)


def build_case_loader(
    base_dir: Path | None = None,
) -> Callable[[str], TestCaseDefinition]:
    """Return a callable that loads a case by identifier."""

    cases = {case.identifier: case for case in discover_cases(base_dir)}

    def _load(identifier: str) -> TestCaseDefinition:
        try:
            return cases[identifier]
        except KeyError as exc:  # pragma: no cover - defensive programming
            available = ", ".join(sorted(cases)) or "<none>"
            raise KeyError(
                f"Unknown test case '{identifier}'. Available identifiers: {available}"
            ) from exc

    return _load


__all__ = [
    "AssertionDefinition",
    "SceneDefinition",
    "TestCaseDefinition",
    "build_case_loader",
    "discover_cases",
    "load_scene",
    "load_test_case",
]
