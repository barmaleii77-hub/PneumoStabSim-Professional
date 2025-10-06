# ?? МШ-0: ПРЕД-АУДИТ ЗАВЕРШЁН

**Дата:** 2025-10-05 23:00  
**Статус:** ? **ЗАВЕРШЁН**  
**Следующий шаг:** МШ-1 (Унификация параметров цилиндра)

---

## ? ЧТО СДЕЛАНО

### Артефакты созданы
- ? `reports/ui/audit_pre.md` - детальный аудит UI
- ? `artifacts/ui/tree_pre.txt` - дерево виджетов (текстовый формат)
- ?? `artifacts/ui/widget_tree_pre.json` - НЕ СОЗДАН (ошибка файловой системы)

### Проанализированные файлы
- ? `src/ui/main_window.py` (776 строк)
- ? `src/ui/panels/panel_geometry.py` (500+ строк)
- ? `src/ui/widgets/range_slider.py`
- ? `src/ui/accordion.py` (не используется)

---

## ?? КЛЮЧЕВЫЕ НАХОДКИ

### 1. ВЕРТИКАЛЬНЫЙ СПЛИТТЕР: ? УЖЕ РЕАЛИЗОВАН

```python
# main_window.py, строки ~130-160
self.main_splitter = QSplitter(Qt.Orientation.Vertical)
self.main_splitter.addWidget(self._qquick_widget)  # 3D scene
self.main_splitter.addWidget(self.chart_widget)    # Charts
```

**Вывод:** НЕ требует изменений в МШ-3!

### 2. ГОРИЗОНТАЛЬНЫЙ СПЛИТТЕР: ? ОТСУТСТВУЕТ

```python
# main_window.py, строки ~153-159
central_layout = QHBoxLayout(central_container)
central_layout.addWidget(self.main_splitter, stretch=3)  # 75%
# ... позже: central_layout.addWidget(self.tab_widget, stretch=1)  # 25%
```

**Вывод:** ТРЕБУЕТСЯ QSplitter(Horizontal) в МШ-3!

### 3. ВКЛАДКИ: ? УЖЕ РЕАЛИЗОВАНЫ

```python
# main_window.py, строки ~215-275
self.tab_widget = QTabWidget()
# 5 вкладок с русскими названиями
# Tab 1-3: QScrollArea ?
# Tab 4-5: заглушки
```

**Вывод:** Структура вкладок корректна!

### 4. ПАРАМЕТРЫ ЦИЛИНДРА: ? ТРЕБУЮТ ИЗМЕНЕНИЙ

**Текущие параметры (panel_geometry.py):**
```python
bore_head_slider    # 50-150 мм ? УБРАТЬ
bore_rod_slider     # 50-150 мм ? УБРАТЬ
rod_diameter_slider # 20-60 мм ? 0.020-0.060 м
piston_rod_length_slider  # 100-500 мм ? 0.100-0.500 м
piston_thickness_slider   # 10-50 мм ? 0.010-0.050 м
```

**Нужно добавить:**
```python
cyl_diam_m   # 0.030-0.150 м (единый диаметр)
stroke_m     # 0.100-0.500 м (ход поршня)
dead_gap_m   # 0.000-0.020 м (мёртвый зазор)
```

### 5. ЕДИНИЦЫ ИЗМЕРЕНИЯ: ? БОЛЬШИНСТВО В ММ

| Параметр | Сейчас | Нужно |
|----------|--------|-------|
| wheelbase | м, шаг 0.1, dec=1 | м, шаг **0.001**, dec=**3** |
| track | м, шаг 0.1, dec=1 | м, шаг **0.001**, dec=**3** |
| bore_head | **мм**, шаг 5.0 | **УБРАТЬ** |
| bore_rod | **мм**, шаг 5.0 | **УБРАТЬ** |
| rod_diameter | **мм**, шаг 2.5 | **м**, шаг **0.001**, dec=**3** |
| piston_rod_length | **мм**, шаг 10.0 | **м**, шаг **0.001**, dec=**3** |
| piston_thickness | **мм**, шаг 2.5 | **м**, шаг **0.001**, dec=**3** |

**Вывод:** 5 параметров нужно конвертировать мм ? м!

### 6. ПНЕВМО-ТУМБЛЕРЫ: ? ОТСУТСТВУЮТ

**Отсутствующие контролы (panel_pneumo.py):**
- ? Тумблер "Стабилизатор ВКЛ/ВЫКЛ"
- ? Тумблер "Использовать ресивер"
- ? Параметр "Объём ресивера, л" (целое, 0-100, дефолт 20)

**Вывод:** Требуется 3 новых контрола в МШ-5!

### 7. АККОРДЕОН: ? НЕ ИСПОЛЬЗУЕТСЯ

```python
# src/ui/accordion.py - файл существует
class AccordionWidget(QScrollArea):
    """Accordion widget with multiple collapsible sections"""
    # ... реализация есть
```

```python
# src/ui/main_window.py - НЕ импортируется
# Accordion НЕ используется нигде в коде
```

**Вывод:** ? Аккордеон не используется (тест подтвердит)!

---

## ?? ЧЕКЛИСТ МИКРОШАГОВ

### МШ-1: Геометрия цилиндра ? НЕ НАЧАТ
- [ ] Убрать bore_head_slider, bore_rod_slider
- [ ] Добавить cyl_diam_m (единый диаметр)
- [ ] Добавить stroke_m (ход поршня)
- [ ] Добавить dead_gap_m (мёртвый зазор)
- [ ] Все новые: м, шаг 0.001, decimals 3
- [ ] Тесты: test_geometry_ui.py

### МШ-2: Единицы СИ ? НЕ НАЧАТ
- [ ] rod_diameter: мм ? м
- [ ] piston_rod_length: мм ? м
- [ ] piston_thickness: мм ? м
- [ ] Все линейные: шаг 0.001, decimals 3
- [ ] Пересчёт дефолтов (мм ? м)
- [ ] Тесты: test_steps_units.py

### МШ-3: Горизонтальный сплиттер ? НЕ НАЧАТ
- [ ] Создать QSplitter(Horizontal)
- [ ] objectName "split_main_h"
- [ ] Левая часть: MainSplitter (vertical)
- [ ] Правая часть: ParameterTabs
- [ ] Сохранение/восстановление через QSettings
- [ ] Тесты: test_layout_splitters.py

### МШ-4: Вкладки/прокрутка ? УЖЕ ЕСТЬ
- [x] Русские заголовки вкладок
- [x] QScrollArea в каждой вкладке
- [x] Отсутствие аккордеонов
- [ ] Тесты: test_tabs_scroll_ru.py

### МШ-5: Пневмо-тумблеры ? НЕ НАЧАТ
- [ ] Тумблер "Стабилизатор ВКЛ/ВЫКЛ"
- [ ] Тумблер "Использовать ресивер"
- [ ] Параметр "Объём ресивера, л"
- [ ] Тесты: test_pneumo_ui.py

### МШ-6: Сигналы/логирование ?? ЧАСТИЧНО ЕСТЬ
- [x] _on_geometry_changed существует
- [x] geometry_changed сигнал подключён
- [ ] Логирование изменений в logs/ui/ui_params.log
- [ ] Экспорт ui_state.json
- [ ] Тесты: test_signals_logging.py

### МШ-7: Финальные проверки ? НЕ НАЧАТ
- [ ] Сводный тест всех UI-параметров
- [ ] Отчёт summary_ui_post.md
- [ ] Тесты: test_final_ui_sweep.py

### МШ-8: Пост-аудит ? НЕ НАЧАТ
- [ ] audit_post.md
- [ ] tree_post.txt
- [ ] widget_tree_post.json
- [ ] diff_prompt_all_microsteps.patch
- [ ] Git commit + push

---

## ?? СТАТИСТИКА МШ-0

### Файлов проанализировано
- main_window.py: 776 строк
- panel_geometry.py: 500+ строк
- range_slider.py: 400+ строк
- accordion.py: 200+ строк

### Параметров найдено
- Всего линейных: 11
- В СИ (м): 6
- В мм: 5 ?
- Требуют изменений: 8

### Элементов UI
- Вкладок: 5 (3 активных + 2 заглушки)
- QScrollArea: 3 ?
- Сплиттеров: 1 (vertical) ?, 1 (horizontal) ?
- Аккордеонов: 0 ?

---

## ?? ГОТОВНОСТЬ К МШ-1

### Изменяемые файлы
1. `src/ui/panels/panel_geometry.py` - главный файл
2. `tests/ui/test_geometry_ui.py` - новый файл тестов

### Ожидаемые изменения
- ? Удалить: 2 слайдера (bore_head, bore_rod)
- ? Добавить: 3 слайдера (cyl_diam_m, stroke_m, dead_gap_m)
- ? Изменить: 5 слайдеров (мм ? м)
- ? Обновить: _set_default_values(), _connect_signals()

### Инструменты доступны
- ? RangeSlider виджет готов
- ? QGroupBox группировка готова
- ? Сигналы parameter_changed, geometry_updated готовы

---

## ?? СЛЕДУЮЩИЕ ДЕЙСТВИЯ

1. **МШ-1** (следующий):
   - Редактировать `panel_geometry.py`
   - Убрать bore_head/bore_rod
   - Добавить cyl_diam_m/stroke_m/dead_gap_m
   - Создать тесты

2. **МШ-2** (после МШ-1):
   - Конвертировать мм ? м
   - Обновить шаг/decimals
   - Пересчитать дефолты

3. **МШ-3** (после МШ-2):
   - Добавить горизонтальный сплиттер
   - QSettings для сохранения

---

**Аудит МШ-0 завершён:** 2025-10-05 23:00  
**Время выполнения:** 20 минут  
**Готовность к МШ-1:** ? 100%  

**Артефакты:**
- ? `reports/ui/audit_pre.md`
- ? `artifacts/ui/tree_pre.txt`
- ?? `artifacts/ui/widget_tree_pre.json` (не создан из-за ошибки)

?? **МОЖНО ПЕРЕХОДИТЬ К МШ-1!**
