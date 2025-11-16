from __future__ import annotations

import logging
import re
import json
import time  # noqa: F401 - оставляем на случай будущих меток времени
from pathlib import Path
from urllib.parse import unquote, urlparse

_REMOTE_URL_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
_IBL_EVENTS_DIR_NAME = "ibl"
_IBL_EVENTS_FILE_PREFIX = "ibl_events_"  # noqa: F401 - сохранено для обратной совместимости
_IBL_EVENTS_SINGLE_FILE_NAME = "ibl_events.jsonl"


def _ensure_ibl_events_path(project_root: Path) -> Path:
    """Гарантировать существование каталога для IBL событий.

    Возвращает путь к *единому* jsonl файлу событий текущих запусков.
    Ранее использовались файлы с таймстампом, теперь консолидируем для
    упрощения анализа (append-only).
    """
    logs_root = project_root / "logs" / _IBL_EVENTS_DIR_NAME
    try:
        logs_root.mkdir(parents=True, exist_ok=True)
    except Exception:
        return project_root / "logs" / _IBL_EVENTS_DIR_NAME / "ibl_events_fallback.jsonl"
    return logs_root / _IBL_EVENTS_SINGLE_FILE_NAME

_ibl_session_path_cache: dict[Path, Path] = {}


def _ibl_session_path(project_root: Path) -> Path:
    cached = _ibl_session_path_cache.get(project_root)
    if cached is not None:
        return cached
    path = _ensure_ibl_events_path(project_root)
    _ibl_session_path_cache[project_root] = path
    return path


def _append_ibl_event(project_root: Path, payload: dict[str, object]) -> None:
    """Записать одно событие JSON в единый журнал IBL (best-effort)."""
    try:
        path = _ibl_session_path(project_root)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _build_candidate_paths(
    path_input: Path,
    *,
    qml_base_dir: Path | None,
    project_root: Path,
) -> list[Path]:
    if path_input.is_absolute():
        return [path_input]
    base_dirs: list[Path] = []
    if qml_base_dir is not None:
        base_dirs.append(qml_base_dir)
    base_dirs.extend(
        [
            project_root / "assets" / "qml",
            project_root / "assets" / "hdr",
            project_root / "assets",
            project_root,
        ]
    )
    deduplicated_base_dirs: list[Path] = []
    for candidate in base_dirs:
        if candidate not in deduplicated_base_dirs:
            deduplicated_base_dirs.append(candidate)
    candidates = [(base / path_input).resolve() for base in deduplicated_base_dirs]
    if not candidates:
        candidates.append(path_input)
    return candidates


def _normalise_file_url(text: str) -> Path:
    parsed = urlparse(text)
    netloc = parsed.netloc
    path_component = unquote(parsed.path or "")
    if netloc and not path_component.startswith("/"):
        combined = f"//{netloc}/{path_component}" if path_component else f"//{netloc}"
        return Path(combined)
    if netloc:
        combined = f"//{netloc}{path_component}"
        return Path(combined)
    return Path(path_component or "/")


def normalise_hdr_path(
    raw_value: str,
    *,
    qml_base_dir: Path | None,
    project_root: Path,
    logger: logging.Logger,
) -> str:
    """Resolve HDR asset references to canonical file URLs + JSON event logging.

    Возвращает file:// URL при успешном обнаружении ассета, либо пустую строку.
    Remote URL возвращается как есть (http/https и др.). При каждом вызове
    записывается JSON событие с полем status: ok|missing|remote|empty.
    """
    stripped = (raw_value or "").strip()
    if not stripped:
        _append_ibl_event(
            project_root,
            {
                "event": "asset_lookup",
                "input": raw_value,
                "status": "empty",
                "resolved": "",
                "candidates": [],
            },
        )
        return ""
    lowered = stripped.lower()
    if lowered.startswith("file://"):
        candidates = [_normalise_file_url(stripped)]
    elif _REMOTE_URL_PATTERN.match(stripped):
        _append_ibl_event(
            project_root,
            {
                "event": "asset_lookup",
                "input": raw_value,
                "status": "remote",
                "resolved": stripped,
                "candidates": [],
            },
        )
        return stripped
    else:
        if len(stripped) >= 2 and stripped[1] == ":":  # windows drive letter
            path_input = Path(stripped)
        else:
            path_input = Path(stripped)
        candidates = _build_candidate_paths(
            path_input,
            qml_base_dir=qml_base_dir,
            project_root=project_root,
        )
    for candidate in candidates:
        try:
            if candidate.exists():
                resolved_url = candidate.resolve().as_uri()
                _append_ibl_event(
                    project_root,
                    {
                        "event": "asset_lookup",
                        "input": raw_value,
                        "status": "ok",
                        "resolved": resolved_url,
                        "candidates": [str(c) for c in candidates],
                    },
                )
                return resolved_url
        except OSError:
            continue
    try:
        preview = ", ".join(str(candidate) for candidate in candidates[:3])
    except Exception:  # pragma: no cover - defensive fallback
        preview = stripped
    logger.warning(
        "normalizeHdrPath: HDR asset not found (input=%s, candidates=%s)",
        raw_value,
        preview,
    )
    _append_ibl_event(
        project_root,
        {
            "event": "asset_lookup",
            "input": raw_value,
            "status": "missing",
            "resolved": "",
            "candidates": [str(c) for c in candidates],
        },
    )
    return ""
