from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QGroupBox,
    QFormLayout,
)
from PyQt6.QtCore import Qt
import qtawesome as qta


class PlotDataDialog(QDialog):
    """
    Dialog for selecting which properties to plot and defining the figure layout.
    """

    def __init__(self, parent=None, custom_properties=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Selection & Layout")
        self.setWindowIcon(qta.icon("fa5s.chart-area", color="#2c3e50"))
        self.setMinimumWidth(350)

        if custom_properties:
            self.properties = custom_properties
        else:
            self.properties = [
                ("Seebeck Coeff.", True),
                ("Electrical Conductivity", True),
                ("Power Factor", True),
                ("Thermal Cond.", True),
                ("Electronic TC", True),
                ("Lattice TC", True),
                ("ZT", True),
                ("Weighted Mobility", False),
            ]

        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # --- Property Selection Group ---
        selection_group = QGroupBox("Select Properties to Plot")
        selection_layout = QVBoxLayout(selection_group)

        self.checkboxes = []
        for prop_name, default_state in self.properties:
            cb = QCheckBox(prop_name)
            cb.setChecked(default_state)
            selection_layout.addWidget(cb)
            self.checkboxes.append(cb)

        layout.addWidget(selection_group)

        # --- Layout Group ---
        layout_group = QGroupBox("Figure Layout")
        layout_form = QFormLayout(layout_group)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 10)
        self.rows_spin.setValue(1)
        layout_form.addRow("Number of Rows:", self.rows_spin)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 10)
        self.cols_spin.setValue(1)
        layout_form.addRow("Number of Columns:", self.cols_spin)

        layout.addWidget(layout_group)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton(" Plot")
        self.ok_button.setIcon(qta.icon("fa5s.check", color="green"))
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton(" Cancel")
        self.cancel_button.setIcon(qta.icon("fa5s.times", color="red"))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def get_selection(self):
        """Returns the selected properties and layout settings."""
        selected_props = []
        for i, cb in enumerate(self.checkboxes):
            if cb.isChecked():
                selected_props.append(self.properties[i][0])

        return {
            "selected_properties": selected_props,
            "rows": self.rows_spin.value(),
            "cols": self.cols_spin.value(),
        }
