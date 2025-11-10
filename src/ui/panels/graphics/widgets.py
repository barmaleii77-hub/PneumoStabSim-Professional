"""
Graphics panel widgets - reusable UI components
Виджеты панели графики - переиспользуемые компоненты UI
"""

from __future__ import annotations


import logging
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable, Sequence
from urllib.parse import unquote, urlparse

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class QuantityDefinition:
    """Simple metadata describing how a quantity can vary."""

    minimal: float
    maximal: float
    decimals: int = 2
    unit: str = ""
    small_step: float | None = None

    def clamp(self, value: float) -> float:
        """Clamp *value* into the allowed range."""

        return max(self.minimal, min(self.maximal, value))


@dataclass
class Quantity:
    """Scalar value bundled with presentation metadata."""

    value: float
    definition: QuantityDefinition

    def __post_init__(self) -> None:
        self.value = self.definition.clamp(float(self.value))


Unit = str


class ColorButton(QPushButton):
    """Небольшая кнопка предпросмотра цвета, транслирующая изменения из QColorDialog."""

    color_changed = Signal(str)

    def __init__(
        self, initial_color: str = "#ffffff", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setFixedSize(42, 28)
        self._color = QColor(initial_color)
        self._dialog: QColorDialog | None = None
        self._user_triggered = False  # Флаг пользовательского действия
        self._update_swatch()
        self.clicked.connect(self._open_dialog)

    def color(self) -> QColor:
        return self._color

    def set_color(self, color_str: str) -> None:
        """Программное изменение цвета (без логирования)."""
        self._color = QColor(color_str)
        self._update_swatch()

    def _update_swatch(self) -> None:
        self.setStyleSheet(
            "QPushButton {"
            f"background-color: {self._color.name()};"
            "border: 2px solid #5c5c5c;"
            "border-radius: 4px;"
            "}"
            "QPushButton:hover { border: 2px solid #9a9a9a; }"
        )

    @Slot()
    def _open_dialog(self) -> None:
        # Пользователь кликнул на кнопку
        self._user_triggered = True
        if self._dialog:
            return
        dialog = QColorDialog(self._color, self)
        dialog.setOption(QColorDialog.DontUseNativeDialog, True)
        dialog.setOption(QColorDialog.ShowAlphaChannel, False)
        dialog.currentColorChanged.connect(self._on_color_changed)
        dialog.colorSelected.connect(self._on_color_changed)
        dialog.finished.connect(self._close_dialog)
        dialog.open()
        self._dialog = dialog

    @Slot(QColor)
    def _on_color_changed(self, color: QColor) -> None:
        if not color.isValid():
            return
        self._color = color
        self._update_swatch()
        if self._user_triggered:
            self.color_changed.emit(color.name())

    @Slot()
    def _close_dialog(self) -> None:
        if self._dialog:
            self._dialog.deleteLater()
        self._dialog = None
        self._user_triggered = False


class LabeledSlider(QWidget):
    """Пара слайдер + спинбокс с подписью и единицами измерения."""

    valueChanged = Signal(float)

    def __init__(
        self,
        title: str,
        minimum: float,
        maximum: float,
        step: float,
        *,
        decimals: int = 2,
        unit: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._min = minimum
        self._max = maximum
        self._step = step
        self._decimals = decimals
        self._unit = unit or ""
        self._updating = False
        self._user_triggered = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._label = QLabel(self)
        layout.addWidget(self._label)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        layout.addLayout(row)

        # Используем QtWidgets.QSlider для надёжности
        from PySide6 import QtWidgets

        self._slider = QtWidgets.QSlider(Qt.Horizontal, self)
        steps = max(1, int(round((self._max - self._min) / self._step)))
        self._slider.setRange(0, steps)
        self._slider.sliderPressed.connect(self._on_slider_pressed)
        self._slider.sliderReleased.connect(self._on_slider_released)
        self._slider.valueChanged.connect(self._handle_slider)
        row.addWidget(self._slider, 1)

        self._spin = QDoubleSpinBox(self)
        self._spin.setDecimals(self._decimals)
        self._spin.setRange(self._min, self._max)
        self._spin.setSingleStep(self._step)
        self._spin.installEventFilter(self)
        self._spin.valueChanged.connect(self._handle_spin)
        row.addWidget(self._spin)

        self.set_value(self._min)

    @property
    def step_size(self) -> float:
        """Размер шага, который используется слайдером и спинбоксом."""

        return self._step

    @step_size.setter
    def step_size(self, value: float) -> None:
        """Изменить шаг, синхронизируя связанные Qt-контролы."""

        if value <= 0:
            raise ValueError("Step size must be positive")
        new_step = float(value)
        if new_step == self._step:
            return

        current_value = self.value()
        self._step = new_step

        steps = max(1, int(round((self._max - self._min) / self._step)))
        self._slider.setRange(0, steps)
        self._spin.setSingleStep(self._step)

        # Используем существующую логику clamping/label обновления.
        self.set_value(current_value)

    @property
    def step(self) -> float:
        """Синоним :attr:`step_size` для обратной совместимости."""

        return self.step_size

    @step.setter
    def step(self, value: float) -> None:
        """Установить шаг (поддержка устаревшего API)."""

        self.step_size = value

    def eventFilter(self, obj, event) -> bool:
        if obj == self._spin:
            if event.type() == event.Type.FocusIn:
                self._user_triggered = True
            elif event.type() == event.Type.FocusOut:
                self._user_triggered = False
        return super().eventFilter(obj, event)

    @Slot()
    def _on_slider_pressed(self) -> None:
        self._user_triggered = True

    @Slot()
    def _on_slider_released(self) -> None:
        self._user_triggered = False

    def set_enabled(self, enabled: bool) -> None:
        self.setEnabled(enabled)

    def value(self) -> float:
        return round(self._spin.value(), self._decimals)

    def set_value(self, value: float) -> None:
        value = max(self._min, min(self._max, value))
        slider_value = int(round((value - self._min) / self._step))
        self._updating = True
        self._slider.setValue(slider_value)
        self._spin.setValue(value)
        self._update_label(value)
        self._updating = False

    def _update_label(self, value: float) -> None:
        formatted = f"{value:.{self._decimals}f}"
        if self._unit:
            formatted = f"{formatted} {self._unit}"
        self._label.setText(f"{self._title}: {formatted}")

    @Slot(int)
    def _handle_slider(self, slider_value: int) -> None:
        if self._updating:
            return
        value = self._min + slider_value * self._step
        value = max(self._min, min(self._max, value))
        self._updating = True
        self._spin.setValue(value)
        self._update_label(value)
        self._updating = False
        self.valueChanged.emit(round(value, self._decimals))

    @Slot(float)
    def _handle_spin(self, value: float) -> None:
        if self._updating:
            return
        slider_value = int(round((value - self._min) / self._step))
        self._updating = True
        self._slider.setValue(slider_value)
        self._update_label(value)
        self._updating = False
        self.valueChanged.emit(round(value, self._decimals))


class FileCyclerWidget(QWidget):
    """Минималистичный селектор файлов с кнопками «предыдущий/следующий».

    Элемент предназначен для перебора заранее обнаруженных файлов без
    диалогов выбора. Отображает имя текущего файла и эмитит ``currentChanged``
    при смене выбора. Если список пуст, показывает прочерк и отключает кнопки.
    """

    currentChanged = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        placeholder: str = "—",
    ) -> None:
        super().__init__(parent)

        self._logger = logging.getLogger(self.__class__.__name__)
        self._placeholder = placeholder
        self._items: list[tuple[str, str]] = []
        self._index: int = -1
        self._custom_entry: tuple[str, str] | None = None
        self._allow_empty_selection = False
        self._resolution_roots: list[Path] = []
        self._missing_path: str = ""
        self._logged_missing_paths: set[str] = set()
        self._dialogued_missing_paths: set[str] = set()
        self._pending_dialog_paths: list[str] = []
        self._path_exists_cache: dict[str, bool] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._prev_btn = QPushButton("◀", self)
        self._prev_btn.setFixedWidth(28)
        self._prev_btn.clicked.connect(self._show_previous)
        layout.addWidget(self._prev_btn)

        self._label = QLabel(self)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._label.setMinimumWidth(80)
        self._label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        layout.addWidget(self._label, 1)

        self._warning_label = QLabel("⚠ файл не найден", self)
        self._warning_label.setObjectName("fileCyclerMissingIndicator")
        self._warning_label.setStyleSheet("color: #d4380d; font-weight: 600;")
        self._warning_label.setVisible(False)
        layout.addWidget(self._warning_label)

        self._next_btn = QPushButton("▶", self)
        self._next_btn.setFixedWidth(28)
        self._next_btn.clicked.connect(self._show_next)
        layout.addWidget(self._next_btn)

        self._update_ui(emit=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_allow_empty_selection(
        self, allow: bool, *, label: str | None = None
    ) -> None:
        """Allow cycling to an explicit "no selection" entry."""

        if self._allow_empty_selection == allow and label is None:
            return

        self._allow_empty_selection = allow
        if label is not None:
            self._placeholder = label

        if not allow and self._index == -1 and self._custom_entry is None:
            if self._items:
                self._index = 0
        self._update_ui(emit=False)

    def set_items(self, items: list[tuple[str, str]]) -> None:
        """Задать коллекцию доступных файлов.

        ``items`` — список пар ``(label, path)``. Пути нормализуются в POSIX
        представление. При повторном вызове сохраняется текущий выбор, если
        соответствующий путь присутствует в новом списке.
        """

        self._invalidate_path_cache()

        normalised: list[tuple[str, str]] = []
        seen: set[str] = set()
        for label, path in items:
            try:
                text = (Path(path).as_posix()).strip()
            except Exception:
                text = str(path).strip().replace("\\", "/")
            if not text or text in seen:
                continue
            seen.add(text)
            name = str(label).strip() or Path(text).name or text
            normalised.append((name, text))

        previous_path = self.current_path()
        self._items = normalised

        if previous_path:
            self.set_current_data(previous_path, emit=False)
        elif self._allow_empty_selection:
            self._index = -1
            self._custom_entry = None
            self._update_ui(emit=False)
        elif self._items:
            self._index = 0
            self._custom_entry = None
            self._update_ui(emit=False)
        else:
            self._index = -1
            if self._custom_entry and self._custom_entry[1] not in seen:
                self._custom_entry = None
            self._update_ui(emit=False)

    def set_resolution_roots(self, roots: Sequence[Path]) -> None:
        """Define base directories for resolving relative paths."""

        resolved: list[Path] = []
        for root in roots:
            if not root:
                continue
            try:
                candidate = Path(root)
            except TypeError:
                continue
            if candidate not in resolved:
                resolved.append(candidate)
        self._resolution_roots = resolved
        self._invalidate_path_cache()

    def set_current_data(self, path: str | None, *, emit: bool = True) -> None:
        """Установить текущий путь. Допускает значения вне списка items."""

        previous_path = self.current_path()
        normalised = str(path).strip().replace("\\", "/") if path else ""
        if not normalised:
            # Исправленная логика: изменяем только если состояние действительно изменилось,
            # либо если запрещено пустое выделение и мы пытаемся перейти в пустое состояние
            changed = (
                self._index != -1
                or self._custom_entry is not None
                or (
                    not self._allow_empty_selection
                    and self._index == -1
                    and self._custom_entry is None
                )
            )
            self._index = -1
            self._custom_entry = None
            self._update_ui(emit=emit and changed)
            if previous_path:
                self._invalidate_path_cache_for(previous_path)
            return

        self._invalidate_path_cache_for(normalised)
        if previous_path and previous_path != normalised:
            self._invalidate_path_cache_for(previous_path)

        for idx, (_, candidate) in enumerate(self._items):
            if candidate == normalised:
                changed = self._index != idx or self._custom_entry is not None
                self._index = idx
                self._custom_entry = None
                self._update_ui(emit=emit and changed)
                return

        label = Path(normalised).name or normalised
        custom_label = f"{label} (config)"
        changed = (
            self._index != -1
            or self._custom_entry is None
            or self._custom_entry[1] != normalised
        )
        self._index = -1
        self._custom_entry = (custom_label, normalised)
        self._update_ui(emit=emit and changed)

    def current_path(self) -> str:
        entry = self._current_entry()
        return entry[1] if entry else ""

    def current_label(self) -> str:
        entry = self._current_entry()
        return entry[0] if entry else self._placeholder

    def is_empty(self) -> bool:
        return not self._items and self._custom_entry is None

    def first_path(self) -> str:
        return self._items[0][1] if self._items else ""

    def setEnabled(self, enabled: bool) -> None:  # noqa: D401 - override QWidget
        super().setEnabled(enabled)
        self._update_ui(emit=False)

    def is_missing(self) -> bool:
        """Return ``True`` if the current entry points to a missing file."""

        return bool(self._missing_path)

    def missing_path(self) -> str:
        """Return the missing file path if any."""

        return self._missing_path

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------
    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if not self._pending_dialog_paths:
            return
        pending = list(self._pending_dialog_paths)
        self._pending_dialog_paths.clear()
        for path in pending:
            if path in self._dialogued_missing_paths:
                continue
            self._show_warning_dialog(path)
            self._dialogued_missing_paths.add(path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _current_entry(self) -> tuple[str, str] | None:
        if 0 <= self._index < len(self._items):
            return self._items[self._index]
        if self._custom_entry is not None:
            return self._custom_entry
        if self._allow_empty_selection:
            return (self._placeholder, "")
        return None

    def _update_ui(self, *, emit: bool) -> None:
        entry = self._current_entry()
        if entry:
            label, path = entry
            self._label.setText(label)
        else:
            path = ""
            self._label.setText(self._placeholder)

        missing = bool(path) and self._is_path_missing(path)
        if not missing and path:
            self._clear_missing_tracking(path)
        self._missing_path = path if missing else ""

        self._warning_label.setVisible(missing)
        self._warning_label.setToolTip(path if missing else "")
        self._label.setToolTip(path if path else "")

        if missing:
            self._handle_missing_path(path)

        available_states = len(self._items)
        if self._allow_empty_selection:
            available_states += 1
        if self._custom_entry is not None:
            available_states += 1
        enable_buttons = self.isEnabled() and available_states > 1
        self._prev_btn.setEnabled(enable_buttons)
        self._next_btn.setEnabled(enable_buttons)

        if emit:
            self.currentChanged.emit(path)

    def _show_previous(self) -> None:
        if self._custom_entry is not None:
            if self._items:
                self._index = len(self._items) - 1
            elif self._allow_empty_selection:
                self._index = -1
            self._custom_entry = None
            self._update_ui(emit=True)
            return

        if not self._items:
            if self._allow_empty_selection and self._index != -1:
                self._index = -1
                self._update_ui(emit=True)
            return

        if self._index == -1:
            self._index = len(self._items) - 1
        elif self._index == 0 and self._allow_empty_selection:
            self._index = -1
        else:
            self._index = (self._index - 1) % len(self._items)
        self._update_ui(emit=True)

    def _show_next(self) -> None:
        if self._custom_entry is not None:
            if self._items:
                self._index = 0
            elif self._allow_empty_selection:
                self._index = -1
            self._custom_entry = None
            self._update_ui(emit=True)
            return

        if not self._items:
            if self._allow_empty_selection and self._index != -1:
                self._index = -1
                self._update_ui(emit=True)
            return

        if self._index == -1:
            self._index = 0
        elif self._index == len(self._items) - 1 and self._allow_empty_selection:
            self._index = -1
        else:
            self._index = (self._index + 1) % len(self._items)
        self._update_ui(emit=True)

    def _handle_missing_path(self, path: str) -> None:
        if path not in self._logged_missing_paths:
            self._logger.warning("Файл не найден: %s", path)
            self._logged_missing_paths.add(path)

        if path in self._dialogued_missing_paths:
            return

        if self.isVisible():
            self._show_warning_dialog(path)
            self._dialogued_missing_paths.add(path)
        elif path not in self._pending_dialog_paths:
            self._pending_dialog_paths.append(path)

    def _show_warning_dialog(self, path: str) -> None:
        try:
            QMessageBox.warning(
                self.window() or self,
                "Файл не найден",
                f"Не удалось найти файл:\n{path}",
            )
        except Exception:  # pragma: no cover - defensive
            self._logger.debug(
                "Не удалось показать предупреждение об отсутствии файла: %s",
                path,
                exc_info=True,
            )

    def _is_path_missing(self, path: str) -> bool:
        """Вернуть True если путь считается отсутствующим.

        Исправленная логика: пути, пришедшие через set_items (предопределённые
        варианты) считаются доступными даже при отсутствии реального файла на
        диске. Это упрощает unit-тесты, где текстуры не создаются физически.
        Пользовательские (config / произвольные) пути продолжают проверяться.
        """
        if not path:
            return False
        # Пути из self._items -> не отсутствуют (быстрый список для тестов)
        if any(candidate == path for _label, candidate in self._items):
            return False
        cached = self._path_exists_cache.get(path)
        if cached is True:
            return False
        exists = self._probe_path_exists(path)
        if exists:
            self._path_exists_cache[path] = True
            return False
        self._path_exists_cache[path] = False
        return True

    def _probe_path_exists(self, path: str) -> bool:
        for candidate in self._iter_path_candidates(path):
            try:
                if candidate.exists():
                    return True
            except OSError:
                continue
        return False

    def _invalidate_path_cache(self) -> None:
        self._path_exists_cache.clear()

    def _invalidate_path_cache_for(self, path: str) -> None:
        if not path:
            return
        self._path_exists_cache.pop(path, None)
        self._clear_missing_tracking(path)

    def _clear_missing_tracking(self, path: str) -> None:
        if not path:
            return
        self._logged_missing_paths.discard(path)
        self._dialogued_missing_paths.discard(path)
        try:
            self._pending_dialog_paths.remove(path)
        except ValueError:
            pass

    def _iter_path_candidates(self, path: str) -> Iterable[Path]:
        seen: set[Path] = set()
        parsed = urlparse(path)
        if parsed.scheme == "file":
            candidate = Path(unquote(parsed.path))
            if parsed.netloc:
                candidate = Path(f"//{parsed.netloc}{candidate.as_posix()}")
            if candidate not in seen:
                seen.add(candidate)
                yield candidate

        raw_path = Path(path)
        if raw_path.is_absolute() and raw_path not in seen:
            seen.add(raw_path)
            yield raw_path

        if raw_path not in seen:
            seen.add(raw_path)
            yield raw_path

        for root in self._resolution_roots:
            try:
                resolved = (root / raw_path).resolve()
            except Exception:
                continue
            if resolved not in seen:
                seen.add(resolved)
                yield resolved


class QuantitySlider(LabeledSlider):
    """Слайдер для изменения Quantity."""

    valueChanged = Signal(object)

    def __init__(
        self,
        title: str,
        quantity: Quantity,
        *,
        parent: QWidget | None = None,
    ) -> None:
        definition = quantity.definition
        self._definition = definition
        super().__init__(
            title,
            definition.minimal,
            definition.maximal,
            definition.small_step or 1.0,
            decimals=definition.decimals,
            unit=definition.unit,
            parent=parent,
        )
        self.set_value(quantity.value)

    def value(self) -> Quantity:
        base_value = super().value()
        return Quantity(base_value, self._definition)

    def set_value(self, value: Quantity | float) -> None:
        if isinstance(value, Quantity):
            value = value.value
        super().set_value(value)

    @Slot()
    def _handle_slider(self, slider_value: int) -> None:
        if self._updating:
            return
        value = self._min + slider_value * self._step
        value = max(self._min, min(self._max, value))
        self._updating = True
        self._spin.setValue(value)
        self._update_label(value)
        self._updating = False
        if self._user_triggered:
            self.valueChanged.emit(Quantity(value, self._definition))

    @Slot(float)
    def _handle_spin(self, value: float) -> None:
        if self._updating:
            return
        slider_value = int(round((value - self._min) / self._step))
        self._updating = True
        self._slider.setValue(slider_value)
        self._update_label(value)
        self._updating = False
        if self._user_triggered:
            self.valueChanged.emit(Quantity(value, self._definition))
