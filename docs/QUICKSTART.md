# Быстрый старт PneumoStabSim

## Минимальные требования

- Python 3.13+
- Windows 10/11 или Linux Ubuntu 20.04+
- OpenGL 3.3+ или DirectX 11+
- 4 GB RAM
- 1 GB свободного места на диске

## Установка за 5 минут

### 0. Подготовка окружения
```bash
cp env.sample .env
python setup_environment.py --python-version 3.13 --install-qt --qt-version 6.7.2
```

*Для Windows можно использовать:* `./activate_environment.ps1 -Setup -InstallQt -PythonVersion 3.13`.

### 1. Клонирование
```bash
git clone https://github.com/barmaleii77-hub/PneumoStabSim-Professional.git
cd PneumoStabSim-Professional
```

### 2. Виртуальное окружение
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate.bat

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Зависимости
```bash
pip install --require-hashes -r requirements.txt
```

### 4. Запуск
```bash
python app.py
```

## Первое использование

1. **Откроется главное окно** с 3D сценой и панелями управления
2. **Панель геометрии** - настройте размеры системы
3. **Панель пневматики** - установите начальное давление
4. **Панель режимов** - выберите автоматический режим
5. **Нажмите "Запуск"** для начала симуляции

## Устранение проблем

### Приложение не запускается
```bash
# Проверьте Python версию
python --version  # Должно быть 3.13+

# Проверьте зависимости
pip list | grep PySide6  # Должно быть 6.10+
