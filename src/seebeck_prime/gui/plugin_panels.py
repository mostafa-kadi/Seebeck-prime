import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
from PyQt6.QtCore import Qt
import qtawesome as qta
from src.ui.widgets.table_widget import ClipboardAwareTableWidget
from src.ui.widgets.plot_window import PlotWindow
"""
Hall Mobility & Carrier Concentration Plugin Dialog.

Provides interactive analysis of Hall effect measurements:
- Direct calculation of Hall mobility (Î¼_H) and carrier concentration (n_H)
- Determination of majority carrier type (n-type vs p-type)
- Raw Hall voltage (V_H, I, B, t) converter
- Temperature-dependent mobility scattering mechanism fitting (Î¼_H ~ T^p)
- Embedded publication-quality visualization
"""

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


try:
    import seebeck_prime.domain.transport.hall as hall_domain
    from seebeck_prime.domain.units.temperature import to_kelvin
    from seebeck_prime.domain.units.transport import sigma_to_base
except ImportError:
    import src.seebeck_prime.domain.transport.hall as hall_domain
    from src.seebeck_prime.domain.units.temperature import to_kelvin
    from src.seebeck_prime.domain.units.transport import sigma_to_base



class HallMobilityDialog(QDialog):
    """
    Dialog for Hall effect transport analysis: Hall mobility, carrier density,
    and carrier scattering exponent fitting.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hall Mobility & Carrier Transport Plugin â€” Seebeck Prime")
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
        self.temp_unit_combo.addItems(["K", "Â°C"])

        self.ec_unit_combo = QComboBox()
        self.ec_unit_combo.addItems(["S/cm", "S/m", "mÎ©Â·cm", "Î©Â·cm"])
        self.ec_unit_combo.setCurrentText("S/cm")

        self.rh_unit_combo = QComboBox()
        self.rh_unit_combo.addItems(["cmÂ³/C", "mÂ³/C"])
        self.rh_unit_combo.setCurrentText("cmÂ³/C")

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
        units_layout.addWidget(QLabel("Transport Unit (Ïƒ / Ï):"))
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
                "Hall Mobility Î¼_H\n(cmÂ²/VÂ·s)",
                "Carrier Density n_H\n(cmâ»Â³)",
                "Carrier Type",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tab_analysis_layout.addWidget(self.table)

        # Summary / Info label
        self.status_label = QLabel(
            "Ready. Formulas: Î¼_H = |R_H|Â·Ïƒ | n_H = r_H / (eÂ·|R_H|) | Carrier type from sign of R_H"
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
        self.raw_vh_unit.addItems(["V", "mV", "Î¼V"])
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
        self.raw_thickness_unit.addItems(["mm", "Î¼m", "cm"])
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
        self.raw_current_unit.addItems(["mA", "A", "Î¼A"])
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

        self.plot_btn = QPushButton(" Plot Î¼_H & n_H vs T")
        self.plot_btn.setIcon(qta.icon("fa5s.chart-line"))
        self.plot_btn.clicked.connect(self.plot_mobility_and_density)

        self.fit_btn = QPushButton(" Fit Scattering Exponent (Î¼ ~ T^p)")
        self.fit_btn.setIcon(qta.icon("fa5s.brain"))
        self.fit_btn.setToolTip("Performs log(Î¼_H) vs log(T) linear regression to extract scattering exponent p")
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
            elif vh_unit == "Î¼V":
                vh_v = vh * 1e-6
            else:
                vh_v = vh

            # 2. Thickness to m
            t = self.raw_thickness_input.value()
            t_unit = self.raw_thickness_unit.currentText()
            if t_unit == "mm":
                t_m = t * 1e-3
            elif t_unit == "Î¼m":
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
            elif i_unit == "Î¼A":
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
                f"<b>R_H:</b> {rh_cm3_c:.5e} cmÂ³/C ({rh_m3_c:.5e} mÂ³/C)<br>"
                f"<b>Carrier Type:</b> <span style='color: {'#2980b9' if carrier_type=='n-type' else '#c0392b'}; font-weight: bold;'>{carrier_type.upper()}</span><br>"
                f"<b>Carrier Density ({'p_H' if carrier_type=='p-type' else 'n_H'}):</b> {n_cm3:.4e} cmâ»Â³ ({n_m3:.4e} mâ»Â³)"
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
                    elif ec_unit == "mÎ©Â·cm":
                        sigma_scm = 1000.0 / ec_val if ec_val != 0 else np.nan
                    elif ec_unit == "Î©Â·cm":
                        sigma_scm = 1.0 / ec_val if ec_val != 0 else np.nan
                    else:
                        sigma_scm = ec_val

                    # Hall coefficient to cmÂ³/C
                    if rh_unit == "mÂ³/C":
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
            
            # Convert R_H to mÂ³/C for SI density then back to cmâ»Â³
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
                f"Calculated {len(rows)} points successfully. Average Î¼_H = {np.nanmean(mu_h_cm2_vs):.2f} cmÂ²/VÂ·s | Average n_H = {np.nanmean(n_h_cm3):.3e} cmâ»Â³"
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
            ax1.plot(temps_k, mu_h, "o-", color="#2980b9", linewidth=1.5, markersize=5, label="Î¼_H (measured)")
            ax1.set_xlabel("Temperature (K)", fontsize=11)
            ax1.set_ylabel("Hall Mobility Î¼_H (cmÂ²/VÂ·s)", fontsize=11)
            ax1.set_title("Hall Mobility vs. Temperature", fontsize=12, fontweight="bold")
            ax1.grid(True, linestyle="--", alpha=0.6)
            ax1.legend()

            # Right: Carrier Density vs T
            ax2.plot(temps_k, n_h, "s-", color="#e74c3c", linewidth=1.5, markersize=5, label="n_H (Hall)")
            ax2.set_xlabel("Temperature (K)", fontsize=11)
            ax2.set_ylabel("Carrier Density n_H (cmâ»Â³)", fontsize=11)
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
        """Fits log(Î¼_H) vs log(T) to extract scattering exponent p."""
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
                regime = "Acoustic Phonon Scattering (Deformation Potential, p â‰ˆ -1.5)"
            elif -1.2 < p_exp <= -0.4:
                regime = "Optical Phonon / Mixed Scattering (-1.0 â‰¤ p â‰¤ -0.5)"
            elif 1.0 <= p_exp <= 2.0:
                regime = "Ionized Impurity Scattering (Brooks-Herring, p â‰ˆ +1.5)"
            elif -0.4 < p_exp < 0.4:
                regime = "Neutral Impurity / Grain Boundary / Alloy Scattering (p â‰ˆ 0)"
            else:
                regime = f"Mixed / Non-parabolic regime (p = {p_exp:.2f})"

            # Generate Log-Log Plot
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.loglog(temps_k, mu_h, "o", color="#2c3e50", markersize=6, label="Measured Î¼_H")

            # Fit curve
            T_fit = np.linspace(np.min(temps_k), np.max(temps_k), 100)
            mu_fit = mu_0 * (T_fit ** p_exp)
            ax.loglog(T_fit, mu_fit, "--", color="#e67e22", linewidth=2.0, label=f"Fit: Î¼ âˆ T^{p_exp:.2f} (RÂ²={r2:.3f})")

            ax.set_xlabel("Temperature T (K) [Log Scale]", fontsize=11)
            ax.set_ylabel("Hall Mobility Î¼_H (cmÂ²/VÂ·s) [Log Scale]", fontsize=11)
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
"""
Single Parabolic Band (SPB) Modeling & Transport Coefficients Plugin Dialog.

Features:
- Rigorous Fermi-Dirac numerical integration and reduced Fermi level (Î·) inversion
- Density-of-states effective mass (m_d* / m_e) estimation from (S, n, T)
- Theoretical Pisarenko curve generation (S vs n) with experimental benchmarking
- Optimal carrier concentration (n_opt) and peak Power Factor (PF_max) prediction
- Single-point and batch table calculation modes
- Full scientific assumption and validity limitation disclosures

Scientific references:
    - Snyder, G. J. & Toberer, E. S. (2008). Complex thermoelectric materials.
      Nature Materials, 7, 105â€“114.
    - May, A. F. & Snyder, G. J. (2012). Modeling thermoelectric properties of semiconductors.
    - Kim, H. S. et al. (2015). APL Materials, 3, 041506.
"""

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
    QDoubleSpinBox,
    QSpinBox,
    QTextEdit,
)


try:
    import seebeck_prime.domain.models.spb as spb_domain
    from seebeck_prime.domain.units.temperature import to_kelvin
    from seebeck_prime.domain.units.transport import seebeck_to_base, seebeck_from_base
except ImportError:
    import src.seebeck_prime.domain.models.spb as spb_domain
    from src.seebeck_prime.domain.units.temperature import to_kelvin
    from src.seebeck_prime.domain.units.transport import seebeck_to_base, seebeck_from_base


class SPBModelingDialog(QDialog):
    """
    Dialog for Single Parabolic Band (SPB) transport analysis, effective mass
    estimation, Pisarenko benchmarking, and carrier concentration optimization.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SPB Modeling & Transport Optimization â€” Seebeck Prime")
        self.resize(1020, 700)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        # =====================================================================
        # Tab 1: Batch Effective Mass & SPB Analysis Table
        # =====================================================================
        tab_table = QWidget()
        tab_table_layout = QVBoxLayout(tab_table)

        # Settings
        settings_group = QGroupBox("Model Configuration & Scattering Mechanism")
        settings_form = QFormLayout(settings_group)

        row_cfg = QHBoxLayout()

        self.scat_combo = QComboBox()
        self.scat_combo.addItem("Acoustic Phonon (Î» = 0, r = -1/2) [Standard]", 0.0)
        self.scat_combo.addItem("Alloy / Polar Optical (Î» = 1, r = 1/2)", 1.0)
        self.scat_combo.addItem("Ionized Impurity (Î» = 2, r = 3/2)", 2.0)

        self.temp_unit_combo = QComboBox()
        self.temp_unit_combo.addItems(["K", "Â°C"])

        self.seebeck_unit_combo = QComboBox()
        self.seebeck_unit_combo.addItems(["Î¼V/K", "V/K", "mV/K"])

        row_cfg.addWidget(QLabel("Scattering Mechanism:"))
        row_cfg.addWidget(self.scat_combo)
        row_cfg.addSpacing(15)
        row_cfg.addWidget(QLabel("Temp Unit:"))
        row_cfg.addWidget(self.temp_unit_combo)
        row_cfg.addSpacing(15)
        row_cfg.addWidget(QLabel("Seebeck Unit:"))
        row_cfg.addWidget(self.seebeck_unit_combo)
        row_cfg.addStretch()

        settings_form.addRow(row_cfg)
        tab_table_layout.addWidget(settings_group)

        # Table
        tab_table_layout.addWidget(
            QLabel("Enter or paste experimental Temperature, Seebeck (|S|), and Carrier Concentration (n).")
        )
        self.table = ClipboardAwareTableWidget(20, 6)
        self.table.setHorizontalHeaderLabels([
            "Temperature",
            "Seebeck |S|",
            "Carrier Conc. n (cmâ»Â³)",
            "Reduced Fermi Î·\n(Calculated)",
            "Effective Mass m_d*/m_e\n(Calculated)",
            "Lorenz Number L\n(10â»â¸ WÂ·Î©/KÂ²)",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tab_table_layout.addWidget(self.table)

        # Status
        self.table_status = QLabel("Ready. Effective mass and reduced Fermi level are calculated via rigorous Fermi-Dirac integrals.")
        self.table_status.setStyleSheet("color: #555; font-size: 11px;")
        tab_table_layout.addWidget(self.table_status)

        self.tabs.addTab(tab_table, qta.icon("fa5s.table"), "Batch SPB Table")

        # =====================================================================
        # Tab 2: Pisarenko Curve & Optimum Power Factor
        # =====================================================================
        tab_pisarenko = QWidget()
        tab_pisarenko_layout = QVBoxLayout(tab_pisarenko)

        pis_group = QGroupBox("Pisarenko & Optimal Transport Parameters")
        pis_form = QFormLayout(pis_group)

        pis_row = QHBoxLayout()

        self.pis_mass_spin = QDoubleSpinBox()
        self.pis_mass_spin.setRange(0.01, 50.0)
        self.pis_mass_spin.setSingleStep(0.05)
        self.pis_mass_spin.setValue(1.0)
        self.pis_mass_spin.setDecimals(3)

        self.pis_temp_spin = QDoubleSpinBox()
        self.pis_temp_spin.setRange(1.0, 3000.0)
        self.pis_temp_spin.setValue(300.0)

        self.pis_mu0_spin = QDoubleSpinBox()
        self.pis_mu0_spin.setRange(0.1, 50000.0)
        self.pis_mu0_spin.setValue(200.0)
        self.pis_mu0_spin.setToolTip("Intrinsic non-degenerate mobility parameter Î¼â‚€ in cmÂ²/(VÂ·s)")

        pis_row.addWidget(QLabel("Effective Mass m_d*/m_e:"))
        pis_row.addWidget(self.pis_mass_spin)
        pis_row.addSpacing(15)
        pis_row.addWidget(QLabel("Temperature (K):"))
        pis_row.addWidget(self.pis_temp_spin)
        pis_row.addSpacing(15)
        pis_row.addWidget(QLabel("Intrinsic Mobility Î¼â‚€ (cmÂ²/Vs):"))
        pis_row.addWidget(self.pis_mu0_spin)
        pis_row.addStretch()

        pis_form.addRow(pis_row)

        self.use_mean_mass_btn = QPushButton(" Use Mean m_d* from Table")
        self.use_mean_mass_btn.setIcon(qta.icon("fa5s.magic"))
        self.use_mean_mass_btn.clicked.connect(self.load_mean_mass_from_table)
        pis_form.addRow(self.use_mean_mass_btn)

        tab_pisarenko_layout.addWidget(pis_group)

        self.pis_result_box = QTextEdit()
        self.pis_result_box.setReadOnly(True)
        self.pis_result_box.setMaximumHeight(140)
        self.pis_result_box.setStyleSheet("background: #f8f9fa; font-family: monospace; font-size: 11px;")
        tab_pisarenko_layout.addWidget(self.pis_result_box)

        tab_pisarenko_layout.addStretch()
        self.tabs.addTab(tab_pisarenko, qta.icon("fa5s.chart-line"), "Pisarenko & Optimization")

        # =====================================================================
        # Tab 3: Single-Point Calculator
        # =====================================================================
        tab_single = QWidget()
        tab_single_layout = QVBoxLayout(tab_single)

        single_group = QGroupBox("Single-Point SPB Converter")
        single_form = QFormLayout(single_group)

        self.single_s_spin = QDoubleSpinBox()
        self.single_s_spin.setRange(0.1, 5000.0)
        self.single_s_spin.setValue(200.0)
        self.single_s_spin.setDecimals(1)

        self.single_n_spin = QDoubleSpinBox()
        self.single_n_spin.setRange(1e12, 1e24)
        self.single_n_spin.setDecimals(2)
        self.single_n_spin.setValue(1.5e19)

        self.single_t_spin = QDoubleSpinBox()
        self.single_t_spin.setRange(1.0, 3000.0)
        self.single_t_spin.setValue(300.0)

        single_form.addRow("Seebeck |S| (Î¼V/K):", self.single_s_spin)
        single_form.addRow("Carrier Density n (cmâ»Â³):", self.single_n_spin)
        single_form.addRow("Temperature T (K):", self.single_t_spin)

        self.single_calc_btn = QPushButton(" Compute SPB Properties")
        self.single_calc_btn.setIcon(qta.icon("fa5s.calculator"))
        self.single_calc_btn.clicked.connect(self.calculate_single_point)
        single_form.addRow(self.single_calc_btn)

        self.single_result_label = QLabel("Click Compute to evaluate SPB parameters.")
        self.single_result_label.setStyleSheet("padding: 12px; background: #edf2f7; border-radius: 4px; font-size: 12px;")
        single_form.addRow(self.single_result_label)

        tab_single_layout.addWidget(single_group)
        tab_single_layout.addStretch()

        self.tabs.addTab(tab_single, qta.icon("fa5s.bolt"), "Single-Point Solver")

        # =====================================================================
        # Tab 4: Model Assumptions & Validity Notes (Mandatory Rule 11)
        # =====================================================================
        tab_notes = QWidget()
        tab_notes_layout = QVBoxLayout(tab_notes)

        notes_edit = QTextEdit()
        notes_edit.setReadOnly(True)
        notes_edit.setHtml("""
        <h3>Single Parabolic Band (SPB) Transport Model â€” Scientific Summary</h3>
        <p><b>Core Assumptions:</b></p>
        <ul>
            <li>Single conduction or valence band with parabolic energy dispersion: <i>E(k) = â„Â²kÂ² / (2m*)</i>.</li>
            <li>Relaxation time approximation with power-law energy dependence: <i>Ï„(E) = Ï„â‚€ E^(Î» - 1/2)</i>.</li>
            <li>Default acoustic phonon scattering (Î» = 0, r = -1/2).</li>
        </ul>
        <p><b>Validity Limitations (When NOT to rely solely on SPB):</b></p>
        <ul>
            <li><b>Bipolar transport:</b> At high temperatures or in narrow-gap materials, both electrons and holes contribute.</li>
            <li><b>Multi-band / Non-parabolicity:</b> High carrier concentrations may populate secondary band valleys or probe non-parabolic band structure (Kane model).</li>
            <li><b>Model Status:</b> Results (effective mass m_d*, reduced Fermi level Î·, predicted optimum) are <i>Model-Calculated</i>, not directly measured.</li>
        </ul>
        <p><b>Key Equations:</b></p>
        <ul>
            <li><i>S(Î·) = (k_B/e) Â· [ ((Î»+2) F_{Î»+1}(Î·)) / ((Î»+1) F_Î»(Î·)) - Î· ]</i></li>
            <li><i>L(Î·) = (k_B/e)Â² Â· [ ((Î»+3) F_{Î»+2}(Î·)) / ((Î»+1) F_Î»(Î·)) - (S(Î·)/(k_B/e) + Î·)Â² ]</i></li>
            <li><i>n = 4Ï€ (2 m_d* k_B T / hÂ²)^(3/2) Â· F_{1/2}(Î·)</i></li>
        </ul>
        <p><b>References:</b> Snyder & Toberer, <i>Nature Mater.</i> <b>7</b>, 105 (2008); Kim et al., <i>APL Mater.</i> <b>3</b>, 041506 (2015).</p>
        """)
        tab_notes_layout.addWidget(notes_edit)
        self.tabs.addTab(tab_notes, qta.icon("fa5s.info-circle"), "Model Assumptions & Validity")

        main_layout.addWidget(self.tabs)

        # Bottom Buttons
        btn_layout = QHBoxLayout()

        self.calc_btn = QPushButton(" Calculate Table")
        self.calc_btn.setIcon(qta.icon("fa5s.calculator"))
        self.calc_btn.setStyleSheet("font-weight: bold;")
        self.calc_btn.clicked.connect(self.calculate_table)

        self.plot_pisarenko_btn = QPushButton(" Generate Pisarenko & Optimum Plot")
        self.plot_pisarenko_btn.setIcon(qta.icon("fa5s.chart-area"))
        self.plot_pisarenko_btn.clicked.connect(self.plot_pisarenko_and_optimum)

        self.plot_lorenz_btn = QPushButton(" Plot Lorenz L(Î·)")
        self.plot_lorenz_btn.setIcon(qta.icon("fa5s.chart-line"))
        self.plot_lorenz_btn.clicked.connect(self.plot_lorenz_curve)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.calc_btn)
        btn_layout.addWidget(self.plot_pisarenko_btn)
        btn_layout.addWidget(self.plot_lorenz_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(btn_layout)

    def _extract_table_data(self):
        """Extract valid (T, S, n) data from table."""
        temps_k = []
        seebecks_uv_k = []
        ns_cm3 = []
        valid_rows = []

        temp_unit = self.temp_unit_combo.currentText()
        seebeck_unit = self.seebeck_unit_combo.currentText()

        for i in range(self.table.rowCount()):
            t_item = self.table.item(i, 0)
            s_item = self.table.item(i, 1)
            n_item = self.table.item(i, 2)

            if t_item and s_item and n_item:
                try:
                    t_val = float(t_item.text().strip())
                    s_val = float(s_item.text().strip())
                    n_val = float(n_item.text().strip())

                    t_k = to_kelvin(t_val, temp_unit)

                    # Seebeck to Î¼V/K
                    if seebeck_unit == "V/K":
                        s_uvk = abs(s_val) * 1e6
                    elif seebeck_unit == "mV/K":
                        s_uvk = abs(s_val) * 1e3
                    else:
                        s_uvk = abs(s_val)

                    if t_k > 0 and s_uvk > 0 and n_val > 0:
                        temps_k.append(t_k)
                        seebecks_uv_k.append(s_uvk)
                        ns_cm3.append(n_val)
                        valid_rows.append(i)
                except ValueError:
                    continue

        return (
            np.array(temps_k),
            np.array(seebecks_uv_k),
            np.array(ns_cm3),
            valid_rows,
        )

    def calculate_table(self):
        """Perform rigorous SPB inversion and effective mass calculation across table rows."""
        try:
            temps_k, seebecks_uv_k, ns_cm3, rows = self._extract_table_data()

            if len(temps_k) == 0:
                QMessageBox.warning(self, "No Data", "Please enter valid Temperature, Seebeck, and Carrier Concentration (n).")
                return

            lambda_scat = float(self.scat_combo.currentData())

            mass_list = []
            eta_list = []
            lorenz_list = []

            for t, s, n in zip(temps_k, seebecks_uv_k, ns_cm3):
                m_eff, eta = spb_domain.calculate_effective_mass(s, n, t, lambda_scat=lambda_scat)
                lorenz = spb_domain.rigorous_lorenz_number(eta, lambda_scat=lambda_scat)

                mass_list.append(m_eff)
                eta_list.append(eta)
                lorenz_list.append(lorenz * 1e8)

            # Update Table
            for idx, eta, m_eff, L_val in zip(rows, eta_list, mass_list, lorenz_list):
                eta_item = QTableWidgetItem(f"{eta:.3f}")
                eta_item.setFlags(eta_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                eta_item.setBackground(Qt.GlobalColor.lightGray)
                self.table.setItem(idx, 3, eta_item)

                m_item = QTableWidgetItem(f"{m_eff:.3f}")
                m_item.setFlags(m_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                m_item.setBackground(Qt.GlobalColor.lightGray)
                self.table.setItem(idx, 4, m_item)

                l_item = QTableWidgetItem(f"{L_val:.3f}")
                l_item.setFlags(l_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                l_item.setBackground(Qt.GlobalColor.lightGray)
                self.table.setItem(idx, 5, l_item)

            valid_m = [m for m in mass_list if not np.isnan(m)]
            mean_m = np.mean(valid_m) if valid_m else np.nan

            self.table_status.setText(
                f"Calculated {len(rows)} data points. Mean Effective Mass m_d* = {mean_m:.3f} m_e | Scattering Î» = {lambda_scat}"
            )
            QMessageBox.information(
                self,
                "Calculation Complete",
                f"Calculated SPB properties for {len(rows)} rows.\nAverage effective mass m_d* = {mean_m:.3f} m_e.",
            )

        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", str(e))

    def calculate_single_point(self):
        """Calculates SPB properties for single point inputs."""
        try:
            s_uvk = self.single_s_spin.value()
            n_cm3 = self.single_n_spin.value()
            t_k = self.single_t_spin.value()
            lambda_scat = float(self.scat_combo.currentData())

            m_eff, eta = spb_domain.calculate_effective_mass(s_uvk, n_cm3, t_k, lambda_scat=lambda_scat)
            lorenz = spb_domain.rigorous_lorenz_number(eta, lambda_scat=lambda_scat)

            # Degeneracy regime
            if eta < -2.0:
                regime = "Non-degenerate (Boltzmann regime, Î· < -2)"
            elif eta > 4.0:
                regime = "Degenerate (Metallic/Sommerfeld regime, Î· > 4)"
            else:
                regime = "Intermediate degeneracy (-2 â‰¤ Î· â‰¤ 4)"

            self.single_result_label.setText(
                f"<b>Density-of-States Effective Mass m_d*:</b> <span style='color: #27ae60; font-weight: bold;'>{m_eff:.4f} m_e</span><br>"
                f"<b>Reduced Fermi Level Î·:</b> {eta:.3f} (<i>{regime}</i>)<br>"
                f"<b>Lorenz Number L:</b> {lorenz:.4e} WÂ·Î©/KÂ² ({lorenz * 1e8:.3f} Ã— 10â»â¸ WÂ·Î©/KÂ²)<br>"
                f"<b>Model Scattering:</b> Î» = {lambda_scat}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_mean_mass_from_table(self):
        """Loads the average effective mass from the table into the Pisarenko tab."""
        temps_k, seebecks_uv_k, ns_cm3, _ = self._extract_table_data()
        if len(temps_k) == 0:
            QMessageBox.warning(self, "No Data", "Please calculate the table first.")
            return

        lambda_scat = float(self.scat_combo.currentData())
        masses = [
            spb_domain.calculate_effective_mass(s, n, t, lambda_scat=lambda_scat)[0]
            for t, s, n in zip(temps_k, seebecks_uv_k, ns_cm3)
        ]
        valid_m = [m for m in masses if not np.isnan(m)]
        if valid_m:
            mean_m = float(np.mean(valid_m))
            mean_t = float(np.mean(temps_k))
            self.pis_mass_spin.setValue(mean_m)
            self.pis_temp_spin.setValue(mean_t)
            QMessageBox.information(
                self, "Updated", f"Set Pisarenko m_d* = {mean_m:.3f} m_e and T = {mean_t:.1f} K from experimental data."
            )

    def plot_pisarenko_and_optimum(self):
        """Generates dual Pisarenko curve and optimal Power Factor plot."""
        try:
            m_eff = self.pis_mass_spin.value()
            t_k = self.pis_temp_spin.value()
            mu_0 = self.pis_mu0_spin.value()
            lambda_scat = float(self.scat_combo.currentData())

            # 1. Generate Pisarenko curve S vs n
            n_curve, s_curve = spb_domain.generate_pisarenko_curve(
                m_eff, t_k, n_min_cm3=1e17, n_max_cm3=1e21, num_points=120, lambda_scat=lambda_scat
            )

            # 2. Optimal transport prediction
            n_opt, pf_max, eta_opt, n_pf_curve, pf_curve = spb_domain.predict_optimal_transport(
                m_eff, t_k, mu_0, lambda_scat=lambda_scat
            )

            # Extract experimental points if available
            temps_k, seebecks_uv_k, ns_cm3, _ = self._extract_table_data()

            # Update results textbox
            self.pis_result_box.setPlainText(
                f"=== SPB Transport Optimization Results ===\n"
                f"Model Effective Mass m_d* : {m_eff:.3f} m_e at T = {t_k:.1f} K (Î» = {lambda_scat})\n"
                f"Optimal Carrier Conc. n_opt: {n_opt:.3e} cmâ»Â³ (Î·_opt = {eta_opt:.2f})\n"
                f"Maximum Power Factor PF_max: {pf_max:.3f} mW/(mÂ·KÂ²)\n"
                f"Intrinsic Mobility Parameter: Î¼â‚€ = {mu_0:.1f} cmÂ²/(VÂ·s)\n"
            )

            # Create Figure
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            # Subplot 1: Pisarenko Plot S vs n
            ax1.semilogx(n_curve, s_curve, "-", color="#2980b9", linewidth=2.2, label=f"Pisarenko: m_d* = {m_eff:.2f} m_e")

            if len(ns_cm3) > 0:
                ax1.semilogx(ns_cm3, seebecks_uv_k, "ro", markersize=6, label="Experimental Data")

            ax1.axvline(n_opt, color="#e67e22", linestyle="--", alpha=0.8, label=f"n_opt = {n_opt:.2e} cmâ»Â³")
            ax1.set_xlabel("Carrier Concentration n (cmâ»Â³)", fontsize=11)
            ax1.set_ylabel("Seebeck Coefficient |S| (Î¼V/K)", fontsize=11)
            ax1.set_title(f"Pisarenko Plot (T = {t_k:.0f} K)", fontsize=12, fontweight="bold")
            ax1.grid(True, which="both", linestyle="--", alpha=0.5)
            ax1.legend(loc="best")

            # Subplot 2: Power Factor vs n
            ax2.semilogx(n_pf_curve, pf_curve, "-", color="#27ae60", linewidth=2.2, label="Calculated PF(n)")
            ax2.plot(n_opt, pf_max, "*", color="#c0392b", markersize=12, label=f"PF_max = {pf_max:.2f} mW/mKÂ²")
            ax2.set_xlabel("Carrier Concentration n (cmâ»Â³)", fontsize=11)
            ax2.set_ylabel("Power Factor (mW/mKÂ²)", fontsize=11)
            ax2.set_title("Predicted Power Factor vs. Doping", fontsize=12, fontweight="bold")
            ax2.grid(True, which="both", linestyle="--", alpha=0.5)
            ax2.legend(loc="best")

            fig.tight_layout()

            pw = PlotWindow(fig, title=f"Pisarenko & Optimization (m_d* = {m_eff:.2f} m_e)", parent=self)
            pw.show()

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))

    def plot_lorenz_curve(self):
        """Plots the Lorenz number L vs reduced Fermi level Î· and Seebeck S."""
        try:
            lambda_scat = float(self.scat_combo.currentData())
            eta_grid = np.linspace(-6.0, 10.0, 100)
            s_grid = [spb_domain.seebeck_from_reduced_fermi_level(e, lambda_scat) for e in eta_grid]
            l_grid = [spb_domain.rigorous_lorenz_number(e, lambda_scat) * 1e8 for e in eta_grid]
            l_kim = [spb_domain.estimate_lorenz(s) * 1e8 for s in s_grid]

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

            # Left: L vs Î·
            ax1.plot(eta_grid, l_grid, "-", color="#8e44ad", linewidth=2.0, label="SPB Rigorous L(Î·)")
            ax1.axhline(2.44, color="gray", linestyle=":", label="Sommerfeld Lâ‚€ = 2.44")
            ax1.axhline(1.50, color="orange", linestyle=":", label="Non-deg. Limit L = 1.50")
            ax1.set_xlabel("Reduced Fermi Level Î· = E_F / (k_BÂ·T)", fontsize=11)
            ax1.set_ylabel("Lorenz Number L (10â»â¸ WÂ·Î©/KÂ²)", fontsize=11)
            ax1.set_title("Lorenz Number vs. Fermi Level", fontsize=12, fontweight="bold")
            ax1.grid(True, linestyle="--", alpha=0.5)
            ax1.legend()

            # Right: L vs |S|
            ax2.plot(s_grid, l_grid, "-", color="#8e44ad", linewidth=2.0, label="SPB Rigorous")
            ax2.plot(s_grid, l_kim, "--", color="#e67e22", linewidth=1.5, label="Kim et al. (2015) fit")
            ax2.set_xlabel("Seebeck Coefficient |S| (Î¼V/K)", fontsize=11)
            ax2.set_ylabel("Lorenz Number L (10â»â¸ WÂ·Î©/KÂ²)", fontsize=11)
            ax2.set_title("Lorenz Number vs. Seebeck Coefficient", fontsize=12, fontweight="bold")
            ax2.grid(True, linestyle="--", alpha=0.5)
            ax2.legend()

            fig.tight_layout()

            pw = PlotWindow(fig, title="Lorenz Number Analysis (SPB Model)", parent=self)
            pw.show()

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))

    def populate_data(self, temps, seebecks, carrier_densities=None):
        """Populate table with data from main application."""
        self.table.blockSignals(True)
        self.table.clearContents()
        n_rows = max(20, len(temps))
        self.table.setRowCount(n_rows)

        for i, t in enumerate(temps):
            if t is not None and not np.isnan(t):
                self.table.setItem(i, 0, QTableWidgetItem(f"{t:.2f}"))
            if seebecks is not None and i < len(seebecks):
                s = seebecks[i]
                if s is not None and not np.isnan(s):
                    self.table.setItem(i, 1, QTableWidgetItem(f"{abs(s):.2f}"))
            if carrier_densities is not None and i < len(carrier_densities):
                n = carrier_densities[i]
                if n is not None and not np.isnan(n):
                    self.table.setItem(i, 2, QTableWidgetItem(f"{n:.3e}"))

        self.table.blockSignals(False)
