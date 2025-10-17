# -*- coding: utf-8 -*-
"""
Анализатор размеров файлов проекта
Помогает выявить файлы, требующие рефакторинга
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List
import json


@dataclass
class FileStats:
    """Статистика файла"""
    path: Path
    lines: int
    size_kb: float
    
    @property
    def relative_path(self) -> str:
        """Относительный путь от корня проекта"""
        try:
            return str(self.path.relative_to(Path.cwd()))
        except ValueError:
            return str(self.path)
    
    @property
    def priority(self) -> str:
        """Приоритет реструктуризации"""
        if self.lines > 1000:
            return "⭐⭐⭐ КРИТИЧЕСКИЙ"
        elif self.lines > 700:
            return "⭐⭐ ВЫСОКИЙ"
        elif self.lines > 500:
            return "⭐ СРЕДНИЙ"
        else:
            return "✅ OK"


def count_lines(file_path: Path) -> int:
    """Подсчитать строки в файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception:
        return 0


def get_file_size_kb(file_path: Path) -> float:
    """Получить размер файла в КБ"""
    try:
        return file_path.stat().st_size / 1024
    except Exception:
        return 0.0


def analyze_directory(
    directory: Path,
    extensions: List[str] = ['.py'],
    exclude_patterns: List[str] = ['__pycache__', 'venv', '.git', 'build', 'dist']
) -> List[FileStats]:
    """Анализировать директорию на предмет больших файлов
    
    Args:
        directory: Директория для анализа
        extensions: Расширения файлов для анализа
        exclude_patterns: Паттерны исключения
    
    Returns:
        Список статистики файлов, отсортированный по убыванию размера
    """
    stats: List[FileStats] = []
    
    for root, dirs, files in os.walk(directory):
        # Исключаем ненужные директории
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = Path(root) / file
                lines = count_lines(file_path)
                size_kb = get_file_size_kb(file_path)
                
                stats.append(FileStats(
                    path=file_path,
                    lines=lines,
                    size_kb=size_kb
                ))
    
    # Сортировка по убыванию строк
    stats.sort(key=lambda x: x.lines, reverse=True)
    return stats


def print_report(stats: List[FileStats], top_n: int = 20):
    """Вывести отчёт о файлах"""
    print("=" * 100)
    print("📊 АНАЛИЗ РАЗМЕРОВ ФАЙЛОВ ПРОЕКТА")
    print("=" * 100)
    print()
    
    # Общая статистика
    total_files = len(stats)
    critical = sum(1 for s in stats if s.lines > 1000)
    high = sum(1 for s in stats if 700 < s.lines <= 1000)
    medium = sum(1 for s in stats if 500 < s.lines <= 700)
    
    print(f"Всего Python файлов: {total_files}")
    print(f"  ⭐⭐⭐ Критические (>1000 строк): {critical}")
    print(f"  ⭐⭐   Высокие (700-1000 строк): {high}")
    print(f"  ⭐     Средние (500-700 строк): {medium}")
    print()
    
    # Топ файлов
    print(f"🔝 ТОП-{top_n} САМЫХ БОЛЬШИХ ФАЙЛОВ:")
    print()
    print(f"{'№':<4} {'Строк':<7} {'Размер':<10} {'Приоритет':<20} {'Файл':<60}")
    print("-" * 100)
    
    for i, stat in enumerate(stats[:top_n], 1):
        print(f"{i:<4} {stat.lines:<7} {stat.size_kb:<10.2f} {stat.priority:<20} {stat.relative_path:<60}")
    
    print()
    print("=" * 100)
    
    # Рекомендации
    print()
    print("💡 РЕКОМЕНДАЦИИ:")
    print()
    if critical > 0:
        print(f"  ⚠️  Найдено {critical} критических файлов - СРОЧНО требуется рефакторинг!")
    if high > 0:
        print(f"  ⚠️  Найдено {high} файлов высокого приоритета - рекомендуется рефакторинг")
    if medium > 0:
        print(f"  ℹ️  Найдено {medium} файлов среднего приоритета - рассмотреть рефакторинг")
    
    if critical == 0 and high == 0:
        print("  ✅ Проект в отличном состоянии! Нет критических файлов.")
    
    print()


def export_json(stats: List[FileStats], output_path: Path):
    """Экспортировать статистику в JSON"""
    data = {
        "timestamp": str(Path.cwd()),
        "total_files": len(stats),
        "files": [
            {
                "path": s.relative_path,
                "lines": s.lines,
                "size_kb": round(s.size_kb, 2),
                "priority": s.priority
            }
            for s in stats
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Статистика экспортирована в: {output_path}")


def main():
    """Главная функция"""
    # Анализируем проект
    project_root = Path.cwd()
    src_dir = project_root / "src"
    
    print(f"🔍 Анализ проекта: {project_root}")
    print(f"📁 Директория src: {src_dir}")
    print()
    
    if not src_dir.exists():
        print("❌ Директория src не найдена!")
        return
    
    # Получаем статистику
    stats = analyze_directory(
        directory=src_dir,
        extensions=['.py'],
        exclude_patterns=['__pycache__', 'venv', '.git', 'build', 'dist', '.pytest_cache']
    )
    
    # Выводим отчёт
    print_report(stats, top_n=30)
    
    # Экспортируем в JSON
    output_path = project_root / "file_stats.json"
    export_json(stats, output_path)


if __name__ == "__main__":
    main()
