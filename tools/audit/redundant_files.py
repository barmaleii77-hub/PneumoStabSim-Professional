"""Анализатор дублирующихся и устаревших файлов в репозитории.

Сценарий помогает выявить документы и скрипты, которые по вероятности
дублируют друг друга или относятся к устаревшим «горячим» фиксам.
Отчёт используется в рамках раздела "Cleanup & Legacy Removal" генерального
плана модернизации.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable, Sequence

__all__ = [
    "AuditCandidate",
    "scan_redundant_files",
    "build_markdown_report",
    "main",
]

_ROOT_KEYWORDS = (
    "report",
    "summary",
    "fix",
    "checklist",
    "guide",
    "status",
    "final",
    "audit",
)
_SCRIPT_KEYWORDS = (
    "fix",
    "legacy",
    "backup",
    "old",
)
_IGNORED_DIRS = {
    ".git",
    ".github",
    "__pycache__",
    "build",
    "dist",
    "logs",
    "venv",
    "env",
    ".venv",
}
_DOC_SUFFIXES = {".md", ".txt"}
_SCRIPT_SUFFIXES = {".py", ".ps1", ".bat"}


@dataclass(slots=True)
class AuditCandidate:
    """Описание файла, который потенциально следует переместить в архив."""

    path: Path
    reasons: list[str]
    size_bytes: int
    modified_at: dt.datetime

    def to_dict(self, root: Path) -> dict[str, object]:
        """Преобразует данные кандидата к сериализуемому виду."""

        return {
            "path": str(self.path.relative_to(root)),
            "reasons": list(self.reasons),
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at.isoformat(timespec="seconds"),
        }


def _iter_project_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _IGNORED_DIRS for part in path.parts):
            continue
        yield path


def _normalise_name(path: Path) -> str:
    base = path.stem.lower()
    base = re.sub(r"v\d+(?:[._-]\d+)*", "", base)
    base = re.sub(r"\d+", "", base)
    base = re.sub(r"[^a-z0-9]+", "", base)
    return base


def _collect_keyword_reasons(path: Path, relative: Path) -> list[str]:
    reasons: list[str] = []
    depth = len(relative.parts)
    lower_name = path.stem.lower()

    if depth == 1 and path.suffix in _DOC_SUFFIXES:
        for keyword in _ROOT_KEYWORDS:
            if keyword in lower_name:
                reasons.append(
                    f"Название содержит ключевое слово '{keyword}' — вероятный служебный отчёт"
                )
                break

    if depth == 1 and path.suffix in _SCRIPT_SUFFIXES:
        for keyword in _SCRIPT_KEYWORDS:
            if keyword in lower_name:
                reasons.append(
                    "Сценарий расположен в корне и выглядит как временный фикс"
                )
                break

    return reasons


def scan_redundant_files(root: Path) -> list[AuditCandidate]:
    """Сканирует репозиторий в поиске дублирующихся или устаревших файлов."""

    root = root.resolve()
    documents: list[Path] = []
    candidates: dict[Path, AuditCandidate] = {}

    for file_path in _iter_project_files(root):
        relative = file_path.relative_to(root)
        reasons = _collect_keyword_reasons(file_path, relative)

        if file_path.suffix in _DOC_SUFFIXES and len(relative.parts) == 1:
            documents.append(file_path)

        if reasons:
            candidate = AuditCandidate(
                path=file_path,
                reasons=reasons,
                size_bytes=file_path.stat().st_size,
                modified_at=dt.datetime.fromtimestamp(
                    file_path.stat().st_mtime, tz=dt.timezone.utc
                ),
            )
            candidates[file_path] = candidate

    # Анализируем похожие названия среди документов верхнего уровня.
    groups: dict[str, list[Path]] = {}
    for document in documents:
        key = _normalise_name(document)
        groups.setdefault(key, []).append(document)

    for group in groups.values():
        if len(group) < 2:
            continue
        reason = "Найдено несколько документов с похожим названием — возможно, их стоит объединить"
        for path in group:
            candidate = candidates.get(path)
            if candidate is None:
                candidate = AuditCandidate(
                    path=path,
                    reasons=[reason],
                    size_bytes=path.stat().st_size,
                    modified_at=dt.datetime.fromtimestamp(
                        path.stat().st_mtime, tz=dt.timezone.utc
                    ),
                )
                candidates[path] = candidate
            elif reason not in candidate.reasons:
                candidate.reasons.append(reason)

    return sorted(candidates.values(), key=lambda cand: cand.path)


def build_markdown_report(candidates: Sequence[AuditCandidate], root: Path) -> str:
    """Строит Markdown-отчёт по найденным кандидатам."""

    lines: list[str] = []
    lines.append("# 📦 Аудит потенциально избыточных файлов")
    lines.append("")
    lines.append(
        f"Дата отчёта: {dt.datetime.now(tz=dt.timezone.utc).isoformat(timespec='seconds')}"
    )
    lines.append("")

    if not candidates:
        lines.append("✅ Подходящих кандидатов не найдено.")
        return "\n".join(lines)

    lines.append(
        "Ниже перечислены файлы, которые соответствуют эвристикам программы очистки."
        "\n"
        "Рекомендуется проверить их и при необходимости перенести в архив `archive/`."
    )
    lines.append("")

    for candidate in candidates:
        rel_path = candidate.path.relative_to(root)
        lines.append(f"## {rel_path}")
        lines.append("")
        lines.append(f"- Размер: {candidate.size_bytes} байт")
        lines.append(
            "- Дата изменения: "
            f"{candidate.modified_at.astimezone(dt.timezone.utc).isoformat(timespec='seconds')}"
        )
        lines.append("- Причины:")
        for reason in candidate.reasons:
            lines.append(f"  - {reason}")
        lines.append("")

    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Поиск потенциально избыточных файлов в репозитории"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Корневая директория проекта (по умолчанию текущая)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Путь для сохранения отчёта (Markdown или JSON)",
    )
    parser.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
        help="Формат отчёта (по умолчанию Markdown)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа для CLI."""

    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    root = args.root.resolve()
    candidates = scan_redundant_files(root)

    if args.output is None:
        report = build_markdown_report(candidates, root)
        print(report)
        return 0

    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "md":
        report = build_markdown_report(candidates, root)
        output_path.write_text(report, encoding="utf-8")
    else:
        payload = [candidate.to_dict(root) for candidate in candidates]
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI запуск
    raise SystemExit(main())
