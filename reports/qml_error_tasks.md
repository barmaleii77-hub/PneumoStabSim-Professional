# Повторяющиеся ошибки загрузки QML

| № | Текст ошибки | Компонент / путь | Источники логов | Комментарий для правки |
|---|---|---|---|---|
| 1 | Cannot assign to non-existent property "ssaoEnabled" | [`assets/qml/main.qml` – `SceneEnvironmentController` (`environmentDefaults`)](../assets/qml/main.qml#L137) | [`qml_errors_full.txt` строки 2–9](../qml_errors_full.txt) | В экземпляре `SceneEnvironmentController` задано свойство `ssaoEnabled`, но оно отсутствует в компоненте: добавить свойство или убрать привязку. |
| 2 | Cannot assign to non-existent property "fogDensity" | [`assets/qml/main.qml` – `SceneEnvironmentController` (`environmentDefaults`)](../assets/qml/main.qml#L137) | [`full_qml_log.txt` строки 54–62](../full_qml_log.txt) | Аналогично, в `SceneEnvironmentController` используется `fogDensity`, которого нет в определении компонента. Добавить поддержку параметра или удалить привязку. |

> В отчётах `QML_PHASE*_INTEGRATION_*.txt` повторяющихся ошибок не обнаружено.
