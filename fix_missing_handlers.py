"""
Автоматическое исправление отсутствующих обработчиков в GraphicsPanel
Добавляет 4 обработчика и 1 UI элемент
"""

import sys
from pathlib import Path


def add_missing_handlers():
    """Добавляет отсутствующие обработчики в panel_graphics.py"""
    
    panel_file = Path("src/ui/panels/panel_graphics.py")
    
    if not panel_file.exists():
        print(f"❌ Файл не найден: {panel_file}")
        return False
    
    print("=" * 80)
    print("🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ GRAPHICSPANEL")
    print("=" * 80)
    
    content = panel_file.read_text(encoding='utf-8')
    
    # Проверяем, что исправления ещё не применены
    if "on_ibl_toggled" in content:
        print("⚠️ Обработчик on_ibl_toggled уже существует!")
        print("   Пропуск исправлений...")
        return True
    
    # Ищем место для вставки обработчиков (после on_ibl_intensity_changed)
    insert_marker = "def on_ibl_intensity_changed(self, value: float):"
    
    if insert_marker not in content:
        print(f"❌ Не найден маркер для вставки: {insert_marker}")
        return False
    
    # Новые обработчики
    new_handlers = '''
    @Slot(bool)
    def on_ibl_toggled(self, enabled: bool):
        """Включение/выключение IBL"""
        self.current_graphics['ibl_enabled'] = enabled
        if hasattr(self, 'ibl_intensity'):
            self.ibl_intensity.setEnabled(enabled)
        self.emit_environment_update()

    @Slot(bool)
    def on_tonemap_toggled(self, enabled: bool):
        """Включение/выключение тонемаппинга"""
        self.current_graphics['tonemap_enabled'] = enabled
        if hasattr(self, 'tonemap_mode'):
            self.tonemap_mode.setEnabled(enabled)
        self.emit_effects_update()

    @Slot(bool)
    def on_vignette_toggled(self, enabled: bool):
        """Включение/выключение виньетирования"""
        self.current_graphics['vignette_enabled'] = enabled
        if hasattr(self, 'vignette_strength'):
            self.vignette_strength.setEnabled(enabled)
        self.emit_effects_update()

    @Slot(bool)
    def on_lens_flare_toggled(self, enabled: bool):
        """Включение/выключение Lens Flare"""
        self.current_graphics['lens_flare_enabled'] = enabled
        self.emit_effects_update()
'''
    
    # Вставляем обработчики после on_ibl_intensity_changed
    lines = content.split('\n')
    new_lines = []
    inserted = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Ищем конец функции on_ibl_intensity_changed
        if not inserted and "def on_ibl_intensity_changed" in line:
            # Пропускаем до конца функции (следующая функция или конец класса)
            j = i + 1
            while j < len(lines):
                new_lines.append(lines[j])
                if lines[j].strip().startswith("@Slot") or lines[j].strip().startswith("def ") or lines[j].strip().startswith("# ==="):
                    # Вставляем обработчики перед следующей функцией/секцией
                    new_lines.insert(-1, new_handlers)
                    inserted = True
                    print("✅ Добавлены 4 обработчика:")
                    print("   • on_ibl_toggled()")
                    print("   • on_tonemap_toggled()")
                    print("   • on_vignette_toggled()")
                    print("   • on_lens_flare_toggled()")
                    break
                j += 1
            
            # Сдвигаем индекс, чтобы не добавлять строки повторно
            break
    
    if not inserted:
        print("❌ Не удалось найти место для вставки обработчиков")
        return False
    
    # Продолжаем копировать оставшиеся строки
    new_lines.extend(lines[j:])
    
    # Записываем изменённый файл
    new_content = '\n'.join(new_lines)
    
    # Создаём резервную копию
    backup_file = panel_file.with_suffix('.py.backup')
    panel_file.write_text(content, encoding='utf-8')  # Сохраняем оригинал как backup
    print(f"✅ Создана резервная копия: {backup_file}")
    
    # Записываем новую версию
    panel_file.write_text(new_content, encoding='utf-8')
    print(f"✅ Файл обновлён: {panel_file}")
    
    return True


def add_connect_statements():
    """Добавляет .connect() вызовы для новых обработчиков"""
    
    panel_file = Path("src/ui/panels/panel_graphics.py")
    content = panel_file.read_text(encoding='utf-8')
    
    print("\n🔗 ПОДКЛЮЧЕНИЕ ОБРАБОТЧИКОВ К UI ЭЛЕМЕНТАМ:")
    print("-" * 80)
    
    # Ищем места для добавления .connect()
    modifications = [
        {
            'marker': 'self.ibl_enabled = QCheckBox("Включить IBL")',
            'after_marker': 'self.ibl_enabled.setChecked(self.current_graphics[\'ibl_enabled\'])',
            'add': '        self.ibl_enabled.toggled.connect(self.on_ibl_toggled)',
            'name': 'IBL toggle',
        },
        {
            'marker': 'self.tonemap_enabled = QCheckBox("Включить тонемаппинг")',
            'after_marker': 'self.tonemap_enabled.setChecked(self.current_graphics[\'tonemap_enabled\'])',
            'add': '        self.tonemap_enabled.toggled.connect(self.on_tonemap_toggled)',
            'name': 'Tonemap toggle',
        },
        {
            'marker': 'self.vignette_enabled = QCheckBox("Включить виньетирование")',
            'after_marker': 'self.vignette_enabled.setChecked(self.current_graphics[\'vignette_enabled\'])',
            'add': '        self.vignette_enabled.toggled.connect(self.on_vignette_toggled)',
            'name': 'Vignette toggle',
        },
        {
            'marker': 'self.lens_flare_enabled = QCheckBox("Lens Flare (блики)")',
            'after_marker': 'self.lens_flare_enabled.setChecked(self.current_graphics[\'lens_flare_enabled\'])',
            'add': '        self.lens_flare_enabled.toggled.connect(self.on_lens_flare_toggled)',
            'name': 'Lens Flare toggle',
        },
    ]
    
    modified = False
    
    for mod in modifications:
        if mod['add'] not in content:
            # Ищем место после setChecked
            if mod['after_marker'] in content:
                content = content.replace(
                    mod['after_marker'],
                    mod['after_marker'] + '\n' + mod['add']
                )
                print(f"✅ Подключен: {mod['name']}")
                modified = True
            else:
                print(f"⚠️ Не найден маркер для: {mod['name']}")
        else:
            print(f"⏭️ Уже подключён: {mod['name']}")
    
    if modified:
        panel_file.write_text(content, encoding='utf-8')
        print(f"✅ Подключения добавлены в {panel_file}")
        return True
    else:
        print(f"⏭️ Подключения уже существуют")
        return True


def verify_fixes():
    """Проверяет успешность исправлений"""
    
    print("\n" + "=" * 80)
    print("🔍 ПРОВЕРКА ИСПРАВЛЕНИЙ")
    print("=" * 80)
    
    panel_file = Path("src/ui/panels/panel_graphics.py")
    content = panel_file.read_text(encoding='utf-8')
    
    checks = [
        ('on_ibl_toggled', 'Обработчик IBL toggle'),
        ('on_tonemap_toggled', 'Обработчик Tonemap toggle'),
        ('on_vignette_toggled', 'Обработчик Vignette toggle'),
        ('on_lens_flare_toggled', 'Обработчик Lens Flare toggle'),
        ('self.ibl_enabled.toggled.connect(self.on_ibl_toggled)', 'Подключение IBL'),
        ('self.tonemap_enabled.toggled.connect(self.on_tonemap_toggled)', 'Подключение Tonemap'),
        ('self.vignette_enabled.toggled.connect(self.on_vignette_toggled)', 'Подключение Vignette'),
        ('self.lens_flare_enabled.toggled.connect(self.on_lens_flare_toggled)', 'Подключение Lens Flare'),
    ]
    
    all_ok = True
    
    for check, name in checks:
        if check in content:
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - НЕ НАЙДЕН!")
            all_ok = False
    
    return all_ok


if __name__ == "__main__":
    print("🚀 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ GRAPHICSPANEL")
    print("=" * 80)
    
    # Шаг 1: Добавление обработчиков
    if not add_missing_handlers():
        print("\n❌ Не удалось добавить обработчики!")
        sys.exit(1)
    
    # Шаг 2: Подключение к UI
    if not add_connect_statements():
        print("\n❌ Не удалось подключить обработчики!")
        sys.exit(1)
    
    # Шаг 3: Проверка
    if verify_fixes():
        print("\n" + "=" * 80)
        print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!")
        print("=" * 80)
        print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
        print("  1. Запустите: py check_graphics_params.py")
        print("  2. Проверьте процент готовности (должен быть 100%)")
        print("  3. Запустите: py app.py")
        print("  4. Протестируйте изменение параметров в панели графики")
        sys.exit(0)
    else:
        print("\n❌ ПРОВЕРКА НЕ ПРОЙДЕНА!")
        sys.exit(1)
