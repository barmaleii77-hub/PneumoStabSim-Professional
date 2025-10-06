#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Проверка виртуального окружения PneumoStabSim
Virtual environment setup check for PneumoStabSim
"""
import sys
import subprocess
from pathlib import Path

def check_virtual_environment():
    """Проверить виртуальное окружение"""
    print("🐍 ПРОВЕРКА ВИРТУАЛЬНОГО ОКРУЖЕНИЯ")
    print("=" * 60)
    
    # Проверяем Python путь
    python_path = Path(sys.executable)
    print(f"Python путь: {python_path}")
    
    if ".venv" in str(python_path):
        print("✅ Виртуальное окружение активно")
        venv_path = python_path.parent.parent
        print(f"📁 Путь к venv: {venv_path}")
    else:
        print("❌ Виртуальное окружение НЕ активно")
        print("   Запустите: .venv\\Scripts\\activate")
        return False
    
    # Версия Python
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"🐍 Python версия: {python_version}")
    
    # Проверяем ключевые пакеты
    print("\n📦 ПРОВЕРКА ПАКЕТОВ:")
    
    required_packages = [
        "numpy", "scipy", "PySide6", "matplotlib", 
        "PyOpenGL", "PyOpenGL_accelerate"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "PyOpenGL_accelerate":
                import OpenGL_accelerate
                print(f"✅ {package}: установлен")
            else:
                __import__(package.lower().replace("-", "_"))
                print(f"✅ {package}: установлен")
        except ImportError:
            print(f"❌ {package}: НЕ УСТАНОВЛЕН")
            missing_packages.append(package)
    
    # Проверяем PySide6 модули
    print("\n🎨 ПРОВЕРКА PYSIDE6 МОДУЛЕЙ:")
    
    pyside6_modules = [
        "PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui",
        "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQuickWidgets"
    ]
    
    for module in pyside6_modules:
        try:
            __import__(module)
            print(f"✅ {module}: OK")
        except ImportError as e:
            print(f"❌ {module}: ОШИБКА - {e}")
            missing_packages.append(module)
    
    print("\n📊 РЕЗУЛЬТАТ:")
    if not missing_packages:
        print("🎉 ВСЕ ПАКЕТЫ УСТАНОВЛЕНЫ ПРАВИЛЬНО!")
        print("   Можно запускать приложение: python app.py")
        return True
    else:
        print(f"❌ Отсутствует {len(missing_packages)} пакетов:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n   Установите: pip install -r requirements.txt")
        return False

def create_activation_scripts():
    """Создать скрипты для активации окружения"""
    
    # Windows batch файл
    activate_bat = """@echo off
echo 🐍 Активация виртуального окружения PneumoStabSim...
call .venv\\Scripts\\activate.bat
echo ✅ Окружение активировано
echo 📋 Доступные команды:
echo    python app.py           - Запуск приложения
echo    python -m pytest tests/ - Запуск тестов  
echo    pip list               - Список пакетов
echo    deactivate             - Деактивация окружения
cmd /k
"""
    
    with open("activate.bat", "w", encoding="utf-8") as f:
        f.write(activate_bat)
    
    print("📄 Создан activate.bat для быстрой активации")
    
    # PowerShell скрипт
    activate_ps1 = """# Активация виртуального окружения PneumoStabSim
Write-Host "🐍 Активация виртуального окружения PneumoStabSim..." -ForegroundColor Green
& .venv\\Scripts\\Activate.ps1
Write-Host "✅ Окружение активировано" -ForegroundColor Green
Write-Host "📋 Доступные команды:" -ForegroundColor Yellow
Write-Host "   python app.py           - Запуск приложения" -ForegroundColor Cyan
Write-Host "   python -m pytest tests/ - Запуск тестов" -ForegroundColor Cyan  
Write-Host "   pip list               - Список пакетов" -ForegroundColor Cyan
Write-Host "   deactivate             - Деактивация окружения" -ForegroundColor Cyan
"""
    
    with open("activate.ps1", "w", encoding="utf-8") as f:
        f.write(activate_ps1)
    
    print("📄 Создан activate.ps1 для PowerShell")

def check_git_ignore():
    """Проверить .gitignore для виртуального окружения"""
    gitignore_path = Path(".gitignore")
    
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding='utf-8')
        if ".venv" not in content:
            print("⚠️  Добавьте .venv в .gitignore")
            with open(".gitignore", "a", encoding="utf-8") as f:
                f.write("\n# Virtual environment\n.venv/\n*.pyc\n__pycache__/\n")
            print("✅ .venv добавлен в .gitignore")
    else:
        print("📄 Создаем .gitignore")
        gitignore_content = """# Virtual environment
.venv/
*.pyc
__pycache__/

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
"""
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        print("✅ .gitignore создан")

def main():
    """Главная функция проверки"""
    print("🚀 УСТАНОВКА ВИРТУАЛЬНОГО ОКРУЖЕНИЯ PNEUMOSTABSIM")
    print("=" * 80)
    
    # Проверяем окружение
    env_ok = check_virtual_environment()
    
    print("\n" + "=" * 60)
    
    # Создаем вспомогательные скрипты
    create_activation_scripts()
    
    print("\n" + "=" * 60)
    
    # Проверяем .gitignore
    check_git_ignore()
    
    print("\n" + "=" * 80)
    
    if env_ok:
        print("🎉 ВИРТУАЛЬНОЕ ОКРУЖЕНИЕ ГОТОВО К РАБОТЕ!")
        print("\n💡 БЫСТРЫЙ ЗАПУСК:")
        print("   Windows:    activate.bat")
        print("   PowerShell: .\\activate.ps1")
        print("   Командная строка: .venv\\Scripts\\activate")
        print("\n🚀 ЗАПУСК ПРИЛОЖЕНИЯ:")
        print("   python app.py")
    else:
        print("❌ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ ОКРУЖЕНИЯ")
        print("   1. Убедитесь что виртуальное окружение активно")
        print("   2. Установите пакеты: pip install -r requirements.txt")
        print("   3. Повторите проверку")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
