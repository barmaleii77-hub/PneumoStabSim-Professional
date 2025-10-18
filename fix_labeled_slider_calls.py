#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полная проверка соответствия ВСЕХ отрефакторенных файлов старым монолитам
Проверяет: GraphicsPanel, GeometryPanel, ModesPanel
ДОБАВЛЕНО: Детальный план добавления отсутствующих параметров
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class WidgetUsage:
    """Информация об использовании виджета"""
    widget_type: str
    parameter: str
    file: str
    line_number: int
    code_line: str


@dataclass
class ComparisonReport:
    """Отчёт о сравнении файлов"""
    panel_name: str = ""
    monolith_widgets: List[WidgetUsage] = field(default_factory=list)
    refactored_widgets: List[WidgetUsage] = field(default_factory=list)
    missing_in_refactored: List[str] = field(default_factory=list)
    extra_in_refactored: List[str] = field(default_factory=list)
    matched_widgets: List[Tuple[str, str]] = field(default_factory=list)
    files_analyzed: Dict[str, int] = field(default_factory=dict)
    
    def print_report(self):
        """Вывести отчёт на экран"""
        print("=" * 80)
        print(f"ПРОВЕРКА: {self.panel_name}")
        print("=" * 80)
        
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Виджетов в монолите: {len(self.monolith_widgets)}")
        print(f"   Виджетов в рефакторинге: {len(self.refactored_widgets)}")
        print(f"   Совпадающих параметров: {len(self.matched_widgets)}")
        print(f"   Отсутствующих в рефакторинге: {len(self.missing_in_refactored)}")
        print(f"   Лишних в рефакторинге: {len(self.extra_in_refactored)}")
        
        print(f"\n📁 ПРОАНАЛИЗИРОВАННЫЕ ФАЙЛЫ РЕФАКТОРИНГА:")
        for filename, count in self.files_analyzed.items():
            print(f"   ✓ {filename}: {count} виджетов")
        
        if len(self.matched_widgets) == len(self.monolith_widgets) and len(self.monolith_widgets) > 0:
            print(f"\n✅ ВСЕ ПАРАМЕТРЫ МОНОЛИТА ПРИСУТСТВУЮТ В РЕФАКТОРИНГЕ!")
        else:
            coverage = len(self.matched_widgets) / len(self.monolith_widgets) * 100 if self.monolith_widgets else 0
            print(f"\n⚠️  ПОКРЫТИЕ: {coverage:.1f}%")
            
            if self.missing_in_refactored:
                print(f"\n❌ ОТСУТСТВУЮТ ({len(self.missing_in_refactored)}):")
                for param in sorted(self.missing_in_refactored)[:10]:
                    print(f"   - {param}")
                if len(self.missing_in_refactored) > 10:
                    print(f"   ... и ещё {len(self.missing_in_refactored) - 10}")


def extract_labeled_sliders(file_path: Path) -> List[WidgetUsage]:
    """Извлечь все LabeledSlider из файла"""
    widgets = []
    
    if not file_path.exists():
        return widgets
    
    content = file_path.read_text(encoding='utf-8')
    
    # Паттерн для self.xxx = LabeledSlider
    pattern = re.compile(
        r'self\.(\w+)\s*=\s*LabeledSlider\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE | re.DOTALL
    )
    
    # Паттерн для старого синтаксиса (без self.)
    pattern_old = re.compile(
        r'(?<!self\.)(\w+)\s*=\s*LabeledSlider\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    
    matches = []
    for match in pattern.finditer(content):
        var_name = match.group(1)
        title = match.group(2).rstrip(':').strip()
        start_pos = match.start()
        line_number = content[:start_pos].count('\n') + 1
        line_start = content.rfind('\n', 0, start_pos) + 1
        line_end = content.find('\n', start_pos)
        if line_end == -1:
            line_end = len(content)
        code_line = content[line_start:line_end].strip()
        
        matches.append(WidgetUsage(
            widget_type='LabeledSlider',
            parameter=title,
            file=str(file_path),
            line_number=line_number,
            code_line=code_line[:80]
        ))
    
    # Старый синтаксис
    for match in pattern_old.finditer(content):
        var_name = match.group(1)
        title = match.group(2).rstrip(':').strip()
        start_pos = match.start()
        
        if not any(w.parameter == title for w in matches):
            line_number = content[:start_pos].count('\n') + 1
            line_start = content.rfind('\n', 0, start_pos) + 1
            line_end = content.find('\n', start_pos)
            if line_end == -1:
                line_end = len(content)
            code_line = content[line_start:line_end].strip()
            
            matches.append(WidgetUsage(
                widget_type='LabeledSlider',
                parameter=title,
                file=str(file_path),
                line_number=line_number,
                code_line=code_line[:80]
            ))
    
    return matches


def compare_panel(monolith_path: Path, refactored_dir: Path, tab_files: List[str], panel_name: str) -> ComparisonReport:
    """Сравнить один монолит с рефакторенными табами"""
    report = ComparisonReport(panel_name=panel_name)
    
    # Анализ монолита
    if monolith_path.exists():
        report.monolith_widgets = extract_labeled_sliders(monolith_path)
    
    # Анализ всех табов
    for tab_name in tab_files:
        tab_path = refactored_dir / tab_name
        if tab_path.exists():
            widgets = extract_labeled_sliders(tab_path)
            report.refactored_widgets.extend(widgets)
            report.files_analyzed[tab_name] = len(widgets)
    
    # Сравнение
    monolith_params = {w.parameter for w in report.monolith_widgets}
    refactored_params = {w.parameter for w in report.refactored_widgets}
    
    report.matched_widgets = [(p, p) for p in (monolith_params & refactored_params)]
    report.missing_in_refactored = list(monolith_params - refactored_params)
    report.extra_in_refactored = list(refactored_params - monolith_params)
    
    return report


def generate_migration_plan(report: ComparisonReport, monolith_path: Path):
    """Генерирует детальный план миграции отсутствующих параметров"""
    if not report.missing_in_refactored:
        return
    
    print("\n" + "=" * 80)
    print(f"📋 ПЛАН МИГРАЦИИ ДЛЯ {report.panel_name}")
    print("=" * 80)
    
    # Категоризация параметров по табам
    tab_assignments = {
        'camera_tab.py': [],
        'environment_tab.py': [],
        'quality_tab.py': [],
        'effects_tab.py': [],
        'lighting_tab.py': [],
    }
    
    # Ключевые слова для определения категории
    categorization = {
        'camera_tab.py': ['fov', 'зрения', 'плоскость', 'near', 'far', 'скорость камеры', 'автоповорота'],
        'environment_tab.py': ['ibl', 'skybox', 'fog', 'туман', 'окружен', 'поворот', 'смещение'],
        'quality_tab.py': ['shadow', 'bias', 'тен', 'fps', 'рендер', 'taa', 'масштаб'],
        'effects_tab.py': ['bloom', 'размыт', 'виньет', 'порог', 'распространение', 'фокус'],
        'lighting_tab.py': ['свет', 'яркость'],
    }
    
    # Читаем монолит для получения деталей
    if monolith_path.exists():
        monolith_content = monolith_path.read_text(encoding='utf-8')
        monolith_lines = monolith_content.split('\n')
    
    # Распределяем параметры по табам
    for param in report.missing_in_refactored:
        param_lower = param.lower()
        assigned = False
        
        # Находим виджет в монолите
        widget = next((w for w in report.monolith_widgets if w.parameter == param), None)
        
        for tab, keywords in categorization.items():
            if any(kw in param_lower for kw in keywords):
                if widget:
                    # Извлекаем полное объявление из монолита
                    start_line = widget.line_number - 1
                    code_snippet = []
                    
                    # Ищем полное объявление (может быть многострочным)
                    for i in range(start_line, min(start_line + 5, len(monolith_lines))):
                        code_snippet.append(monolith_lines[i])
                        if ')' in monolith_lines[i]:
                            break
                    
                    tab_assignments[tab].append({
                        'param': param,
                        'line': widget.line_number,
                        'code': '\n'.join(code_snippet)
                    })
                else:
                    tab_assignments[tab].append({
                        'param': param,
                        'line': 0,
                        'code': f'# TODO: Добавить {param}'
                    })
                assigned = True
                break
        
        if not assigned and widget:
            # Если не смогли определить - добавляем в прочее
            print(f"   ⚠️  Не удалось определить таб для: {param} (строка {widget.line_number})")
    
    # Выводим план
    for tab, params in tab_assignments.items():
        if params:
            print(f"\n{'='*80}")
            print(f"📄 {tab} - добавить {len(params)} параметров:")
            print(f"{'='*80}")
            
            for item in params:
                print(f"\n   ▶ {item['param']} (исходная строка: {item['line']})")
                print(f"      Код для копирования:")
                for line in item['code'].split('\n'):
                    if line.strip():
                        print(f"      {line}")


def main():
    """Основная функция - проверка ВСЕХ панелей"""
    print("🔍 ПОЛНАЯ ПРОВЕРКА ВСЕХ РЕФАКТОРЕННЫХ ПАНЕЛЕЙ")
    print("=" * 80)
    print()
    
    # Конфигурация панелей для проверки
    panels = [
        {
            'name': 'GraphicsPanel',
            'monolith': Path('src/ui/panels/panel_graphics.py'),
            'refactored_dir': Path('src/ui/panels/graphics'),
            'tabs': [
                'lighting_tab.py',
                'environment_tab.py',
                'quality_tab.py',
                'camera_tab.py',
                'materials_tab.py',
                'effects_tab.py',
            ]
        },
        {
            'name': 'GeometryPanel',
            'monolith': Path('src/ui/panels/panel_geometry.py'),
            'refactored_dir': Path('src/ui/panels/geometry'),
            'tabs': [
                'frame_tab.py',
                'suspension_tab.py',
                'cylinder_tab.py',
                'options_tab.py',
            ]
        },
        {
            'name': 'ModesPanel',
            'monolith': Path('src/ui/panels/panel_modes.py'),
            'refactored_dir': Path('src/ui/panels/modes'),
            'tabs': [
                'control_tab.py',
                'simulation_tab.py',
                'physics_tab.py',
                'road_excitation_tab.py',
            ]
        },
    ]
    
    # Результаты по всем панелям
    all_reports: List[ComparisonReport] = []
    
    for panel_config in panels:
        print(f"\n{'='*80}")
        print(f"📋 Анализ: {panel_config['name']}")
        print(f"{'='*80}")
        
        if not panel_config['monolith'].exists():
            print(f"⚠️  Монолит не найден: {panel_config['monolith']}")
            continue
        
        if not panel_config['refactored_dir'].exists():
            print(f"⚠️  Директория рефакторинга не найдена: {panel_config['refactored_dir']}")
            continue
        
        print(f"📖 Монолит: {panel_config['monolith']}")
        print(f"📁 Рефакторинг: {panel_config['refactored_dir']}")
        print()
        
        report = compare_panel(
            panel_config['monolith'],
            panel_config['refactored_dir'],
            panel_config['tabs'],
            panel_config['name']
        )
        
        all_reports.append(report)
        report.print_report()
        
        # ✅ НОВОЕ: Генерируем план миграции для GraphicsPanel
        if panel_config['name'] == 'GraphicsPanel' and report.missing_in_refactored:
            generate_migration_plan(report, panel_config['monolith'])
    
    # Общая сводка
    print("\n\n" + "=" * 80)
    print("📊 ОБЩАЯ СВОДКА ПО ВСЕМ ПАНЕЛЯМ")
    print("=" * 80)
    
    total_monolith = sum(len(r.monolith_widgets) for r in all_reports)
    total_refactored = sum(len(r.refactored_widgets) for r in all_reports)
    total_matched = sum(len(r.matched_widgets) for r in all_reports)
    total_missing = sum(len(r.missing_in_refactored) for r in all_reports)
    
    print(f"\n📈 ИТОГО:")
    print(f"   Виджетов в монолитах: {total_monolith}")
    print(f"   Виджетов в рефакторинге: {total_refactored}")
    print(f"   Совпадающих: {total_matched}")
    print(f"   Отсутствующих: {total_missing}")
    
    if total_monolith > 0:
        overall_coverage = total_matched / total_monolith * 100
        print(f"\n🎯 ОБЩЕЕ ПОКРЫТИЕ: {overall_coverage:.1f}%")
    
    print("\n📋 ПО ПАНЕЛЯМ:")
    for report in all_reports:
        if len(report.monolith_widgets) > 0:
            coverage = len(report.matched_widgets) / len(report.monolith_widgets) * 100
            status = "✅" if coverage == 100 else "⚠️"
            print(f"   {status} {report.panel_name}: {coverage:.1f}% ({len(report.matched_widgets)}/{len(report.monolith_widgets)})")
    
    # Рекомендации
    print("\n" + "=" * 80)
    print("💡 РЕКОМЕНДАЦИИ")
    print("=" * 80)
    
    ready_panels = [r for r in all_reports if len(r.missing_in_refactored) == 0 and len(r.monolith_widgets) > 0]
    incomplete_panels = [r for r in all_reports if len(r.missing_in_refactored) > 0]
    
    if ready_panels:
        print(f"\n✅ ГОТОВЫ К ЗАМЕНЕ ({len(ready_panels)} панелей):")
        for r in ready_panels:
            print(f"   ✓ {r.panel_name}")
    
    if incomplete_panels:
        print(f"\n⚠️  ТРЕБУЮТ ДОРАБОТКИ ({len(incomplete_panels)} панелей):")
        for r in incomplete_panels:
            print(f"   • {r.panel_name}: добавить {len(r.missing_in_refactored)} параметров")
    
    print("\n✅ Анализ завершён!")
    print("\n📝 Смотрите план миграции выше для детальных инструкций")


if __name__ == "__main__":
    main()
