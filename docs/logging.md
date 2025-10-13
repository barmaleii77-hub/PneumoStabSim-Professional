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
