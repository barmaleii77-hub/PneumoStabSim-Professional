# ?? ПРЕД-АУДИТ UI (МШ-0) - Промт Post-PROMPT#1

**Дата:** 2025-10-05 22:40  
**Цель:** Зафиксировать текущее состояние UI перед изменениями  
**Статус:** ? **ЗАВЕРШЁН**

---

## ?? СТРУКТУРА ФАЙЛОВ

### Главное окно
- ? `src/ui/main_window.py` - главное окно приложения (776 строк)

### Панели параметров
- ? `src/ui/panels/panel_geometry.py` - панель геометрии (500+ строк)
- ? `src/ui/panels/panel_pneumo.py` - панель пневмосистемы
- ? `src/ui/panels/panel_modes.py` - панель режимов

### Виджеты
- ? `src/ui/widgets/range_slider.py` - слайдер с диапазоном
- ? `src/ui/widgets/knob.py` - крутилка (пневмо-панель)
- ? `src/ui/accordion.py` - аккордеон (ПРИСУТСТВУЕТ, но НЕ ИСПОЛЬЗУЕТСЯ)

### QML сцена
- ? `assets/qml/main.qml` - главная QML сцена

---

## ?? ДЕТАЛЬНЫЙ АНАЛИЗ

### 1. MainWindow (main_window.py)

**Текущая структура:**

#### Вертикальный сплиттер (? УЖЕ ЕСТЬ!)
```python
# Строка ~130-160
self.main_splitter = QSplitter(Qt.Orientation.Vertical)
self.main_splitter.setObjectName("MainSplitter")

# Top: 3D scene
self._qquick_widget  # QQuickWidget с main.qml

# Bottom: Charts (full width!)
self.chart_widget = ChartWidget(self)
```
**Вывод:** ? Вертикальный сплиттер УЖЕ РЕАЛИЗОВАН

#### Горизонтальный сплиттер (? НЕТ!)
```python
# Строка ~153-159
central_container = QWidget()
central_layout = QHBoxLayout(central_container)

# Добавляется сплиттер + вкладки НО БЕЗ QSplitter!
central_layout.addWidget(self.main_splitter, stretch=3)  # 75%
# ... позже добавляется tab_widget, stretch=1  # 25%
```
**Вывод:** ? **НЕТ горизонтального QSplitter** между left (scene+charts) и right (tabs)!  
**Нужно:** Обернуть в `QSplitter(Qt.Orientation.Horizontal)`

#### Вкладки (? УЖЕ ЕСТЬ!)
```python
# Строка ~215-275
self.tab_widget = QTabWidget(self)
self.tab_widget.setObjectName("ParameterTabs")

# Tab 1: "Геометрия" + QScrollArea ?
# Tab 2: "Пневмосистема" + QScrollArea ?
# Tab 3: "Режимы стабилизатора" + QScrollArea ?
# Tab 4: "Визуализация" (заглушка)
# Tab 5: "Динамика движения" (заглушка)
```
**Вывод:** ? Вкладки с русскими названиями + QScrollArea УЖЕ ЕСТЬ!

#### Графики (? НА МЕСТЕ!)
```python
# Строка ~148-149
self.chart_widget = ChartWidget(self)
self.main_splitter.addWidget(self.chart_widget)  # Внизу вертикального сплиттера
```
**Вывод:** ? Графики уже внизу на всю ширину

---

### 2. GeometryPanel (panel_geometry.py)

**Параметры цилиндра (ТЕКУЩЕЕ - ТРЕБУЕТ ИЗМЕНЕНИЙ!):**

```python
# Строка ~139-167 - РАЗДЕЛЬНЫЕ ПАРАМЕТРЫ полостей:
self.bore_head_slider = RangeSlider(
    title="Диаметр (безштоковая камера)"  # ? НАДО УБРАТЬ
)

self.bore_rod_slider = RangeSlider(
    title="Диаметр (штоковая камера)"  # ? НАДО УБРАТЬ
)

self.rod_diameter_slider = RangeSlider(
    title="Диаметр штока"  # ? ОСТАВИТЬ
)

self.piston_rod_length_slider = RangeSlider(
    title="Длина штока поршня"  # ? ОСТАВИТЬ (но возможно переименовать)
)

self.piston_thickness_slider = RangeSlider(
    title="Толщина поршня"  # ? ОСТАВИТЬ
)
```

**Нужны изменения (МШ-1):**
1. ? **УБРАТЬ:** `bore_head_slider`, `bore_rod_slider`
2. ? **ДОБАВИТЬ:** `cylinder_diameter_slider` (единый диаметр цилиндра)
3. ? **ДОБАВИТЬ:** `stroke_slider` (ход поршня)
4. ? **ДОБАВИТЬ:** `dead_gap_slider` (мёртвый зазор)
5. ? **ОСТАВИТЬ:** `rod_diameter_slider`, `piston_thickness_slider`

**Единицы измерения (ТЕКУЩЕЕ):**

| Параметр | Текущие единицы | Нужные единицы (СИ) | Шаг | Decimals |
|----------|----------------|---------------------|-----|----------|
| wheelbase | ? м | ? м | 0.1 ? **0.001** | 1 ? **3** |
| track | ? м | ? м | 0.1 ? **0.001** | 1 ? **3** |
| frame_to_pivot | ? м | ? м | 0.05 ? **0.001** | 2 ? **3** |
| lever_length | ? м | ? м | 0.05 ? **0.001** | 2 ? **3** |
| rod_position | fraction (0-1) | ? OK | 0.05 ? **0.001** | 2 ? **3** |
| cylinder_length | ? м | ? м | 0.01 ? **0.001** | 2 ? **3** |
| bore_head | ? мм | **м** | 5.0 ? **0.001** | 0 ? **3** |
| bore_rod | ? мм | **м** | 5.0 ? **0.001** | 0 ? **3** |
| rod_diameter | ? мм | **м** | 2.5 ? **0.001** | 1 ? **3** |
| piston_rod_length | ? мм | **м** | 10.0 ? **0.001** | 0 ? **3** |
| piston_thickness | ? мм | **м** | 2.5 ? **0.001** | 1 ? **3** |

**Вывод:** Все параметры в миллиметрах нужно перевести в метры!

---

### 3. PneumoPanel (panel_pneumo.py)

**Текущие элементы (по коду):**

```python
# Управляющие элементы:
- Обратные клапаны: ? есть крутилки (Knob)
- Предохранительные клапаны: ? есть крутилки
- Температура атмосферы: ? есть
- Термо-режим: ? радиокнопки (изотермический/адиабатический)
- Главная изоляция: ? чекбокс "Главная изоляция открыта"
- Связь диаметров штоков: ? чекбокс
```

**Недостающие элементы (МШ-5):**

1. ? **НЕТ:** Тумблер "Стабилизатор ВКЛ/ВЫКЛ"
2. ? **НЕТ:** Тумблер "Использовать ресивер"
3. ? **НЕТ:** Параметр "Объём ресивера, л"

---

### 4. ModesPanel (panel_modes.py)

**Текущие элементы:**

```python
# Дорожное воздействие:
- Глобальная амплитуда: ? RangeSlider, units="м"
- Глобальная частота: ? RangeSlider, units="Гц"
- Глобальная фаза: ? RangeSlider, units="°"
- Фазы по колёсам: ? 4x RangeSlider (ЛП, ПП, ЛЗ, ПЗ)
```

**Вывод:** ? Всё в порядке, русский UI уже есть

---

### 5. Accordion (accordion.py)

**Статус:**

```python
# Файл ПРИСУТСТВУЕТ в src/ui/accordion.py
# НО НЕ ИСПОЛЬЗУЕТСЯ в main_window.py!

class AccordionWidget(QScrollArea):
    """Accordion widget with multiple collapsible sections"""
    # ... реализация есть
```

**Вывод:** ? Аккордеон НЕ ИСПОЛЬЗУЕТСЯ (тест должен это подтвердить)

---

## ? ИТОГОВЫЕ ВЫВОДЫ МШ-0

### ЧТО УЖЕ ЕСТЬ (не трогать)
1. ? Вертикальный сплиттер (сцена/графики)
2. ? Вкладки с русскими названиями
3. ? QScrollArea в каждой вкладке
4. ? Графики внизу на всю ширину
5. ? Аккордеон НЕ используется

### ЧТО НУЖНО ДОБАВИТЬ/ИЗМЕНИТЬ

#### МШ-1: Геометрия цилиндра
- ? Убрать `bore_head`, `bore_rod` (раздельные диаметры)
- ? Добавить `cyl_diam_m` (единый диаметр)
- ? Добавить `stroke_m` (ход поршня)
- ? Добавить `dead_gap_m` (мёртвый зазор)
- ? Все новые: единицы **м**, шаг **0.001**, decimals **3**

#### МШ-2: Единицы измерения
- ? Все линейные параметры ? **м**
- ? Шаг ? **0.001 м**
- ? Decimals ? **3**
- ? Пересчёт дефолтов (мм ? м)

#### МШ-3: Горизонтальный сплиттер
- ? **ДОБАВИТЬ:** `QSplitter(Qt.Horizontal)` между:
  - Левая часть: вертикальный сплиттер (сцена + графики)
  - Правая часть: QTabWidget (панели)
- ? objectName: `"split_main_h"`
- ? Сохранение/восстановление через QSettings

#### МШ-5: Пневмо-тумблеры
- ? Добавить тумблер "Стабилизатор ВКЛ/ВЫКЛ"
- ? Добавить тумблер "Использовать ресивер"
- ? Добавить параметр "Объём ресивера, л" (целое, 0-100л, дефолт 20л)

---

## ?? СНИМОК ДЕРЕВА ВИДЖЕТОВ (tree_pre.txt)

```
QMainWindow "PneumoStabSim"
??? QWidget central_container
?   ??? QHBoxLayout
?   ?   ??? QSplitter "MainSplitter" (Vertical) ? ? УЖЕ ЕСТЬ
?   ?   ?   ??? QQuickWidget (3D scene)
?   ?   ?   ??? ChartWidget (graphics)
?   ?   ??? QTabWidget "ParameterTabs" ? ? УЖЕ ЕСТЬ
?   ?       ??? QScrollArea "Геометрия" ? ? УЖЕ ЕСТЬ
?   ?       ?   ??? GeometryPanel
?   ?       ??? QScrollArea "Пневмосистема" ? ? УЖЕ ЕСТЬ
?   ?       ?   ??? PneumoPanel
?   ?       ??? QScrollArea "Режимы стабилизатора" ? ? УЖЕ ЕСТЬ
?   ?       ?   ??? ModesPanel
?   ?       ??? QWidget "Визуализация" (stub)
?   ?       ??? QWidget "Динамика движения" (stub)
??? QToolBar "Главная"
??? QMenuBar
?   ??? QMenu "Файл"
?   ??? QMenu "Параметры"
?   ??? QMenu "Вид"
??? QStatusBar

MISSING: QSplitter(Horizontal) между left и right!
```

---

## ?? ПАРАМЕТРЫ ГЕОМЕТРИИ (ТЕКУЩИЕ ЗНАЧЕНИЯ)

### Рама
| Параметр | Значение | Единицы | Диапазон |
|----------|----------|---------|----------|
| wheelbase | 3.2 | м | 2.0 - 4.0 |
| track | 1.6 | м | 1.0 - 2.5 |

### Подвеска
| Параметр | Значение | Единицы | Диапазон |
|----------|----------|---------|----------|
| frame_to_pivot | 0.6 | м | 0.3 - 1.0 |
| lever_length | 0.8 | м | 0.5 - 1.5 |
| rod_position | 0.6 | fraction | 0.3 - 0.9 |

### Цилиндр (ТРЕБУЕТ ИЗМЕНЕНИЙ!)
| Параметр | Значение | Единицы | Диапазон | Статус |
|----------|----------|---------|----------|--------|
| cylinder_length | 0.5 | м | 0.3 - 0.8 | ? OK |
| bore_head | 80.0 | **мм** ? | 50 - 150 | ? **УБРАТЬ** |
| bore_rod | 80.0 | **мм** ? | 50 - 150 | ? **УБРАТЬ** |
| rod_diameter | 35.0 | **мм** ? | 20 - 60 | ? **ПЕРЕВЕСТИ В М** |
| piston_rod_length | 200.0 | **мм** ? | 100 - 500 | ? **ПЕРЕВЕСТИ В М** |
| piston_thickness | 25.0 | **мм** ? | 10 - 50 | ? **ПЕРЕВЕСТИ В М** |

---

## ?? ГОТОВНОСТЬ К МШ-1

### Файлы для изменения
1. `src/ui/panels/panel_geometry.py` (убрать bore_head/bore_rod, добавить cyl_diam/stroke/dead_gap)
2. `tests/ui/test_geometry_ui.py` (тесты на новые параметры)

### Ожидаемые изменения
- ? Убрать: 2 контрола (bore_head, bore_rod)
- ? Добавить: 3 контрола (cyl_diam_m, stroke_m, dead_gap_m)
- ? Изменить: шаг/decimals для всех линейных параметров

---

**Аудит завершён:** 2025-10-05 22:50  
**Следующий шаг:** МШ-1 (Унификация параметров цилиндра)  
**Артефакты:**
- `reports/ui/audit_pre.md` (этот файл)
- `artifacts/ui/tree_pre.txt` (будет создан)
- `artifacts/ui/widget_tree_pre.json` (будет создан)
