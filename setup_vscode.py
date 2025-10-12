#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code Setup Automation для PneumoStabSim Professional
Автоматическая настройка профессиональной среды разработки
"""

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import time

class VSCodeSetup:
    """Автоматизированная настройка VS Code для PneumoStabSim"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.vscode_dir = self.project_root / '.vscode'
        self.success_count = 0
        self.error_count = 0
        self.warnings = []
        
    def log_success(self, message: str):
        """Логирование успешных операций"""
        print(f"✅ {message}")
        self.success_count += 1
    
    def log_error(self, message: str):
        """Логирование ошибок"""
        print(f"❌ {message}")
        self.error_count += 1
    
    def log_warning(self, message: str):
        """Логирование предупреждений"""
        print(f"⚠️ {message}")
        self.warnings.append(message)
    
    def log_info(self, message: str):
        """Информационные сообщения"""
        print(f"ℹ️ {message}")
    
    def ensure_vscode_directory(self) -> bool:
        """Создание директории .vscode если не существует"""
        try:
            self.vscode_dir.mkdir(exist_ok=True)
            self.log_success("Директория .vscode готова")
            return True
        except Exception as e:
            self.log_error(f"Не удалось создать .vscode: {e}")
            return False
    
    def check_python_setup(self) -> bool:
        """Проверка настройки Python"""
        try:
            # Проверяем Python
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.log_success(f"Python настроен: {version}")
                return True
            else:
                self.log_error("Python не найден в системе")
                return False
        except Exception as e:
            self.log_error(f"Ошибка проверки Python: {e}")
            return False
    
    def check_required_packages(self) -> bool:
        """Проверка необходимых пакетов Python"""
        required_packages = ['PySide6', 'numpy', 'scipy', 'pytest']
        missing_packages = []
        
        for package in required_packages:
            try:
                result = subprocess.run([
                    sys.executable, '-c', f'import {package.lower()}'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_success(f"Пакет {package} установлен")
                else:
                    missing_packages.append(package)
                    self.log_error(f"Пакет {package} не найден")
            except Exception:
                missing_packages.append(package)
                self.log_error(f"Ошибка проверки пакета {package}")
        
        if missing_packages:
            self.log_warning(f"Отсутствующие пакеты: {', '.join(missing_packages)}")
            self.log_info("Запустите: pip install -r requirements.txt")
            return False
        
        return True
    
    def check_vscode_executable(self) -> Optional[str]:
        """Поиск исполняемого файла VS Code"""
        possible_paths = [
            "code",  # В PATH
            r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(os.getenv('USERNAME', '')),
            r"C:\Program Files\Microsoft VS Code\Code.exe",
            r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
            "/usr/bin/code",
            "/snap/bin/code",
            "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log_success(f"VS Code найден: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                continue
        
        self.log_warning("VS Code не найден автоматически")
        return None
    
    def install_extensions(self, code_path: str) -> bool:
        """Установка рекомендуемых расширений"""
        extensions = [
            "ms-python.python",
            "ms-python.debugpy", 
            "ms-python.black-formatter",
            "ms-python.flake8",
            "ms-python.isort",
            "formulahendry.code-runner",
            "ms-vscode.vscode-json",
            "redhat.vscode-yaml",
            "eamodio.gitlens",
            "PKief.material-icon-theme"
        ]
        
        self.log_info(f"Установка {len(extensions)} расширений VS Code...")
        
        installed_count = 0
        for extension in extensions:
            try:
                result = subprocess.run([
                    code_path, '--install-extension', extension, '--force'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    self.log_success(f"Установлено: {extension}")
                    installed_count += 1
                else:
                    self.log_warning(f"Не удалось установить: {extension}")
            except subprocess.TimeoutExpired:
                self.log_warning(f"Таймаут установки: {extension}")
            except Exception as e:
                self.log_warning(f"Ошибка установки {extension}: {e}")
        
        self.log_info(f"Установлено {installed_count}/{len(extensions)} расширений")
        return installed_count > 0
    
    def validate_configurations(self) -> bool:
        """Проверка существующих конфигураций"""
        config_files = {
            'settings.json': 'Основные настройки',
            'launch.json': 'Конфигурация отладки',
            'tasks.json': 'Настройка задач',
            'extensions.json': 'Рекомендуемые расширения'
        }
        
        all_valid = True
        
        for filename, description in config_files.items():
            file_path = self.vscode_dir / filename
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)  # Проверка валидности JSON
                    self.log_success(f"{description}: {filename} ✓")
                except json.JSONDecodeError as e:
                    self.log_error(f"Невалидный JSON в {filename}: {e}")
                    all_valid = False
                except Exception as e:
                    self.log_error(f"Ошибка чтения {filename}: {e}")
                    all_valid = False
            else:
                self.log_warning(f"Отсутствует: {filename}")
                all_valid = False
        
        return all_valid
    
    def create_workspace_file(self) -> bool:
        """Создание файла workspace для VS Code"""
        workspace_config = {
            "folders": [
                {
                    "name": "PneumoStabSim-Professional",
                    "path": "."
                }
            ],
            "settings": {
                "python.defaultInterpreterPath": "py",
                "python.terminal.activateEnvironment": True,
                "files.autoSave": "afterDelay",
                "editor.formatOnSave": True
            },
            "extensions": {
                "recommendations": [
                    "ms-python.python",
                    "ms-python.debugpy",
                    "ms-python.black-formatter",
                    "formulahendry.code-runner"
                ]
            }
        }
        
        workspace_file = self.project_root / 'PneumoStabSim.code-workspace'
        
        try:
            with open(workspace_file, 'w', encoding='utf-8') as f:
                json.dump(workspace_config, f, indent=4, ensure_ascii=False)
            
            self.log_success(f"Создан workspace файл: {workspace_file}")
            return True
        except Exception as e:
            self.log_error(f"Не удалось создать workspace файл: {e}")
            return False
    
    def setup_python_path(self) -> bool:
        """Настройка PYTHONPATH в .env файле"""
        env_file = self.project_root / '.env'
        
        env_content = f"""# PneumoStabSim Professional Environment
PYTHONPATH={self.project_root};{self.project_root}/src
PYTHONIOENCODING=utf-8

# Qt Configuration  
QSG_RHI_BACKEND=d3d11
QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true

# Development Mode
DEVELOPMENT=true
DEBUG=false
"""
        
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            self.log_success(f"Создан .env файл: {env_file}")
            return True
        except Exception as e:
            self.log_error(f"Не удалось создать .env файл: {e}")
            return False
    
    def create_batch_scripts(self) -> bool:
        """Создание batch скриптов для быстрого запуска"""
        
        scripts = {
            'run_app.bat': '@echo off\npy app.py\npause',
            'run_debug.bat': '@echo off\npy app.py --debug\npause',  
            'run_tests.bat': '@echo off\npy -m pytest tests/ -v\npause',
            'setup_env.bat': '@echo off\npy -m pip install -r requirements.txt --upgrade\npause',
            'open_vscode.bat': '@echo off\ncode .\npause'
        }
        
        created_count = 0
        for filename, content in scripts.items():
            script_path = self.project_root / filename
            
            try:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log_success(f"Создан скрипт: {filename}")
                created_count += 1
            except Exception as e:
                self.log_error(f"Не удалось создать {filename}: {e}")
        
        return created_count > 0
    
    def run_comprehensive_setup(self) -> bool:
        """Запуск полной настройки VS Code"""
        
        print("=" * 60)
        print("🚀 VS CODE SETUP - PneumoStabSim Professional")  
        print("=" * 60)
        print()
        
        # 1. Проверка базовых требований
        print("📋 Шаг 1: Проверка системы...")
        if not self.check_python_setup():
            return False
        
        if not self.ensure_vscode_directory():
            return False
        
        # 2. Проверка пакетов Python
        print("\n🐍 Шаг 2: Проверка пакетов Python...")
        if not self.check_required_packages():
            self.log_warning("Некоторые пакеты отсутствуют, но продолжаем...")
        
        # 3. Поиск VS Code
        print("\n🔍 Шаг 3: Поиск VS Code...")
        code_path = self.check_vscode_executable()
        
        # 4. Установка расширений
        if code_path:
            print("\n📦 Шаг 4: Установка расширений VS Code...")
            self.install_extensions(code_path)
        else:
            self.log_warning("Пропуск установки расширений (VS Code не найден)")
        
        # 5. Проверка конфигураций
        print("\n⚙️ Шаг 5: Проверка конфигураций...")
        self.validate_configurations()
        
        # 6. Создание дополнительных файлов  
        print("\n📄 Шаг 6: Создание дополнительных файлов...")
        self.create_workspace_file()
        self.setup_python_path()
        
        # 7. Batch скрипты (только для Windows)
        if sys.platform == 'win32':
            print("\n📜 Шаг 7: Создание batch скриптов...")
            self.create_batch_scripts()
        
        # Финальный отчет
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ НАСТРОЙКИ")
        print("=" * 60)
        
        print(f"✅ Успешных операций: {self.success_count}")
        print(f"❌ Ошибок: {self.error_count}")
        print(f"⚠️ Предупреждений: {len(self.warnings)}")
        
        if self.warnings:
            print("\nПредупреждения:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        print("\n🎯 РЕКОМЕНДАЦИИ:")
        print("1. Откройте проект в VS Code: code .")
        print("2. Выберите интерпретатор Python: Ctrl+Shift+P → Python: Select Interpreter")
        print("3. Запустите тесты: Ctrl+Shift+P → Python: Run All Tests")
        print("4. Запустите приложение: F5 или Ctrl+F5")
        
        if code_path:
            print(f"\n🚀 Автоматический запуск VS Code...")
            try:
                subprocess.Popen([code_path, str(self.project_root)])
                self.log_success("VS Code запущен!")
            except Exception as e:
                self.log_error(f"Не удалось запустить VS Code: {e}")
        
        print("\n✅ Настройка VS Code завершена!")
        return self.error_count == 0

def main():
    """Основная функция"""
    try:
        setup = VSCodeSetup()
        success = setup.run_comprehensive_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Настройка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💀 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
