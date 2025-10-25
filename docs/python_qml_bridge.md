# Мост Python ↔ QML

```mermaid
graph TD
 SettingsManager["SettingsManager\n(app_settings.json)"] -->|стартовые значения| MainWindow
 GraphicsPanel["Qt панели"] -->|Qt-сигналы| SignalsRouter
 SimulationManager -->|StateSnapshot| SignalsRouter
 SignalsRouter -->|queue_update(...)| QMLBridge
 QMLBridge -->|setProperty('pendingPythonUpdates')| QMLRoot["QML root Item"]
 QMLBridge -->|invokeMethod('apply*Updates')| QMLRoot
 MainWindow -->|context property "window"| QMLRoot
 QMLRoot -->|batchUpdatesApplied(...)| MainWindow
 IblProbeLoader["IblProbeLoader.qml"] -->|window.logIblEvent(...)| MainWindow
```

## Обзор

`QMLBridge` и вспомогательные модули (`SignalsRouter`, `StateSync`, `UISetup`) обеспечивают синхронизацию состояний между Python и QML. Ниже перечислены основные сценарии и правила изменений.

## Прямые вызовы QML-функций

- Карта `QML_UPDATE_METHODS` описывает соответствие категорий (`geometry`, `lighting`, `quality`, `camera`, `effects`, `animation`, `materials`, `environment`, `simulation`) методам QML (`apply*Updates`, `update*`). С 2025-08-15 соответствия берутся из метаданных `config/qml_bridge.yaml`, которые парсятся модулем `src/ui/qml_bridge.py` и реэкспортируются в класс `QMLBridge`. 【F:config/qml_bridge.yaml†L1-L35】【F:src/ui/qml_bridge.py†L1-L147】【F:src/ui/main_window/qml_bridge.py†L28-L61】
  Правило: добавляя новую функцию в QML, зарегистрируйте её в YAML и убедитесь, что QML реализует обработчик.
- `QMLBridge.invoke_qml_function()` инкапсулирует `QMetaObject.invokeMethod`, добавляя логирование через `EventLogger`. 【F:src/ui/main_window/qml_bridge.py†L235-L276】 
 Правило: любые изменения сигнатуры должны оставаться совместимыми с `Qt.ConnectionType.DirectConnection` и существующими тестовыми стабами.

## Батч-обновления свойств

- `QMLBridge.queue_update()` агрегирует частичные обновления и планирует немедленный сброс таймером. 【F:src/ui/main_window/qml_bridge.py†L107-L143】
- `QMLBridge.flush_updates()` сначала пытается записать целый пакет в свойство `pendingPythonUpdates`; при отказе автоматически вызывает методы из `QML_UPDATE_METHODS`. 【F:src/ui/main_window/qml_bridge.py†L120-L193】
- Корневой QML-элемент реагирует на изменение `pendingPythonUpdates` и делегирует обработку `applyBatchedUpdates`. 【F:assets/qml/main.qml†L18-L166】
 
Правила изменений:
1. Новый ключ в пакете должен поддерживаться в `applyBatchedUpdates` (иначе ACK вернёт частичное применение).
2. Если структура данных не сериализуется в JSON, адаптируйте `_prepare_for_qml` для преобразования (`Path`, `numpy`). 【F:src/ui/main_window/qml_bridge.py†L279-L321】
3. При изменении имени свойства `pendingPythonUpdates` обновите QML и все места, где проверяется `_qml_pending_property_supported`.

## Синхронизация состояния симуляции

- `QMLBridge.set_simulation_state()` превращает `StateSnapshot` в payload с рычагами, цилиндрами, линиями и агрегатами, затем отправляет его через `pendingPythonUpdates`. 【F:src/ui/main_window/qml_bridge.py†L195-L279】
- `SignalsRouter._queue_simulation_update()` использует очередь батчей для инкрементальных обновлений между тикерами физики. 【F:src/ui/main_window/signals_router.py†L150-L213】
 
Правила: поддерживайте ключи `levers`, `pistons`, `lines`, `aggregates`, `frame`, `tank` синхронными с QML (`apply3DUpdates`, `applySimulationUpdates`) и с `StateSnapshot` (иначе отладка станет невозможной).

## Логирование и подтверждения

- QML эмитит `batchUpdatesApplied(summary)`, а `SignalsRouter` подключает его к `MainWindow._on_qml_batch_ack`, далее `QMLBridge.handle_qml_ack` помечает пакеты применёнными и обновляет Graphics Logger. Подключение теперь осуществляется через `register_qml_signals`, читающий YAML-описание. 【F:assets/qml/main.qml†L16-L166】【F:config/qml_bridge.yaml†L37-L44】【F:src/ui/qml_bridge.py†L116-L147】【F:src/ui/main_window/signals_router.py†L187-L218】【F:src/ui/main_window/qml_bridge.py†L360-L434】
- `MainWindow.logQmlEvent()` позволяет QML писать в `EventLogger` (диагностика вызовов). 【F:src/ui/main_window/main_window_refactored.py†L205-L244】
- `IblProbeLoader.qml` вызывает `window.logIblEvent(message)`; сообщение проксируется в `IblSignalLogger.logIblEvent`. 【F:assets/qml/components/IblProbeLoader.qml†L1-L47】【F:src/ui/ibl_logger.py†L7-L75】
 
Правила: сохраняйте сигнатуры (`(dict)` для ACK, `(str, str)` для `logQmlEvent`, `(str)` для `logIblEvent`). При изменении форматов обновляйте документацию и анализаторы логов.

## Контрольные вопросы при доработке моста

1. Требуется ли новый контекст в QML? Добавьте его до `setSource` и задокументируйте в `docs/PYTHON_QML_API.md`.
2. Нужны ли тесты/стабы для `QMLBridge`? Обновите лёгкие паддинги (try/except блок в заголовке файла) для корректной работы без PySide6.
3. Отражены ли изменения в `applyBatchedUpdates` и `QMLBridge.QML_UPDATE_METHODS`/`config/qml_bridge.yaml`? Несогласованность приводит к «тихому» игнорированию параметров.
