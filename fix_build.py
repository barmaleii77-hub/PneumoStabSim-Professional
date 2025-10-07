#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Автоматическое исправление проблем PneumoStabSim
Устраняет типичные ошибки сборки и настройки
"""

import os
import sys
import shutil
from pathlib import Path
import json

def fix_missing_init_files():
    """Создаёт отсутствующие __init__.py файлы"""
    print("🔧 Проверка __init__.py файлов...")
    
    init_locations = [
        "src/__init__.py",
        "src/ui/__init__.py",
        "src/ui/panels/__init__.py", 
        "src/ui/widgets/__init__.py",
        "src/runtime/__init__.py",
        "src/common/__init__.py",
        "src/physics/__init__.py",
        "src/pneumo/__init__.py",
        "src/mechanics/__init__.py",
        "src/road/__init__.py",
        "src/app/__init__.py",
        "src/core/__init__.py",
        "tests/__init__.py",
        "tests/ui/__init__.py"
    ]
    
    created = []
    
    for init_path in init_locations:
        path = Path(init_path)
        if not path.exists():
            # Создаём директорию если нужно
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Создаём простой __init__.py
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'# {path.parent.name} package\n')
            
            created.append(str(path))
    
    if created:
        print(f"✅ Создано __init__.py файлов: {len(created)}")
        for path in created:
            print(f"   📁 {path}")
    else:
        print("✅ Все __init__.py файлы на месте")

def fix_logs_directory():
    """Создаёт директорию logs если отсутствует"""
    print("🔧 Проверка директории logs...")
    
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Создана директория logs/")
        
        # Создаём .gitignore для логов
        gitignore = logs_dir / ".gitignore"
        with open(gitignore, 'w', encoding='utf-8') as f:
            f.write("# Ignore log files\n*.log\n*.txt\n")
        print("✅ Создан logs/.gitignore")
    else:
        print("✅ Директория logs/ существует")

def fix_environment_variables():
    """Проверяет и исправляет переменные окружения Qt"""
    print("🔧 Проверка переменных окружения Qt...")
    
    required_env = {
        "QSG_RHI_BACKEND": "d3d11",
        "QSG_INFO": "1",
        "QT_LOGGING_RULES": "js.debug=true;qt.qml.debug=true"
    }
    
    fixed = []
    
    for var, value in required_env.items():
        current = os.environ.get(var)
        if current != value:
            os.environ[var] = value
            fixed.append(f"{var}={value}")
    
    if fixed:
        print(f"✅ Исправлены переменные окружения: {len(fixed)}")
        for fix in fixed:
            print(f"   🔧 {fix}")
    else:
        print("✅ Переменные окружения Qt настроены корректно")

def fix_qml_permissions():
    """Исправляет права доступа к QML файлам"""
    print("🔧 Проверка прав доступа к QML файлам...")
    
    qml_dir = Path("assets/qml")
    if qml_dir.exists():
        try:
            # Проверяем доступность основного файла
            main_qml = qml_dir / "main.qml"
            if main_qml.exists():
                with open(main_qml, 'r', encoding='utf-8') as f:
                    _ = f.read(100)  # Читаем первые 100 символов
                print("✅ QML файлы доступны для чтения")
            else:
                print("⚠️ assets/qml/main.qml отсутствует")
        except Exception as e:
            print(f"❌ Проблема с доступом к QML: {e}")
    else:
        print("⚠️ Директория assets/qml/ не найдена")

def create_launcher_script():
    """Создаёт удобный launcher скрипт"""
    print("🔧 Создание launcher скрипта...")
    
    launcher_content = '''@echo off
rem PneumoStabSim Launcher
rem Автоматический запуск с правильными параметрами

echo ================================================
echo   PneumoStabSim - Pneumatic Stabilizer Simulator
echo   Version: 2.0.0 (Russian UI + Qt Quick 3D)
echo ================================================
echo.

rem Установка переменных окружения
set QSG_RHI_BACKEND=d3d11
set QSG_INFO=1
set QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true

rem Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ОШИБКА: Python не найден в PATH
    echo Убедитесь что Python установлен и добавлен в PATH
    pause
    exit /b 1
)

rem Проверка наличия app.py
if not exist "app.py" (
    echo ОШИБКА: app.py не найден
    echo Запустите скрипт из корневой директории проекта
    pause
    exit /b 1
)

echo Запуск PneumoStabSim...
echo.

rem Запуск приложения
python app.py %*

rem Пауза при ошибке
if %errorlevel% neq 0 (
    echo.
    echo Приложение завершилось с ошибкой (код: %errorlevel%)
    pause
)
'''
    
    launcher_path = Path("run.bat")
    with open(launcher_path, 'w', encoding='cp1251') as f:  # Windows кодировка для .bat
        f.write(launcher_content)
    
    print("✅ Создан run.bat launcher")
    print("   Теперь можно запускать через: run.bat")

def create_development_config():
    """Создаёт конфигурационный файл для разработки"""
    print("🔧 Создание конфигурации разработки...")
    
    dev_config = {
        "debug_mode": True,
        "log_level": "DEBUG",
        "auto_save_settings": True,
        "render_backend": "d3d11",
        "physics_timestep": 0.001,
        "ui_update_rate": 60,
        "default_window_size": [1400, 900],
        "russian_ui": True,
        "test_mode_duration": 5.0,
        "geometry_defaults": {
            "frame_length": 3.2,
            "frame_height": 0.65,
            "track_width": 1.6,
            "lever_length": 0.8,
            "cylinder_length": 0.5
        }
    }
    
    config_path = Path("dev_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(dev_config, f, indent=2, ensure_ascii=False)
    
    print("✅ Создан dev_config.json")
    print("   Настройки для разработки и отладки")

def fix_import_paths():
    """Исправляет проблемы с импортами"""
    print("🔧 Проверка путей импорта...")
    
    # Добавляем текущую директорию в sys.path если её там нет
    current_dir = str(Path.cwd())
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print("✅ Добавлена текущая директория в sys.path")
    
    # Проверяем критические импорты
    try:
        import src.ui.main_window
        import src.runtime.sim_loop
        import src.common
        print("✅ Критические модули импортируются")
    except ImportError as e:
        print(f"❌ Проблема с импортами: {e}")

def create_troubleshooting_guide():
    """Создаёт руководство по устранению проблем"""
    print("🔧 Создание руководства по устранению проблем...")
    
    guide_content = '''# РУКОВОДСТВО ПО УСТРАНЕНИЮ ПРОБЛЕМ
## PneumoStabSim v2.0.0

### Частые проблемы и решения

#### 1. Ошибки импорта модулей
**Проблема:** ImportError, ModuleNotFoundError
**Решение:**
```bash
# Убедитесь что находитесь в корневой директории проекта
python build_check.py  # Проверка всех импортов

# Если проблемы остались:
python fix_build.py    # Автоматическое исправление
```

#### 2. Qt не запускается / чёрный экран
**Проблема:** QML не загружается, окно не отображается
**Решение:**
```bash
# Проверьте переменные окружения:
set QSG_RHI_BACKEND=d3d11
set QSG_INFO=1

# Запустите в режиме отладки:
python app.py --debug
```

#### 3. Отсутствуют зависимости
**Проблема:** Пакеты numpy, PySide6 и др. не найдены
**Решение:**
```bash
pip install -r requirements.txt

# Или по отдельности:
pip install numpy==2.3.3 scipy==1.16.2 pyside6==6.9.3
```

#### 4. Ошибки прав доступа к файлам
**Проблема:** Permission denied, файлы не читаются
**Решение:**
- Запустите от имени администратора
- Проверьте антивирус (может блокировать Qt)
- Убедитесь что файлы не заблокированы

#### 5. Python не найден
**Проблема:** 'python' не распознается как команда
**Решение:**
- Установите Python 3.9+ с официального сайта
- Добавьте Python в PATH
- Используйте `py` вместо `python` в Windows

### Команды для диагностики

```bash
# Полная проверка системы
python build_check.py

# Автоматическое исправление
python fix_build.py  

# Тестовый запуск (5 секунд)
python app.py --test-mode

# Запуск с отладкой
python app.py --debug

# Неблокирующий режим
python app.py --no-block
```

### Контакты для поддержки

- GitHub: https://github.com/barmaleii77-hub/NewRepo2
- Issues: Создайте issue с описанием проблемы
- Logs: Проверьте файлы в папке logs/

### Системные требования

- Python 3.9+ (рекомендуется 3.13+)
- Windows 10/11 (рекомендуется)
- DirectX 11 совместимая видеокарта
- 4GB RAM минимум
- 2GB свободного места на диске

### Версия документа
Последнее обновление: январь 2025
'''
    
    guide_path = Path("TROUBLESHOOTING.md")
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ Создан TROUBLESHOOTING.md")
    print("   Подробное руководство по решению проблем")

def main():
    """Основная функция исправления"""
    print("🛠️ АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ ПРОБЛЕМ")
    print("PneumoStabSim v2.0.0 Build Fixer")
    print("="*50)
    
    fixes = [
        ("Создание __init__.py файлов", fix_missing_init_files),
        ("Создание директории logs", fix_logs_directory),
        ("Настройка переменных окружения", fix_environment_variables),
        ("Проверка прав доступа к QML", fix_qml_permissions),
        ("Создание launcher скрипта", create_launcher_script),
        ("Создание конфигурации разработки", create_development_config),
        ("Исправление путей импорта", fix_import_paths),
        ("Создание руководства по устранению проблем", create_troubleshooting_guide),
    ]
    
    print(f"\nВыполняется {len(fixes)} исправлений...\n")
    
    for fix_name, fix_func in fixes:
        try:
            fix_func()
        except Exception as e:
            print(f"❌ Ошибка в '{fix_name}': {e}")
        print()
    
    print("="*50)
    print("🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО")
    print("\nСозданные файлы:")
    print("  📁 logs/              - Директория для логов")
    print("  🚀 run.bat            - Launcher для Windows")
    print("  ⚙️ dev_config.json   - Конфигурация разработки") 
    print("  📖 TROUBLESHOOTING.md - Руководство по проблемам")
    print("\nТеперь можно запускать:")
    print("  python build_check.py  # Проверка")
    print("  python app.py          # Запуск приложения")
    print("  run.bat               # Запуск через launcher")

if __name__ == "__main__":
    main()
