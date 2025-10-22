# A-4.1: АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ КИНЕМАТИЧЕСКИХ ОГРАНИЧЕНИЙ

## ?? Результаты анализа

### ? Найденные компоненты:

**1. Кинематические модули существуют:**
- `src/mechanics/kinematics.py` - полная реализация LeverKinematics и CylinderKinematics
- `tests/test_kinematics.py` - комплексные тесты кинематики
- Правильная архитектура с Point2, LeverState, CylinderState

**2. GeometryPanel существует:**
- `src/ui/panels/panel_geometry.py` - панель с базовой валидацией
- Унифицированные параметры цилиндра (cyl_diam_m, rod_diam_m, stroke_m)
- Основные проверки зависимостей

### ? Недостающие компоненты:

**1. GeometryState отсутствует:**
- Нет модуля `src/ui/geo_state.py`
- Нет centralized state management
- Нет автоматической нормализации

**2. Ограниченные кинематические ограничения:**
- В GeometryPanel есть только базовые проверки
- Нет точного расчёта stroke_max через кинематику
- Отсутствуют детальные кинематические связи

**3. Нет интеграции между UI и кинематикой:**
- GeometryPanel не использует LeverKinematics
- Нет автоматического расчёта stroke_max
- Ограничения проверяются только при валидации

---

## ?? Текущая реализация stroke_max

### В GeometryPanel._validate_geometry():
```python
stroke = self.parameters['stroke_m']
cylinder_length = self.parameters['cylinder_length']
piston_thickness = self.parameters['piston_thickness_m']
dead_gap = self.parameters['dead_gap_m']

min_cylinder_length = stroke + piston_thickness + 2 * dead_gap
```

**Проблема**: Это геометрическое ограничение цилиндра, НЕ кинематическое ограничение подвески!

### Что должно быть:
```python
# Кинематический расчёт максимального хода:
lever_kinematics = LeverKinematics(...)
max_lever_angle = calculate_max_lever_angle(wheelbase, lever_geometry)
stroke_max_kinematic = calculate_stroke_from_angle(lever_kinematics, max_lever_angle)

# Реальное ограничение:
stroke <= min(stroke_max_kinematic, stroke_max_cylinder)
```

---

## ??? План A-4.2: Создание GeometryState с кинематикой

### Шаг 1: Создать GeometryState
```python
# src/ui/geo_state.py
@dataclass
class GeometryState:
    # Основные параметры
    wheelbase: float = 3.200
    lever_length: float = 0.800
    frame_to_pivot: float = 0.600
    # ... другие параметры

    # Кинематические ограничения
    def calculate_stroke_max_kinematic(self) -> float:
        """Точный кинематический расчёт stroke_max"""
        # Используем LeverKinematics для расчёта

    def validate_kinematic_constraints(self) -> List[str]:
        """Проверка всех кинематических ограничений"""
```

### Шаг 2: Интеграция с GeometryPanel
```python
# В GeometryPanel.__init__():
self.geo_state = GeometryState()

# В _on_parameter_changed():
corrections = self.geo_state.apply_kinematic_corrections(param_name, value)
```

### Шаг 3: Кинематические расчёты
```python
def calculate_max_lever_angle(wheelbase: float, lever_geometry: float) -> float:
    """Максимальный угол поворота рычага без пересечений"""

def calculate_stroke_from_lever_angle(kinematics: LeverKinematics, angle: float) -> float:
    """Расчёт хода цилиндра по углу рычага"""
```

---

## ?? Приоритеты A-4:

**Высокий приоритет:**
1. ? Создание GeometryState с кинематическими методами
2. ? Интеграция LeverKinematics в UI
3. ? Точный расчёт stroke_max через кинематику

**Средний приоритет:**
4. Угловые ограничения рычагов
5. Проверка пересечений элементов
6. Автоматическая коррекция параметров

**Низкий приоритет:**
7. Визуализация кинематических ограничений
8. Оптимизация параметров подвески

---

## ?? A-4.2: Начинаем реализацию

**Следующий шаг**: Создание GeometryState с базовыми кинематическими расчётами

**Файлы для создания/изменения:**
1. `src/ui/geo_state.py` - новый модуль (создать)
2. `src/ui/panels/panel_geometry.py` - интеграция (обновить)
3. `test_a4_kinematics.py` - тесты (создать)

**Готов к реализации A-4.2** ?
