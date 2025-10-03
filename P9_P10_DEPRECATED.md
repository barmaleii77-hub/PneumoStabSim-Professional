# ?? DEPRECATED: OpenGL Implementation

**Дата:** 3 октября 2025  
**Статус:** ? **УСТАРЕЛО - Заменено на Qt Quick 3D**

---

## ?? МИГРАЦИЯ

**Этот отчёт описывает устаревшую реализацию на OpenGL.**

**Новая реализация:** Qt Quick 3D with RHI/Direct3D

См. актуальную документацию:
- `QTQUICK3D_MIGRATION_SUCCESS.md` - отчёт о миграции
- `QTQUICK3D_ARCHITECTURE.md` - архитектура Qt Quick 3D (TODO)
- `assets/qml/main.qml` - QML сцена

---

## ?? ИСТОРИЧЕСКАЯ ИНФОРМАЦИЯ

**Проблемы с OpenGL подходом:**
- ? Silent crashes на некоторых системах
- ? Проблемы с драйверами
- ? Сложная интеграция с QWidget UI
- ? Threading issues

**Преимущества Qt Quick 3D:**
- ? RHI backend (Direct3D/Vulkan/Metal)
- ? Declarative QML
- ? PBR materials встроенные
- ? Лучшая производительность
- ? Нет проблем с threading

---

## ??? УСТАРЕВШИЕ ФАЙЛЫ

**Удалены:**
- `src/ui/gl_view.py` - OpenGL widget
- `src/ui/gl_scene.py` - OpenGL scene manager

**Deprecated:**
- `test_p9_opengl.py` - тесты OpenGL
- `test_with_surface_format.py` - тесты форматов
- `P9_P10_REPORT.md` - этот файл

---

**Не используйте эту документацию для новой разработки!**
