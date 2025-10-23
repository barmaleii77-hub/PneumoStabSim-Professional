# Комплексный отчёт по настройке окружения

Документ описывает актуальные требования к окружению разработки PneumoStabSim Professional и порядок регулярных проверок конфигурации.

##1. Базовые требования

- Python3.13.x (64-bit)
- pip24+
- Git2.40+
- Qt рендеринг: PySide66.10.0+
- Дополнительные библиотеки: numpy, scipy, matplotlib, Pillow, psutil, python-dotenv, PyYAML

##2. Подготовка рабочей станции

1. Создать и активировать виртуальное окружение:
 ```bash
 python -m venv .venv
 source .venv/bin/activate # Windows: .venv\Scripts\activate
 ```
2. Установить основные зависимости:
 ```bash
 pip install -r requirements.txt
 ```
3. Подтянуть dev-инструменты и утилиту аудита конфигурации:
 ```bash
 pip install -r requirements-dev.txt
 ```
4. Установить pre-commit хуки (автоматически подключают аудит конфигурации):
 ```bash
 pre-commit install
 ```

##3. Регулярный аудит конфигурации

Новая утилита `tools/audit_config.py` автоматически выполняет:
- проверку схемы `config/app_settings.json` по `config/schemas/app_settings.schema.json`;
- сравнение c эталоном `config/baseline/app_settings.json`;
- контроль контрольной суммы из `config/config_hashes.json`;
- генерацию отчёта `reports/config_audit_report.md`.

###3.1 Локальный запуск

```bash
python tools/audit_config.py --update-report
```

Утилита обновит отчёт и завершит работу с ненулевым кодом при нарушении схемы, изменении хеша или расхождении с эталоном. Pre-commit хук автоматически выполняет ту же проверку перед каждым коммитом.

###3.2 Интеграция с командой

- При целевых изменениях конфигурации обязательно обновлять baseline (`config/baseline/app_settings.json`) и значение SHA256 в `config/config_hashes.json`.
- Отчёт `reports/config_audit_report.md` хранится в репозитории и должен коммититься вместе с изменениями параметров.

##4. Проверка перед коммитом

1. Обновить виртуальное окружение: `pip install -r requirements-dev.txt` (при необходимости).
2. Выполнить linters и тесты (см. раздел «CI/CD»):
 ```bash
 pre-commit run --all-files
 pytest
 ```
3. Убедиться в отсутствии незакоммиченных изменений после выполнения `audit_config`.

##5. Синхронизация с CI/CD

GitHub Actions запускает `python tools/audit_config.py --update-report` в lint-джобе. Если отчёт не соответствует ожидаемому состоянию или конфигурация расходится с эталоном, сборка завершится ошибкой.

##6. Канонический набор файлов конфигурации

| Назначение | Файл |
| ---------- | ---- |
| Рабочая конфигурация | `config/app_settings.json` |
| Эталон | `config/baseline/app_settings.json` |
| JSON Schema | `config/schemas/app_settings.schema.json` |
| Контрольные суммы | `config/config_hashes.json` |
| Отчёт аудита | `reports/config_audit_report.md` |

Документ обновлён с учётом внедрения конфигурационного линтера (январь2025).
