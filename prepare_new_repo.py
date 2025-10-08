#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания нового GitHub репозитория PneumoStabSim
Автоматическая подготовка проекта к миграции
"""
import subprocess
import sys
import os
import json
from pathlib import Path


def run_git_command(command):
    """Выполнить git команду и вернуть результат"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)


def check_git_status():
    """Проверить состояние git репозитория"""
    print("🔍 Проверяем состояние Git репозитория...")
    
    success, output = run_git_command("git status --porcelain")
    if success:
        if output:
            print(f"⚠️ Есть незафиксированные изменения:")
            print(output)
            return False
        else:
            print("✅ Рабочая директория чистая")
            return True
    else:
        print(f"❌ Ошибка проверки git статуса: {output}")
        return False


def count_project_files():
    """Подсчитать файлы проекта"""
    print("\n📊 Анализируем структуру проекта...")
    
    important_dirs = ['src', 'assets', 'tests', 'docs', 'config', 'tools', 'reports']
    important_files = ['app.py', 'requirements.txt', 'pyproject.toml', 'README.md', 'launch.py']
    
    total_files = 0
    structure = {}
    
    for item in important_dirs:
        if os.path.exists(item):
            count = sum(1 for _ in Path(item).rglob('*') if _.is_file())
            structure[item] = count
            total_files += count
            print(f"  📁 {item}/: {count} файлов")
    
    for item in important_files:
        if os.path.exists(item):
            structure[item] = "✅"
            total_files += 1
            print(f"  📄 {item}: ✅")
        else:
            structure[item] = "❌"
            print(f"  📄 {item}: ❌")
    
    print(f"\n📈 Общее количество файлов: {total_files}")
    return total_files, structure


def generate_new_repo_names():
    """Сгенерировать варианты имен для нового репозитория"""
    suggestions = [
        "PneumoStabSim-Professional",
        "PneumaticStabilizer-Qt3D", 
        "StabilizerSim-Russian",
        "PneumoStabSim-Advanced",
        "PneumoStab-Simulator",
        "Qt3D-PneumoStabilizer"
    ]
    return suggestions


def create_migration_script(repo_name):
    """Создать скрипт миграции"""
    script_content = f'''@echo off
echo ===== МИГРАЦИЯ PNEUMOSTABSIM В НОВЫЙ РЕПОЗИТОРИЙ =====
echo.
echo Новый репозиторий: {repo_name}
echo URL: https://github.com/barmaleii77-hub/{repo_name}
echo.

echo Шаг 1: Добавляем новый remote...
git remote add new-repo https://github.com/barmaleii77-hub/{repo_name}.git

echo Шаг 2: Проверяем состояние...
git status

echo Шаг 3: Отправляем в новый репозиторий...
git push -u new-repo main

echo Шаг 4: Проверяем результат...
git remote -v

echo.
echo ===== МИГРАЦИЯ ЗАВЕРШЕНА =====
echo Новый репозиторий: https://github.com/barmaleii77-hub/{repo_name}
echo.
pause
'''
    
    with open(f"migrate_to_{repo_name.lower().replace('-', '_')}.bat", 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    return f"migrate_to_{repo_name.lower().replace('-', '_')}.bat"


def main():
    """Основная функция"""
    print("🚀 АВТОМАТИЧЕСКАЯ ПОДГОТОВКА К СОЗДАНИЮ НОВОГО GITHUB РЕПОЗИТОРИЯ")
    print("=" * 70)
    
    # Проверяем git статус
    if not check_git_status():
        print("❌ Пожалуйста, зафиксируйте все изменения перед созданием нового репозитория")
        return 1
    
    # Анализируем проект
    total_files, structure = count_project_files()
    
    # Показываем варианты имен
    print(f"\n🎯 РЕКОМЕНДУЕМЫЕ ИМЕНА ДЛЯ НОВОГО РЕПОЗИТОРИЯ:")
    suggestions = generate_new_repo_names()
    for i, name in enumerate(suggestions, 1):
        print(f"  {i}. {name}")
        print(f"     URL: https://github.com/barmaleii77-hub/{name}")
    
    # Создаем инструкцию
    print(f"\n📋 ПОШАГОВАЯ ИНСТРУКЦИЯ:")
    print(f"1. Перейдите на GitHub: https://github.com/barmaleii77-hub")
    print(f"2. Нажмите 'New repository'")
    print(f"3. Выберите имя из списка выше (рекомендуется: {suggestions[0]})")
    print(f"4. Описание: 'Professional Pneumatic Stabilizer Simulator with Qt Quick 3D and Russian UI'")
    print(f"5. Установите Public")
    print(f"6. НЕ добавляйте README, .gitignore, License (у нас уже есть)")
    print(f"7. Нажмите 'Create repository'")
    
    # Создаем скрипты миграции для каждого варианта
    print(f"\n🔧 Создаем скрипты миграции...")
    for name in suggestions[:3]:  # Создаем скрипты для топ-3 вариантов
        script_file = create_migration_script(name)
        print(f"  ✅ Создан: {script_file}")
    
    # Создаем сводку проекта
    project_info = {
        "name": "PneumoStabSim",
        "version": "2.0.0",
        "total_files": total_files,
        "structure": structure,
        "main_features": [
            "Qt Quick 3D визуализация",
            "Русский интерфейс",
            "Пневматическая физическая модель", 
            "Режимы запуска: обычный, неблокирующий, тестовый",
            "Direct3D 11 backend",
            "Панели управления с вкладками"
        ],
        "requirements": [
            "Python 3.8+",
            "PySide6 6.5+",
            "NumPy, SciPy",
            "Windows 10/11"
        ]
    }
    
    with open("project_migration_info.json", "w", encoding="utf-8") as f:
        json.dump(project_info, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Информация о проекте сохранена в: project_migration_info.json")
    
    print(f"\n🎉 ПРОЕКТ ГОТОВ К МИГРАЦИИ!")
    print(f"📁 Всего файлов готово к переносу: {total_files}")
    print(f"🚀 После создания репозитория на GitHub запустите один из bat файлов")
    print(f"💡 Рекомендуется: {suggestions[0]}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
