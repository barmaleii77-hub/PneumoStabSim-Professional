"""Анализатор размеров файлов MainWindow модуля"""

from pathlib import Path


def analyze_mainwindow_module():
    """Анализ размеров файлов MainWindow модуля"""

    base_dir = Path("src/ui/main_window")

    files = [
        "main_window_refactored.py",
        "ui_setup.py",
        "qml_bridge.py",
        "signals_router.py",
        "state_sync.py",
        "menu_actions.py",
        "__init__.py",
        "README.md",
    ]

    print("=" * 70)
    print("📊 MainWindow Module - File Sizes Analysis")
    print("=" * 70)

    total = 0
    for filename in files:
        filepath = base_dir / filename
        if filepath.exists():
            lines = len(filepath.read_text(encoding="utf-8").splitlines())
            total += lines
            print(f"{filename:45} {lines:5} lines")

    print("-" * 70)
    print(f"{'TOTAL (8 files)':45} {total:5} lines")
    print("=" * 70)
    print()

    # Compare with original
    original_file = Path("src/ui/main_window.py")
    if original_file.exists():
        orig_lines = len(original_file.read_text(encoding="utf-8").splitlines())
        print("Original file: src/ui/main_window.py")
        print(f"{'main_window.py (ORIGINAL)':45} {orig_lines:5} lines")
        print()

        coordinator_lines = len(
            (base_dir / "main_window_refactored.py")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        reduction = round((1 - coordinator_lines / orig_lines) * 100, 1)

        print(
            f"✅ Coordinator reduction: -{reduction}% ({orig_lines} → {coordinator_lines} lines)"
        )
        print(f"✅ Average module size: {total // len(files)} lines")
        print(f"✅ Total lines (including docs): {total} lines")
    print("=" * 70)


if __name__ == "__main__":
    analyze_mainwindow_module()
