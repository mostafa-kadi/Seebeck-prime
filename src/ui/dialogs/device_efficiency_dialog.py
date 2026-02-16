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
    QLineEdit,
)
from PyQt6.QtCore import Qt
import qtawesome as qta
import numpy as np

from src.ui.widgets.table_widget import ClipboardAwareTableWidget
import src.ui.logic.device_efficiency_logic as logic


class DeviceEfficiencyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Device-Level Efficiency Calculator")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Settings Group
        settings_group = QGroupBox("Operating Conditions")
        settings_layout = QFormLayout(settings_group)

        self.tc_input = QLineEdit("300")
        self.th_input = QLineEdit("600")

        # Add labels with units
        self.tc_label = QLabel("Cold Side Temperature (Tc) [K]:")
        self.th_label = QLabel("Hot Side Temperature (Th) [K]:")

        settings_layout.addRow(self.tc_label, self.tc_input)
        settings_layout.addRow(self.th_label, self.th_input)

        layout.addWidget(settings_group)

        # Instructions
        layout.addWidget(
            QLabel(
                "Verify or enter material properties below. ZT will be calculated from inputs if not provided."
            )
        )

        # Table
        # Columns: T, S, Sigma, Kappa, ZT (output/input)
        self.table = ClipboardAwareTableWidget(20, 5)
        self.table.setHorizontalHeaderLabels(
            [
                "Temperature (K)",
                "Seebeck (μV/K)",
                "Elec. Cond. (S/cm)",
                "Thermal Cond. (W/mK)",
                "ZT",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        # Results Group
        results_group = QGroupBox("Calculated Efficiency Results")
        results_layout = QFormLayout(results_group)

        self.zt_avg_label = QLabel("---")
        self.zt_eng_label = QLabel("---")
        self.eff_max_label = QLabel("---")
        self.eff_eng_label = QLabel("---")
        self.carnot_label = QLabel("---")

        results_layout.addRow("Average ZT (ZT_avg):", self.zt_avg_label)
        results_layout.addRow("Engineering ZT (ZT_eng):", self.zt_eng_label)
        results_layout.addRow("Carnot Efficiency:", self.carnot_label)
        results_layout.addRow("Max. Efficiency (const. prop.):", self.eff_max_label)
        results_layout.addRow("Engineering Efficiency:", self.eff_eng_label)

        layout.addWidget(results_group)

        # Info
        info_label = QLabel(
            "ZT_avg is the integral average. ZT_eng follows Snyder et al. (Energy Environ. Sci., 2012, 5, 5147)."
        )
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.calc_btn = QPushButton(" Calculate Efficiency")
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
            tc = float(self.tc_input.text())
            th = float(self.th_input.text())

            if th <= tc:
                QMessageBox.warning(self, "Input Error", "Th must be greater than Tc.")
                return

            # Read Data
            temps = []
            seebecks = []  # in V/K
            sigmas = []  # in S/m
            kappas = []  # in W/mK

            for i in range(self.table.rowCount()):
                t_item = self.table.item(i, 0)
                s_item = self.table.item(i, 1)
                sig_item = self.table.item(i, 2)
                kap_item = self.table.item(i, 3)

                if t_item and s_item and sig_item and kap_item:
                    try:
                        t_val = float(t_item.text())
                        s_val = float(s_item.text()) * 1e-6  # uV/K -> V/K
                        sig_val = float(sig_item.text()) * 100.0  # S/cm -> S/m
                        kap_val = float(kap_item.text())

                        temps.append(t_val)
                        seebecks.append(s_val)
                        sigmas.append(sig_val)
                        kappas.append(kap_val)
                    except ValueError:
                        continue

            if len(temps) < 2:
                QMessageBox.warning(
                    self,
                    "No Data",
                    "Please enter at least 2 rows of valid numeric data.",
                )
                return

            # Perform calculation
            results = logic.calculate_efficiencies(
                np.array(temps),
                np.array(seebecks),
                np.array(sigmas),
                np.array(kappas),
                tc,
                th,
            )

            if results:
                self.zt_avg_label.setText(f"{results['ZT_avg']:.4f}")
                self.zt_eng_label.setText(f"{results['ZT_eng']:.4f}")
                self.carnot_label.setText(f"{results['Carnot']*100:.2f}%")
                self.eff_max_label.setText(f"{results['Efficiency_Max']*100:.2f}%")
                self.eff_eng_label.setText(f"{results['Efficiency_Eng']*100:.2f}%")

                # Update ZT column in table
                for i in range(len(temps)):
                    # Calculate local ZT
                    pf = (seebecks[i] ** 2) * sigmas[i]
                    zt = (pf * temps[i]) / kappas[i]
                    item = QTableWidgetItem(f"{zt:.4f}")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(Qt.GlobalColor.lightGray)
                    self.table.setItem(i, 4, item)

            else:
                QMessageBox.warning(
                    self, "Range Error", "Data points do not cover the [Tc, Th] range."
                )

        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", str(e))

    def populate_data(self, temps, seebecks, sigmas, kappas):
        """
        Populates the table with data from the main window.
        Assumes inputs are in common units (K, uV/K, S/cm, W/mK).
        """
        self.table.blockSignals(True)
        self.table.clearContents()
        self.table.setRowCount(max(20, len(temps)))

        for i, (t, s, sig, k) in enumerate(zip(temps, seebecks, sigmas, kappas)):
            if t is not None and not np.isnan(t):
                self.table.setItem(i, 0, QTableWidgetItem(f"{t:.4f}"))
            if s is not None and not np.isnan(s):
                self.table.setItem(i, 1, QTableWidgetItem(f"{s:.4f}"))
            if sig is not None and not np.isnan(sig):
                self.table.setItem(i, 2, QTableWidgetItem(f"{sig:.4f}"))
            if k is not None and not np.isnan(k):
                self.table.setItem(i, 3, QTableWidgetItem(f"{k:.4f}"))

        self.table.blockSignals(False)

        # Set Th and Tc defaults based on data
        if len(temps) > 0:
            valid_temps = [t for t in temps if not np.isnan(t)]
            if valid_temps:
                self.tc_input.setText(f"{min(valid_temps):.0f}")
                self.th_input.setText(f"{max(valid_temps):.0f}")
