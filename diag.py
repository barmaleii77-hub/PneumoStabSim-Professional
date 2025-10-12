import sys
import os

print("🚀 PNEUMOSTABSIM DIAGNOSTIC")
print("=" * 40)
print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
print(f"Platform: {sys.platform}")
print(f"Directory: {os.getcwd()}")

try:
    import PySide6
    print("✅ PySide6: OK")
except ImportError:
    print("❌ PySide6: FAILED")

try:
    from src.common import init_logging
    print("✅ src.common: OK")
except ImportError:
    print("❌ src.common: FAILED")

print("=" * 40)
print("Файлы проекта:")
files = ["app.py", "src/common.py", "src/ui/main_window.py"]
for f in files:
    if os.path.exists(f):
        print(f"✅ {f}")
    else:
        print(f"❌ {f}")

print("=" * 40)
