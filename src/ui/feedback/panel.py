"""Qt widget that wraps the QML feedback form."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget

from .controller import FeedbackController

_LOGGER = logging.getLogger(__name__)

_QML_PATH = Path(__file__).with_name("FeedbackForm.qml")


class FeedbackPanel(QWidget):
    """Embeddable widget that hosts the QML feedback form."""

    def __init__(
        self,
        window: QWidget,
        controller: FeedbackController | None = None,
    ) -> None:
        super().__init__(window)
        self._controller = controller or FeedbackController(parent=self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._quick_widget = QQuickWidget(self)
        self._quick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        layout.addWidget(self._quick_widget)

        engine = self._quick_widget.engine()
        context = engine.rootContext()
        context.setContextProperty("feedbackController", self._controller)

        if not _QML_PATH.exists():
            _LOGGER.error("Feedback QML form missing: %s", _QML_PATH)
            return

        self._quick_widget.setSource(QUrl.fromLocalFile(str(_QML_PATH)))


__all__ = ["FeedbackPanel"]
