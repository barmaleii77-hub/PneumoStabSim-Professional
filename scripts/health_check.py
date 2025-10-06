#!/usr/bin/env python3
"""
Проверка состояния проекта и зависимостей
"""
import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Проверяет версию Python"""
    version = sys.version_info
    print(f"Python версия: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 13):
        print("❌ Требуется Python 3.13+")
        return False
    else:
        print("✅ Версия Python подходит")
        return True

def check_dependencies():
    """Проверяет основные зависимости"""
    required_packages = {
        'PySide6': '6.9.0',
        'numpy': '2.0.0',
        'scipy': '1.10.0',
        'matplotlib': '3.5.0'
    }
    
    all_ok = True
    
    for package, min_version in required_packages.items():
        try:
            module = importlib.import_module(package.lower().replace('-', '_'))
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {package}: {version}")
        except ImportError:
            print(f"❌ {package} не установлен")
            all_ok = False
    
    return all_ok

def check_project_structure():
    """Проверяет структуру проекта"""
    required_dirs = [
        'src', 'src/ui', 'src/core', 'tests', 'assets', 
        'docs', 'config', 'scripts'
    ]
    
    required_files = [
        'app.py', 'requirements.txt', '.editorconfig', 
        '.gitignore', 'README.md'
    ]
    
    all_ok = True
    
    print("\nПроверка директорий:")
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ отсутствует")
            all_ok = False
    
    print("\nПроверка файлов:")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} отсутствует")
            all_ok = False
    
    return all_ok

def check_git_status():
    """Проверяет статус Git репозитория"""
    try:
        # Проверяем, что мы в git репозитории
        subprocess.run(['git', 'status'], 
                      capture_output=True, check=True, text=True)
        print("✅ Git репозиторий инициализирован")
        
        # Проверяем удаленный репозиторий
        result = subprocess.run(['git', 'remote', '-v'], 
                               capture_output=True, text=True)
        if result.stdout:
            print("✅ Удаленный репозиторий настроен")
        else:
            print("⚠️ Удаленный репозиторий не настроен")
        
        return True
    except subprocess.CalledProcessError:
        print("❌ Git репозиторий не инициализирован")
        return False

def main():
    """Основная функция проверки"""
    print("=== ПРОВЕРКА СОСТОЯНИЯ ПРОЕКТА ===\n")
    
    checks = [
        ("Python версия", check_python_version),
        ("Зависимости", check_dependencies), 
        ("Структура проекта", check_project_structure),
        ("Git репозиторий", check_git_status)
    ]
    
    results = {}
    
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        results[name] = check_func()
    
    print("\n=== ИТОГОВЫЙ РЕЗУЛЬТАТ ===")
    
    all_passed = all(results.values())
    
    for name, passed in results.items():
        status = "✅ ПРОШЛА" if passed else "❌ ПРОВАЛЕНА"
        print(f"{name}: {status}")
    
    if all_passed:
        print(f"\n🎉 Все проверки пройдены! Проект готов к работе.")
        return 0
    else:
        print(f"\n⚠️ Есть проблемы, которые нужно исправить.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
