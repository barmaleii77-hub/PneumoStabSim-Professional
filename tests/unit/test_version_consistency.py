"""Ensure release version metadata matches published documentation."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load_config_version() -> str:
    settings_path = ROOT / "config" / "app_settings.json"
    with settings_path.open(encoding="utf-8") as fh:
        metadata = json.load(fh)["metadata"]
    version = metadata.get("version")
    if not isinstance(version, str):
        raise AssertionError("metadata.version отсутствует или имеет неверный тип")
    return version


def _assert_pattern(path: Path, pattern: str, expected_version: str) -> None:
    text = path.read_text(encoding="utf-8")
    match = re.search(pattern, text)
    assert match is not None, f"Не найден шаблон `{pattern}` в {path}"
    version = match.groupdict().get("ver")
    if version is None and match.groups():
        version = match.group(1)
    assert version == expected_version, (
        f"Версия {version!r} в {path} не совпадает с metadata.version {expected_version!r}"
    )


def test_release_version_is_in_sync_with_documentation() -> None:
    version = _load_config_version()

    checks = {
        ROOT / "README.md": [
            r"Version-(?P<ver>\d+\.\d+\.\d+)-orange\.svg",
            r"Новое в версии (?P<ver>\d+\.\d+\.\d+)",
            r"Professional v(?P<ver>\d+\.\d+\.\d+)\*\* -",
        ],
        ROOT / "docs" / "README.md": [
            r"Professional v(?P<ver>\d+\.\d+\.\d+) — Documentation Hub",
            r"Project Layout \(v(?P<ver>\d+\.\d+\.\d+)\)",
            r"релиза v(?P<ver>\d+\.\d+\.\d+)",
        ],
        ROOT / "docs" / "SETTINGS_ARCHITECTURE.md": [
            r"\*\*Версия:\*\* PneumoStabSim Professional v(?P<ver>\d+\.\d+\.\d+)",
            r"\"version\": \"(?P<ver>\d+\.\d+\.\d+)\"",
        ],
        ROOT / "docs" / "HDR_PATHS_UNIFIED.md": [
            r"PneumoStabSim Professional v(?P<ver>\d+\.\d+\.\d+)",
            r"\*\*Версия\*\*: v(?P<ver>\d+\.\d+\.\d+)",
        ],
        ROOT / "docs" / "settings_control_matrix.md": [
            r"\|\s*``metadata\.version``\s*\|\s*\"(?P<ver>\d+\.\d+\.\d+)\"",
        ],
        ROOT / "docs" / "CHANGELOG_MODULAR.md": [
            r"Модуляризация v(?P<ver>\d+\.\d+\.\d+)",
        ],
        ROOT / "assets" / "hdr" / "README.md": [
            r"Path Unification \(v(?P<ver>\d+\.\d+\.\d+)\)",
        ],
    }

    for target, patterns in checks.items():
        for pattern in patterns:
            _assert_pattern(target, pattern, version)
