"""
Модуль накопления и вывода предупреждений и ошибок.

Собирает warnings/errors на протяжении работы приложения
и выводит их в конце для удобства диагностики.
"""


class WarningErrorCollector:
    """Коллектор предупреждений и ошибок приложения."""

    def __init__(self) -> None:
        self._items: list[tuple[str, str]] = []

    def log_warning(self, msg: str) -> None:
        """Накапливает warning для вывода в конце."""
        self._items.append(("WARNING", msg))

    def log_error(self, msg: str) -> None:
        """Накапливает error для вывода в конце."""
        self._items.append(("ERROR", msg))

    def print_all(self) -> None:
        """Выводит все накопленные warnings/errors."""
        if not self._items:
            return

        print("\n" + "=" * 60)
        print("⚠️  WARNINGS & ERRORS:")
        print("=" * 60)

        warnings = [msg for level, msg in self._items if level == "WARNING"]
        errors = [msg for level, msg in self._items if level == "ERROR"]

        if warnings:
            print("\n⚠️  Warnings:")
            for w in warnings:
                print(f"  • {w}")

        if errors:
            print("\n❌ Errors:")
            for e in errors:
                print(f"  • {e}")

        print("=" * 60 + "\n")


# Глобальный экземпляр коллектора
_collector = WarningErrorCollector()


def log_warning(msg: str) -> None:
    """Накапливает warning для вывода в конце."""
    _collector.log_warning(msg)


def log_error(msg: str) -> None:
    """Накапливает error для вывода в конце."""
    _collector.log_error(msg)


def print_warnings_errors() -> None:
    """Выводит все накопленные warnings/errors."""
    _collector.print_all()
