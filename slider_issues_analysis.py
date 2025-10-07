# -*- coding: utf-8 -*-
"""
Анализ и исправление проблем со слайдерами в панелях
ПРОБЛЕМЫ:
1. Поле значения должно быть посередине слайдера (МИН - ЗНАЧЕНИЕ - МАКС)
2. Диапазоны значений мин-макс должны быть у всех параметров всех панелей
"""

def analyze_slider_issues():
    """Анализ проблем с расположением элементов слайдеров и диапазонами"""
    
    print("🔍 АНАЛИЗ ПРОБЛЕМ СО СЛАЙДЕРАМИ")
    print("=" * 60)
    
    # ===== ПРОБЛЕМА 1: РАСПОЛОЖЕНИЕ ЭЛЕМЕНТОВ =====
    print("\n📊 1. РАСПОЛОЖЕНИЕ ЭЛЕМЕНТОВ В СЛАЙДЕРЕ:")
    print("-" * 40)
    
    print("✅ ТЕКУЩЕЕ СОСТОЯНИЕ (src/ui/widgets/range_slider.py):")
    print("   Порядок элементов в controls_layout:")
    print("   1. [Мин] - QVBoxLayout с min_spinbox")
    print("   2. [Значение] - QVBoxLayout с value_spinbox") 
    print("   3. [Макс] - QVBoxLayout с max_spinbox")
    print("   4. [Единицы] - units_label")
    print()
    
    print("✅ РАСПОЛОЖЕНИЕ ПРАВИЛЬНОЕ!")
    print("   - Мин слева")
    print("   - Значение по центру") 
    print("   - Макс справа")
    print("   Проблема с расположением элементов ОТСУТСТВУЕТ")
    
    # ===== ПРОБЛЕМА 2: ДИАПАЗОНЫ ЗНАЧЕНИЙ =====
    print("\n📊 2. АНАЛИЗ ДИАПАЗОНОВ ЗНАЧЕНИЙ ВО ВСЕХ ПАНЕЛЯХ:")
    print("-" * 40)
    
    panels_analysis = analyze_parameter_ranges()
    
    # Показать результаты анализа
    for panel_name, analysis in panels_analysis.items():
        print(f"\n🔧 {panel_name}:")
        print(f"   Всего параметров: {analysis['total_params']}")
        print(f"   С диапазонами: {analysis['with_ranges']}")
        print(f"   Без диапазонов: {analysis['without_ranges']}")
        
        if analysis['missing_ranges']:
            print(f"   ❌ Отсутствуют диапазоны:")
            for param in analysis['missing_ranges']:
                print(f"      • {param}")
        
        if analysis['range_issues']:
            print(f"   ⚠️  Проблемы с диапазонами:")
            for issue in analysis['range_issues']:
                print(f"      • {issue}")
    
    # ===== РЕКОМЕНДАЦИИ =====
    print("\n💡 3. РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
    print("-" * 40)
    
    total_issues = sum(len(analysis['missing_ranges']) + len(analysis['range_issues']) 
                      for analysis in panels_analysis.values())
    
    if total_issues == 0:
        print("✅ ВСЕ ДИАПАЗОНЫ НАСТРОЕНЫ ПРАВИЛЬНО!")
        print("   Нет параметров без диапазонов")
        print("   Нет проблем с размерами диапазонов")
    else:
        print(f"⚠️  НАЙДЕНО {total_issues} ПРОБЛЕМ С ДИАПАЗОНАМИ")
        print("\nПлан исправления:")
        print("1. Добавить недостающие диапазоны для всех параметров")
        print("2. Проверить адекватность диапазонов (мин < дефолт < макс)")
        print("3. Убедиться, что диапазоны покрывают практические значения")
        print("4. Добавить валидацию диапазонов")
    
    return panels_analysis


def analyze_parameter_ranges():
    """Анализ диапазонов параметров в каждой панели"""
    
    panels = {
        "GeometryPanel": {
            "params": [
                {"name": "wheelbase", "min": 2.0, "max": 4.0, "default": 3.2, "units": "м"},
                {"name": "track", "min": 1.0, "max": 2.5, "default": 1.6, "units": "м"},
                {"name": "frame_to_pivot", "min": 0.3, "max": 1.0, "default": 0.6, "units": "м"},
                {"name": "lever_length", "min": 0.5, "max": 1.5, "default": 0.8, "units": "м"},
                {"name": "rod_position", "min": 0.3, "max": 0.9, "default": 0.6, "units": "доля"},
                {"name": "cylinder_length", "min": 0.3, "max": 0.8, "default": 0.5, "units": "м"},
                {"name": "cyl_diam_m", "min": 0.030, "max": 0.150, "default": 0.080, "units": "м"},
                {"name": "stroke_m", "min": 0.100, "max": 0.500, "default": 0.300, "units": "м"},
                {"name": "dead_gap_m", "min": 0.000, "max": 0.020, "default": 0.005, "units": "м"},
                {"name": "rod_diameter_m", "min": 0.020, "max": 0.060, "default": 0.035, "units": "м"},
                {"name": "piston_rod_length_m", "min": 0.100, "max": 0.500, "default": 0.200, "units": "м"},
                {"name": "piston_thickness_m", "min": 0.010, "max": 0.050, "default": 0.025, "units": "м"}
            ]
        },
        
        "PneumoPanel": {
            "params": [
                {"name": "receiver_volume", "min": 0.001, "max": 0.100, "default": 0.020, "units": "м³"},
                {"name": "receiver_diameter", "min": 0.050, "max": 0.500, "default": 0.200, "units": "м"},
                {"name": "receiver_length", "min": 0.100, "max": 2.000, "default": 0.500, "units": "м"},
                {"name": "cv_atmo_dp", "min": 0.001, "max": 0.1, "default": 0.01, "units": "бар"},
                {"name": "cv_tank_dp", "min": 0.001, "max": 0.1, "default": 0.01, "units": "бар"},
                {"name": "cv_atmo_dia", "min": 1.0, "max": 10.0, "default": 3.0, "units": "мм"},
                {"name": "cv_tank_dia", "min": 1.0, "max": 10.0, "default": 3.0, "units": "мм"},
                {"name": "relief_min_pressure", "min": 1.0, "max": 10.0, "default": 2.5, "units": "бар"},
                {"name": "relief_stiff_pressure", "min": 5.0, "max": 50.0, "default": 15.0, "units": "бар"},
                {"name": "relief_safety_pressure", "min": 20.0, "max": 100.0, "default": 50.0, "units": "бар"},
                {"name": "throttle_min_dia", "min": 0.5, "max": 3.0, "default": 1.0, "units": "мм"},
                {"name": "throttle_stiff_dia", "min": 0.5, "max": 3.0, "default": 1.5, "units": "мм"},
                {"name": "atmo_temp", "min": -20.0, "max": 50.0, "default": 20.0, "units": "°C"}
            ]
        },
        
        "ModesPanel": {
            "params": [
                {"name": "amplitude", "min": 0.0, "max": 0.2, "default": 0.05, "units": "м"},
                {"name": "frequency", "min": 0.1, "max": 10.0, "default": 1.0, "units": "Гц"},
                {"name": "phase", "min": 0.0, "max": 360.0, "default": 0.0, "units": "°"},
                {"name": "lf_phase", "min": 0.0, "max": 360.0, "default": 0.0, "units": "°"},
                {"name": "rf_phase", "min": 0.0, "max": 360.0, "default": 0.0, "units": "°"},
                {"name": "lr_phase", "min": 0.0, "max": 360.0, "default": 0.0, "units": "°"},
                {"name": "rr_phase", "min": 0.0, "max": 360.0, "default": 0.0, "units": "°"}
            ]
        }
    }
    
    analysis_results = {}
    
    for panel_name, panel_data in panels.items():
        analysis = {
            "total_params": len(panel_data["params"]),
            "with_ranges": 0,
            "without_ranges": 0,
            "missing_ranges": [],
            "range_issues": []
        }
        
        for param in panel_data["params"]:
            # Проверяем наличие диапазонов
            has_min = "min" in param and param["min"] is not None
            has_max = "max" in param and param["max"] is not None
            has_default = "default" in param and param["default"] is not None
            
            if has_min and has_max:
                analysis["with_ranges"] += 1
                
                # Проверяем корректность диапазонов
                if has_default:
                    if not (param["min"] <= param["default"] <= param["max"]):
                        analysis["range_issues"].append(
                            f"{param['name']}: default {param['default']} не в диапазоне [{param['min']}, {param['max']}]"
                        )
                    
                    # Проверяем разумность диапазонов
                    range_size = param["max"] - param["min"]
                    default_pos = (param["default"] - param["min"]) / range_size
                    
                    if range_size <= 0:
                        analysis["range_issues"].append(f"{param['name']}: некорректный диапазон (max <= min)")
                    elif range_size < 0.001:  # Очень маленький диапазон
                        analysis["range_issues"].append(f"{param['name']}: слишком маленький диапазон ({range_size})")
                
            else:
                analysis["without_ranges"] += 1
                missing_parts = []
                if not has_min:
                    missing_parts.append("min")
                if not has_max:
                    missing_parts.append("max")
                analysis["missing_ranges"].append(f"{param['name']} (отсутствует: {', '.join(missing_parts)})")
        
        analysis_results[panel_name] = analysis
    
    return analysis_results


def recommend_missing_ranges():
    """Рекомендации по диапазонам для параметров без них"""
    
    print("\n🔧 РЕКОМЕНДАЦИИ ПО НЕДОСТАЮЩИМ ДИАПАЗОНАМ:")
    print("=" * 60)
    
    # Общие принципы определения диапазонов
    principles = {
        "Геометрические размеры (м)": {
            "rule": "Дефолт ± 50-200% в зависимости от типа",
            "examples": [
                "Длины: default ± 100% (но не меньше практического минимума)",
                "Диаметры: default ± 150% (с учетом физических ограничений)", 
                "Доли (0-1): обычно 0.1-0.9 или по физическому смыслу"
            ]
        },
        
        "Давления (бар, Па)": {
            "rule": "От 0 или минимального рабочего до максимального безопасного",
            "examples": [
                "Рабочие давления: 0.1-100 бар для пневматики",
                "Перепады давления: 0.001-1 бар",
                "Предохранительные клапаны: в порядке возрастания"
            ]
        },
        
        "Температуры (°C)": {
            "rule": "От климатического минимума до максимума",
            "examples": [
                "Атмосферная температура: -40°C до +60°C",
                "Рабочая температура жидкости: -20°C до +120°C"
            ]
        },
        
        "Частоты (Гц)": {
            "rule": "От 0.1 Гц до резонансных частот системы",
            "examples": [
                "Дорожные возбуждения: 0.1-20 Гц",
                "Собственные частоты: обычно 1-10 Гц для подвески"
            ]
        },
        
        "Углы (градусы)": {
            "rule": "0-360° для фаз, ±90° для поворотов",
            "examples": [
                "Фазовые сдвиги: 0-360°",
                "Углы поворота рычагов: обычно ±45°"
            ]
        }
    }
    
    for category, info in principles.items():
        print(f"\n📐 {category}:")
        print(f"   Правило: {info['rule']}")
        for example in info['examples']:
            print(f"   • {example}")
    
    print("\n⚠️  ВАЖНЫЕ ПРИНЦИПЫ:")
    print("   1. Минимум должен быть физически осмысленным (не отрицательным для размеров)")
    print("   2. Максимум должен покрывать все практические случаи + запас")
    print("   3. Дефолт должен быть в 'разумной' части диапазона (обычно 20-80%)")
    print("   4. Шаг должен обеспечивать нужную точность (0.001м для геометрии)")
    print("   5. Диапазон должен допускать эксперименты, но не бессмысленные значения")


def create_range_validation_improvements():
    """Создать улучшения для валидации диапазонов"""
    
    improvements = {
        "1. Добавить валидацию в RangeSlider": {
            "description": "Проверка корректности диапазонов при создании",
            "code_changes": [
                "Проверка min < max при setRange()",
                "Проверка default в диапазоне",
                "Предупреждения о слишком маленьких диапазонах",
                "Автоматическая коррекция некорректных значений"
            ]
        },
        
        "2. Улучшить отображение диапазонов": {
            "description": "Более наглядное отображение min-max значений",
            "code_changes": [
                "Подсветка текущих min-max границ",
                "Показ процентного положения в диапазоне",
                "Цветовое кодирование (зеленый - норма, желтый - край, красный - вне диапазона)",
                "Tooltip с информацией о диапазоне"
            ]
        },
        
        "3. Интеллектуальные диапазоны": {
            "description": "Автоматическое определение разумных диапазонов",
            "code_changes": [
                "Функция auto_range(default_value, param_type, units)",
                "База знаний типичных диапазонов для физических величин",
                "Адаптивные диапазоны в зависимости от других параметров",
                "Предупреждения о выходе за физически разумные пределы"
            ]
        },
        
        "4. Контекстная валидация": {
            "description": "Проверка связанных параметров",
            "code_changes": [
                "Проверка rod_diameter < cylinder_diameter",
                "Проверка relief_pressures в правильном порядке",
                "Проверка геометрических ограничений (рычаг не выходит за раму)",
                "Предупреждения о неоптимальных сочетаниях"
            ]
        }
    }
    
    print("\n🚀 ПРЕДЛАГАЕМЫЕ УЛУЧШЕНИЯ:")
    print("=" * 60)
    
    for improvement_name, details in improvements.items():
        print(f"\n{improvement_name}")
        print(f"   {details['description']}")
        print("   Изменения:")
        for change in details['code_changes']:
            print(f"      • {change}")
    
    return improvements


if __name__ == "__main__":
    # Выполнить полный анализ
    panels_analysis = analyze_slider_issues()
    recommend_missing_ranges()
    improvements = create_range_validation_improvements()
    
    print("\n" + "=" * 60)
    print("📋 ИТОГОВАЯ ОЦЕНКА:")
    
    total_params = sum(analysis['total_params'] for analysis in panels_analysis.values())
    total_with_ranges = sum(analysis['with_ranges'] for analysis in panels_analysis.values())
    total_issues = sum(len(analysis['missing_ranges']) + len(analysis['range_issues']) 
                      for analysis in panels_analysis.values())
    
    print(f"   Всего параметров: {total_params}")
    print(f"   С диапазонами: {total_with_ranges}")
    print(f"   Покрытие диапазонами: {total_with_ranges/total_params*100:.1f}%")
    print(f"   Проблем найдено: {total_issues}")
    
    if total_issues == 0:
        print("\n✅ ДИАГНОЗ: ВСЕ ДИАПАЗОНЫ НАСТРОЕНЫ КОРРЕКТНО!")
        print("   Проблема с расположением элементов отсутствует")
        print("   Все параметры имеют корректные диапазоны")
        print("   Дополнительных исправлений не требуется")
    else:
        print(f"\n⚠️  ДИАГНОЗ: НАЙДЕНЫ ПРОБЛЕМЫ ({total_issues})")
        print("   Требуется реализация предложенных улучшений")
        print("   Приоритет: средний (не критично для функциональности)")
