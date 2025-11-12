# Graphics Panel Audit Summary

## Summary

- GraphicsPanel теперь полностью синхронизирован с `config/app_settings.json`:
  вкладка окружения использует актуальные диапазоны из
  `EnvironmentSliderRange` и отображает значения в метрах/децибелах вместо
  устаревших мм. Данные тумана, SSAO и отражений считываются/записываются через
  `SettingsManager`, что исключает рассинхронизацию с QML.
- Поддержка HDR реализована end-to-end: `FileCyclerWidget` сканирует каталоги
  `assets/hdr/`, `assets/hdri/`, `assets/qml/assets/`, а статус `⚠ файл не
  найден` помогает сразу заметить недостающие ассеты. Python-уровень
  нормализует пути через `normalizeHdrPath`, поэтому и Windows, и Linux получают
  корректный `file://` URL.
- Вкладка эффектов экспонирует HDR-параметры bloom (`glowHDRMinimumValue`,
  `glowHDRMaximumValue`, `glowHDRScale`) и синхронизирована с TonemappingPanel —
  пресеты HDR автоматически обновляют связанный UI и настройки.

Актуальные ограничения `scene`-блока отслеживаются в плане Phase 4; оставшиеся
поля синхронизируются через `SettingsManager`.

## Testing

✅ `python -m pytest tests/unit/ui/test_hdr_discovery.py tests/unit/ui/test_main_window_hdr_paths.py`
