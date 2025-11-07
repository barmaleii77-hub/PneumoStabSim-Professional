"""
Пред-аудит проекта перед микрошагами UI
"""

import sys
import json
import time
from pathlib import Path


def ensure_dir(path):
    """Создание директории если не существует"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return Path(path)


def check_environment():
    """Проверка окружения"""
    info = {
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "executable": sys.executable,
    }

    # Проверка PySide6
    try:
        import PySide6

        info["pyside6_available"] = True
        info["pyside6_version"] = getattr(PySide6, "__version__", "unknown")
    except ImportError:
        info["pyside6_available"] = False

    return info


def check_structure():
    """Проверка структуры проекта"""
    paths = ["src/", "tests/", "reports/", "logs/", "artifacts/", "assets/qml/"]
    result = {}

    for path in paths:
        p = Path(path)
        result[path] = {
            "exists": p.exists(),
            "is_dir": p.is_dir() if p.exists() else False,
            "file_count": len(list(p.rglob("*"))) if p.exists() and p.is_dir() else 0,
        }

    return result


def check_key_files():
    """Проверка ключевых файлов"""
    files = [
        "src/ui/main_window.py",
        "src/ui/panels/panel_geometry.py",
        "src/ui/panels/panel_pneumo.py",
        "src/ui/geo_state.py",
        "src/ui/geo_state_new.py",
        "src/pneumo/receiver.py",
        "src/runtime/state.py",
        "src/runtime/sim_loop.py",
    ]

    result = {}
    for file_path in files:
        p = Path(file_path)
        result[file_path] = {
            "exists": p.exists(),
            "size": p.stat().st_size if p.exists() else 0,
            "modified": time.ctime(p.stat().st_mtime) if p.exists() else None,
        }

    return result


def check_geometry_status():
    """Проверка статуса геометрии (Часть A)"""
    status = {
        "files_present": False,
        "unified_params": False,
        "si_units": False,
        "validation": False,
    }

    # Проверка файлов
    geo_files = [
        "src/ui/panels/panel_geometry.py",
        "src/ui/geo_state.py",
        "src/ui/geo_state_new.py",
    ]
    status["files_present"] = all(Path(f).exists() for f in geo_files)

    # Проверка содержимого panel_geometry.py
    panel_geo = Path("src/ui/panels/panel_geometry.py")
    if panel_geo.exists():
        try:
            content = panel_geo.read_text(encoding="utf-8")
            # 5 основных параметров цилиндра
            required_params = [
                "cyl_diam_m",
                "rod_diam_m",
                "stroke_m",
                "piston_thickness_m",
                "dead_gap_m",
            ]
            status["unified_params"] = all(
                param in content for param in required_params
            )
            status["si_units"] = "decimals=3" in content and "step=0.001" in content
        except Exception as e:
            print(f"Ошибка чтения {panel_geo}: {e}")

    return status


def check_receiver_status():
    """Проверка статуса ресивера (Часть B)"""
    status = {
        "files_present": False,
        "dual_modes": False,
        "volume_control": False,
        "thermodynamics": False,
    }

    # Проверка файлов
    recv_files = ["src/pneumo/receiver.py", "src/ui/panels/panel_pneumo.py"]
    status["files_present"] = all(Path(f).exists() for f in recv_files)

    # Проверка panel_pneumo.py
    panel_pneumo = Path("src/ui/panels/panel_pneumo.py")
    if panel_pneumo.exists():
        try:
            content = panel_pneumo.read_text(encoding="utf-8")
            status["dual_modes"] = "R1" in content and "R2" in content
            status["volume_control"] = "receiver_change_volume" in content
        except Exception as e:
            print(f"Ошибка чтения {panel_pneumo}: {e}")

    # Проверка receiver.py
    receiver_py = Path("src/pneumo/receiver.py")
    if receiver_py.exists():
        try:
            content = receiver_py.read_text(encoding="utf-8")
            status["thermodynamics"] = (
                "isothermal" in content and "adiabatic" in content
            )
        except Exception as e:
            print(f"Ошибка чтения {receiver_py}: {e}")

    return status


def check_ui_structure():
    """Проверка структуры UI"""
    status = {
        "main_window": False,
        "tabs": False,
        "scroll_areas": False,
        "splitters": False,
    }

    main_window = Path("src/ui/main_window.py")
    if main_window.exists():
        try:
            content = main_window.read_text(encoding="utf-8")
            status["main_window"] = True
            status["tabs"] = "QTabWidget" in content
            status["scroll_areas"] = "QScrollArea" in content
            status["splitters"] = "QSplitter" in content
        except Exception as e:
            print(f"Ошибка чтения {main_window}: {e}")

    return status


def check_tests():
    """Проверка тестов"""
    status = {
        "tests_dir": False,
        "ui_tests": False,
        "geometry_tests": False,
        "receiver_tests": False,
        "smoke_tests": False,
    }

    tests_dir = Path("tests")
    status["tests_dir"] = tests_dir.exists() and tests_dir.is_dir()

    if status["tests_dir"]:
        ui_tests = tests_dir / "ui"
        status["ui_tests"] = ui_tests.exists()

        if status["ui_tests"]:
            test_files = list(ui_tests.glob("*.py"))
            status["geometry_tests"] = any("geometry" in f.name for f in test_files)
            status["receiver_tests"] = any("receiver" in f.name for f in test_files)

        smoke_tests = list(tests_dir.rglob("*smoke*.py"))
        status["smoke_tests"] = len(smoke_tests) > 0

    return status


def create_report(audit_data):
    """Создание отчета"""
    # Создание директорий
    reports_dir = ensure_dir("reports/ui")
    artifacts_dir = ensure_dir("artifacts/ui")
    ensure_dir("logs/ui")

    # Основной отчет
    report_path = reports_dir / "audit_pre.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Пред-аудит проекта перед микрошагами UI\n\n")
        f.write(f"**Дата:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Окружение
        f.write("## 🐍 Окружение Python\n\n")
        env = audit_data["environment"]
        f.write(f"- **Версия Python:** {env['python_version']}\n")
        f.write(f"- **Платформа:** {env['platform']}\n")
        f.write(
            f"- **PySide6 доступен:** {'✅' if env['pyside6_available'] else '❌'}\n"
        )
        if env.get("pyside6_version"):
            f.write(f"- **Версия PySide6:** {env['pyside6_version']}\n")
        f.write("\n")

        # Структура
        f.write("## 📁 Структура проекта\n\n")
        for path, info in audit_data["structure"].items():
            icon = "✅" if info["exists"] else "❌"
            f.write(f"- **{path}** {icon}")
            if info["exists"] and info["is_dir"]:
                f.write(f" ({info['file_count']} файлов)")
            f.write("\n")
        f.write("\n")

        # Ключевые файлы
        f.write("## 📄 Ключевые файлы\n\n")
        for file_path, info in audit_data["files"].items():
            icon = "✅" if info["exists"] else "❌"
            f.write(f"- **{file_path}** {icon}")
            if info["exists"]:
                f.write(f" ({info['size']} bytes)")
            f.write("\n")
        f.write("\n")

        # Геометрия
        f.write("## 🔧 Состояние геометрии (Часть A)\n\n")
        geo = audit_data["geometry"]
        f.write(f"- **Файлы геометрии:** {'✅' if geo['files_present'] else '❌'}\n")
        f.write(
            f"- **Унифицированные параметры:** {'✅' if geo['unified_params'] else '❌'}\n"
        )
        f.write(
            f"- **СИ единицы (м, шаг 0.001, decimals=3):** {'✅' if geo['si_units'] else '❌'}\n"
        )
        f.write("\n")

        # Ресивер
        f.write("## 🌀 Состояние ресивера (Часть B)\n\n")
        recv = audit_data["receiver"]
        f.write(f"- **Файлы ресивера:** {'✅' if recv['files_present'] else '❌'}\n")
        f.write(f"- **Режимы R1/R2:** {'✅' if recv['dual_modes'] else '❌'}\n")
        f.write(f"- **Контроль объема:** {'✅' if recv['volume_control'] else '❌'}\n")
        f.write(
            f"- **Термодинамика (изотерма/адиабата):** {'✅' if recv['thermodynamics'] else '❌'}\n"
        )
        f.write("\n")

        # UI структура
        f.write("## 🖼️ Структура UI\n\n")
        ui = audit_data["ui"]
        f.write(f"- **Главное окно:** {'✅' if ui['main_window'] else '❌'}\n")
        f.write(f"- **Вкладки (QTabWidget):** {'✅' if ui['tabs'] else '❌'}\n")
        f.write(f"- **Области прокрутки:** {'✅' if ui['scroll_areas'] else '❌'}\n")
        f.write(f"- **Сплиттеры:** {'✅' if ui['splitters'] else '❌'}\n")
        f.write("\n")

        # Тесты
        f.write("## 🧪 Структура тестов\n\n")
        tests = audit_data["tests"]
        f.write(f"- **Директория tests/:** {'✅' if tests['tests_dir'] else '❌'}\n")
        f.write(f"- **UI тесты:** {'✅' if tests['ui_tests'] else '❌'}\n")
        f.write(f"- **Тесты геометрии:** {'✅' if tests['geometry_tests'] else '❌'}\n")
        f.write(f"- **Тесты ресивера:** {'✅' if tests['receiver_tests'] else '❌'}\n")
        f.write(f"- **Smoke тесты:** {'✅' if tests['smoke_tests'] else '❌'}\n")
        f.write("\n")

        # Рекомендации
        f.write("## 📋 Рекомендации для микрошагов\n\n")
        f.write("### MS-A-ACCEPT (Приемка геометрии)\n")
        if not geo["unified_params"]:
            f.write("- ⚠️ Проверить унификацию 5 параметров цилиндра\n")
        if not geo["si_units"]:
            f.write("- ⚠️ Проверить единицы СИ (метры, шаг 0.001, decimals=3)\n")

        f.write("\n### MS-B-ACCEPT (Приемка ресивера)\n")
        if not recv["dual_modes"]:
            f.write("- ⚠️ Проверить реализацию режимов R1/R2\n")
        if not recv["thermodynamics"]:
            f.write("- ⚠️ Проверить термодинамические расчеты\n")

        f.write("\n### MS-C (Горизонтальный сплиттер)\n")
        f.write("- 📝 Добавить горизонтальный сплиттер (левая область ↔ вкладки)\n")

        f.write("\n### MS-D (Пневмо-панель тумблеры)\n")
        f.write("- 📝 Добавить системные тумблеры в пневмо-панель\n")

    # JSON дамп данных
    json_path = artifacts_dir / "audit_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False, default=str)

    return report_path, json_path


def main():
    print("🔍 Начинаю пред-аудит проекта перед микрошагами UI...")

    # Сбор данных аудита
    audit_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": check_environment(),
        "structure": check_structure(),
        "files": check_key_files(),
        "geometry": check_geometry_status(),
        "receiver": check_receiver_status(),
        "ui": check_ui_structure(),
        "tests": check_tests(),
    }

    # Создание отчетов
    report_path, json_path = create_report(audit_data)

    # Краткая сводка
    print("\n📊 КРАТКАЯ СВОДКА ПРЕД-АУДИТА:")
    print(f"🐍 Python: {audit_data['environment']['python_version']}")
    print(
        f"📁 Структура: {sum(1 for info in audit_data['structure'].values() if info['exists'])}/{len(audit_data['structure'])} директорий"
    )
    print(
        f"📄 Ключевые файлы: {sum(1 for info in audit_data['files'].values() if info['exists'])}/{len(audit_data['files'])}"
    )
    print(
        f"🔧 Геометрия готова: {'✅' if audit_data['geometry']['unified_params'] else '❌'}"
    )
    print(f"🌀 Ресивер готов: {'✅' if audit_data['receiver']['dual_modes'] else '❌'}")
    print(f"🖼️ UI структура: {'✅' if audit_data['ui']['main_window'] else '❌'}")
    print(f"🧪 Тесты: {'✅' if audit_data['tests']['ui_tests'] else '❌'}")

    print("\n✅ Пред-аудит завершен!")
    print(f"📄 Отчет: {report_path}")
    print(f"🗂️ Данные: {json_path}")

    # Обновление плана управления
    control_plan_path = Path("reports/feedback/CONTROL_PLAN.json")
    if control_plan_path.exists():
        try:
            with open(control_plan_path, encoding="utf-8") as f:
                plan = json.load(f)

            step_info = {
                "area": "ui",
                "step": "pre_audit",
                "status": "completed",
                "timestamp": audit_data["timestamp"],
                "artifacts": {"report": str(report_path), "data": str(json_path)},
            }

            plan.setdefault("microsteps", []).append(step_info)

            with open(control_plan_path, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)

            print(f"📋 План управления обновлен: {control_plan_path}")
        except Exception as e:
            print(f"⚠️ Не удалось обновить план управления: {e}")


if __name__ == "__main__":
    main()
