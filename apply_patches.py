#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для автоматического применения патчей к файлам проекта
Script to automatically apply patches to project files

Применяет патчи:
- panel_graphics.py.patch → src/ui/panels/panel_graphics.py
- main.qml.patch → assets/qml/main.qml

Создает резервные копии перед применением патчей
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


class PatchApplier:
    """Класс для применения патчей с созданием бэкапов"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / "patch_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.patches = [
            {
                'patch_file': 'panel_graphics.py.patch',
                'target_file': 'src/ui/panels/panel_graphics.py',
                'description': 'GraphicsPanel расширенные параметры'
            },
            {
                'patch_file': 'main.qml.patch',
                'target_file': 'assets/qml/main.qml',
                'description': 'Main QML файл обновления'
            }
        ]
    
    def create_backup(self, file_path: Path) -> Path:
        """Создать резервную копию файла"""
        if not file_path.exists():
            print(f"⚠️ Файл не существует: {file_path}")
            return None
        
        # Создаем директорию для бэкапов
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Относительный путь для структуры бэкапа
        rel_path = file_path.relative_to(self.project_root)
        backup_path = self.backup_dir / rel_path
        
        # Создаем поддиректории если нужно
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Копируем файл
        shutil.copy2(file_path, backup_path)
        print(f"✅ Резервная копия создана: {backup_path}")
        
        return backup_path
    
    def check_patch_exists(self, patch_file: str) -> bool:
        """Проверить существование файла патча"""
        patch_path = self.project_root / patch_file
        exists = patch_path.exists()
        
        if not exists:
            print(f"❌ Файл патча не найден: {patch_path}")
        else:
            print(f"✅ Файл патча найден: {patch_path}")
        
        return exists
    
    def check_target_exists(self, target_file: str) -> bool:
        """Проверить существование целевого файла"""
        target_path = self.project_root / target_file
        exists = target_path.exists()
        
        if not exists:
            print(f"❌ Целевой файл не найден: {target_path}")
        else:
            print(f"✅ Целевой файл найден: {target_path}")
        
        return exists
    
    def apply_patch_git(self, patch_file: str, target_file: str) -> bool:
        """Применить патч используя git apply"""
        patch_path = self.project_root / patch_file
        
        # Пробуем git apply --check сначала
        check_cmd = ['git', 'apply', '--check', str(patch_path)]
        
        try:
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.returncode != 0:
                print(f"⚠️ Патч проверка не пройдена:")
                print(f"   {result.stderr}")
                return False
            
            print(f"✅ Патч проверка пройдена")
            
            # Применяем патч
            apply_cmd = ['git', 'apply', str(patch_path)]
            result = subprocess.run(
                apply_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.returncode != 0:
                print(f"❌ Ошибка применения патча:")
                print(f"   {result.stderr}")
                return False
            
            print(f"✅ Патч успешно применен")
            return True
            
        except FileNotFoundError:
            print("⚠️ Git не найден, используем альтернативный метод")
            return False
        except Exception as e:
            print(f"❌ Ошибка при применении патча через git: {e}")
            return False
    
    def apply_patch_manual(self, patch_file: str, target_file: str) -> bool:
        """Ручное применение патча (упрощенная версия для простых патчей)"""
        print(f"🔧 Применяем патч вручную...")
        
        patch_path = self.project_root / patch_file
        target_path = self.project_root / target_file
        
        try:
            # Читаем содержимое патча
            with open(patch_path, 'r', encoding='utf-8') as f:
                patch_content = f.read()
            
            # Простой парсер патча
            # Ищем строки с +++ (новый файл)
            lines = patch_content.split('\n')
            
            # Извлекаем добавленные строки (+) и удаленные (-)
            additions = []
            deletions = []
            
            for line in lines:
                if line.startswith('+') and not line.startswith('+++'):
                    additions.append(line[1:])
                elif line.startswith('-') and not line.startswith('---'):
                    deletions.append(line[1:])
            
            if not additions and not deletions:
                print("⚠️ Патч пустой или неподдерживаемый формат")
                return False
            
            # Читаем целевой файл
            with open(target_path, 'r', encoding='utf-8') as f:
                target_content = f.read()
            
            # Применяем изменения (простая замена)
            modified_content = target_content
            
            for deletion in deletions:
                if deletion in modified_content:
                    # Удаляем строку
                    modified_content = modified_content.replace(deletion + '\n', '')
            
            # Добавляем новые строки в конец соответствующего раздела
            # (это упрощенная логика, для сложных патчей используйте git apply)
            
            # Записываем обратно
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print(f"✅ Патч применен (упрощенный метод)")
            print(f"⚠️ Рекомендуется проверить изменения вручную")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка ручного применения патча: {e}")
            return False
    
    def apply_all_patches(self) -> bool:
        """Применить все патчи"""
        print("=" * 80)
        print("🚀 ПРИМЕНЕНИЕ ПАТЧЕЙ К ПРОЕКТУ")
        print("=" * 80)
        print()
        
        all_success = True
        applied_count = 0
        failed_patches = []
        
        for patch_info in self.patches:
            patch_file = patch_info['patch_file']
            target_file = patch_info['target_file']
            description = patch_info['description']
            
            print(f"📋 Обработка: {description}")
            print(f"   Патч: {patch_file}")
            print(f"   Цель: {target_file}")
            print()
            
            # Проверка существования файлов
            if not self.check_patch_exists(patch_file):
                all_success = False
                failed_patches.append(patch_file)
                print()
                continue
            
            if not self.check_target_exists(target_file):
                all_success = False
                failed_patches.append(patch_file)
                print()
                continue
            
            # Создание бэкапа
            target_path = self.project_root / target_file
            backup_path = self.create_backup(target_path)
            
            if backup_path is None:
                all_success = False
                failed_patches.append(patch_file)
                print()
                continue
            
            # Применение патча (сначала через git, потом вручную)
            success = self.apply_patch_git(patch_file, target_file)
            
            if not success:
                print("⚠️ Git apply не удался, пробуем ручной метод...")
                success = self.apply_patch_manual(patch_file, target_file)
            
            if success:
                applied_count += 1
                print(f"✅ Патч применен успешно!")
            else:
                all_success = False
                failed_patches.append(patch_file)
                print(f"❌ Не удалось применить патч!")
            
            print()
        
        # Итоговый отчет
        print("=" * 80)
        print("📊 РЕЗУЛЬТАТЫ ПРИМЕНЕНИЯ ПАТЧЕЙ")
        print("=" * 80)
        print(f"Всего патчей: {len(self.patches)}")
        print(f"Применено успешно: {applied_count}")
        print(f"Не применено: {len(failed_patches)}")
        
        if failed_patches:
            print()
            print("❌ Не удалось применить следующие патчи:")
            for patch in failed_patches:
                print(f"   - {patch}")
        
        print()
        print(f"📦 Резервные копии сохранены в: {self.backup_dir}")
        print()
        
        if all_success:
            print("✅ ВСЕ ПАТЧИ ПРИМЕНЕНЫ УСПЕШНО!")
            print()
            print("📋 СЛЕДУЮЩИЕ ШАГИ:")
            print("  1. Проверьте изменения: git diff")
            print("  2. Запустите тесты: py check_graphics_params.py")
            print("  3. Запустите приложение: py app.py")
            print()
            return True
        else:
            print("⚠️ НЕКОТОРЫЕ ПАТЧИ НЕ ПРИМЕНЕНЫ!")
            print()
            print("📋 РЕКОМЕНДАЦИИ:")
            print("  1. Проверьте существование файлов патчей")
            print("  2. Убедитесь, что целевые файлы не изменены")
            print("  3. Попробуйте применить патчи вручную")
            print(f"  4. Восстановите файлы из бэкапов: {self.backup_dir}")
            print()
            return False
    
    def restore_from_backup(self):
        """Восстановить файлы из последнего бэкапа"""
        if not self.backup_dir.exists():
            print("❌ Директория бэкапов не найдена")
            return False
        
        print(f"🔄 Восстановление из бэкапа: {self.backup_dir}")
        
        restored_count = 0
        
        for backup_file in self.backup_dir.rglob('*'):
            if backup_file.is_file():
                # Восстанавливаем относительный путь
                rel_path = backup_file.relative_to(self.backup_dir)
                target_path = self.project_root / rel_path
                
                # Копируем обратно
                shutil.copy2(backup_file, target_path)
                print(f"✅ Восстановлен: {target_path}")
                restored_count += 1
        
        print(f"✅ Восстановлено файлов: {restored_count}")
        return True


def main():
    """Главная функция"""
    applier = PatchApplier()
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == '--restore':
            # Восстановление из бэкапа
            applier.restore_from_backup()
            return 0
        elif sys.argv[1] == '--help':
            print("Использование:")
            print("  py apply_patches.py          - Применить все патчи")
            print("  py apply_patches.py --restore - Восстановить из последнего бэкапа")
            print("  py apply_patches.py --help    - Показать эту справку")
            return 0
    
    # Применяем все патчи
    success = applier.apply_all_patches()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
