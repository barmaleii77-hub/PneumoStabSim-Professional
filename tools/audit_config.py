"""Utility for auditing application configuration files.

The original module lost all indentation which rendered it invalid Python code.
This rewritten version restores a compact but functional implementation that
validates the configuration against a schema, compares it with a baseline and
(optionally) produces a Markdown report.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft7Validator

JsonType = Any


@dataclass(slots=True)
class DiffEntry:
    """Single difference between the baseline and current configuration."""

    path: str
    baseline: JsonType
    current: JsonType


@dataclass(slots=True)
class AuditResult:
    """Aggregated information produced by :func:`run_audit`."""

    schema_errors: list[str]
    baseline_schema_errors: list[str]
    diffs: list[DiffEntry]
    expected_hash: str | None
    actual_hash: str
    metadata_parameters: int | None
    counted_parameters: int
    timestamp: dt.datetime

    @property
    def has_failures(self) -> bool:
        """Return ``True`` when the audit encountered mismatches or errors."""

        if self.schema_errors or self.baseline_schema_errors or self.diffs:
            return True
        if self.expected_hash is not None and self.expected_hash != self.actual_hash:
            return True
        return False


def read_json(path: Path) -> JsonType:
    """Load a JSON document using UTF-8 encoding."""

    with path.open(encoding="utf-8") as file:
        return json.load(file)


def compute_sha256(path: Path) -> str:
    """Calculate the SHA256 digest of ``path``."""

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_schema(data: JsonType, schema: JsonType) -> list[str]:
    """Validate ``data`` using ``schema`` returning human readable errors."""

    validator = Draft7Validator(schema)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda err: err.path):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


_MISSING = object()


def diff_dict(baseline: JsonType, current: JsonType, prefix: str = "") -> list[DiffEntry]:
    """Recursively diff two JSON-like objects."""

    if isinstance(baseline, dict) and isinstance(current, dict):
        diffs: list[DiffEntry] = []
        baseline_keys = set(baseline)
        current_keys = set(current)
        for key in sorted(baseline_keys | current_keys):
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            if key not in baseline:
                diffs.append(DiffEntry(new_prefix, "<missing>", current[key]))
                continue
            if key not in current:
                diffs.append(DiffEntry(new_prefix, baseline[key], "<missing>"))
                continue
            diffs.extend(diff_dict(baseline[key], current[key], new_prefix))
        return diffs

    if isinstance(baseline, list) and isinstance(current, list):
        diffs = []
        length = max(len(baseline), len(current))
        for index in range(length):
            base_item = baseline[index] if index < len(baseline) else _MISSING
            current_item = current[index] if index < len(current) else _MISSING
            new_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
            if base_item is _MISSING:
                diffs.append(DiffEntry(new_prefix, "<missing>", current_item))
                continue
            if current_item is _MISSING:
                diffs.append(DiffEntry(new_prefix, base_item, "<missing>"))
                continue
            diffs.extend(diff_dict(base_item, current_item, new_prefix))
        return diffs

    if baseline != current:
        return [DiffEntry(prefix or "<root>", baseline, current)]

    return []


def count_parameters(data: JsonType) -> int:
    """Count scalar values (ints, floats, strings, bools) inside ``data``."""

    if isinstance(data, dict):
        return sum(count_parameters(value) for value in data.values())
    if isinstance(data, list):
        return sum(count_parameters(value) for value in data)
    if isinstance(data, (int, float, str, bool)) or data is None:
        return 1
    return 0


def load_reference_hash(hashes_path: Path, key: str) -> str | None:
    """Return stored SHA256 checksum for ``key`` if the hashes file exists."""

    if not hashes_path.exists():
        return None
    hashes = read_json(hashes_path)
    entry = hashes.get(key, {}) if isinstance(hashes, dict) else {}
    sha_value = entry.get("sha256") if isinstance(entry, dict) else None
    return sha_value if isinstance(sha_value, str) else None


def build_report(result: AuditResult, config_path: Path, baseline_path: Path) -> str:
    """Create a Markdown report summarising the audit results."""

    timestamp = result.timestamp.isoformat(timespec="seconds")
    status = "✅ Без критических отклонений" if not result.has_failures else "⚠️ Требуется внимание"
    hash_status = (
        "Совпадает"
        if result.expected_hash is None or result.expected_hash == result.actual_hash
        else "Не совпадает"
    )
    metadata_note = (
        "совпадает"
        if result.metadata_parameters is None
        or result.metadata_parameters == result.counted_parameters
        else "отличается"
    )

    schema_section = ["### Проверка схемы"]
    if result.schema_errors:
        schema_section.append("- ❌ Текущий файл не соответствует схеме:")
        schema_section.extend(f" - {error}" for error in result.schema_errors)
    else:
        schema_section.append("- ✅ Текущий файл соответствует JSON Schema")

    if result.baseline_schema_errors:
        schema_section.append("- ❌ Эталонный файл не соответствует схеме:")
        schema_section.extend(f" - {error}" for error in result.baseline_schema_errors)
    else:
        schema_section.append("- ✅ Эталонный файл соответствует JSON Schema")

    diff_section = ["### Сравнение с эталоном"]
    if result.diffs:
        diff_section.append(f"- ⚠️ Найдено расхождений: {len(result.diffs)}")
        for entry in result.diffs[:20]:
            diff_section.append(
                " - `{}: эталон = `{}` → текущий = `{}`".format(
                    entry.path, entry.baseline, entry.current
                )
            )
        if len(result.diffs) > 20:
            diff_section.append(f" - … ещё {len(result.diffs) - 20} расхождений")
    else:
        diff_section.append("- ✅ Конфигурация совпадает с эталоном")

    stats_section = [
        "### Статистика",
        f"- Всего параметров: {result.counted_parameters}",
        "- Значение из metadata.total_parameters: {} ({})".format(
            result.metadata_parameters if result.metadata_parameters is not None else "—",
            metadata_note,
        ),
        "- Контрольная сумма SHA256: `{}` (ожидаемая: `{}`) — {}".format(
            result.actual_hash,
            result.expected_hash or "—",
            hash_status,
        ),
    ]

    report_lines = [
        "# Отчёт аудита конфигурации",
        "",
        f"- Дата проверки: {timestamp}",
        f"- Проверяемый файл: `{config_path}`",
        f"- Эталонный файл: `{baseline_path}`",
        f"- Итоговый статус: {status}",
        "",
        *schema_section,
        "",
        *diff_section,
        "",
        *stats_section,
        "",
        "---",
        "",
        "> Отчёт формируется автоматически утилитой `tools/audit_config.py`.",
    ]
    return "\n".join(report_lines) + "\n"


def run_audit(config_path: Path, schema_path: Path, baseline_path: Path, hashes_path: Path) -> AuditResult:
    """Execute the audit workflow and return an :class:`AuditResult`."""

    config = read_json(config_path)
    baseline = read_json(baseline_path)
    schema = read_json(schema_path)

    schema_errors = validate_schema(config, schema)
    baseline_schema_errors = validate_schema(baseline, schema)
    diffs = diff_dict(baseline, config)
    expected_hash = load_reference_hash(hashes_path, "app_settings")
    actual_hash = compute_sha256(config_path)

    metadata_parameters = None
    metadata_section = config.get("metadata") if isinstance(config, dict) else None
    if isinstance(metadata_section, dict):
        metadata_value = metadata_section.get("total_parameters")
        if isinstance(metadata_value, int):
            metadata_parameters = metadata_value

    counted_parameters = count_parameters(config.get("current", {})) if isinstance(config, dict) else 0

    return AuditResult(
        schema_errors=schema_errors,
        baseline_schema_errors=baseline_schema_errors,
        diffs=diffs,
        expected_hash=expected_hash,
        actual_hash=actual_hash,
        metadata_parameters=metadata_parameters,
        counted_parameters=counted_parameters,
        timestamp=dt.datetime.now(dt.timezone.utc),
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Аудит конфигурации приложения")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/app_settings.json"),
        help="Путь до проверяемого JSON",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("config/schemas/app_settings.schema.json"),
        help="Путь до JSON Schema",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("config/baseline/app_settings.json"),
        help="Путь до эталонного файла",
    )
    parser.add_argument(
        "--hashes",
        type=Path,
        default=Path("config/config_hashes.json"),
        help="Файл с эталонными контрольными суммами",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/config_audit_report.md"),
        help="Файл Markdown-отчёта",
    )
    parser.add_argument(
        "--update-report",
        action="store_true",
        help="Перегенерировать отчёт по результатам проверки",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Возвращать ненулевой код при любом предупреждении",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    args = parse_args(argv)
    result = run_audit(args.config, args.schema, args.baseline, args.hashes)

    if args.update_report:
        report_content = build_report(result, args.config, args.baseline)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report_content, encoding="utf-8")

    if result.has_failures:
        return 1

    if args.strict:
        hash_mismatch = result.expected_hash and result.expected_hash != result.actual_hash
        if hash_mismatch:
            return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution
    raise SystemExit(main())
