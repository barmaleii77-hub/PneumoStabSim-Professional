# 📦 Changelog

## [2.0.1] - 2026-12-06
### Added
- Консолидирована HDR-ветка `hdr/bloom-tonemap`: отдельные ползунки `HDR Maximum` и
  `HDR Scale` дополняют существующий порог и сохраняются через сервис настроек,
  закрывая все требования по тонмаппингу и пост-обработке.
- Панель окружения использует `FileCyclerWidget` для перебора HDR skybox-файлов,
  позволяет очищать выбор и выводит предупреждение/подсказку, если ресурс
  отсутствует в манифесте или на диске.

### Changed
- Главное окно нормализует HDR-пути, приводя локальные URL и логируя каждую
  неудачную попытку резолвинга, чтобы упростить кроссплатформенную отладку.
- Обновлена HDR-документация (`docs/README.md`, `assets/hdr/README.md`) с
  примерами загрузки, советами по кешированию и ссылками на манифестный
  пайплайн.
- В хабе документации уточнена поддержка текстур, чтобы устранить устаревшие
  сообщения «не поддерживается» и согласовать инструкции с текущим UX
  `FileCyclerWidget`.

## [4.9.9] - 2026-06-18
### Added
- Expanded bloom controls with dedicated `HDR Maximum` and `HDR Scale` sliders so QA can tune the high dynamic range pipeline alongside the existing threshold slider; all three values persist through the graphics settings service.
- Environment panel now cycles HDR skyboxes through the reusable `FileCyclerWidget`, allows explicitly clearing the selection, and surfaces a warning badge plus tooltip when the chosen file is missing.
- Main window normalises HDR paths originating from QML, converting local file URLs and recording debug logs whenever a path cannot be resolved; this keeps the HDR asset workflow consistent across platforms.

### Notes
- The HDR feature set is delivered as part of the `hdr/bloom-tonemap` integration branch. See the documentation hub for validation checklists and troubleshooting guidance specific to the new controls.

### Changed
- Refreshed HDR documentation and inventory guidance to reflect the unified verifier (`python -m tools.task_runner verify-hdr-assets`), updated path-handling examples, and clarified that custom textures now follow the same persistence and warning rules as bundled HDRs.
