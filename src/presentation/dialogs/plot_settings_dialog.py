import os
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QLabel,
    QGroupBox,
    QScrollArea,
    QWidget,
    QLineEdit,
    QColorDialog,
    QGridLayout,
)
from PyQt6.QtCore import Qt
import qtawesome as qta
import seebeck_prime.presentation.ui_utils as ui_utils


class PlotSettingsDialog(QDialog):
    def __init__(self, sample_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Settings")
        self.setMinimumSize(600, 500)
        self.sample_names = sample_names

        # Default properties to plot.
        # The same columns and units as the default Multi-Sample path
        # (S/cm, uV/K, mW/(m*K^2)) so both paths report identical numbers
        # - audit issue SE-016 (author decision: Multi-Sample uses S/cm).
        self.properties = [
            ("Sigma_Scm", "Electrical Conductivity (S/cm)"),
            ("S_uVK", "Seebeck Coefficient (μV/K)"),
            ("PF_mW", "Power Factor (mW/mK²)"),
            ("Kappa_total", "Total Thermal Cond. (W/mK)"),
            ("Electronic TC", "Electronic TC (W/mK)"),
            ("Lattice TC", "Lattice TC (W/mK)"),
            ("ZT", "ZT"),
        ]

        # Colors and Markers
        self.default_colors = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
        ]
        self.markers = ["o", "s", "D", "^", "v", "<", ">", "p", "h", "*"]

        self.settings = {
            "selected_props": [],  # indices
            "multi_panel": False,
            "sample_styles": {},  # {name: {label: str, color: hex, marker: str}}
        }

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. Properties Selection
        prop_group = QGroupBox("Select Properties to Plot")
        prop_layout = QGridLayout(prop_group)
        self.prop_checkboxes = []
        for i, (key, label) in enumerate(self.properties):
            cb = QCheckBox(key)
            cb.setChecked(True)
            prop_layout.addWidget(cb, i // 2, i % 2)
            self.prop_checkboxes.append(cb)
        main_layout.addWidget(prop_group)

        # 2. Layout Options
        layout_group = QGroupBox("Layout Options")
        layout_grid = QGridLayout(layout_group)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Separate Windows", "Single Figure (Multi-panel)"])
        layout_grid.addWidget(QLabel("Plot Mode:"), 0, 0)
        layout_grid.addWidget(self.mode_combo, 0, 1)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 10)
        self.rows_spin.setValue(1)
        layout_grid.addWidget(QLabel("Rows:"), 1, 0)
        layout_grid.addWidget(self.rows_spin, 1, 1)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 10)
        self.cols_spin.setValue(2)
        layout_grid.addWidget(QLabel("Columns:"), 1, 2)
        layout_grid.addWidget(self.cols_spin, 1, 3)

        main_layout.addWidget(layout_group)

        # 3. Sample Customization (Scrollable)
        sample_group = QGroupBox("Sample Style Customization")
        sample_layout = QVBoxLayout(sample_group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.sample_grid = QGridLayout(scroll_content)

        self.sample_grid.addWidget(QLabel("<b>Original Name</b>"), 0, 0)
        self.sample_grid.addWidget(QLabel("<b>Display Label</b>"), 0, 1)
        self.sample_grid.addWidget(QLabel("<b>Color</b>"), 0, 2)
        self.sample_grid.addWidget(QLabel("<b>Symbol</b>"), 0, 3)

        self.style_widgets = {}  # {name: {label_edit, color_btn, marker_combo}}

        for i, name in enumerate(self.sample_names):
            row = i + 1
            name_label = QLabel(name)
            name_label.setToolTip(name)

            label_edit = QLineEdit(name)

            color = self.default_colors[i % len(self.default_colors)]
            color_btn = QPushButton()
            color_btn.setFixedWidth(40)
            color_btn.setStyleSheet(
                f"background-color: {color}; border: 1px solid gray;"
            )
            color_btn.clicked.connect(
                lambda checked=False, n=name, b=color_btn: self.pick_color(n, b)
            )

            marker_combo = QComboBox()
            marker_combo.addItems(self.markers)
            marker_combo.setCurrentIndex(i % len(self.markers))

            self.sample_grid.addWidget(name_label, row, 0)
            self.sample_grid.addWidget(label_edit, row, 1)
            self.sample_grid.addWidget(color_btn, row, 2)
            self.sample_grid.addWidget(marker_combo, row, 3)

            self.style_widgets[name] = {
                "label_edit": label_edit,
                "color_btn": color_btn,
                "marker_combo": marker_combo,
                "color": color,
            }

        scroll.setWidget(scroll_content)
        sample_layout.addWidget(scroll)
        main_layout.addWidget(sample_group)

        # 4. Global Buttons
        btn_layout = QHBoxLayout()
        self.plot_btn = QPushButton(" Generate Plot(s)")
        self.plot_btn.setIcon(qta.icon("fa5s.chart-line"))
        self.plot_btn.clicked.connect(self.accept)
        self.plot_btn.setDefault(True)

        self.cancel_btn = QPushButton(" Cancel")
        self.cancel_btn.setIcon(qta.icon("fa5s.times"))
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.plot_btn)
        main_layout.addLayout(btn_layout)

    def pick_color(self, name, btn):
        color = ui_utils.pick_color(
            initial_color=self.style_widgets[name]["color"], parent=self
        )
        if color:
            self.style_widgets[name]["color"] = color
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid gray;")

    def get_settings(self):
        selected_props = []
        for i, cb in enumerate(self.prop_checkboxes):
            if cb.isChecked():
                selected_props.append(self.properties[i])

        sample_styles = {}
        for name, widgets in self.style_widgets.items():
            sample_styles[name] = {
                "label": widgets["label_edit"].text(),
                "color": widgets["color"],
                "marker": widgets["marker_combo"].currentText(),
            }

        return {
            "selected_props": selected_props,
            "multi_panel": self.mode_combo.currentIndex() == 1,
            "rows": self.rows_spin.value(),
            "cols": self.cols_spin.value(),
            "sample_styles": sample_styles,
        }
