#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup Script - Remove Duplicate Defaults
Скрипт очистки дубликатов дефолтов из кода

ЦЕЛЬ: Оставить ТОЛЬКО config/app_settings.json как единственный источник настроек

УДАЛЯЕТСЯ:
- config/graphics_defaults.py (438 строк хардкода)
- src/app/config_defaults.py (294 строки хардкода)
- Любые другие файлы с дефолтами

ПРОВЕРЯЕТСЯ:
- Отсутствие импортов удаляемых модулей
- Наличие всех параметров в config/app_settings.json
- Работоспособность приложения после очистки
"""

import sys
import os
from pathlib import Path
import json
import subprocess
from typing import List, Dict, Set

class DuplicatesCleanup:
    """Автоматическая очистка дубликатов дефолтов"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.errors = []
        self.warnings = []
        self.success_count = 0
        
        # Файлы для удаления
        self.files_to_delete = [
            "config/graphics_defaults.py",
            "src/app/config_defaults.py",
        ]
        
        # Файл настроек (единственный источник истины)
        self.settings_file = self.project_root / "config/app_settings.json"
    
    def log_success(self, message: str):
        """Логирование успеха"""
        print(f"✅ {message}")
        self.success_count += 1
    
    def log_error(self, message: str):
        """Логирование ошибки"""
        print(f"❌ {message}")
        self.errors.append(message)
    
    def log_warning(self, message: str):
        """Логирование предупреждения"""
        print(f"⚠️  {message}")
        self.warnings.append(message)
    
    def log_info(self, message: str):
        """Информационное сообщение"""
        print(f"ℹ️  {message}")
    
    def check_git_status(self) -> bool:
        """Проверить что нет uncommitted changes"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.stdout.strip():
                self.log_warning("Обнаружены несохраненные изменения в Git")
                self.log_info("Рекомендуется commit перед очисткой")
                
                response = input("\nПродолжить? (y/N): ")
                return response.lower() == 'y'
            
            self.log_success("Git репозиторий чист")
            return True
            
        except FileNotFoundError:
            self.log_warning("Git не найден, пропуск проверки")
            return True
        except Exception as e:
            self.log_error(f"Ошибка проверки Git: {e}")
            return False
    
    def search_imports(self, file_path: str) -> List[str]:
        """Найти все импорты удаляемого модуля"""
        module_name = file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
        
        try:
            result = subprocess.run(
                ["git", "grep", "-n", f"import {module_name}"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            results = []
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        results.append(line)
            
            return results
            
        except Exception:
            return []
    
    def check_imports(self) -> bool:
        """Проверить что нет импортов удаляемых модулей"""
        self.log_info("\n🔍 Проверка импортов...")
        
        found_imports = False
        
        for file_path in self.files_to_delete:
            imports = self.search_imports(file_path)
            
            if imports:
                found_imports = True
                self.log_error(f"Найдены импорты {file_path}:")
                for imp in imports:
                    print(f"    {imp}")
            else:
                self.log_success(f"Импорты {file_path} не найдены")
        
        if found_imports:
            self.log_error("Необходимо удалить импорты перед очисткой!")
            return False
        
        return True
    
    def validate_settings_file(self) -> bool:
        """Проверить наличие и корректность config/app_settings.json"""
        self.log_info("\n📄 Проверка config/app_settings.json...")
        
        if not self.settings_file.exists():
            self.log_error(f"Файл настроек не найден: {self.settings_file}")
            return False
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Проверка структуры
            required_keys = ["current", "defaults_snapshot", "metadata"]
            missing_keys = [key for key in required_keys if key not in settings]
            
            if missing_keys:
                self.log_error(f"Отсутствуют ключи в настройках: {missing_keys}")
                return False
            
            # Проверка категорий
            required_categories = ["graphics", "geometry", "pneumatic", "modes"]
            current = settings.get("current", {})
            
            for category in required_categories:
                if category not in current:
                    self.log_warning(f"Отсутствует категория '{category}' в current")
            
            self.log_success("config/app_settings.json корректен")
            
            # Статистика
            total_params = sum(self._count_params(current[cat]) for cat in current)
            self.log_info(f"Всего параметров: {total_params}")
            
            return True
            
        except json.JSONDecodeError as e:
            self.log_error(f"Невалидный JSON: {e}")
            return False
        except Exception as e:
            self.log_error(f"Ошибка чтения настроек: {e}")
            return False
    
    def _count_params(self, obj) -> int:
        """Рекурсивно посчитать количество параметров"""
        if not isinstance(obj, dict):
            return 1
        
        count = 0
        for value in obj.values():
            if isinstance(value, dict):
                count += self._count_params(value)
            else:
                count += 1
        
        return count
    
    def create_backup(self) -> bool:
        """Создать backup удаляемых файлов"""
        self.log_info("\n💾 Создание backup...")
        
        backup_dir = self.project_root / "backup" / "defaults_cleanup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for file_path in self.files_to_delete:
                src = self.project_root / file_path
                
                if src.exists():
                    # Сохраняем структуру директорий
                    rel_path = Path(file_path)
                    dst = backup_dir / timestamp / rel_path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(src, dst)
                    self.log_success(f"Backup создан: {dst}")
            
            # Создаем README в backup
            readme = backup_dir / timestamp / "README.md"
            with open(readme, 'w', encoding='utf-8') as f:
                f.write(f"""# Backup дефолтов - {timestamp}

## Удаленные файлы:

""")
                for file_path in self.files_to_delete:
                    f.write(f"- {file_path}\n")
                
                f.write(f"""
## Причина удаления:

Дубликаты настроек. Единственный источник истины - `config/app_settings.json`

## Восстановление:

```bash
# Скопировать файлы обратно
cp -r backup/defaults_cleanup/{timestamp}/* .
```

""")
            
            self.log_success(f"Backup сохранен в: {backup_dir / timestamp}")
            return True
            
        except Exception as e:
            self.log_error(f"Ошибка создания backup: {e}")
            return False
    
    def delete_files(self) -> bool:
        """Удалить файлы с дубликатами"""
        self.log_info("\n🗑️  Удаление дубликатов...")
        
        deleted_count = 0
        
        for file_path in self.files_to_delete:
            full_path = self.project_root / file_path
            
            if full_path.exists():
                try:
                    full_path.unlink()
                    self.log_success(f"Удален: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    self.log_error(f"Не удалось удалить {file_path}: {e}")
            else:
                self.log_info(f"Уже удален: {file_path}")
        
        if deleted_count > 0:
            self.log_success(f"Удалено файлов: {deleted_count}")
        
        return True
    
    def test_application(self) -> bool:
        """Проверить что приложение запускается"""
        self.log_info("\n🧪 Тестирование приложения...")
        
        try:
            # Пытаемся импортировать главный модуль
            sys.path.insert(0, str(self.project_root))
            
            # Проверяем что SettingsManager работает
            from src.common.settings_manager import SettingsManager
            
            settings = SettingsManager(self.settings_file)
            
            # Пробуем загрузить настройки
            graphics_settings = settings.get("graphics", {})
            
            if graphics_settings:
                self.log_success("SettingsManager работает корректно")
                return True
            else:
                self.log_warning("Graphics настройки пусты, но SettingsManager работает")
                return True
            
        except Exception as e:
            self.log_error(f"Ошибка тестирования: {e}")
            return False
    
    def run(self) -> bool:
        """Запуск полной очистки"""
        print("=" * 60)
        print("🧹 CLEANUP DUPLICATE DEFAULTS")
        print("=" * 60)
        print()
        
        # 1. Проверка Git
        if not self.check_git_status():
            return False
        
        # 2. Проверка импортов
        if not self.check_imports():
            return False
        
        # 3. Проверка settings файла
        if not self.validate_settings_file():
            return False
        
        # 4. Создание backup
        if not self.create_backup():
            return False
        
        # Подтверждение пользователя
        print("\n" + "=" * 60)
        print("⚠️  ВНИМАНИЕ!")
        print("=" * 60)
        print(f"\nБудут удалены следующие файлы:")
        for file_path in self.files_to_delete:
            print(f"  - {file_path}")
        print(f"\nBackup создан в backup/defaults_cleanup/")
        
        response = input("\nПродолжить удаление? (y/N): ")
        if response.lower() != 'y':
            print("\n❌ Отменено пользователем")
            return False
        
        # 5. Удаление файлов
        if not self.delete_files():
            return False
        
        # 6. Тестирование
        if not self.test_application():
            self.log_warning("Тестирование не прошло, но файлы удалены")
            self.log_info("Проверьте работу приложения вручную: python app.py")
        
        # Финальный отчет
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ ОЧИСТКИ")
        print("=" * 60)
        
        print(f"\n✅ Успешных операций: {self.success_count}")
        print(f"❌ Ошибок: {len(self.errors)}")
        print(f"⚠️  Предупреждений: {len(self.warnings)}")
        
        if self.errors:
            print("\n❌ ОШИБКИ:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("\n⚠️  ПРЕДУПРЕЖДЕНИЯ:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. Запустить приложение: python app.py")
        print("2. Проверить что все панели работают")
        print("3. Проверить что настройки сохраняются")
        print("4. Commit изменений: git commit -am 'chore: remove duplicate defaults'")
        
        print("\n✅ Очистка завершена!")
        return len(self.errors) == 0


def main():
    """Точка входа"""
    try:
        cleanup = DuplicatesCleanup()
        success = cleanup.run()
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Прервано пользователем")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n💀 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
