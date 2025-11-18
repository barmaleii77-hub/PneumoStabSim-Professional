# 🚀 PneumoStabSim Professional - Симулятор пневматического стабилизатора

**PneumoStabSim Professional v4.9.8** - Профессиональный симулятор пневматической подвески с Qt Quick3D, IBL окружением и расширенной графикой

[![Python](https://img.shields.io/badge/Python-3.11%E2%80%933.13-blue.svg)](https://python.org)
[![Qt](https://img.shields.io/badge/Qt-PySide6%206.10-green.svg)](https://qt.io)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](.)
[![Version](https://img.shields.io/badge/Version-4.9.8-orange.svg)](archive/2025-11/root-reports/PROJECT_STATUS.md)

## 🧭 Engineering Charter

## 🆕 Новое в версии 4.9.8

- Первоначальная интеграция модульных панелей (geometry, graphics, modes)
- Qt Quick 3D сцена (main.qml v2.0.1) с поддержкой IBL и Fog 6.10
- Миграция HDR путей и нормализация через normalise_hdr_path()
- Автоматизированные тесты (pytest + pytest-qt fallback)

## 🛠️ Подготовка Linux окружения для тестов

Для корректной работы PyTest-фикстур, использующих PySide6 и парсинг YAML, убедитесь, что в системе установлены базовые Qt/GL
библиотеки и Python-зависимости:

```bash
sudo apt-get update
sudo apt-get install -y libgl1 libegl1 libxkbcommon0
make uv-sync
```

Альтернатива: выполните `scripts/setup_linux.sh` (без флага `--skip-system`) — скрипт установит системные пакеты, синхронизирует
Python-зависимости (включая PyYAML 6.0.3) и подготовит окружение для запуска `pytest`.
