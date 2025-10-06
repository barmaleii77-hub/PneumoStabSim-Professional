# МШ-2: Приведение всех линейных параметров к СИ и шагу 0.001м

## ВЫПОЛНЕНО ?

Дата: 2024-01-XX  
Статус: **ЗАВЕРШЕНО**  

### Цель
Привести все линейные параметры в GeometryPanel к единицам СИ (метры) с единым шагом 0.001м и decimals=3.

### Изменения

#### 1. Frame Dimensions (Размеры рамы)
**До:**
```python
# Wheelbase: step=0.1, decimals=1  
# Track: step=0.1, decimals=1
```

**После:**
```python
# Wheelbase: minimum=2.000, maximum=4.000, value=3.200, step=0.001, decimals=3
# Track: minimum=1.000, maximum=2.500, value=1.600, step=0.001, decimals=3
```

#### 2. Suspension Geometry (Геометрия подвески)  
**До:**
```python
# frame_to_pivot: step=0.05, decimals=2
# lever_length: step=0.05, decimals=2
# rod_position: step=0.05, decimals=2
```

**После:**
```python  
# frame_to_pivot: minimum=0.300, maximum=1.000, value=0.600, step=0.001, decimals=3
# lever_length: minimum=0.500, maximum=1.500, value=0.800, step=0.001, decimals=3
# rod_position: minimum=0.300, maximum=0.900, value=0.600, step=0.001, decimals=3
```

#### 3. Default Values (Значения по умолчанию)
Обновлены для консистентности с новой точностью:
```python
defaults = {
    'wheelbase': 3.200,       # было 3.2
    'track': 1.600,           # было 1.6  
    'frame_to_pivot': 0.600,  # было 0.6
    'lever_length': 0.800,    # было 0.8
    'rod_position': 0.600,    # было 0.6
    # ... цилиндр уже был в СИ из МШ-1
}
```

### Результат

Все линейные параметры теперь используют:
- **Единицы СИ:** метры (м)
- **Единый шаг:** 0.001 м (1 мм)  
- **Точность:** decimals=3
- **Консистентность:** унифицированный интерфейс

### Файлы изменены

1. `src/ui/panels/panel_geometry.py` - основные изменения
   - `_create_frame_group()` - обновлены wheelbase/track слайдеры
   - `_create_suspension_group()` - обновлены frame_to_pivot/lever_length слайдеры  
   - `_set_default_values()` - обновлены дефолтные значения

### Валидация

- ? Компиляция без ошибок
- ? Импорт модуля успешен
- ? Все линейные параметры в СИ
- ? Единый шаг 0.001 для всех линейных параметров
- ? Консистентная точность decimals=3

### Следующий шаг

**МШ-3:** Обновление логики dependency resolution для работы с новыми единицами СИ.

---
**Статус:** МШ-2 завершён успешно. Готов к переходу на МШ-3.