"""Утилита аудита конфигурации PneumoStabSim Professional.

Скрипт выполняет комплексную проверку конфигурационных файлов:
- валидацию структуры по JSON Schema;
- контроль контрольных сумм SHA256;
- поиск отклонений относительно эталонных значений;
- генерацию сводного Markdown-отчёта при необходимости.

Использование:
 python tools/audit_config.py --check
 python tools/audit_config.py --update-report
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
 """Описание отличий между текущим файлом и эталоном."""

 path: str
 baseline: JsonType
 current: JsonType


@dataclass(slots=True)
class AuditResult:
 """Результаты аудита конфигурации."""

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
 """Возвращает True, если выявлены ошибки или расхождения."""

 return bool(
 self.schema_errors
 or self.baseline_schema_errors
 or self.diffs
 or (
 self.expected_hash is not None
 and self.expected_hash != self.actual_hash
 )
 )


# Additional functions for reading JSON, computing SHA256, validating schema, etc.
# ...

if __name__ == "__main__":
 raise SystemExit(main())
