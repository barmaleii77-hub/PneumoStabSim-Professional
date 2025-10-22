# 🔍 ДИАГНОСТИКА: ExtendedSceneEnvironment - Переопределение дефолтов

## Проблема

Вы подозреваете, что **`ExtendedSceneEnvironment` может переопределять дефолтные свойства** Qt, что может вызывать рассинхронизацию IBL/AA настроек.

---

## Гипотеза

**ExtendedSceneEnvironment** (из `QtQuick3D.Helpers`) расширяет стандартный `SceneEnvironment` и может устанавливать **свои дефолтные значения** для:

- `antialiasingMode`
- `antialiasingQuality`
- `tonemapMode`
- `glowEnabled`
- `aoEnabled`
- и других свойств...

Если дефолты **отличаются** от стандартного `SceneEnvironment`, это может объяснить, почему:

1. ✅ Python отправляет правильные параметры
2. ✅ QML функции вызываются (EVENTS sync = OK)
3. ❌ Но настройки НЕ применяются (ExtendedSceneEnvironment переопределяет их)

---

## Тест

Создан специальный тестовый файл для **сравнения дефолтов**:

### Файлы

1. **`test_extended_vs_standard_scene_environment.qml`** - QML тест с двумя View3D:
   - **Левая половина** - `SceneEnvironment` (стандартный)
   - **Правая половина** - `ExtendedSceneEnvironment`

2. **`test_extended_scene_environment.py`** - Python запускатор теста

### Запуск

```bash
python test_extended_scene_environment.py
```

### Что проверяем

Тест выводит в консоль **дефолтные значения** для обоих типов:

```javascript
STANDARD SceneEnvironment:
  backgroundMode: ...
  clearColor: ...
  antialiasingMode: ???    // <-- Проверяем!
  antialiasingQuality: ??? // <-- Проверяем!

EXTENDED SceneEnvironment:
  backgroundMode: ...
  clearColor: ...
  antialiasingMode: ???    // <-- Сравниваем!
  antialiasingQuality: ??? // <-- Сравниваем!
  glowEnabled: ???         // <-- Доп. свойства
  aoEnabled: ???
  tonemapMode: ???
  ...
```

---

## Интерпретация результатов

### ✅ Если дефолты ОДИНАКОВЫЕ

```
STANDARD antialiasingMode: 0 (NoAA)
EXTENDED antialiasingMode: 0 (NoAA)
```

**Вывод:** ExtendedSceneEnvironment **безопасен**, не переопределяет дефолты.

**Действие:** Ищем проблему в другом месте (биндинги, порядок обновлений и т.д.)

---

### ❌ Если дефолты РАЗНЫЕ

```
STANDARD antialiasingMode: 0 (NoAA)
EXTENDED antialiasingMode: 2 (MSAA)  // <-- Переопределение!
```

**Вывод:** ExtendedSceneEnvironment **переопределяет дефолты!**

**Действие:** Исправить проблему одним из способов:

#### **Вариант 1: Явное задание всех свойств**

```qml
environment: ExtendedSceneEnvironment {
    // ✅ Явно задаём ВСЕ важные свойства
    antialiasingMode: root.aaPrimaryMode === "ssaa" ? SceneEnvironment.SSAA :
                     root.aaPrimaryMode === "msaa" ? SceneEnvironment.MSAA :
                     SceneEnvironment.NoAA

    antialiasingQuality: root.aaQualityLevel === "high" ? SceneEnvironment.High :
                        root.aaQualityLevel === "medium" ? SceneEnvironment.Medium :
                        SceneEnvironment.Low

    // И все остальные...
}
```

**Проблема:** Дефолты ExtendedSceneEnvironment могут **обнулиться при обновлении** свойств.

#### **Вариант 2: Вернуться к SceneEnvironment**

```qml
// ❌ БЫЛО (может переопределять):
environment: ExtendedSceneEnvironment {
    ...
}

// ✅ СТАЛО (стандартное поведение):
environment: SceneEnvironment {
    // Только базовые свойства, без расширенных эффектов
    backgroundMode: ...
    clearColor: ...
    antialiasingMode: ...
    antialiasingQuality: ...
    // Эффекты добавляем вручную через другие механизмы
}
```

**Недостаток:** Теряем доступ к расширенным эффектам (bloom, vignette, lens flare и т.д.)

#### **Вариант 3: Гибридный подход**

```qml
environment: ExtendedSceneEnvironment {
    // ✅ Биндинг ВСЕХ свойств через Qt.binding()
    Component.onCompleted: {
        // Антиалиасинг
        antialiasingMode = Qt.binding(() => {
            if (root.aaPrimaryMode === "ssaa") return SceneEnvironment.SSAA
            if (root.aaPrimaryMode === "msaa") return SceneEnvironment.MSAA
            return SceneEnvironment.NoAA
        })

        antialiasingQuality = Qt.binding(() => {
            if (root.aaQualityLevel === "high") return SceneEnvironment.High
            if (root.aaQualityLevel === "medium") return SceneEnvironment.Medium
            return SceneEnvironment.Low
        })

        // Эффекты
        glowEnabled = Qt.binding(() => root.bloomEnabled)
        aoEnabled = Qt.binding(() => root.ssaoEnabled)
        tonemapMode = Qt.binding(() => root.tonemapMode)

        // IBL
        lightProbe = Qt.binding(() => (root.iblLightingEnabled && root.iblReady) ? iblLoader.probe : null)

        // И так далее для ВСЕХ свойств...
    }
}
```

**Преимущество:** Биндинги **НИКОГДА** не теряются, даже если ExtendedSceneEnvironment переопределяет дефолты.

---

## Примеры из документации Qt

### **ExtendedSceneEnvironment - ПРАВИЛЬНОЕ использование**

Из документации Qt Quick 3D Helpers:

```qml
import QtQuick3D.Helpers

View3D {
    environment: ExtendedSceneEnvironment {
        // ⚠️ ВАЖНО: Все свойства должны быть явно заданы!
        backgroundMode: SceneEnvironment.Color
        clearColor: "#000000"

        // Антиалиасинг - ВСЕГДА задавайте явно
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: SceneEnvironment.High

        // Эффекты - задавайте явно
        tonemapMode: SceneEnvironment.TonemapModeFilmic
        glowEnabled: true
        aoEnabled: true

        // ✅ Или используйте биндинги для динамических значений
        Component.onCompleted: {
            tonemapMode = Qt.binding(() => myTonemapMode)
        }
    }
}
```

---

## Рекомендации

### 1. **Запустите тест**
```bash
python test_extended_scene_environment.py
```

### 2. **Проверьте консоль**
- Сравните `antialiasingMode` и `antialiasingQuality`
- Проверьте доп. свойства (`glowEnabled`, `aoEnabled`, и т.д.)

### 3. **Если дефолты разные:**
- Используйте **Вариант 3 (Qt.binding)** для надёжности
- Или перейдите на **Вариант 2 (SceneEnvironment)** для простоты

### 4. **Если дефолты одинаковые:**
- Проблема НЕ в ExtendedSceneEnvironment
- Ищите в другом месте (порядок обновлений, батч-обновления и т.д.)

---

## Связанные файлы

- `assets/qml/main.qml` - строка 1212 (environment: ExtendedSceneEnvironment)
- `src/ui/panels/panel_graphics.py` - отправка параметров в QML
- `docs/EXTENDED_SCENE_ENVIRONMENT_GUIDE.md` - гайд по использованию

---

## Статус

**🧪 Тест готов к запуску**

Запустите тест и проверьте результаты, чтобы подтвердить или опровергнуть гипотезу.

---

**Дата:** 2024
**Версия:** 1.0
**Автор:** GitHub Copilot (AI Assistant)
