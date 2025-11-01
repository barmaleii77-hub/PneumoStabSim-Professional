from __future__ import annotations

import logging
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

_REMOTE_URL_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


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

    # Удаляем возможные дубликаты, сохраняя порядок поиска (в т.ч. если
    # qml_base_dir уже указывает на одну из папок выше).
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
        # Network paths: file://server/share.hdr
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
    """Resolve HDR asset references to canonical file URLs.

    Args:
        raw_value: Original path or URL supplied by the UI/settings.
        qml_base_dir: Base directory of the loaded QML file, when available.
        project_root: Repository root used as a fallback search location.
        logger: Logger used to report missing assets.

    Returns:
        Normalised file URL string when the asset exists, an untouched remote URL,
        or an empty string if the asset could not be located.
    """

    stripped = (raw_value or "").strip()
    if not stripped:
        return ""

    lowered = stripped.lower()
    if lowered.startswith("file://"):
        candidates = [_normalise_file_url(stripped)]
    elif _REMOTE_URL_PATTERN.match(stripped):
        # Remote URLs (http, https, s3, etc.) are returned verbatim.
        return stripped
    else:
        # Windows drive letters may parse as schemes; treat them as local paths.
        if len(stripped) >= 2 and stripped[1] == ":":
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
                return candidate.resolve().as_uri()
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
    return ""
