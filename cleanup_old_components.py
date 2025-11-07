#!/usr/bin/env python3
"""
Очистка устаревших QML компонентов
Удаляет старые файлы, которые заменены модульными версиями
"""

from pathlib import Path
from datetime import datetime
import shutil


def cleanup_old_components():
    """Удалить устаревшие компоненты"""

    print("=" * 70)
    print("🧹 ОЧИСТКА УСТАРЕВШИХ QML КОМПОНЕНТОВ")
    print("=" * 70)
    print()

    # Список устаревших файлов
    old_files = [
        "assets/qml/components/CorrectedSuspensionCorner.qml",  # Заменён на geometry/SuspensionCorner.qml
        "assets/qml/components/Materials.qml",  # Заменён на scene/SharedMaterials.qml
        "assets/qml/UFrameScene.qml",  # Старая тестовая сцена
        "assets/qml/main_interactive_frame.qml",  # Старая интерактивная версия
    ]

    removed_count = 0
    backed_up_count = 0
    not_found_count = 0

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"assets/qml/backup_{timestamp}")

    for file_path_str in old_files:
        file_path = Path(file_path_str)

        if not file_path.exists():
            print(f"⏭️  {file_path.name}: НЕ НАЙДЕН (уже удалён)")
            not_found_count += 1
            continue

        print(f"📁 Обработка: {file_path}")

        # Создаём backup директорию при первом использовании
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True)
            print(f"   💾 Создана backup директория: {backup_dir}")

        # Копируем в backup
        backup_path = backup_dir / file_path.name
        shutil.copy2(file_path, backup_path)
        backed_up_count += 1
        print(f"   ✅ Сохранён backup: {backup_path.name}")

        # Удаляем оригинал
        file_path.unlink()
        removed_count += 1
        print(f"   🗑️  Удалён: {file_path.name}")

    print()
    print("=" * 70)
    print("📊 СТАТИСТИКА ОЧИСТКИ:")
    print("=" * 70)
    print(f"   Удалено файлов:      {removed_count}")
    print(f"   Сохранено в backup:  {backed_up_count}")
    print(f"   Уже отсутствовали:   {not_found_count}")
    print(f"   Всего обработано:    {len(old_files)}")

    if backup_dir.exists():
        print()
        print(f"💾 Backup сохранён в: {backup_dir}")

    print()
    print("=" * 70)
    print("✅ ОЧИСТКА ЗАВЕРШЕНА!")
    print("=" * 70)

    return removed_count


def validate_modular_structure():
    """Проверить, что модульные замены на месте"""

    print()
    print("=" * 70)
    print("🔍 ПРОВЕРКА МОДУЛЬНОЙ СТРУКТУРЫ")
    print("=" * 70)
    print()

    required_modules = {
        "geometry/SuspensionCorner.qml": "assets/qml/geometry/SuspensionCorner.qml",
        "scene/SharedMaterials.qml": "assets/qml/scene/SharedMaterials.qml",
        "geometry/Frame.qml": "assets/qml/geometry/Frame.qml",
        "geometry/CylinderGeometry.qml": "assets/qml/geometry/CylinderGeometry.qml",
        "lighting/DirectionalLights.qml": "assets/qml/lighting/DirectionalLights.qml",
        "lighting/PointLights.qml": "assets/qml/lighting/PointLights.qml",
        "camera/CameraController.qml": "assets/qml/camera/CameraController.qml",
    }

    all_present = True

    for name, path_str in required_modules.items():
        path = Path(path_str)
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {name}: {size} байт")
        else:
            print(f"❌ {name}: ОТСУТСТВУЕТ!")
            all_present = False

    print()
    if all_present:
        print("✅ Все модульные компоненты на месте!")
    else:
        print("⚠️ КРИТИЧНО: Некоторые модули отсутствуют!")

    print("=" * 70)

    return all_present


def main():
    """Главная функция"""

    print()
    print("🚀 Запуск очистки устаревших компонентов...")
    print()

    # Очистка
    removed = cleanup_old_components()

    # Проверка модульной структуры
    valid = validate_modular_structure()

    print()
    if removed > 0 and valid:
        print("🎉 УСПЕХ!")
        print(f"   Удалено {removed} устаревших файлов")
        print("   Модульная архитектура проверена")
    elif removed == 0:
        print("✅ НЕТ ИЗМЕНЕНИЙ")
        print("   Устаревшие файлы уже были удалены")
    else:
        print("⚠️ ПРЕДУПРЕЖДЕНИЕ")
        print("   Некоторые модули отсутствуют!")
        print("   Проверьте структуру проекта")


if __name__ == "__main__":
    main()
