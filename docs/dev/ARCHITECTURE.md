# Документация разработчика

## Архитектура системы

### Основные компоненты

1. **UI Layer** (`src/ui/`) - пользовательский интерфейс
2. **Core Layer** (`src/core/`) - ядро симуляции  
3. **Physics Layer** (`src/physics/`) - физические расчеты
4. **Pneumatics Layer** (`src/pneumo/`) - пневматические системы
5. **Mechanics Layer** (`src/mechanics/`) - механические расчеты

### Паттерны проектирования

- **MVC** - Model-View-Controller для UI
- **Observer** - для обновления UI при изменении данных
- **Factory** - для создания различных типов компонентов
- **Strategy** - для различных алгоритмов симуляции

### Потоки данных

```
UI Events -> Controller -> Model -> Physics Engine -> Results -> UI Update
```

## Соглашения кодирования

### Python код
- Следуем PEP 8
- Используем type hints
- Документация в формате Google docstring
- Максимальная длина строки: 88 символов (Black formatter)

### QML код  
- Отступы: 4 пробела
- CamelCase для компонентов
- camelCase для свойств и методов

### Git workflow
- Ветка `master` - стабильная версия
- Feature branches: `feature/feature-name`
- Hotfix branches: `hotfix/issue-description`
- Коммиты в формате: `type: description`

## Настройка среды разработки

### Рекомендуемые IDE
- PyCharm Professional (лучшая поддержка Qt)
- VS Code с расширениями Python и QML
- Qt Creator для QML разработки

### Необходимые расширения VS Code
- Python
- QML  
- EditorConfig
- GitLens
- Python Docstring Generator
