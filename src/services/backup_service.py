"""Backup and restore utilities for user generated data.

The backup service consolidates all directories and files that may contain
user-supplied content (profiles, session exports, telemetry captures, etc.) and
provides a deterministic archive format.  Archives are standard ZIP files that
carry a small JSON manifest (`PSS_BACKUP_MANIFEST.json`) describing what was
included.  The manifest allows administrators to audit the contents before
restoring and ensures forward compatibility if the list of data sources evolves
in future releases.
"""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Sequence, cast

from src.diagnostics.logger_factory import get_logger


__all__ = [
    "BackupReport",
    "BackupService",
    "RestoreReport",
    "discover_user_data_sources",
]


_MANIFEST_FILENAME = "PSS_BACKUP_MANIFEST.json"
_DEFAULT_BACKUP_DIR = Path("backups")

# Default directories/files that contain user generated data.  The list is kept
# intentionally broad so we do not miss artefacts that operators rely on during
# incident response or auditing.
_DEFAULT_USER_DATA_SOURCES: tuple[Path, ...] = (
    Path("config/app_settings.json"),
    Path("config/orbit_presets.json"),
    Path("config/user_profiles"),
    Path("config/ui_layouts"),
    Path("reports"),
)


@dataclass(slots=True)
class BackupReport:
    """Result returned after creating a backup archive."""

    archive_path: Path
    created_at: datetime
    included: tuple[Path, ...]
    skipped: tuple[Path, ...]


@dataclass(slots=True)
class RestoreReport:
    """Result returned after restoring a backup archive."""

    archive_path: Path
    target_root: Path
    restored: tuple[Path, ...]
    skipped: tuple[Path, ...]
    manifest: dict[str, object] | None


@dataclass(frozen=True, slots=True)
class _UserDataSource:
    """Internal representation mapping absolute and relative paths."""

    absolute_path: Path
    relative_path: Path


def discover_user_data_sources() -> tuple[Path, ...]:
    """Return the default list of user data sources.

    The function exposes the canonical list so other modules (documentation
    generators, diagnostics tooling, etc.) can display the same information
    without importing :class:`BackupService`.
    """

    return _DEFAULT_USER_DATA_SOURCES


class BackupService:
    """Create and restore archives containing user generated content."""

    def __init__(
        self,
        *,
        root: Path | str | None = None,
        backup_dir: Path | str | None = None,
        data_sources: Sequence[Path | str] | None = None,
    ) -> None:
        self._logger = get_logger("services.backup")
        self._root = Path(root or Path.cwd()).resolve()

        if backup_dir is None:
            backup_dir_path = _DEFAULT_BACKUP_DIR
        else:
            backup_dir_path = Path(backup_dir)
        if not backup_dir_path.is_absolute():
            backup_dir_path = (self._root / backup_dir_path).resolve()
        self._backup_dir = backup_dir_path
        self._backup_dir.mkdir(parents=True, exist_ok=True)

        chosen_sources = data_sources or _DEFAULT_USER_DATA_SOURCES
        self._sources = self._normalise_sources(chosen_sources)

    # ------------------------------------------------------------------ helpers
    def _normalise_sources(
        self, sources: Sequence[Path | str]
    ) -> tuple[_UserDataSource, ...]:
        normalised: list[_UserDataSource] = []
        seen: set[Path] = set()
        for entry in sources:
            raw = Path(entry)
            if raw in seen:
                continue
            seen.add(raw)
            absolute = (self._root / raw).resolve() if not raw.is_absolute() else raw
            try:
                relative = absolute.relative_to(self._root)
            except ValueError:
                # Place external sources under a synthetic namespace to avoid
                # collisions with project files.
                relative = Path("external") / absolute.name
            normalised.append(
                _UserDataSource(absolute_path=absolute, relative_path=relative)
            )
        return tuple(normalised)

    @staticmethod
    def _slugify(label: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", label.strip().lower())
        slug = re.sub(r"-+", "-", slug).strip("-_")
        return slug or "manual"

    @staticmethod
    def _write_directory_entry(archive: zipfile.ZipFile, relative: Path) -> None:
        name = relative.as_posix().rstrip("/") + "/"
        info = zipfile.ZipInfo(name)
        archive.writestr(info, "")

    def _iter_directory(self, source: _UserDataSource) -> Iterator[tuple[Path, Path]]:
        absolute = source.absolute_path
        base = source.relative_path
        for item in sorted(absolute.rglob("*")):
            yield item, base / item.relative_to(absolute)

    def _serialise_manifest(
        self,
        *,
        created_at: datetime,
        included: Iterable[Path],
        skipped: Iterable[Path],
    ) -> str:
        manifest = {
            "version": "1.0",
            "created_at": created_at.isoformat(),
            "root": str(self._root),
            "sources": [str(src.relative_path) for src in self._sources],
            "included": sorted({str(path) for path in included}),
            "skipped": sorted({str(path) for path in skipped}),
        }
        return json.dumps(manifest, ensure_ascii=False, indent=2)

    @staticmethod
    def _safe_member(member: str) -> Path | None:
        path = Path(member)
        if member.endswith("/"):
            # Directories are handled separately and do not need validation here.
            return path
        if Path(member).name == _MANIFEST_FILENAME:
            return None
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Refusing to restore unsafe archive member: {member}")
        return path

    # ---------------------------------------------------------------- operations
    def create_backup(
        self,
        *,
        label: str | None = None,
        include_timestamp: bool = True,
    ) -> BackupReport:
        """Create a ZIP archive containing user data sources."""

        created_at = datetime.now(timezone.utc)
        parts: list[str] = ["backup"]
        if include_timestamp:
            parts.append(created_at.strftime("%Y%m%d-%H%M%S"))
        if label:
            parts.append(self._slugify(label))
        archive_name = "_".join(parts) + ".zip"
        archive_path = self._backup_dir / archive_name

        included: set[Path] = set()
        skipped: set[Path] = set()

        with zipfile.ZipFile(
            archive_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            for source in self._sources:
                absolute = source.absolute_path
                relative = source.relative_path
                if not absolute.exists():
                    skipped.add(relative)
                    self._logger.warning(
                        "backup_source_missing",
                        source=str(absolute),
                        relative=str(relative),
                    )
                    continue

                if absolute.is_file():
                    archive.write(absolute, relative.as_posix())
                    included.add(relative)
                    continue

                if absolute.is_dir():
                    has_entries = False
                    for filesystem_path, archive_path_relative in self._iter_directory(
                        source
                    ):
                        if filesystem_path.is_dir():
                            # Only add explicit entries for empty directories.
                            if not any(filesystem_path.iterdir()):
                                self._write_directory_entry(
                                    archive,
                                    archive_path_relative,
                                )
                                included.add(archive_path_relative)
                            continue
                        archive.write(filesystem_path, archive_path_relative.as_posix())
                        included.add(archive_path_relative)
                        has_entries = True
                    if not has_entries:
                        self._write_directory_entry(archive, relative)
                        included.add(relative)
                    continue

                skipped.add(relative)
                self._logger.warning(
                    "backup_source_unsupported",
                    source=str(absolute),
                    relative=str(relative),
                )

            archive.writestr(
                _MANIFEST_FILENAME,
                self._serialise_manifest(
                    created_at=created_at, included=included, skipped=skipped
                ),
            )

        self._logger.info(
            "backup_created",
            archive=str(archive_path),
            included=len(included),
            skipped=len(skipped),
        )
        return BackupReport(
            archive_path=archive_path,
            created_at=created_at,
            included=tuple(sorted(included)),
            skipped=tuple(sorted(skipped)),
        )

    def list_archives(self) -> list[Path]:
        """Return available backup archives sorted by modification time (desc)."""

        if not self._backup_dir.exists():
            return []
        archives = [path for path in self._backup_dir.glob("*.zip") if path.is_file()]
        archives.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        return archives

    def inspect_backup(self, archive_path: Path | str) -> dict[str, object]:
        """Load the manifest embedded inside a backup archive."""

        archive = Path(archive_path)
        with zipfile.ZipFile(archive, "r") as handle:
            try:
                with handle.open(_MANIFEST_FILENAME) as manifest_handle:
                    return cast(dict[str, object], json.load(manifest_handle))
            except KeyError as exc:  # pragma: no cover
                # Legacy archives might not have manifests.
                raise KeyError(
                    f"Archive {archive} does not contain {_MANIFEST_FILENAME}."
                ) from exc

    def prune_backups(self, *, keep: int) -> list[Path]:
        """Keep the newest ``keep`` backups, deleting older ones."""

        if keep < 0:
            raise ValueError("keep must be non-negative")
        archives = self.list_archives()
        if keep >= len(archives):
            return []
        to_remove = archives[keep:]
        for archive in to_remove:
            try:
                archive.unlink()
                self._logger.info("backup_removed", archive=str(archive))
            except OSError as exc:
                self._logger.error(
                    "backup_remove_failed", archive=str(archive), error=str(exc)
                )
        return to_remove

    def restore_backup(
        self,
        archive_path: Path | str,
        *,
        target_root: Path | str | None = None,
        overwrite: bool = False,
    ) -> RestoreReport:
        """Restore files from an archive into ``target_root``."""

        archive = Path(archive_path)
        if not archive.exists():
            raise FileNotFoundError(f"Archive not found: {archive}")

        target = Path(target_root) if target_root is not None else self._root
        target = target.resolve()
        target.mkdir(parents=True, exist_ok=True)

        restored: list[Path] = []
        skipped: list[Path] = []

        manifest: dict[str, object] | None = None

        with zipfile.ZipFile(archive, "r") as handle:
            try:
                with handle.open(_MANIFEST_FILENAME) as manifest_handle:
                    manifest = cast(dict[str, object], json.load(manifest_handle))
            except KeyError:
                manifest = None

            for member in handle.namelist():
                if member == _MANIFEST_FILENAME:
                    continue
                relative = self._safe_member(member)
                if relative is None:
                    continue

                if member.endswith("/"):
                    destination_dir = (target / relative).resolve()
                    if not destination_dir.is_relative_to(target):
                        raise ValueError(
                            f"Archive member escapes target directory: {member}"
                        )
                    destination_dir.mkdir(parents=True, exist_ok=True)
                    continue

                destination = (target / relative).resolve()
                if not destination.is_relative_to(target):
                    raise ValueError(
                        f"Archive member escapes target directory: {member}"
                    )
                if destination.exists() and not overwrite:
                    skipped.append(destination.relative_to(target))
                    continue

                destination.parent.mkdir(parents=True, exist_ok=True)
                with handle.open(member) as source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output)
                restored.append(destination.relative_to(target))

        self._logger.info(
            "backup_restored",
            archive=str(archive),
            restored=len(restored),
            skipped=len(skipped),
            target=str(target),
        )
        return RestoreReport(
            archive_path=archive,
            target_root=target,
            restored=tuple(restored),
            skipped=tuple(skipped),
            manifest=manifest,
        )

    # ---------------------------------------------------------------- properties
    @property
    def backup_dir(self) -> Path:
        """Directory where backups are stored."""

        return self._backup_dir

    @property
    def data_sources(self) -> tuple[_UserDataSource, ...]:
        """Return the resolved data sources."""

        return self._sources

    @property
    def root(self) -> Path:
        """Base directory used to resolve relative paths."""

        return self._root
