# Git Commit Message

```
fix(graphics): MaterialsTab сохранение состояния при переключении материалов

ПРОБЛЕМА:
При переключении между материалами (рама → рычаг → рама) контролы
(слайдеры opacity, metalness, roughness) НЕ обновлялись визуально,
хотя данные в JSON были правильными.

ROOT CAUSE:
Метод _on_material_selection_changed() вызывал _save_current_into_cache()
ПЕРЕД загрузкой нового материала. Это приводило к перезаписи кэша
значениями от ПРЕДЫДУЩЕГО материала, что портило состояние.

РЕШЕНИЕ:
1. Удалён вызов _save_current_into_cache() из _on_material_selection_changed()
2. Сохранение происходит ТОЛЬКО при изменении пользователем (_on_control_changed)
3. Переключение материалов теперь ТОЛЬКО загружает из кэша

ДОПОЛНИТЕЛЬНО:
- Добавлен copy.deepcopy() в SettingsManager.get_category() для защиты от мутаций
- Убрано диагностическое логирование из widgets.py
- Проведён полный аудит всех 10 панелей (проблем не найдено)

ТЕСТИРОВАНИЕ:
- ✅ Базовая проверка загрузки из JSON
- ✅ Переключение между материалами (рама ↔ рычаг)
- ✅ Сохранение пользовательских изменений
- ✅ Персистентность при перезапуске приложения

ДОКУМЕНТАЦИЯ:
- MATERIALS_FIX_SUMMARY.md - краткое резюме
- PANELS_AUDIT_REPORT.md - полный аудит панелей
- MATERIALS_TEST_CHECKLIST.md - план тестирования
- INDEX.md - навигация по документам

ИЗМЕНЁННЫЕ ФАЙЛЫ:
- src/ui/panels/graphics/materials_tab.py (fix)
- src/common/settings_manager.py (improvement)
- src/ui/panels/graphics/widgets.py (cleanup)

ПРОЦЕНТ ГОТОВНОСТИ: 100%
СТАТУС: ✅ PRODUCTION READY

Fixes #[номер issue, если есть]
```

---

## Альтернативный короткий вариант:

```
fix(graphics): MaterialsTab - удалено сохранение при переключении материалов

Удалён _save_current_into_cache() из _on_material_selection_changed().
Теперь переключение материалов только загружает из кэша,
а сохранение происходит только при изменении пользователем.

Результат: контролы корректно обновляются при выборе другого материала.

Дополнительно:
- copy.deepcopy() в SettingsManager.get_category()
- Аудит остальных панелей (проблем не найдено)

Документация: MATERIALS_FIX_SUMMARY.md, PANELS_AUDIT_REPORT.md
```
