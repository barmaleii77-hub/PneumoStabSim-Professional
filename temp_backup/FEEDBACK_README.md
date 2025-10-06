# ?? FEEDBACK README - Как работать с отчётами и логами

**Дата создания:** 2025-10-05 23:00  
**Промт:** Post-PROMPT#1 UI Fixes  
**Версия:** 1.0

---

## ?? ЧТО ТАКОЕ FEEDBACK?

Этот файл объясняет, где найти информацию о выполнении промта:
- Логи изменений
- Отчёты по микрошагам
- Результаты тестов
- Артефакты (дампы, патчи)

---

## ?? СТРУКТУРА ФАЙЛОВ

### 1. ОТЧЁТЫ (`reports/ui/`)

#### Пред-аудит (МШ-0)
```
reports/ui/audit_pre.md       - Детальный анализ ПЕРЕД изменениями
reports/ui/MS_0_COMPLETE.md   - Сводка МШ-0 (завершён)
```

**Что внутри:**
- Текущая структура UI
- Список параметров
- Найденные проблемы
- План изменений

#### Отчёты по МШ (МШ-1..МШ-7)
```
reports/ui/MS_1_COMPLETE.md   - Геометрия цилиндра
reports/ui/MS_2_COMPLETE.md   - Единицы СИ
reports/ui/MS_3_COMPLETE.md   - Горизонтальный сплиттер
reports/ui/MS_4_COMPLETE.md   - Вкладки/прокрутка
reports/ui/MS_5_COMPLETE.md   - Пневмо-тумблеры
reports/ui/MS_6_COMPLETE.md   - Сигналы/логирование
reports/ui/MS_7_COMPLETE.md   - Финальные проверки
```

**Что внутри каждого:**
- Что изменено
- Файлы затронуты
- Диффы кода
- Результаты тестов
- Ошибки (если были)

#### Пост-аудит (МШ-8)
```
reports/ui/audit_post.md      - Анализ ПОСЛЕ всех изменений
reports/ui/FINAL_SUMMARY.md   - Сводка ВСЕГО промта
```

**Что внутри:**
- Сравнение до/после
- Итоговый список изменений
- Все артефакты
- Инструкции по Git

---

### 2. АРТЕФАКТЫ (`artifacts/ui/`)

#### Дампы UI
```
artifacts/ui/tree_pre.txt          - Дерево виджетов ДО (текст)
artifacts/ui/widget_tree_pre.json  - Дерево виджетов ДО (JSON)
artifacts/ui/tree_post.txt         - Дерево виджетов ПОСЛЕ (текст)
artifacts/ui/widget_tree_post.json - Дерево виджетов ПОСЛЕ (JSON)
```

**Как читать:**
- Текстовые (.txt) - для визуального сравнения
- JSON (.json) - для программного анализа

#### Патчи и состояние
```
artifacts/ui/diff_prompt_all.patch - Полный патч всех изменений
artifacts/ui/ui_state.json         - Состояние UI (параметры)
```

**Как использовать:**
- `.patch` - можно применить через `git apply`
- `ui_state.json` - текущие значения всех UI-параметров

---

### 3. ЛОГИ (`logs/`)

#### UI логи
```
logs/ui/ui_params.log    - Изменения параметров UI (МШ-6+)
logs/ui/ui_events.log    - События UI (клики, изменения)
```

**Формат:**
```
2025-10-05 23:00:15 [INFO] Parameter changed: wheelbase 3.2 -> 3.5 м
2025-10-05 23:00:16 [INFO] geometry_changed signal emitted
```

#### Тестовые логи
```
logs/tests/test_smoke.log    - Smoke тесты
logs/tests/test_ui.log       - UI тесты
logs/tests/test_geometry.log - Тесты геометрии
```

**Формат:**
```
2025-10-05 23:00:20 [PASS] test_cylinder_diameter_units
2025-10-05 23:00:21 [FAIL] test_stroke_slider_range
   Expected: 0.100-0.500 м
   Got: 0.3-0.8 м
```

#### Логи сборки
```
logs/build/build.log    - Сборка проекта
logs/build/errors.log   - Ошибки компиляции
```

---

### 4. РЕЗУЛЬТАТЫ ТЕСТОВ (`reports/tests/`)

#### XML отчёты (JUnit)
```
reports/tests/smoke_test_results.xml
reports/tests/ui_tests_results.xml
reports/tests/geometry_tests_results.xml
```

**Как читать:**
- Открыть в IDE (VS Code, PyCharm)
- Или конвертировать в HTML

#### Markdown отчёты
```
reports/tests/smoke_test_report.md
reports/tests/ui_tests_report.md
reports/tests/final_test_report.md
```

**Формат:**
```markdown
# Test Report - МШ-1

## Summary
- Total tests: 15
- Passed: 13 ?
- Failed: 2 ?
- Skipped: 0

## Failed Tests
1. test_stroke_slider_range
   - Expected: 0.100-0.500 м
   - Got: 0.3-0.8 м
   - Fix: Update range in panel_geometry.py line 156
```

---

## ?? КАК НАЙТИ ИНФОРМАЦИЮ?

### Вопрос: "Какие файлы изменены?"

**Ответ:**
1. Открыть `reports/ui/MS_*_COMPLETE.md` для конкретного МШ
2. Раздел "Файлы для изменения"
3. Или смотреть `artifacts/ui/diff_prompt_all.patch`

### Вопрос: "Почему тест провалился?"

**Ответ:**
1. Открыть `logs/tests/test_*.log`
2. Найти строку с `[FAIL]`
3. Посмотреть Expected vs Got
4. Открыть соответствующий `reports/tests/*_report.md`

### Вопрос: "Как изменился параметр X?"

**Ответ:**
1. Открыть `logs/ui/ui_params.log`
2. Найти строки с `Parameter changed: X`
3. Или посмотреть `artifacts/ui/ui_state.json` - текущее значение

### Вопрос: "Что сделано в МШ-N?"

**Ответ:**
1. Открыть `reports/ui/MS_N_COMPLETE.md`
2. Раздел "Что сделано"
3. Раздел "Критерии успеха" - чеклист

### Вопрос: "Какие ошибки компиляции?"

**Ответ:**
1. Открыть `logs/build/errors.log`
2. Или запустить `py -m py_compile src/**/*.py`

---

## ?? ТЕСТЫ

### Как запустить тесты?

#### Smoke тесты (окружение)
```bash
python tests/smoke/test_env_build_qml.py
```

**Проверяет:**
- Версии Python, Qt, PySide6
- Импорты модулей
- Загрузку QML
- Структуру путей

#### UI тесты (конкретный МШ)
```bash
# МШ-1: Геометрия
python tests/ui/test_geometry_ui.py

# МШ-2: Единицы
python tests/ui/test_steps_units.py

# МШ-3: Сплиттеры
python tests/ui/test_layout_splitters.py

# Все UI тесты
python run_ui_tests.py
```

#### Комплексные тесты (весь промт)
```bash
python comprehensive_test_prompt1.py
```

---

## ?? КОНТРОЛЬНЫЙ ПЛАН

**Файл:** `reports/feedback/CONTROL_PLAN.md`

**Содержит:**
- Прогресс всех МШ
- Статус каждого МШ (? завершён, ? в работе, ?? ожидает)
- Критерии успеха
- Ожидаемые изменения

**Как читать:**
- Таблица МШ - общий прогресс
- Раздел конкретного МШ - детали

---

## ?? ЧАСТЫЕ ПРОБЛЕМЫ

### Проблема: "Файл логов не найден"

**Решение:**
1. Убедиться, что МШ выполнен полностью
2. Логи создаются в конце МШ
3. Проверить путь: `logs/ui/` или `logs/tests/`

### Проблема: "Тест провалился"

**Решение:**
1. Открыть `logs/tests/test_*.log`
2. Найти Expected vs Got
3. Исправить код
4. Запустить тест повторно
5. Проверить `reports/tests/*_report.md`

### Проблема: "Ошибка компиляции"

**Решение:**
1. Открыть `logs/build/errors.log`
2. Найти файл и строку с ошибкой
3. Исправить синтаксис
4. Запустить `py -m py_compile <файл>`
5. Проверить get_errors()

---

## ?? WORKFLOW

### Типичный цикл МШ:

1. **Начало МШ-N:**
   - Читать `reports/ui/MS_N_COMPLETE.md` (план)
   - Проверить "Критерии успеха"

2. **Во время работы:**
   - Изменять файлы
   - Логи автоматически пишутся в `logs/ui/`
   - Тесты запускаются после изменений

3. **После изменений:**
   - Запустить smoke тесты
   - Запустить UI тесты для МШ-N
   - Проверить `logs/tests/test_*.log`
   - Проверить `reports/tests/*_report.md`

4. **Завершение МШ-N:**
   - Обновить `reports/ui/MS_N_COMPLETE.md` (фактические результаты)
   - Обновить `reports/feedback/CONTROL_PLAN.md` (статус ? ?)
   - Создать `artifacts/ui/diff_ms_N.patch`

5. **Переход к МШ-(N+1):**
   - Повторить с шага 1

---

## ?? CHEAT SHEET

### Быстрый доступ к файлам:

| Что нужно | Файл |
|-----------|------|
| Что изменено в МШ-N? | `reports/ui/MS_N_COMPLETE.md` |
| Какие ошибки тестов? | `logs/tests/test_*.log` |
| Полный патч | `artifacts/ui/diff_prompt_all.patch` |
| Текущие параметры UI | `artifacts/ui/ui_state.json` |
| Дерево виджетов ДО | `artifacts/ui/tree_pre.txt` |
| Дерево виджетов ПОСЛЕ | `artifacts/ui/tree_post.txt` |
| План работ | `reports/feedback/CONTROL_PLAN.md` |
| Финальная сводка | `reports/ui/FINAL_SUMMARY.md` |

### Быстрые команды:

```bash
# Проверить логи тестов
cat logs/tests/test_ui.log | grep "FAIL"

# Проверить изменения параметров
cat logs/ui/ui_params.log | tail -20

# Запустить все UI тесты
python run_ui_tests.py

# Проверить ошибки компиляции
python -m py_compile src/ui/panels/panel_geometry.py
```

---

## ?? КОНТАКТЫ / ПОМОЩЬ

**Если что-то непонятно:**
1. Прочитать этот README
2. Открыть `reports/feedback/CONTROL_PLAN.md`
3. Проверить логи в `logs/`
4. Создать issue с указанием:
   - МШ номер
   - Файл и строка
   - Сообщение об ошибке

---

**Обновлено:** 2025-10-05 23:00  
**Следующий МШ:** МШ-1 (Геометрия цилиндра)  
**Готовность:** ? 100%

?? **ВСЁ ГОТОВО ДЛЯ РАБОТЫ!**
