from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QColorDialog,
    QGroupBox,
    QFormLayout,
)
from PyQt6.QtCore import Qt
import qtawesome as qta
import src.ui.logic.ui_utils as ui_utils


class PlotOptionsDialog(QDialog):
    """
    Dialog for customizing plot options such as line style, color, markers, etc.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Options")
        self.setWindowIcon(qta.icon("mdi.chart-line", color="blue"))
        self.resize(400, 500)

        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # --- Plot Type Group ---
        plot_type_group = QGroupBox("Plot Type")
        plot_type_layout = QFormLayout(plot_type_group)

        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Line Plot", "Scatter Plot", "Line + Scatter"])
        self.plot_type_combo.setCurrentText("Line + Scatter")
        plot_type_layout.addRow("Type:", self.plot_type_combo)

        layout.addWidget(plot_type_group)

        # --- Plot Style (Theme) Group ---
        style_group = QGroupBox("Theme / Style")
        style_layout = QFormLayout(style_group)
        self.style_combo = QComboBox()
        self.style_combo.addItems(
            [
                "Science",
                "Science (Notebook)",
                "IEEE",
                "Nature",
                "High-Vis",
                "Vibrant",
                "Muted",
            ]
        )
        self.style_combo.setCurrentText("Science (Notebook)")
        style_layout.addRow("Theme:", self.style_combo)
        layout.addWidget(style_group)

        # --- Line Style Group ---
        line_group = QGroupBox("Line Style")
        line_layout = QFormLayout(line_group)

        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(["Solid", "Dashed", "Dotted", "Dash-Dot"])
        line_layout.addRow("Style:", self.line_style_combo)

        self.line_width_spin = QSpinBox()
        self.line_width_spin.setRange(1, 10)
        self.line_width_spin.setValue(2)
        line_layout.addRow("Width:", self.line_width_spin)

        layout.addWidget(line_group)

        # --- Marker Group ---
        marker_group = QGroupBox("Markers")
        marker_layout = QFormLayout(marker_group)

        self.marker_combo = QComboBox()
        self.marker_combo.addItems(
            ["None", "Circle", "Square", "Triangle", "Diamond", "Star"]
        )
        self.marker_combo.setCurrentText("Circle")
        marker_layout.addRow("Shape:", self.marker_combo)

        self.marker_size_spin = QSpinBox()
        self.marker_size_spin.setRange(1, 20)
        self.marker_size_spin.setValue(6)
        marker_layout.addRow("Size:", self.marker_size_spin)

        layout.addWidget(marker_group)

        # --- Color Group ---
        color_group = QGroupBox("Colors")
        color_layout = QVBoxLayout(color_group)

        # Line Color
        line_color_layout = QHBoxLayout()
        line_color_layout.addWidget(QLabel("Line Color:"))
        self.line_color_button = QPushButton()
        self.line_color_button.setFixedSize(50, 30)
        self.line_color_button.setStyleSheet("background-color: blue;")
        self.line_color_button.clicked.connect(self.choose_line_color)
        line_color_layout.addWidget(self.line_color_button)
        line_color_layout.addStretch()
        color_layout.addLayout(line_color_layout)

        # Marker Color
        marker_color_layout = QHBoxLayout()
        marker_color_layout.addWidget(QLabel("Marker Color:"))
        self.marker_color_button = QPushButton()
        self.marker_color_button.setFixedSize(50, 30)
        self.marker_color_button.setStyleSheet("background-color: red;")
        self.marker_color_button.clicked.connect(self.choose_marker_color)
        marker_color_layout.addWidget(self.marker_color_button)
        marker_color_layout.addStretch()
        color_layout.addLayout(marker_color_layout)

        layout.addWidget(color_group)

        # --- Grid and Legend ---
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self.grid_check = QCheckBox("Show Grid")
        self.grid_check.setChecked(False)
        options_layout.addWidget(self.grid_check)

        self.legend_check = QCheckBox("Show Legend")
        self.legend_check.setChecked(True)
        options_layout.addWidget(self.legend_check)

        layout.addWidget(options_group)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Store initial colors
        self.line_color = "blue"
        self.marker_color = "red"

    def choose_line_color(self):
        """Open color dialog for line color."""
        color = ui_utils.pick_color(self.line_color, self)
        if color:
            self.line_color = color
            self.line_color_button.setStyleSheet(
                f"background-color: {self.line_color};"
            )

    def choose_marker_color(self):
        """Open color dialog for marker color."""
        color = ui_utils.pick_color(self.marker_color, self)
        if color:
            self.marker_color = color
            self.marker_color_button.setStyleSheet(
                f"background-color: {self.marker_color};"
            )

    def get_options(self):
        """Return the selected plot options as a dictionary."""
        return {
            "plot_type": self.plot_type_combo.currentText(),
            "plot_style": self.style_combo.currentText(),
            "line_style": self.line_style_combo.currentText(),
            "line_width": self.line_width_spin.value(),
            "marker": self.marker_combo.currentText(),
            "marker_size": self.marker_size_spin.value(),
            "line_color": self.line_color,
            "marker_color": self.marker_color,
            "show_grid": self.grid_check.isChecked(),
            "show_legend": self.legend_check.isChecked(),
        }
