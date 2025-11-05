"""Minimal GUI wrapper around :class:`~src.services.backup_service.BackupService`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from src.diagnostics.logger_factory import get_logger
from src.services import BackupService, discover_user_data_sources

try:  # pragma: no cover - exercised indirectly in environments with Qt
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:  # pragma: no cover - Qt is optional for the test environment
    _HAS_QT = False


_QT_USER_ROLE = 32
_QMB_CRITICAL = None
_QMB_INFORMATION = None

if _HAS_QT:  # pragma: no branch - executed only when Qt is present
    _QT_USER_ROLE = getattr(Qt, "UserRole", _QT_USER_ROLE)
    _QMB_CRITICAL = getattr(QMessageBox, "Critical", None)
    _QMB_INFORMATION = getattr(QMessageBox, "Information", None)


LOGGER = get_logger("app.backup_gui")


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PneumoStabSim backup GUI")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root that contains the configuration and reports directories.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Directory where backup archives are stored (relative to root by default).",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


if not _HAS_QT:

    def run(argv: Sequence[str] | None = None) -> int:
        """Fallback entry point when Qt is not installed."""

        args = _parse_args(argv)
        LOGGER.warning(
            "backup_gui_unavailable",
            reason="pyside6_missing",
            root=str(args.root),
            backup_dir=str(args.backup_dir) if args.backup_dir else "<default>",
        )
        print(
            "PySide6 is not available. Install PySide6 or use the CLI: "
            "python -m src.cli.backup",
            file=sys.stderr,
        )
        return 1


else:  # pragma: no cover - requires GUI stack in the execution environment

    class BackupWindow(QWidget):
        """Qt widget presenting the most common backup operations."""

        def __init__(self, service: BackupService) -> None:
            super().__init__()
            self._service = service
            self._logger = LOGGER.bind(component="BackupWindow")
            self.setWindowTitle("PneumoStabSim Backup Manager")

            layout = QVBoxLayout(self)

            sources_text = "\n".join(
                f"• {path}" for path in discover_user_data_sources()
            )
            sources_label = QLabel(
                "<b>Tracked data sources</b><br>" + sources_text.replace("\n", "<br>")
            )
            sources_label.setWordWrap(True)
            layout.addWidget(sources_label)

            self._list = QListWidget(self)
            selection_mode = getattr(QListWidget, "SingleSelection", None)
            if selection_mode is not None:
                self._list.setSelectionMode(selection_mode)
            layout.addWidget(self._list)

            button_row = QHBoxLayout()
            layout.addLayout(button_row)

            self._create_button = QPushButton("Create backup", self)
            self._create_button.clicked.connect(self._create_backup)
            button_row.addWidget(self._create_button)

            self._restore_button = QPushButton("Restore…", self)
            self._restore_button.clicked.connect(self._restore_selected)
            button_row.addWidget(self._restore_button)

            self._inspect_button = QPushButton("Inspect manifest", self)
            self._inspect_button.clicked.connect(self._inspect_selected)
            button_row.addWidget(self._inspect_button)

            self._refresh_button = QPushButton("Refresh", self)
            self._refresh_button.clicked.connect(self.refresh)
            button_row.addWidget(self._refresh_button)

            self.refresh()

        # ------------------------------------------------------------ utilities
        def _selected_archive(self) -> Path | None:
            item = self._list.currentItem()
            if item is None:
                return None
            data = item.data(_QT_USER_ROLE)
            if not data:
                return None
            return Path(str(data))

        def _show_error(self, message: str) -> None:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Backup manager")
            if _QMB_CRITICAL is not None:
                dlg.setIcon(_QMB_CRITICAL)
            dlg.setText(message)
            dlg.exec()

        def refresh(self) -> None:
            self._list.clear()
            archives = self._service.list_archives()
            if not archives:
                QListWidgetItem("No backups found.", self._list)
                return

            for archive in archives:
                text = archive.name
                tooltip = archive.as_posix()
                try:
                    manifest = self._service.inspect_backup(archive)
                    created = manifest.get("created_at", "unknown")
                    text = f"{archive.name} — {created}"
                    tooltip = json.dumps(manifest, indent=2, ensure_ascii=False)
                except Exception as exc:  # pragma: no cover - manifest missing
                    self._logger.warning(
                        "backup_manifest_missing",
                        archive=str(archive),
                        error=str(exc),
                    )
                item = QListWidgetItem(text, self._list)
                item.setData(_QT_USER_ROLE, archive.as_posix())
                item.setToolTip(tooltip)

        # -------------------------------------------------------------- handlers
        def _create_backup(self) -> None:
            try:
                report = self._service.create_backup()
            except Exception as exc:  # pragma: no cover - filesystem errors are rare
                self._logger.error("backup_create_failed", error=str(exc))
                self._show_error(f"Failed to create backup: {exc}")
                return

            self._logger.info("backup_created_gui", archive=str(report.archive_path))
            self.refresh()
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Backup created")
            dlg.setText(f"Archive stored at:\n{report.archive_path}")
            if _QMB_INFORMATION is not None:
                dlg.setIcon(_QMB_INFORMATION)
            dlg.exec()

        def _restore_selected(self) -> None:
            archive = self._selected_archive()
            if archive is None:
                self._show_error("Select a backup before restoring.")
                return

            target_dir = QFileDialog.getExistingDirectory(
                self,
                "Select restore destination",
                str(self._service.root),
            )
            if not target_dir:
                return

            try:
                report = self._service.restore_backup(
                    archive,
                    target_root=Path(target_dir),
                )
            except Exception as exc:  # pragma: no cover - filesystem errors are rare
                self._logger.error("backup_restore_failed", error=str(exc))
                self._show_error(f"Failed to restore backup: {exc}")
                return

            message = [f"Restored {len(report.restored)} files."]
            if report.skipped:
                skipped_paths = "\n".join(str(path) for path in report.skipped)
                message.append(f"Skipped existing files:\n{skipped_paths}")
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Restore complete")
            dlg.setText("\n\n".join(message))
            if _QMB_INFORMATION is not None:
                dlg.setIcon(_QMB_INFORMATION)
            dlg.exec()

        def _inspect_selected(self) -> None:
            archive = self._selected_archive()
            if archive is None:
                self._show_error("Select a backup to inspect.")
                return

            try:
                manifest = self._service.inspect_backup(archive)
            except Exception as exc:  # pragma: no cover - manifest missing
                self._logger.error("backup_inspect_failed", error=str(exc))
                self._show_error(f"Unable to load manifest: {exc}")
                return

            dlg = QMessageBox(self)
            dlg.setWindowTitle("Backup manifest")
            dlg.setText(json.dumps(manifest, indent=2, ensure_ascii=False))
            if _QMB_INFORMATION is not None:
                dlg.setIcon(_QMB_INFORMATION)
            dlg.exec()

    def run(argv: Sequence[str] | None = None) -> int:
        args = _parse_args(argv)
        service = BackupService(root=args.root, backup_dir=args.backup_dir)

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        window = BackupWindow(service)
        window.resize(640, 480)
        window.show()
        LOGGER.info(
            "backup_gui_started",
            root=str(service.root),
            backup_dir=str(service.backup_dir),
        )
        return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run())
