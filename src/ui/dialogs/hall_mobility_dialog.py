"""
Hall Mobility & Carrier Concentration Plugin Dialog.

Provides interactive analysis of Hall effect measurements:
- Direct calculation of Hall mobility (μ_H) and carrier concentration (n_H)
- Determination of majority carrier type (n-type vs p-type)
- Raw Hall voltage (V_H, I, B, t) converter
- Temperature-dependent mobility scattering mechanism fitting (μ_H ~ T^p)
- Embedded publication-quality visualization
"""

import numpy as np
import matplotlib.pyplot as plt
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
    QTabWidget,
    QWidget,
    QLineEdit,
    QDoubleSpinBox,
    QSplitter,
)
from PyQt6.QtCore import Qt
import qtawesome as qta

from src.ui.widgets.table_widget import ClipboardAwareTableWidget
from src.ui.widgets.plot_window import PlotWindow

try:
    import seebeck_prime.plugins.hall as hall_domain
    from seebeck_prime.domain.units import to_kelvin
except ImportError:
    import src.seebeck_prime.plugins.hall as hall_domain
    from src.seebeck_prime.domain.units import to_kelvin




class HallMobilityDialog(QDialog):
    """
    Dialog for Hall effect transport analysis: Hall mobility, carrier density,
    and carrier scattering exponent fitting.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hall Mobility & Carrier Transport Plugin — Seebeck Prime")
        self.resize(950, 650)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Tab widget for Direct Mode vs Raw Voltage Mode
        self.tabs = QTabWidget()

        # Tab 1: Table-based Hall Transport Analysis
        tab_analysis = QWidget()
        tab_analysis_layout = QVBoxLayout(tab_analysis)

        # Settings Group
        settings_group = QGroupBox("Input Settings & Physical Assumptions")
        settings_layout = QFormLayout(settings_group)

        units_layout = QHBoxLayout()

        self.temp_unit_combo = QComboBox()
        self.temp_unit_combo.addItems(["K", "°C"])

        self.ec_unit_combo = QComboBox()
        self.ec_unit_combo.addItems(["S/cm", "S/m", "mΩ·cm", "Ω·cm"])
        self.ec_unit_combo.setCurrentText("S/cm")

        self.rh_unit_combo = QComboBox()
        self.rh_unit_combo.addItems(["cm³/C", "m³/C"])
        self.rh_unit_combo.setCurrentText("cm³/C")

        self.hall_factor_spin = QDoubleSpinBox()
        self.hall_factor_spin.setRange(0.5, 3.0)
        self.hall_factor_spin.setSingleStep(0.01)
        self.hall_factor_spin.setValue(1.0)
        self.hall_factor_spin.setToolTip(
            "Hall scattering factor r_H (1.0 = degenerate/standard, 1.18 = acoustic phonon SPB)"
        )

        units_layout.addWidget(QLabel("Temp Unit:"))
        units_layout.addWidget(self.temp_unit_combo)
        units_layout.addSpacing(10)
        units_layout.addWidget(QLabel("Transport Unit (σ / ρ):"))
        units_layout.addWidget(self.ec_unit_combo)
        units_layout.addSpacing(10)
        units_layout.addWidget(QLabel("R_H Unit:"))
        units_layout.addWidget(self.rh_unit_combo)
        units_layout.addSpacing(10)
        units_layout.addWidget(QLabel("Hall Factor (r_H):"))
        units_layout.addWidget(self.hall_factor_spin)
        units_layout.addStretch()

        settings_layout.addRow(units_layout)
        tab_analysis_layout.addWidget(settings_group)

        # Instruction label
        tab_analysis_layout.addWidget(
            QLabel(
                "Paste or enter Temperature, Conductivity/Resistivity, and Hall Coefficient (R_H). "
                "Calculated results update automatically."
            )
        )

        # Table
        self.table = ClipboardAwareTableWidget(20, 6)
        self.table.setHorizontalHeaderLabels(
            [
                "Temperature",
                "Conductivity / Resistivity",
                "Hall Coeff. R_H",
                "Hall Mobility μ_H\n(cm²/V·s)",
                "Carrier Density n_H\n(cm⁻³)",
                "Carrier Type",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tab_analysis_layout.addWidget(self.table)

        # Summary / Info label
        self.status_label = QLabel(
            "Ready. Formulas: μ_H = |R_H|·σ | n_H = r_H / (e·|R_H|) | Carrier type from sign of R_H"
        )
        self.status_label.setStyleSheet("color: #555; font-size: 11px;")
        tab_analysis_layout.addWidget(self.status_label)

        self.tabs.addTab(tab_analysis, qta.icon("fa5s.table"), "Hall Data Table")

        # Tab 2: Raw Voltage Converter Tool
        tab_raw = QWidget()
        tab_raw_layout = QVBoxLayout(tab_raw)

        raw_group = QGroupBox("Single-Point Hall Coefficient from Raw Measurements")
        raw_form = QFormLayout(raw_group)

        self.raw_vh_input = QDoubleSpinBox()
        self.raw_vh_input.setRange(-1e6, 1e6)
        self.raw_vh_input.setDecimals(6)
        self.raw_vh_input.setValue(0.000120)
        self.raw_vh_unit = QComboBox()
        self.raw_vh_unit.addItems(["V", "mV", "μV"])
        self.raw_vh_unit.setCurrentText("mV")

        vh_layout = QHBoxLayout()
        vh_layout.addWidget(self.raw_vh_input)
        vh_layout.addWidget(self.raw_vh_unit)
        raw_form.addRow("Hall Voltage (V_H):", vh_layout)

        self.raw_thickness_input = QDoubleSpinBox()
        self.raw_thickness_input.setRange(1e-6, 100.0)
        self.raw_thickness_input.setDecimals(4)
        self.raw_thickness_input.setValue(1.0)
        self.raw_thickness_unit = QComboBox()
        self.raw_thickness_unit.addItems(["mm", "μm", "cm"])
        self.raw_thickness_unit.setCurrentText("mm")

        t_layout = QHBoxLayout()
        t_layout.addWidget(self.raw_thickness_input)
        t_layout.addWidget(self.raw_thickness_unit)
        raw_form.addRow("Sample Thickness (t):", t_layout)

        self.raw_current_input = QDoubleSpinBox()
        self.raw_current_input.setRange(1e-6, 100.0)
        self.raw_current_input.setDecimals(4)
        self.raw_current_input.setValue(10.0)
        self.raw_current_unit = QComboBox()
        self.raw_current_unit.addItems(["mA", "A", "μA"])
        self.raw_current_unit.setCurrentText("mA")

        i_layout = QHBoxLayout()
        i_layout.addWidget(self.raw_current_input)
        i_layout.addWidget(self.raw_current_unit)
        raw_form.addRow("Excitation Current (I):", i_layout)

        self.raw_field_input = QDoubleSpinBox()
        self.raw_field_input.setRange(0.001, 50.0)
        self.raw_field_input.setDecimals(3)
        self.raw_field_input.setValue(1.0)
        self.raw_field_unit = QComboBox()
        self.raw_field_unit.addItems(["Tesla (T)", "Gauss (G)"])

        b_layout = QHBoxLayout()
        b_layout.addWidget(self.raw_field_input)
        b_layout.addWidget(self.raw_field_unit)
        raw_form.addRow("Magnetic Field (B):", b_layout)

        self.raw_calc_btn = QPushButton(" Calculate R_H & Carrier Properties")
        self.raw_calc_btn.setIcon(qta.icon("fa5s.bolt"))
        self.raw_calc_btn.clicked.connect(self.calculate_single_raw)
        raw_form.addRow(self.raw_calc_btn)

        self.raw_result_label = QLabel("Result: Enter parameters and click Calculate.")
        self.raw_result_label.setStyleSheet("font-weight: bold; padding: 10px; background: #f0f4f8; border-radius: 4px;")
        raw_form.addRow(self.raw_result_label)

        tab_raw_layout.addWidget(raw_group)
        tab_raw_layout.addStretch()

        self.tabs.addTab(tab_raw, qta.icon("fa5s.microchip"), "Raw Voltage Converter")
        main_layout.addWidget(self.tabs)

        # Action Buttons
        btn_layout = QHBoxLayout()

        self.calc_btn = QPushButton(" Calculate All")
        self.calc_btn.setIcon(qta.icon("fa5s.calculator"))
        self.calc_btn.setStyleSheet("font-weight: bold;")
        self.calc_btn.clicked.connect(self.calculate_table)

        self.plot_btn = QPushButton(" Plot μ_H & n_H vs T")
        self.plot_btn.setIcon(qta.icon("fa5s.chart-line"))
        self.plot_btn.clicked.connect(self.plot_mobility_and_density)

        self.fit_btn = QPushButton(" Fit Scattering Exponent (μ ~ T^p)")
        self.fit_btn.setIcon(qta.icon("fa5s.brain"))
        self.fit_btn.setToolTip("Performs log(μ_H) vs log(T) linear regression to extract scattering exponent p")
        self.fit_btn.clicked.connect(self.fit_scattering_mechanism)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.calc_btn)
        btn_layout.addWidget(self.plot_btn)
        btn_layout.addWidget(self.fit_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(btn_layout)

    def calculate_single_raw(self):
        """Calculate Hall coefficient and carrier density from single raw voltage inputs."""
        try:
            # 1. Voltage to V
            vh = self.raw_vh_input.value()
            vh_unit = self.raw_vh_unit.currentText()
            if vh_unit == "mV":
                vh_v = vh * 1e-3
            elif vh_unit == "μV":
                vh_v = vh * 1e-6
            else:
                vh_v = vh

            # 2. Thickness to m
            t = self.raw_thickness_input.value()
            t_unit = self.raw_thickness_unit.currentText()
            if t_unit == "mm":
                t_m = t * 1e-3
            elif t_unit == "μm":
                t_m = t * 1e-6
            elif t_unit == "cm":
                t_m = t * 1e-2
            else:
                t_m = t

            # 3. Current to A
            i = self.raw_current_input.value()
            i_unit = self.raw_current_unit.currentText()
            if i_unit == "mA":
                i_a = i * 1e-3
            elif i_unit == "μA":
                i_a = i * 1e-6
            else:
                i_a = i

            # 4. Field to Tesla
            b = self.raw_field_input.value()
            b_unit = self.raw_field_unit.currentText()
            if "Gauss" in b_unit:
                b_t = b * 1e-4
            else:
                b_t = b

            rh_m3_c = hall_domain.calculate_hall_coefficient_from_raw(vh_v, t_m, i_a, b_t)
            rh_cm3_c = rh_m3_c * 1e6

            carrier_type = hall_domain.determine_carrier_type(rh_m3_c)
            hall_factor = self.hall_factor_spin.value()
            n_m3 = hall_domain.calculate_hall_carrier_density(rh_m3_c, hall_factor=hall_factor)
            n_cm3 = n_m3 * 1e-6

            self.raw_result_label.setText(
                f"<b>R_H:</b> {rh_cm3_c:.5e} cm³/C ({rh_m3_c:.5e} m³/C)<br>"
                f"<b>Carrier Type:</b> <span style='color: {'#2980b9' if carrier_type=='n-type' else '#c0392b'}; font-weight: bold;'>{carrier_type.upper()}</span><br>"
                f"<b>Carrier Density ({'p_H' if carrier_type=='p-type' else 'n_H'}):</b> {n_cm3:.4e} cm⁻³ ({n_m3:.4e} m⁻³)"
            )
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", str(e))

    def _extract_table_data(self):
        """Extracts and standardizes numeric data from table."""
        temps_k = []
        sigmas_s_cm = []
        rhs_cm3_c = []
        valid_row_indices = []

        temp_unit = self.temp_unit_combo.currentText()
        ec_unit = self.ec_unit_combo.currentText()
        rh_unit = self.rh_unit_combo.currentText()

        for i in range(self.table.rowCount()):
            t_item = self.table.item(i, 0)
            ec_item = self.table.item(i, 1)
            rh_item = self.table.item(i, 2)

            if t_item and ec_item and rh_item:
                try:
                    t_val = float(t_item.text().strip())
                    ec_val = float(ec_item.text().strip())
                    rh_val = float(rh_item.text().strip())

                    # Temperature to K
                    t_k = to_kelvin(t_val, temp_unit)

                    # Transport to S/cm
                    if ec_unit == "S/cm":
                        sigma_scm = ec_val
                    elif ec_unit == "S/m":
                        sigma_scm = ec_val * 0.01
                    elif ec_unit == "mΩ·cm":
                        sigma_scm = 1000.0 / ec_val if ec_val != 0 else np.nan
                    elif ec_unit == "Ω·cm":
                        sigma_scm = 1.0 / ec_val if ec_val != 0 else np.nan
                    else:
                        sigma_scm = ec_val

                    # Hall coefficient to cm³/C
                    if rh_unit == "m³/C":
                        rh_cm3 = rh_val * 1e6
                    else:
                        rh_cm3 = rh_val

                    temps_k.append(t_k)
                    sigmas_s_cm.append(sigma_scm)
                    rhs_cm3_c.append(rh_cm3)
                    valid_row_indices.append(i)
                except ValueError:
                    continue

        return (
            np.array(temps_k),
            np.array(sigmas_s_cm),
            np.array(rhs_cm3_c),
            valid_row_indices,
        )

    def calculate_table(self):
        """Calculates Hall mobility, carrier density, and type for each row in table."""
        try:
            temps_k, sigmas_s_cm, rhs_cm3_c, rows = self._extract_table_data()

            if len(temps_k) == 0:
                QMessageBox.warning(self, "No Data", "Please enter valid numeric data for Temperature, Transport, and R_H.")
                return

            hall_factor = self.hall_factor_spin.value()

            # Calculate in cm units directly
            mu_h_cm2_vs = hall_domain.calculate_hall_mobility_cm2_vs(rhs_cm3_c, sigmas_s_cm)
            
            # Convert R_H to m³/C for SI density then back to cm⁻³
            rhs_m3_c = rhs_cm3_c * 1e-6
            n_h_m3 = hall_domain.calculate_hall_carrier_density(rhs_m3_c, hall_factor=hall_factor)
            n_h_cm3 = n_h_m3 * 1e-6
            carrier_types = hall_domain.determine_carrier_type(rhs_cm3_c)

            # Update table items
            for idx, mu, n_val, ctype in zip(rows, mu_h_cm2_vs, n_h_cm3, carrier_types):
                mu_item = QTableWidgetItem(f"{mu:.2f}")
                mu_item.setFlags(mu_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                mu_item.setBackground(Qt.GlobalColor.lightGray)
                self.table.setItem(idx, 3, mu_item)

                n_item = QTableWidgetItem(f"{n_val:.3e}")
                n_item.setFlags(n_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                n_item.setBackground(Qt.GlobalColor.lightGray)
                self.table.setItem(idx, 4, n_item)

                type_item = QTableWidgetItem(ctype.upper())
                type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                type_item.setBackground(Qt.GlobalColor.lightGray)
                type_item.setForeground(Qt.GlobalColor.darkBlue if ctype == "n-type" else Qt.GlobalColor.darkRed)
                self.table.setItem(idx, 5, type_item)

            self.status_label.setText(
                f"Calculated {len(rows)} points successfully. Average μ_H = {np.nanmean(mu_h_cm2_vs):.2f} cm²/V·s | Average n_H = {np.nanmean(n_h_cm3):.3e} cm⁻³"
            )
            QMessageBox.information(self, "Success", f"Successfully calculated Hall transport properties for {len(rows)} data rows.")

        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", str(e))

    def plot_mobility_and_density(self):
        """Opens publication-quality dual plot of Hall mobility and carrier density vs Temperature."""
        try:
            temps_k, sigmas_s_cm, rhs_cm3_c, _ = self._extract_table_data()
            if len(temps_k) < 2:
                QMessageBox.warning(self, "Insufficient Data", "Need at least 2 data points to generate plots.")
                return

            hall_factor = self.hall_factor_spin.value()
            mu_h = hall_domain.calculate_hall_mobility_cm2_vs(rhs_cm3_c, sigmas_s_cm)
            rhs_m3 = rhs_cm3_c * 1e-6
            n_h = hall_domain.calculate_hall_carrier_density(rhs_m3, hall_factor=hall_factor) * 1e-6

            # Create Matplotlib Figure
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

            # Left: Hall Mobility vs T
            ax1.plot(temps_k, mu_h, "o-", color="#2980b9", linewidth=1.5, markersize=5, label="μ_H (measured)")
            ax1.set_xlabel("Temperature (K)", fontsize=11)
            ax1.set_ylabel("Hall Mobility μ_H (cm²/V·s)", fontsize=11)
            ax1.set_title("Hall Mobility vs. Temperature", fontsize=12, fontweight="bold")
            ax1.grid(True, linestyle="--", alpha=0.6)
            ax1.legend()

            # Right: Carrier Density vs T
            ax2.plot(temps_k, n_h, "s-", color="#e74c3c", linewidth=1.5, markersize=5, label="n_H (Hall)")
            ax2.set_xlabel("Temperature (K)", fontsize=11)
            ax2.set_ylabel("Carrier Density n_H (cm⁻³)", fontsize=11)
            ax2.set_title("Carrier Concentration vs. Temperature", fontsize=12, fontweight="bold")
            ax2.grid(True, linestyle="--", alpha=0.6)
            ax2.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
            ax2.legend()

            fig.tight_layout()

            # Show in PlotWindow
            pw = PlotWindow(fig, title="Hall Transport Properties vs. Temperature", parent=self)
            pw.show()

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))

    def fit_scattering_mechanism(self):
        """Fits log(μ_H) vs log(T) to extract scattering exponent p."""
        try:
            temps_k, sigmas_s_cm, rhs_cm3_c, _ = self._extract_table_data()
            if len(temps_k) < 3:
                QMessageBox.warning(self, "Insufficient Data", "Need at least 3 points across temperature to fit scattering mechanism exponent.")
                return

            mu_h = hall_domain.calculate_hall_mobility_cm2_vs(rhs_cm3_c, sigmas_s_cm)
            p_exp, mu_0, r2 = hall_domain.fit_scattering_exponent(temps_k, mu_h)

            if np.isnan(p_exp):
                QMessageBox.warning(self, "Fit Failed", "Could not fit power law. Ensure temperatures and mobilities are strictly positive.")
                return

            # Determine dominant mechanism interpretation
            if -1.8 <= p_exp <= -1.2:
                regime = "Acoustic Phonon Scattering (Deformation Potential, p ≈ -1.5)"
            elif -1.2 < p_exp <= -0.4:
                regime = "Optical Phonon / Mixed Scattering (-1.0 ≤ p ≤ -0.5)"
            elif 1.0 <= p_exp <= 2.0:
                regime = "Ionized Impurity Scattering (Brooks-Herring, p ≈ +1.5)"
            elif -0.4 < p_exp < 0.4:
                regime = "Neutral Impurity / Grain Boundary / Alloy Scattering (p ≈ 0)"
            else:
                regime = f"Mixed / Non-parabolic regime (p = {p_exp:.2f})"

            # Generate Log-Log Plot
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.loglog(temps_k, mu_h, "o", color="#2c3e50", markersize=6, label="Measured μ_H")

            # Fit curve
            T_fit = np.linspace(np.min(temps_k), np.max(temps_k), 100)
            mu_fit = mu_0 * (T_fit ** p_exp)
            ax.loglog(T_fit, mu_fit, "--", color="#e67e22", linewidth=2.0, label=f"Fit: μ ∝ T^{p_exp:.2f} (R²={r2:.3f})")

            ax.set_xlabel("Temperature T (K) [Log Scale]", fontsize=11)
            ax.set_ylabel("Hall Mobility μ_H (cm²/V·s) [Log Scale]", fontsize=11)
            ax.set_title(f"Scattering Mechanism Fit: p = {p_exp:.2f}\n{regime}", fontsize=11, fontweight="bold")
            ax.grid(True, which="both", linestyle="--", alpha=0.5)
            ax.legend(loc="best")
            fig.tight_layout()

            pw = PlotWindow(fig, title=f"Scattering Fit: p = {p_exp:.2f} ({regime})", parent=self)
            pw.show()

        except Exception as e:
            QMessageBox.critical(self, "Fit Error", str(e))

    def populate_data(self, temps, conductivities, hall_coeffs=None):
        """
        Populate table with data from main application window.
        Assumes default units: Temp=K, Conductivity=S/cm.
        """
        self.table.blockSignals(True)
        self.table.clearContents()
        n_rows = max(20, len(temps))
        self.table.setRowCount(n_rows)

        for i, t in enumerate(temps):
            if t is not None and not np.isnan(t):
                self.table.setItem(i, 0, QTableWidgetItem(f"{t:.2f}"))
            if conductivities is not None and i < len(conductivities):
                c = conductivities[i]
                if c is not None and not np.isnan(c):
                    self.table.setItem(i, 1, QTableWidgetItem(f"{c:.4f}"))
            if hall_coeffs is not None and i < len(hall_coeffs):
                rh = hall_coeffs[i]
                if rh is not None and not np.isnan(rh):
                    self.table.setItem(i, 2, QTableWidgetItem(f"{rh:.5f}"))

        self.table.blockSignals(False)
