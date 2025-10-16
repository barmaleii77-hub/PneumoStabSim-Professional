# 🔧 IBL FLAGS INDEPENDENCE FIX v4.9.5

## Проблема

При переключении **Master IBL checkbox** автоматически копировалось значение в подчинённые флаги `iblLightingEnabled` и `iblBackgroundEnabled`, что **нарушало независимость** управления освещением и фоном.

### Симптомы

1. ✅ Включаем **Master IBL** → включается освещение ✅
2. ⚠️ Выключаем **IBL Lighting** → освещение выключается ✅
3. ❌ Выключаем **Master IBL** → **освещение снова включается** ❌ (неожиданное поведение!)

### Причина

В функции `applyEnvironmentUpdates()` при обработке `ibl_enabled` или `ibl.enabled` автоматически переприсваивалось значение:

```qml
// ❌ НЕПРАВИЛЬНО (было):
if (params.ibl_enabled !== undefined) {
    iblEnabled = !!params.ibl_enabled
    iblLightingEnabled = iblEnabled  // <-- Автоматическое копирование!
}
```

Это **ломало независимость** флагов.

---

## Решение

### Изменения в `assets/qml/main.qml`

#### 1. **Инициализация флагов (строка ~236)**

```qml
// ✅ CRITICAL FIX v4.9.5: НЕЗАВИСИМОЕ начальное значение для iblLightingEnabled!
// НЕ копируем startIblEnabled - пусть каждый флаг независим с самого начала!
property bool iblLightingEnabled: true   // По умолчанию ВКЛ (независимо от master)
property bool iblBackgroundEnabled: startSkyboxEnabled
```

**Было:** `iblLightingEnabled: startIblEnabled` — копировалось из master флага  
**Стало:** `iblLightingEnabled: true` — независимое значение по умолчанию

#### 2. **Функция `applyEnvironmentUpdates()` (строка ~636)**

##### a) Плоские ключи (backward compatibility)

```qml
// ✅ КРИТИЧНО: Master флаг НЕ влияет на подфлаги
if (params.ibl_enabled !== undefined) {
    iblEnabled = !!params.ibl_enabled
    console.log("  🔧 IBL master enabled обновлен:", iblEnabled)
    // ❌ УДАЛЕНО: iblLightingEnabled = iblEnabled
    // Каждый флаг теперь полностью независим
}

// ✅ Раздельное управление
if (params.ibl_lighting_enabled !== undefined) {
    iblLightingEnabled = !!params.ibl_lighting_enabled
    console.log("  💡 IBL lighting обновлен:", iblLightingEnabled)
}

if (params.ibl_background_enabled !== undefined) {
    iblBackgroundEnabled = !!params.ibl_background_enabled
    console.log("  🎨 IBL background обновлен:", iblBackgroundEnabled)
}
```

##### b) Вложенная структура (nested)

```qml
if (params.ibl) {
    const ibl = params.ibl
    
    // ✅ Master флаг больше НЕ влияет на подфлаги!
    if (ibl.enabled !== undefined) {
        iblEnabled = !!ibl.enabled
        console.log("  🔧 IBL master (nested) обновлен:", iblEnabled)
        // ❌ КРИТИЧНО: НЕ переопределяем lighting/background!
    }
    
    // ✅ Независимое управление
    if (ibl.lighting_enabled !== undefined) {
        iblLightingEnabled = !!ibl.lighting_enabled
        console.log("  💡 IBL lighting (nested) обновлен:", iblLightingEnabled)
    }
    
    if (ibl.background_enabled !== undefined) {
        iblBackgroundEnabled = !!ibl.background_enabled
        console.log("  🎨 IBL background (nested) обновлен:", iblBackgroundEnabled)
    }
}
```

#### 3. **Детальный лог состояния**

Добавлен подробный лог ДО и ПОСЛЕ обновления для диагностики:

```qml
function applyEnvironmentUpdates(params) {
    // ✅ ДО обновления
    console.log("🌍 ═══ applyEnvironmentUpdates START ═══")
    console.log("  📥 Входные параметры:", JSON.stringify(params))
    console.log("  📊 ТЕКУЩЕЕ состояние ДО обновления:")
    console.log("     iblEnabled:", iblEnabled)
    console.log("     iblLightingEnabled:", iblLightingEnabled)
    console.log("     iblBackgroundEnabled:", iblBackgroundEnabled)
    
    // ... обработка параметров ...
    
    // ✅ ПОСЛЕ обновления
    console.log("  📊 ФИНАЛЬНОЕ состояние ПОСЛЕ обновления:")
    console.log("     iblEnabled:", iblEnabled)
    console.log("     iblLightingEnabled:", iblLightingEnabled)
    console.log("     iblBackgroundEnabled:", iblBackgroundEnabled)
    console.log("🌍 ═══ applyEnvironmentUpdates END ═══")
}
```

---

## Результат

### ✅ Теперь флаги **полностью независимы**

1. **Master IBL** (`iblEnabled`) — общий флаг доступности IBL системы
2. **IBL Lighting** (`iblLightingEnabled`) — управляет ТОЛЬКО освещением от IBL
3. **IBL Background** (`iblBackgroundEnabled`) — управляет ТОЛЬКО отображением skybox

Каждый флаг можно включать/выключать **независимо** без влияния друг на друга.

### 🧪 Тестирование

**Тестовый сценарий:**

```python
# 1. Включаем Master IBL
panel.ibl_enabled_check.setChecked(True)
# → iblEnabled = True
# → iblLightingEnabled БЕЗ ИЗМЕНЕНИЙ (остается прежним)
# → iblBackgroundEnabled БЕЗ ИЗМЕНЕНИЙ (остается прежним)

# 2. Выключаем IBL Lighting
panel.ibl_lighting_check.setChecked(False)
# → iblLightingEnabled = False
# → iblEnabled БЕЗ ИЗМЕНЕНИЙ
# → iblBackgroundEnabled БЕЗ ИЗМЕНЕНИЙ

# 3. Выключаем Master IBL
panel.ibl_enabled_check.setChecked(False)
# → iblEnabled = False
# → iblLightingEnabled БЕЗ ИЗМЕНЕНИЙ (остается False!)
# → iblBackgroundEnabled БЕЗ ИЗМЕНЕНИЙ
```

---

## Файлы изменены

- `assets/qml/main.qml`:
  - Строка ~236: Независимая инициализация `iblLightingEnabled`
  - Строка ~636: Полное переписывание `applyEnvironmentUpdates()`
  - Добавлены детальные логи состояния

---

## Совместимость

✅ **Backward compatibility сохранена:**
- Поддерживаются плоские ключи (`ibl_enabled`, `ibl_lighting_enabled`, и т.д.)
- Поддерживается вложенная структура (`params.ibl.enabled`, `params.ibl.lighting_enabled`, и т.д.)

✅ **Безопасность:**
- Каждый флаг проверяется на `undefined` перед применением
- Используется `!!` для явного преобразования в boolean

---

## Версия

**v4.9.5** - IBL Flags Independence Fix  
**Дата:** 2024  
**Автор:** GitHub Copilot (AI Assistant)

---

## Следующие шаги

1. ✅ **Запустить приложение** с новым кодом
2. ✅ **Проверить логи** в консоли при переключении чекбоксов
3. ✅ **Убедиться** что флаги НЕ влияют друг на друга
4. ✅ **Проверить диагностику** `analyze_logs.py` на предмет рассинхрона

---

**🚀 Статус:** ИСПРАВЛЕНО ✅  
**📝 Требуется тестирование:** ДА (необходим перезапуск приложения)
