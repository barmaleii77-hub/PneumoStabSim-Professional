# Инструкции по работе с виртуальным окружением

## ?? Активация виртуального окружения

### Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

### Windows CMD:
```cmd
venv\Scripts\activate.bat
```

## ?? Установка зависимостей
После активации виртуального окружения:
```powershell
pip install -r requirements.txt
```

## ?? Запуск приложения
```powershell
python app.py
```

## ?? Проверка установленных пакетов
```powershell
pip list
```

## ? Деактивация окружения
```powershell  
deactivate
```

## ?? Обновление requirements.txt
Если добавили новые пакеты:
```powershell
pip freeze > requirements.txt
```

## ? Преимущества виртуального окружения:
- Изоляция зависимостей проекта
- Точные версии библиотек
- Чистая среда разработки
- Воспроизводимость окружения