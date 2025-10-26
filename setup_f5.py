#!/usr/bin/env python3
"""
F5 IDE Setup - Настройка F5 запуска для всех популярных IDE
"""

import json
from pathlib import Path


class F5SetupManager:
    """Менеджер настройки F5 для различных IDE"""

    def __init__(self):
        self.project_root = Path(__file__).parent

    def setup_all_ides(self):
        """Настройка всех поддерживаемых IDE"""
        print("🔧 Настройка F5 запуска для всех IDE...")

        results = {
            "VS Code": self.setup_vscode(),
            "Visual Studio": self.setup_visual_studio(),
            "PyCharm": self.setup_pycharm(),
            "Sublime Text": self.setup_sublime(),
            "Atom": self.setup_atom(),
        }

        print("\n📋 Результаты настройки:")
        for ide, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {ide}")

        return results

    def setup_vscode(self):
        """Настройка VS Code (уже выполнено)"""
        vscode_dir = self.project_root / ".vscode"
        launch_file = vscode_dir / "launch.json"
        return launch_file.exists()

    def setup_visual_studio(self):
        """Настройка Visual Studio (уже выполнено)"""
        pyproj_file = self.project_root / "PneumoStabSim.pyproj"
        sln_file = self.project_root / "PneumoStabSim.sln"
        return pyproj_file.exists() and sln_file.exists()

    def setup_pycharm(self):
        """Настройка PyCharm"""
        idea_dir = self.project_root / ".idea"
        runconf_dir = idea_dir / "runConfigurations"

        if not runconf_dir.exists():
            runconf_dir.mkdir(parents=True, exist_ok=True)

        # Создать workspace.xml для PyCharm
        workspace_content = """<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="RunManager" selected="Python.🚀 PneumoStabSim">
    <list>
      <item itemvalue="Python.🚀 PneumoStabSim" />
      <item itemvalue="Python.🐛 PneumoStabSim (Debug)" />
      <item itemvalue="Python.🛡️ PneumoStabSim (Safe Mode)" />
      <item itemvalue="Python.⚡ PneumoStabSim (Performance)" />
    </list>
  </component>
</project>"""

        workspace_file = idea_dir / "workspace.xml"
        try:
            workspace_file.write_text(workspace_content, encoding="utf-8")
            return True
        except Exception:
            return False

    def setup_sublime(self):
        """Настройка Sublime Text"""
        sublime_config = {
            "build_systems": [
                {
                    "name": "PneumoStabSim - Run",
                    "cmd": ["python", "app.py"],
                    "working_dir": "${project_path}",
                    "env": {"PYTHONPATH": "${project_path};${project_path}/src"},
                    "variants": [
                        {"name": "Debug Mode", "cmd": ["python", "app.py", "--debug"]},
                        {
                            "name": "Safe Mode",
                            "cmd": ["python", "app.py", "--safe-mode"],
                        },
                    ],
                }
            ]
        }

        # Создать .sublime-project файл
        sublime_project = {
            "folders": [
                {
                    "path": ".",
                    "folder_exclude_patterns": [
                        "venv",
                        ".venv",
                        "__pycache__",
                        ".git",
                        "logs",
                        "build",
                        "dist",
                        ".pytest_cache",
                    ],
                }
            ],
            "settings": {"python_interpreter": "./venv/Scripts/python.exe"},
            "build_systems": sublime_config["build_systems"],
        }

        try:
            project_file = self.project_root / "PneumoStabSim.sublime-project"
            project_file.write_text(
                json.dumps(sublime_project, indent=2), encoding="utf-8"
            )
            return True
        except Exception:
            return False

    def setup_atom(self):
        """Настройка Atom (через package script-runner)"""
        # Создание script-runner конфигурации для Atom
        atom_config = {
            "python": {
                "command": "python",
                "args": ["{FILE_ACTIVE}"],
                "cwd": "{PROJECT_PATH}",
                "env": {"PYTHONPATH": "{PROJECT_PATH};{PROJECT_PATH}/src"},
            }
        }

        try:
            # Atom использует .atom-build.json для конфигурации
            atom_file = self.project_root / ".atom-build.json"
            atom_build = {
                "cmd": "python",
                "args": ["app.py"],
                "cwd": "{PROJECT_PATH}",
                "env": {"PYTHONPATH": "{PROJECT_PATH};{PROJECT_PATH}/src"},
                "targets": {
                    "Debug Mode": {"cmd": "python", "args": ["app.py", "--debug"]},
                    "Safe Mode": {"cmd": "python", "args": ["app.py", "--safe-mode"]},
                },
            }

            atom_file.write_text(json.dumps(atom_build, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False

    def create_universal_launcher(self):
        """Создание универсального launcher скрипта"""
        launcher_content = '''#!/usr/bin/env python3
"""Universal F5 Launcher - работает из любой IDE"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import and run the F5 launcher
from f5_launch import F5LaunchConfig

if __name__ == "__main__":
    launcher = F5LaunchConfig()

    # Determine launch mode from arguments
    if "--debug" in sys.argv:
        launcher.launch_debug_mode()
    elif "--safe-mode" in sys.argv:
        launcher.launch_normal_mode()  # Safe mode is normal mode with --safe-mode
    else:
        launcher.launch_normal_mode()
'''

        try:
            universal_file = self.project_root / "universal_f5.py"
            universal_file.write_text(launcher_content, encoding="utf-8")
            print(f"✅ Создан универсальный launcher: {universal_file}")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания универсального launcher: {e}")
            return False

    def print_f5_instructions(self):
        """Печать инструкций по использованию F5 в разных IDE"""
        instructions = """
🎯 ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ F5 В РАЗНЫХ IDE

📝 Visual Studio 2022:
   1. Откройте PneumoStabSim.sln
   2. Нажмите F5 для запуска с отладкой
   3. Ctrl+F5 для запуска без отладки

📝 VS Code:
   1. Откройте папку проекта
   2. Нажмите F5 или Ctrl+F5
   3. Выберите конфигурацию из выпадающего меню

📝 PyCharm:
   1. Откройте папку как проект
   2. Нажмите Shift+F10 или F5
   3. Конфигурации будут автоматически обнаружены

📝 Sublime Text:
   1. Откройте PneumoStabSim.sublime-project
   2. Нажмите Ctrl+B для сборки
   3. Выберите вариант из меню

📝 Любая IDE:
   1. Запустите: python universal_f5.py
   2. Или: python f5_launch.py
   3. Или: F5_Launch.bat (Windows)

🚀 БЫСТРЫЕ КОМАНДЫ:
   • python f5_launch.py          - Обычный запуск
   • python f5_launch.py --debug  - Отладочный режим
   • F5_Launch.bat               - Windows ярлык
   • F5_Launch.bat debug         - Windows ярлык (отладка)

⚙️ ГОРЯЧИЕ КЛАВИШИ:
   • F5         - Запуск с отладкой
   • Ctrl+F5    - Запуск без отладки
   • Shift+F5   - Остановка отладки
   • F9         - Точка останова
   • F10        - Пошаговое выполнение
   • F11        - Заход в функцию
"""
        print(instructions)


def main():
    """Основная функция настройки"""
    print("🔧 F5 IDE Setup Manager")
    print("=" * 40)

    manager = F5SetupManager()

    # Настройка всех IDE
    results = manager.setup_all_ides()

    # Создание универсального launcher
    manager.create_universal_launcher()

    # Вывод инструкций
    manager.print_f5_instructions()

    print("\n" + "=" * 40)
    print("✅ F5 настройка завершена!")
    print("🚀 Теперь можете использовать F5 в любой IDE!")


if __name__ == "__main__":
    main()
