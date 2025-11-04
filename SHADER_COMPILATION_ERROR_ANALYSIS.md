# Детальный анализ ошибок компиляции шейдеров (без рекомендаций)

## 1. Структура ошибок компиляции шейдеров

### 1.1 Общее количество
- Всего строк с `ERROR`: 108
- Уникальных ошибок компиляции: 36 (по сообщениям `2 compilation errors`)
- Реальных failed shader compilations: 36 (18 повторов × 2)

### 1.2 Распределение по типам шейдеров
```
Fragment shaders: 30 ошибок (83.3%)
Vertex shaders:    6 ошибок (16.7%)
```

### 1.3 Распределение по строкам кода (ERROR line numbers)
```
Строка 38:  24 ошибки (33.3%)
Строка 34:  12 ошибок (16.7%)
Строка 35:  12 ошибок (16.7%)
Строка 60:  12 ошибок (16.7%)
Строка 76:  12 ошибок (16.7%)
```

## 2. Тип ошибки: `qt_customMain` not found

### 2.1 Паттерн
```
Failed to compile [fragment|vertex] shader: 
ERROR: :[line_number]: 'qt_customMain' : no matching overloaded function found
ERROR: :[line_number]: '' : compilation terminated
ERROR: 2 compilation errors.  No code generated.
```

### 2.2 Частота
- Каждая ошибка повторяется дважды (два прохода компиляции Qt RHI)
- Временной диапазон: 16:48:16 – 16:48:17 (1 секунда)

## 3. Shader resolution (какие шейдеры загружаются)

### 3.1 Успешно resolved shaders
```
Desktop shader 'bloom.frag' → 'bloom.frag'
Desktop shader 'bloom_fallback.frag' → 'bloom_fallback.frag'
Desktop shader 'ssao.frag' → 'ssao.frag'
Desktop shader 'ssao_fallback.frag' → 'ssao_fallback.frag'
Desktop shader 'dof.frag' → 'dof.frag'
Desktop shader 'dof_fallback.frag' → 'dof_fallback.frag'
Desktop shader 'motion_blur.frag' → 'motion_blur.frag'
Desktop shader 'motion_blur_fallback.frag' → 'motion_blur_fallback.frag'
Desktop shader 'fog.vert' → 'fog.vert'
Desktop shader 'fog.frag' → 'fog.frag'
Desktop shader 'fog_fallback.frag' → 'fog_fallback.frag'
```

### 3.2 Shader resolution profile
- Используемый профиль: Desktop (не GLES)
- Директория поиска: `../../shaders/effects/` (единая директория для всех профилей после миграции)

## 4. Shader availability check failures

### 4.1 Ошибки доступности (Invalid state)
```
motion_blur_core.frag (HEAD) – Invalid state
motion_blur_core.frag (GET) – Invalid state
motion_blur.frag (HEAD) – Invalid state
motion_blur.frag (GET) – Invalid state
dof_fallback_glsl450.frag (HEAD/GET) – Invalid state
dof_fallback_desktop.frag (HEAD/GET) – Invalid state
dof_fallback_core.frag (HEAD/GET) – Invalid state
```

### 4.2 Manifest mismatch errors

*(устранено после объединения шейдеров в `effects/`; записи `post_effects/` больше не фигурируют в манифесте и предупреждения не появляются).* 

## 5. Effect pipeline hashes
```
DEFAULT>:fca02b85997f4af4ac5f493d12a38a23084a249e:1:0
DEFAULT>:360c8262680cb26928e444db30aa772f3e09894b:1:0
DEFAULT>:cb3e62544d13ae9084cf88fd3f3dbd86a40068e7:1:0
DEFAULT>:5fca73276dc57be376f00d097080c7207685e641:1:0
>:331ac8d667de7bebab584c6ff10ae477bf864e4d:1:0
```

Интерпретация:
- `DEFAULT>` – используется vertex shader по умолчанию
- Hash – SHA1-отпечаток скомпилированного shader code
- `:1:0` – индексы variant:pass

## 6. Временная последовательность ошибок
```
16:48:14 – Shader resolution (11 успешных)
16:48:14 – Shader availability checks (множественные Invalid state)
16:48:14 – Manifest mismatch warnings
16:48:16 – Первая волна компиляций (18 ошибок qt_customMain)
16:48:17 – Вторая волна компиляций (18 повторов тех же ошибок)
```

## 7. Проблема: директории шейдеров

### 7.1 Текущий порядок поиска
```
1. ../../shaders/effects/       (единый каталог для desktop и GLES)
2. Legacy fallback              (архивные GLSL 330 варианты)
```

### 7.2 Консолидация ресурсов
- Все `_es` и `_fallback_es` файлы перенесены в `effects/`, что исключает расхождения между профилями.
- Манифест больше не содержит ссылок на `post_effects/`, поэтому Qt не пытается загрузить дубликаты.
- Проверка `shaderVariantMissingWarnings` корректно сигнализирует только о реальных пропущенных файлах.

### 7.3 Историческая справка
- Ранее `post_effects/` содержал исправленные GLES-шейдеры, но Qt отдавал приоритет `effects/`, вызывая предупреждения о mismatch.
- После переноса файлы из `post_effects/` удалены, а ссылки обновлены на новый путь.

## 8. Статистика успешности
```
Шейдеров resolved:        11 (100%)
Шейдеров загружено:       11 (100%)
Шейдеров скомпилировано:   0 (0%)
Шейдеров с ошибками:      11 (100%)
```

## 9. Корреляция: номера строк → типы шейдеров

### Строка 38 (24 ошибки)
- Тип: Fragment shader
- Вероятный файл: `bloom.frag` или `ssao.frag`

### Строка 76 (12 ошибок)
- Тип: Vertex shader
- Вероятный файл: `fog.vert`

### Строки 34, 35, 60 (по 12 ошибок)
- Тип: Fragment shaders
- Вероятные файлы: `dof.frag`, `motion_blur.frag`, `ssao.frag`

## 10. Финальная сводка

| Метрика | Значение |
|---------|----------|
| Всего ошибок в логе | 108 строк |
| Уникальных компиляций | 18 |
| Повторов | 2× каждая |
| Fragment shader fails | 30 |
| Vertex shader fails | 6 |
| Используемая директория | `effects/` (объединённая) |
| Игнорируемая директория | *(нет; `post_effects/` удалена)* |
| Тип ошибки | `qt_customMain` not found (исторический отчёт) |
| Причина | До миграции Desktop profile загружал старые шейдеры из `effects/` с устаревшим `#define MAIN main` |
| Эффекты | Все используют fallback shaders |
| Функциональность | Приложение работает, эффекты деградированы |
