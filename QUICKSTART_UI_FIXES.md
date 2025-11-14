# 🚀 БЫСТРЫЙ СТАРТ: Проверка исправлений UI тестов

## ✅ Что было исправлено
- ✅ test_qml_signals (удалены недопустимые refresh())
- ✅ test_post_effects_bypass (добавлен onEffectsBypassChanged)
- ✅ test_shared_materials_fallback (добавлены AssetsLoader)
- ✅ test_file_cycler_warning_resets (инвалидация кеша)
- ✅ test_main_qml_screenshots (обновлены baselines)

## 🔧 Быстрая проверка (30 сек)

### Вариант 1: Авто-скрипт
```sh
python check_fixed_tests.py
```

### Вариант 2: Ручной запуск
```sh
# Один за другим
pytest tests/ui/test_qml_signals.py -xvs
pytest tests/ui/test_post_effects_bypass_fail_safe.py -xvs
pytest tests/ui/test_shared_materials_fallback.py -xvs
pytest tests/ui/test_file_cycler_warning_resets_when_file_reappears.py -xvs
pytest tests/ui/test_main_qml_screenshots.py -xvs
```

## 🧪 Полная проверка проекта (5-10 мин)
```sh
make autonomous-check
```

## 📤 Отправка изменений
```sh
# Проверить статус
git status

# Если нужно, добавить файлы
git add check_fixed_tests.py FINAL_UI_FIXES_REPORT.md

# Создать дополнительный commit (опционально)
git commit -m "docs: добавлены отчёт и скрипт проверки UI тестов"

# Push в удалённый репозиторий
git push origin feature/hdr-assets-migration
```

## 🔍 Детальный отчёт
См. `FINAL_UI_FIXES_REPORT.md`

## ❓ Проблемы?

### Тест всё ещё падает
1. Проверьте, что изменения применились: `git diff HEAD~1`
2. Проверьте кэш Python: `find . -type d -name __pycache__ -exec rm -rf {} +`
3. Перезапустите тест с флагом `--tb=short` для краткого трейсбека

### PowerShell не выполняет команды
Используйте `cmd.exe` или Git Bash вместо PowerShell

### QtCharts не найден
```sh
pip install PySide6-Addons
# или
pip install PySide6[all]
```

## 📞 Контакты
Если нужна помощь — создайте issue в репозитории или пингуйте @maintainers

---
**Последнее обновление:** 2025-11-14
