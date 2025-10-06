# МШ-3: Обновление логики dependency resolution

## ВЫПОЛНЕНО ?

Дата: 2024-01-XX  
Статус: **ЗАВЕРШЕНО**

### Цель
Обновить методы `_check_dependencies()` и `_resolve_conflict()` для работы с новыми унифицированными параметрами в СИ единицах.

### Изменения

#### 1. Геометрические ограничения (СИ единицы)
**До:**
```python
max_lever_reach = wheelbase / 2.0 - 0.1  # 0.1м clearance
message: f'Текущее: {frame_to_pivot + lever_length:.2f}м'
```

**После:**
```python  
max_lever_reach = wheelbase / 2.0 - 0.100  # 100mm clearance explicit
message: f'Текущее: {frame_to_pivot + lever_length:.3f}м'  # 3 decimals for SI
```

#### 2. Гидравлические ограничения (унифицированные параметры)
**До:**
```python
rod_diameter = self.parameters['rod_diameter']  # mm
min_bore = min(bore_head, bore_rod)             # mm  
```

**После:**
```python
rod_diameter = self.parameters['rod_diam_m']    # meters
cyl_diameter = self.parameters['cyl_diam_m']    # meters (unified)
# Both head and rod use same diameter now!
```

#### 3. Stroke constraints (новая логика)
**Добавлено:**
```python
if param_name in ['stroke_m', 'cylinder_length', 'piston_thickness_m', 'dead_gap_m']:
    min_cylinder_length = stroke + piston_thickness + 2 * dead_gap
    # Detailed breakdown in error message
```

#### 4. 3D Scene геометрия (конверсия СИ ? мм)
**Обновлено:**
```python
geometry_3d = {
    'boreHead': self.parameters.get('cyl_diam_m', 0.080) * 1000,  # m -> mm
    'boreRod': self.parameters.get('cyl_diam_m', 0.080) * 1000,   # Same as boreHead!
    'strokeLength': self.parameters.get('stroke_m', 0.300) * 1000,  # m -> mm
    # ... все параметры корректно конвертируются из СИ в мм
}
```

#### 5. Пресеты (обновлены для унифицированных параметров)
**Обновлено:**
```python
presets = {
    0: {  # Стандартный грузовик
        'cyl_diam_m': 0.080, 'rod_diam_m': 0.035, 'stroke_m': 0.300,
        'cylinder_length': 0.500, 'piston_thickness_m': 0.020, 'dead_gap_m': 0.005
    },
    # ... все пресеты обновлены для новых параметров
}
```

### Результат

#### Унифицированная логика dependency resolution:
- ? **Геометрические ограничения** работают с СИ единицами и точностью 0.001м
- ? **Гидравлические ограничения** используют unified `cyl_diam_m` параметр  
- ? **Stroke constraints** поддерживают все новые параметры
- ? **3D Scene конверсия** корректно преобразует СИ ? мм
- ? **Пресеты** обновлены для всех новых параметров

#### Консистентность:
- Все расчёты в СИ единицах (метры)
- Точность 0.001м (1мм) везде
- Унифицированный диаметр цилиндра
- Детальные сообщения об ошибках

### Файлы изменены

1. `src/ui/panels/panel_geometry.py`
   - `_check_dependencies()` - полностью обновлён для унифицированных параметров
   - `_on_parameter_changed()` - обновлена логика emit geometry_changed  
   - `_on_preset_changed()` - пресеты обновлены для новых параметров

2. `tests/ui/test_ms3_dependency.py` - тесты для валидации МШ-3

### Валидация

- ? Компиляция без ошибок  
- ? Импорт модуля успешен
- ? Dependency check работает корректно
- ? Геометрические ограничения в СИ единицах
- ? Гидравлические ограничения с унифицированными параметрами
- ? Stroke constraints с новой логикой

### Следующий шаг

**МШ-4:** Создание comprehensive тестов для всего рефакторинга и финальная валидация.

---
**Статус:** МШ-3 завершён успешно. Dependency resolution обновлён для унифицированных параметров СИ.