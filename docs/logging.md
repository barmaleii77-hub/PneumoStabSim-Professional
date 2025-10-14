# Логирование и диагностика

Подсистемы
- Основной лог `logs/PneumoStabSim_*.log` — старт/закрытие, ошибки
- Graphics Logger — отслеживание изменений UI параметров (lighting/environment/quality/camera/effects/materials)
- Event Logger — события Python↔QML: сигналы, вызовы QML, ACK
- IBL Logger — события загрузки HDR (`IblProbeLoader`)

Диагностика (терминал)
- По завершении запускается `run_log_diagnostics()`
- Выводит метрики: MAIN/GRAPHICS/IBL/EVENTS
- Если sync < 90%, проверьте соответствие payload формату QML функций

Типовые проверки
- Есть ли логи `apply*Updates()` в QML?
- Совпадают ли имена ключей payload с ожидаемыми (см. docs/python_qml_bridge.md)?
- Нужные HDR существуют? Пути разрешаются через `resolveUrl()`?

# PneumoStabSim Logging Policy

- Always-on logging: enabled for every run, no user toggle
- Clean start: on application launch, previous logs are deleted (both timestamped and run.log)
- Queue-based non-blocking file logging, UTF-8
- On normal exit: built-in diagnostics run automatically and print analysis summary to console
- Console remains clean during runtime (info/debug to files), only final analysis + warnings/errors are printed
- User input tracing: UI clicks, sliders, combos, color picks; QML canvas mouse events; full Python↔QML signal path logged
- From click to pixel: we trace events from UI click to QML function call and scene properties affecting rendering

Implementation notes:
- `logging_setup.init_logging()` creates a timestamped file and run.log; rotate_old_logs(keep_count=0) is called before init to delete old logs
- `event_logger` and `graphics_logger` record structured JSON-friendly data in parallel
- `app.py` runs `run_log_diagnostics()` after exit to summarize results to console

Pilot settings and responsibilities
- Pilot must always read, rotate, and analyze logs automatically on each run
- Pilot must interpret analysis results and act on findings without prompting the user
- User only sees: final analysis summary, warnings, and errors in console

Persistence of user graphics settings
- Settings are auto-saved on normal application exit (no Save button)
- Reset button restores defaults; current UI updates are emitted and saved on close
