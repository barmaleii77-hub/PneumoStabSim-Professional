# ⚡ QUICK START: Полное логирование UI событий

## 🎯 Цель
Логировать **ВСЕ** действия пользователя в Python и QML для анализа синхронизации.

---

## 📦 Что создано

| Файл | Описание |
|------|----------|
| `src/common/event_logger.py` | ✅ Unified EventLogger (Singleton) |
| `src/common/logging_widgets.py` | ✅ Wrappers для QCheckBox, QComboBox |
| `src/common/logging_slider_wrapper.py` | ✅ Wrapper для LabeledSlider |
| `assets/qml/components/MouseEventLogger.qml` | ✅ QML компонент логирования мыши |
| `integrate_event_logging.py` | ✅ Скрипт автоматической интеграции |
| `analyze_event_sync.py` | ✅ Анализатор событий (обновлен) |
| `COMPREHENSIVE_EVENT_LOGGING_FINAL.md` | 📚 Полная документация |

---

## 🚀 Применение (5 минут)

### **Шаг 1: Автоматическая интеграция Python**

```bash
python integrate_event_logging.py
```

**Что делает:**
- ✅ Создает бэкап `panel_graphics.py.backup`
- ✅ Добавляет импорты
- ✅ Инициализирует `event_logger`
- ✅ Заменяет `LabeledSlider` на версию с логированием
- ✅ Обновляет подключения слайдеров
- ⚠️ Выводит список QCheckBox для ручной доработки

### **Шаг 2: Ручная доработка QCheckBox**

Для каждого QCheckBox из списка (см. вывод скрипта):

**❌ БЫЛО:**
```python
fog_enabled = QCheckBox("Включить туман", self)
fog_enabled.stateChanged.connect(
    lambda state: self._update_environment("fog_enabled", state == Qt.Checked)
)
```

**✅ СТАЛО:**
```python
fog_enabled = QCheckBox("Включить туман", self)

def on_fog_changed(state: int):
    checked = (state == Qt.Checked)
    self.event_logger.log_user_click(
        widget_name="fog_enabled",
        widget_type="QCheckBox",
        value=checked,
        text="Включить туман"
    )
    self._update_environment("fog_enabled", checked)

fog_enabled.stateChanged.connect(on_fog_changed)
```

### **Шаг 3: Добавить MouseEventLogger в QML**

Откройте `assets/qml/main.qml` и добавьте:

```qml
import QtQuick
import QtQuick3D
import "components"

Window {
    id: root
    
    View3D {
        id: view3D
        anchors.fill: parent
        
        // ... existing 3D content ...
        
        // ✅ НОВОЕ: Логирование мыши
        MouseEventLogger {
            id: mouseLogger
            enableLogging: true
            componentName: "main.qml"
            z: -1
        }
    }
}
```

### **Шаг 4: Тестирование**

```bash
python app.py
```

1. Подвигайте слайдеры
2. Покликайте чекбоксы
3. Выберите значения в комбобоксах
4. Поперетаскивайте мышью 3D сцену
5. Закройте приложение

### **Шаг 5: Проверка результатов**

После закрытия приложения автоматически выведется:

```
============================================================
🔍 ДИАГНОСТИКА ЛОГОВ И СОБЫТИЙ
============================================================

🔗 Анализ событий Python↔QML...
   📁 События экспортированы: logs/events_20241215_164523.json
   Всего сигналов: 89
   Синхронизировано: 87
   Пропущено QML: 2
   Процент синхронизации: 97.8%
   
   📈 События по типам:
      USER_SLIDER: 45
      USER_CLICK: 15
      MOUSE_DRAG: 34
      MOUSE_WHEEL: 12
      ...
============================================================
```

### **Шаг 6: Детальный анализ (опционально)**

```bash
# Консольный отчет
python analyze_event_sync.py

# HTML отчет
python analyze_event_sync.py --html
```

---

## 📊 Что логируется

### Python
- ✅ Клики на QCheckBox
- ✅ Изменения слайдеров (LabeledSlider)
- ✅ Выбор в комбобоксах (QComboBox)
- ✅ Выбор цвета (ColorButton)
- ✅ Изменения state
- ✅ Вызовы .emit()

### QML
- ✅ Нажатие мыши (left/right/middle)
- ✅ Перетаскивание (drag)
- ✅ Прокрутка колесика (zoom)
- ✅ Получение сигналов из Python
- ✅ Вызовы QML функций
- ✅ Изменения QML свойств

---

## 🎯 Целевые метрики

| Метрика | Цель | Критично |
|---------|------|----------|
| Sync Rate | >95% | <90% |
| Missing QML | 0 | >5 |
| Avg Latency | <20ms | >100ms |

---

## 📚 Документация

- `COMPREHENSIVE_EVENT_LOGGING_FINAL.md` - Полная документация
- `FULL_UI_EVENT_LOGGING_GUIDE.md` - Подробное руководство
- `EVENT_LOGGING_README.md` - Базовое описание

---

## ✅ Готово!

Система логирования **всех** UI событий настроена и готова к использованию.

**Время интеграции**: ~5 минут  
**Результат**: Полная прозрачность Python↔QML синхронизации
