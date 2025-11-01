import logging
from pathlib import Path

from src.ui.main_window_pkg._hdr_paths import normalise_hdr_path


def test_normalise_hdr_path_resolves_assets_hdr(tmp_path: Path) -> None:
    project_root = tmp_path
    qml_dir = project_root / "assets" / "qml"
    hdr_dir = project_root / "assets" / "hdr"
    qml_dir.mkdir(parents=True)
    hdr_dir.mkdir(parents=True)

    hdr_file = hdr_dir / "placeholder_env.hdr"
    hdr_file.write_text("placeholder", encoding="utf-8")

    result = normalise_hdr_path(
        "placeholder_env.hdr",
        qml_base_dir=qml_dir,
        project_root=project_root,
        logger=logging.getLogger("test"),
    )

    assert result == hdr_file.resolve().as_uri()
