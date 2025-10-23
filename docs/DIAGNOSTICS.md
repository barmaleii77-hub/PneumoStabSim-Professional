# Диагностика и трассировка сигналов

Новый модуль `src.diagnostics.signal_tracing` объединяет подписки на Qt-сигналы, логирование и передачу данных в QML.

## Быстрый старт (Python)

```python
from src.diagnostics import SignalTracer

tracer = SignalTracer(max_records=250)
detach = tracer.attach(qobject, "statusChanged", alias="status")

# ... выполнение приложения ...

# Проверяем, что сигнал не потерялся
tracer.assert_emitted("status", min_count=1)

# Снимаем подписку и очищаем историю
detach()
tracer.dispose()
```

### Подписка на несколько сигналов

```python
tracer.attach_many(viewModel, ["started", "finished"], alias_prefix="vm:")
```

### Встроенные проверки

* `assert_emitted(signal, min_count=...)` — гарантирует, что сигнал пришёл нужное число раз.
* `register_sink(callback)` — добавляет обработчик, который будет вызываться при каждом новом сигнале (например, для интеграции с внешним логгером).
* `register_reset_hook(callback)` — уведомляет GUI о полном очищении буфера.

## Интеграция с QML/GUI

### Qt-мост

```python
from src.diagnostics import SignalTracer, SignalTracerBridge

tracer = SignalTracer()
bridge = SignalTracerBridge(tracer)

# Передайте bridge в контекст QML, например через rootContext().setContextProperty("signalTracer", bridge)
```

`SignalTracerBridge` эмитирует сигналы:

* `traceAdded(dict trace)` — отправляется при каждом зафиксированном Qt-сигнале.
* `traceReset()` — вызывается при очистке буфера.

### Компоненты в `assets/qml/components`

* `SignalTracePanel` — готовая панель с `ListView` и кнопкой очистки, автоматически ограничивает размер истории (`maxEntries`).
* `SignalTraceIndicator` — компактный виджет-счётчик, подсвечивающий появление новых сигналов.

Использование в QML:

```qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import Components 1.0

SignalTracePanel {
    id: tracePanel
    anchors.fill: parent

    Connections {
        target: signalTracer
        function onTraceAdded(trace) {
            tracePanel.appendTrace(trace)
      indicator.increment()
        }

        function onTraceReset() {
     tracePanel.clear()
            indicator.reset()
        }
    }
}
```

## Проверка в CI

Добавленные unit-тесты (`tests/unit/test_signal_tracing.py`) входят в стандартный прогон `pytest` и гарантируют:

* фиксацию сигналов и корректность аргументов;
* обработку отсутствующих Qt-сигналов (вызов `SignalTracingError`);
* обнаружение «пропавших» сигналов через `MissingSignalError`.

Тесты автоматически выполняются в CI (см. `.github/workflows/ci.yml`), поэтому пропущенные сигналы и регрессии будут обнаружены до мерджа.
