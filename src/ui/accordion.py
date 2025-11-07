"""
Accordion Widget - Collapsible sections for parameters
Replaces dock widgets with classic accordion layout
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QFrame,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve


class AccordionSection(QWidget):
    """Single collapsible section in accordion"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self._is_expanded = False
        self._animation_duration = 200  # ms

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header button
        self.header_button = QPushButton(f"? {title}")
        self.header_button.setCheckable(True)
        self.header_button.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                background-color: #2a2a3e;
                color: #ffffff;
                border: none;
                border-bottom: 1px solid #1a1a2e;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #3a3a4e;
            }
            QPushButton:checked {
                background-color: #4a4a5e;
            }
        """
        )
        self.header_button.clicked.connect(self._on_header_clicked)

        main_layout.addWidget(self.header_button)

        # Content container
        self.content_container = QFrame()
        self.content_container.setStyleSheet(
            """
            QFrame {
                background-color: #1e1e2e;
                border: none;
            }
        """
        )
        self.content_container.setMaximumHeight(0)  # Initially collapsed

        # Content layout (will be populated externally)
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(12, 8, 12, 8)
        self.content_layout.setSpacing(6)

        main_layout.addWidget(self.content_container)

        # Animation for expand/collapse
        self.animation = QPropertyAnimation(self.content_container, b"maximumHeight")
        self.animation.setDuration(self._animation_duration)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def _on_header_clicked(self):
        """Handle header click to expand/collapse"""
        if self.header_button.isChecked():
            self.expand()
        else:
            self.collapse()

    def expand(self):
        """Expand section"""
        if self._is_expanded:
            return

        # Update header
        title = self.header_button.text().replace("?", "?")
        self.header_button.setText(title)
        self.header_button.setChecked(True)

        # Animate expansion
        # Calculate content height
        content_height = self.content_layout.sizeHint().height()

        self.animation.setStartValue(0)
        self.animation.setEndValue(content_height)
        self.animation.start()

        self._is_expanded = True

    def collapse(self):
        """Collapse section"""
        if not self._is_expanded:
            return

        # Update header
        title = self.header_button.text().replace("?", "?")
        self.header_button.setText(title)
        self.header_button.setChecked(False)

        # Animate collapse
        current_height = self.content_container.maximumHeight()

        self.animation.setStartValue(current_height)
        self.animation.setEndValue(0)
        self.animation.start()

        self._is_expanded = False

    def set_content_widget(self, widget: QWidget):
        """Set content widget for this section"""
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new widget
        self.content_layout.addWidget(widget)
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def is_expanded(self) -> bool:
        """Check if section is expanded"""
        return self._is_expanded


class AccordionWidget(QScrollArea):
    """Accordion widget with multiple collapsible sections

    Replaces the dock widget approach with a classic accordion.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Configure scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Style
        self.setStyleSheet(
            """
            QScrollArea {
                background-color: #1a1a2e;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1a2e;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a5e;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a5a6e;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
        )

        # Main container
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setWidget(self.container)

        # Sections storage
        self.sections = {}

    def add_section(
        self, name: str, title: str, content_widget: QWidget, expanded: bool = False
    ) -> AccordionSection:
        """Add a new section to accordion

        Args:
            name: Internal name for section
            title: Display title for section header
            content_widget: Widget to show in section content
            expanded: Whether section starts expanded

        Returns:
            AccordionSection instance
        """
        section = AccordionSection(title, self)
        section.set_content_widget(content_widget)

        self.container_layout.addWidget(section)
        self.sections[name] = section

        if expanded:
            section.expand()

        return section

    def get_section(self, name: str) -> AccordionSection:
        """Get section by name"""
        return self.sections.get(name)

    def expand_section(self, name: str):
        """Expand specific section"""
        if name in self.sections:
            self.sections[name].expand()

    def collapse_section(self, name: str):
        """Collapse specific section"""
        if name in self.sections:
            self.sections[name].collapse()

    def collapse_all(self):
        """Collapse all sections"""
        for section in self.sections.values():
            section.collapse()

    def expand_all(self):
        """Expand all sections"""
        for section in self.sections.values():
            section.expand()


# Export
__all__ = ["AccordionWidget", "AccordionSection"]
