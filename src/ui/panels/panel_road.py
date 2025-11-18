"""
Road profiles configuration panel
Controls for loading and selecting road excitation profiles
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QLabel,
    QComboBox,
    QFileDialog,
    QTextEdit,
    QSizePolicy,
    QMessageBox,
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont
import os


class RoadPanel(QWidget):
    """Panel for road profile configuration

    Provides controls for:
    - Loading CSV road profiles
    - Selecting preset road scenarios
    - Applying profiles to specific wheels
    - Profile information display
    """

    # Signals
    load_csv_profile = Signal(str)  # file_path
    apply_preset = Signal(str)  # preset_name
    apply_to_wheels = Signal(str, list)  # profile_name, wheel_list
    clear_profiles = Signal()  # Clear all profiles

    def __init__(self, parent=None):
        super().__init__(parent)

        # Current profile information
        self.current_csv_path = ""
        self.current_preset = ""
        self.available_presets = [
            "Smooth Highway",
            "City Streets",
            "Rough Road",
            "Off-Road",
            "Speed Bumps",
            "Pothole Field",
            "Sine Wave 1Hz",
            "Sine Wave 2Hz",
            "Chirp Sweep",
            "Step Input",
        ]

        # Setup UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Title
        title_label = QLabel("Road Profiles")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # CSV file loading group
        csv_group = self._create_csv_group()
        layout.addWidget(csv_group)

        # Preset selection group
        preset_group = self._create_preset_group()
        layout.addWidget(preset_group)

        # Wheel assignment group
        assignment_group = self._create_assignment_group()
        layout.addWidget(assignment_group)

        # Profile information group
        info_group = self._create_info_group()
        layout.addWidget(info_group)

        # Control buttons
        buttons_layout = self._create_buttons()
        layout.addLayout(buttons_layout)

        layout.addStretch()

    def _create_csv_group(self) -> QGroupBox:
        """Create CSV file loading group"""
        group = QGroupBox("Load CSV Profile")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        # File path display
        path_layout = QHBoxLayout()
        path_layout.setSpacing(4)

        self.csv_path_label = QLabel("No file selected")
        self.csv_path_label.setStyleSheet("QLabel { color: gray; font-style: italic; }")
        path_layout.addWidget(self.csv_path_label)

        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setMaximumWidth(80)
        path_layout.addWidget(self.browse_button)

        layout.addLayout(path_layout)

        # Load button
        self.load_csv_button = QPushButton("Load CSV Profile")
        self.load_csv_button.setEnabled(False)
        layout.addWidget(self.load_csv_button)

        return group

    def _create_preset_group(self) -> QGroupBox:
        """Create preset selection group"""
        group = QGroupBox("Preset Profiles")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        # Preset selection combo box
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(4)

        preset_label = QLabel("Preset:")
        preset_layout.addWidget(preset_label)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Select preset...")
        self.preset_combo.addItems(self.available_presets)
        preset_layout.addWidget(self.preset_combo)

        layout.addLayout(preset_layout)

        # Apply preset button
        self.apply_preset_button = QPushButton("Apply Preset")
        self.apply_preset_button.setEnabled(False)
        layout.addWidget(self.apply_preset_button)

        return group

    def _create_assignment_group(self) -> QGroupBox:
        """Create wheel assignment group"""
        group = QGroupBox("Apply to Wheels")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        # Quick apply buttons
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(4)

        self.apply_all_button = QPushButton("All Wheels")
        self.apply_front_button = QPushButton("Front Only")
        self.apply_rear_button = QPushButton("Rear Only")

        quick_layout.addWidget(self.apply_all_button)
        quick_layout.addWidget(self.apply_front_button)
        quick_layout.addWidget(self.apply_rear_button)

        layout.addLayout(quick_layout)

        # Individual wheel buttons
        individual_layout = QHBoxLayout()
        individual_layout.setSpacing(4)

        self.apply_lf_button = QPushButton("LF")
        self.apply_rf_button = QPushButton("RF")
        self.apply_lr_button = QPushButton("LR")
        self.apply_rr_button = QPushButton("RR")

        # Make them smaller
        for btn in [
            self.apply_lf_button,
            self.apply_rf_button,
            self.apply_lr_button,
            self.apply_rr_button,
        ]:
            btn.setMaximumWidth(50)

        individual_layout.addWidget(self.apply_lf_button)
        individual_layout.addWidget(self.apply_rf_button)
        individual_layout.addWidget(self.apply_lr_button)
        individual_layout.addWidget(self.apply_rr_button)
        individual_layout.addStretch()

        layout.addLayout(individual_layout)

        # Disable all initially
        for btn in [
            self.apply_all_button,
            self.apply_front_button,
            self.apply_rear_button,
            self.apply_lf_button,
            self.apply_rf_button,
            self.apply_lr_button,
            self.apply_rr_button,
        ]:
            btn.setEnabled(False)

        return group

    def _create_info_group(self) -> QGroupBox:
        """Create profile information display group"""
        group = QGroupBox("Profile Information")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        # Information text area
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(100)
        self.info_text.setReadOnly(True)
        self.info_text.setPlainText("No profile loaded.")
        layout.addWidget(self.info_text)

        return group

    def _create_buttons(self) -> QHBoxLayout:
        """Create control buttons"""
        layout = QHBoxLayout()
        layout.setSpacing(4)

        # Clear all profiles
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self._clear_all_profiles)
        layout.addWidget(self.clear_button)

        # Refresh presets
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_presets)
        layout.addWidget(self.refresh_button)

        layout.addStretch()

        return layout

    def _connect_signals(self):
        """Connect widget signals"""
        # CSV loading
        self.browse_button.clicked.connect(self._browse_csv_file)
        self.load_csv_button.clicked.connect(self._load_csv_file)

        # Preset selection
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        self.apply_preset_button.clicked.connect(self._apply_current_preset)

        # Wheel assignment buttons
        self.apply_all_button.clicked.connect(
            lambda: self._apply_to_wheels(["LF", "RF", "LR", "RR"])
        )
        self.apply_front_button.clicked.connect(
            lambda: self._apply_to_wheels(["LF", "RF"])
        )
        self.apply_rear_button.clicked.connect(
            lambda: self._apply_to_wheels(["LR", "RR"])
        )

        self.apply_lf_button.clicked.connect(lambda: self._apply_to_wheels(["LF"]))
        self.apply_rf_button.clicked.connect(lambda: self._apply_to_wheels(["RF"]))
        self.apply_lr_button.clicked.connect(lambda: self._apply_to_wheels(["LR"]))
        self.apply_rr_button.clicked.connect(lambda: self._apply_to_wheels(["RR"]))

    @Slot()
    def _browse_csv_file(self):
        """Browse for CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Road Profile CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.current_csv_path = file_path

            # Update display
            filename = os.path.basename(file_path)
            self.csv_path_label.setText(filename)
            self.csv_path_label.setStyleSheet("QLabel { color: black; }")

            # Enable load button
            self.load_csv_button.setEnabled(True)

            # Show basic file info
            try:
                file_size = os.path.getsize(file_path)
                self.info_text.setPlainText(
                    f"Selected file: {filename}\nSize: {file_size} bytes"
                )
            except Exception as e:
                self.info_text.setPlainText(
                    f"Selected file: {filename}\nError reading file info: {e}"
                )

    @Slot()
    def _load_csv_file(self):
        """Load the selected CSV file"""
        if not self.current_csv_path:
            return

        try:
            # Emit signal to load the CSV
            self.load_csv_profile.emit(self.current_csv_path)

            # Update info
            filename = os.path.basename(self.current_csv_path)
            self.info_text.setPlainText(f"Loaded CSV profile: {filename}")

            # Enable wheel assignment buttons
            self._enable_assignment_buttons(True)

            # Clear preset selection
            self.preset_combo.setCurrentIndex(0)

        except Exception as e:
            QMessageBox.critical(
                self, "Error Loading CSV", f"Failed to load CSV file:\n{str(e)}"
            )

    @Slot(str)
    def _on_preset_selected(self, preset_name: str):
        """Handle preset selection

        Args:
            preset_name: Name of selected preset
        """
        if preset_name and preset_name != "Select preset...":
            self.current_preset = preset_name
            self.apply_preset_button.setEnabled(True)

            # Show preset description
            self._show_preset_info(preset_name)
        else:
            self.current_preset = ""
            self.apply_preset_button.setEnabled(False)

    def _show_preset_info(self, preset_name: str):
        """Show information about the selected preset

        Args:
            preset_name: Name of preset to describe
        """
        descriptions = {
            "Smooth Highway": "Low amplitude, high frequency road surface typical of good highways",
            "City Streets": "Medium amplitude with mixed frequencies for urban driving",
            "Rough Road": "High amplitude, low frequency excitation for poor road conditions",
            "Off-Road": "Random, high amplitude excitation for off-road terrain",
            "Speed Bumps": "Periodic high amplitude bumps at regular intervals",
            "Pothole Field": "Random negative excitations simulating potholes",
            "Sine Wave 1Hz": "Pure sinusoidal excitation at 1 Hz",
            "Sine Wave 2Hz": "Pure sinusoidal excitation at 2 Hz",
            "Chirp Sweep": "Frequency sweep from 0.1 to 10 Hz",
            "Step Input": "Step input for system response testing",
        }

        description = descriptions.get(preset_name, "No description available")
        self.info_text.setPlainText(f"Preset: {preset_name}\n\n{description}")

    @Slot()
    def _apply_current_preset(self):
        """Apply the currently selected preset"""
        if not self.current_preset:
            return

        try:
            # Emit signal to apply preset
            self.apply_preset.emit(self.current_preset)

            # Update info
            self.info_text.setPlainText(f"Applied preset: {self.current_preset}")

            # Enable wheel assignment buttons
            self._enable_assignment_buttons(True)

            # Clear CSV path
            self.current_csv_path = ""
            self.csv_path_label.setText("No file selected")
            self.csv_path_label.setStyleSheet(
                "QLabel { color: gray; font-style: italic; }"
            )
            self.load_csv_button.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(
                self, "Error Applying Preset", f"Failed to apply preset:\n{str(e)}"
            )

    def _apply_to_wheels(self, wheels: list):
        """Apply current profile to specified wheels

        Args:
            wheels: List of wheel names (e.g., ["LF", "RF"])
        """
        if self.current_csv_path:
            profile_name = os.path.basename(self.current_csv_path)
        elif self.current_preset:
            profile_name = self.current_preset
        else:
            QMessageBox.warning(
                self, "No Profile", "No profile is currently loaded or selected."
            )
            return

        # Emit signal
        self.apply_to_wheels.emit(profile_name, wheels)

        # Update info
        wheels_str = ", ".join(wheels)
        current_info = self.info_text.toPlainText()
        self.info_text.setPlainText(
            f"{current_info}\n\nApplied to wheels: {wheels_str}"
        )

    def _enable_assignment_buttons(self, enabled: bool):
        """Enable or disable wheel assignment buttons

        Args:
            enabled: True to enable buttons
        """
        for btn in [
            self.apply_all_button,
            self.apply_front_button,
            self.apply_rear_button,
            self.apply_lf_button,
            self.apply_rf_button,
            self.apply_lr_button,
            self.apply_rr_button,
        ]:
            btn.setEnabled(enabled)

    @Slot()
    def _clear_all_profiles(self):
        """Clear all loaded profiles"""
        # Reset state
        self.current_csv_path = ""
        self.current_preset = ""

        # Reset UI
        self.csv_path_label.setText("No file selected")
        self.csv_path_label.setStyleSheet("QLabel { color: gray; font-style: italic; }")
        self.load_csv_button.setEnabled(False)

        self.preset_combo.setCurrentIndex(0)
        self.apply_preset_button.setEnabled(False)

        self._enable_assignment_buttons(False)

        self.info_text.setPlainText("All profiles cleared.")

        # Emit signal
        self.clear_profiles.emit()

    @Slot()
    def _refresh_presets(self):
        """Refresh available presets"""
        # In a real implementation, this might reload presets from a file
        # For now, just show a message
        QMessageBox.information(self, "Refresh Presets", "Preset list refreshed.")

    def get_current_profile_info(self) -> dict:
        """Get information about currently loaded profile

        Returns:
            Dictionary with profile information
        """
        return {
            "csv_path": self.current_csv_path,
            "preset": self.current_preset,
            "has_profile": bool(self.current_csv_path or self.current_preset),
        }

    def get_parameters(self) -> dict:
        """Return a snapshot of the current road panel state."""

        return {
            "csv_path": self.current_csv_path,
            "preset": self.current_preset,
            "has_profile": bool(self.current_csv_path or self.current_preset),
            "available_presets": list(self.available_presets),
        }

    def collect_state(self) -> dict:
        """Return a detached copy of the UI state for persistence."""

        return dict(self.get_parameters())
