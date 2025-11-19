import os
import sys
from pathlib import Path


def test_launcher_script_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    launcher = root / "scripts" / "interactive_launcher.py"
    assert launcher.exists(), "interactive_launcher.py должен существовать"


def test_launcher_env_prep_import() -> None:
    # smoke: ensure module imports without executing GUI
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import scripts.interactive_launcher as L  # type: ignore

    env = os.environ.copy()
    L.ensure_qt_environment(env)
    assert "QT_QUICK_CONTROLS_STYLE" in env
    assert "PSS_QML_SCENE" in env
