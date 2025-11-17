# 🚀 PneumoStabSim Professional - Симулятор пневматического стабилизатора

**PneumoStabSim Professional v2.0.1** - Профессиональный симулятор пневматической подвески с Qt Quick3D, IBL окружением и расширенной графикой

[![Python](https://img.shields.io/badge/Python-3.11%E2%80%933.13-blue.svg)](https://python.org)
[![Qt](https://img.shields.io/badge/Qt-PySide6%206.10-green.svg)](https://qt.io)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](.)
[![Version](https://img.shields.io/badge/Version-2.0.1-orange.svg)](archive/2025-11/root-reports/PROJECT_STATUS.md)

## 🧭 Engineering Charter

## 🆕 Новое в версии 2.0.1

- Первоначальная интеграция модульных панелей (geometry, graphics, modes)
- Qt Quick 3D сцена (main.qml v4.9.9) с поддержкой IBL и Fog 6.10
- Миграция HDR путей и нормализация через normalise_hdr_path()
- Автоматизированные тесты (pytest + pytest-qt fallback)
