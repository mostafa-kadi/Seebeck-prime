from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QHeaderView,
    QComboBox,
    QLabel,
    QGroupBox,
    QFormLayout,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt
import qtawesome as qta
import numpy as np

from src.ui.widgets.table_widget import ClipboardAwareTableWidget
import src.ui.logic.weighted_mobility_logic as wm_logic


class WeightedMobilityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Weighted Mobility Calculator")
        self.resize(700, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Settings Group
        settings_group = QGroupBox("Input Settings")
        settings_layout = QFormLayout(settings_group)

        # Units
        units_layout = QHBoxLayout()

        self.temp_unit_combo = QComboBox()
        self.temp_unit_combo.addItems(["K", "°C"])

        self.rho_unit_combo = QComboBox()
        self.rho_unit_combo.addItems(["mΩ·cm", "S/cm", "Ω·m", "S/m"])
        self.rho_unit_combo.setCurrentText("S/cm")

        units_layout.addWidget(QLabel("Temperature Unit:"))
        units_layout.addWidget(self.temp_unit_combo)
        units_layout.addSpacing(20)
        units_layout.addWidget(QLabel("Electrical Transport Unit:"))
        units_layout.addWidget(self.rho_unit_combo)
        units_layout.addStretch()

        settings_layout.addRow(units_layout)
        layout.addWidget(settings_group)

        # Instructions
        layout.addWidget(
            QLabel(
                "Paste or enter data below. Output is calculated automatically on button click."
            )
        )

        # Table
        self.table = ClipboardAwareTableWidget(20, 4)
        self.table.setHorizontalHeaderLabels(
            [
                "Temperature",
                "Resis./Cond.",
                "Seebeck (μV/K)",
                "Weighted Mobility\n(cm²/Vs)",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        # Constants Info
        info_label = QLabel(
            "Based on Snyder et al. approximation.\nFormula: μ_w = 331 * (mΩcm/ρ) * (T/300)^-1.5 * F(S)"
        )
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.calc_btn = QPushButton(" Calculate Weighted Mobility")
        self.calc_btn.setIcon(qta.icon("fa5s.calculator"))
        self.calc_btn.clicked.connect(self.calculate)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.calc_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def calculate(self):
        try:
            # Read Data
            temps = []
            rhos = []
            seebecks = []
            rows = []

            rho_unit = self.rho_unit_combo.currentText()
            temp_unit = self.temp_unit_combo.currentText()

            for i in range(self.table.rowCount()):
                t_item = self.table.item(i, 0)
                r_item = self.table.item(i, 1)
                s_item = self.table.item(i, 2)

                if t_item and r_item and s_item:
                    try:
                        t_val = float(t_item.text())
                        r_val = float(r_item.text())
                        s_val = float(s_item.text())

                        # Convert Temp to Kelvin
                        if temp_unit == "°C":
                            t_val += 273.15

                        # Convert to mOhm.cm for calculation
                        rho_mOhm_cm = wm_logic.convert_to_mOhm_cm(r_val, rho_unit)

                        temps.append(t_val)
                        rhos.append(rho_mOhm_cm)
                        seebecks.append(s_val)
                        rows.append(i)
                    except ValueError:
                        continue  # Skip invalid rows

            if not temps:
                QMessageBox.warning(self, "No Data", "Please enter valid numeric data.")
                return

            # Calculate
            mu_w = wm_logic.calculate_weighted_mobility(temps, rhos, seebecks)

            # Update Table
            for idx, val in zip(rows, mu_w):
                res_item = QTableWidgetItem(f"{val:.4f}")
                res_item.setFlags(
                    res_item.flags() & ~Qt.ItemFlag.ItemIsEditable
                )  # Read only
                res_item.setBackground(Qt.GlobalColor.lightGray)
                self.table.setItem(idx, 3, res_item)

            QMessageBox.information(
                self, "Success", "Weighted Mobility calculated successfully."
            )

        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", str(e))

    def populate_data(self, temps, conductivities, seebecks):
        """
        Populates the table with data from the main window.
        Assumes inputs are already in the units selected in the comboboxes
        (K, S/cm, uV/K by default).
        """
        self.table.blockSignals(True)
        self.table.clearContents()
        self.table.setRowCount(max(20, len(temps)))

        for i, (t, c, s) in enumerate(zip(temps, conductivities, seebecks)):
            if t is not None and not np.isnan(t):
                self.table.setItem(i, 0, QTableWidgetItem(f"{t:.4f}"))
            if c is not None and not np.isnan(c):
                self.table.setItem(i, 1, QTableWidgetItem(f"{c:.4f}"))
            if s is not None and not np.isnan(s):
                self.table.setItem(i, 2, QTableWidgetItem(f"{s:.4f}"))

        self.table.blockSignals(False)

        # Auto-calculate if data is present
        if len(temps) > 0:
            self.calculate()
