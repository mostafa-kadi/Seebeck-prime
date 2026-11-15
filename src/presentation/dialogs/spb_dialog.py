"""
Single Parabolic Band (SPB) Modeling & Transport Coefficients Plugin Dialog.

Features:
- Rigorous Fermi-Dirac numerical integration and reduced Fermi level (η) inversion
- Density-of-states effective mass (m_d* / m_e) estimation from (S, n, T)
- Theoretical Pisarenko curve generation (S vs n) with experimental benchmarking
- Optimal carrier concentration (n_opt) and peak Power Factor (PF_max) prediction
- Single-point and batch table calculation modes
- Full scientific assumption and validity limitation disclosures

Scientific references:
    - Snyder, G. J. & Toberer, E. S. (2008). Complex thermoelectric materials.
      Nature Materials, 7, 105–114.
    - May, A. F. & Snyder, G. J. (2012). Modeling thermoelectric properties of semiconductors.
    - Kim, H. S. et al. (2015). APL Materials, 3, 041506.
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
    QDoubleSpinBox,
    QSpinBox,
    QTextEdit,
)
from PyQt6.QtCore import Qt
import qtawesome as qta

from seebeck_prime.presentation.table_widget import ClipboardAwareTableWidget
from seebeck_prime.presentation.plot_window import PlotWindow

from seebeck_prime.application import models as spb_domain
from seebeck_prime.application.use_cases import LEGACY_DEFAULT_LORENZ
from seebeck_prime.application.unit_conversion import (
    convert_temperature_to_kelvin,
    seebeck_to_uvk,
)
from seebeck_prime.application.spb_batch import (
    calculate_spb_batch_mean_parameters,
    calculate_spb_batch_rows,
)



class SPBModelingDialog(QDialog):
    """
    Dialog for Single Parabolic Band (SPB) transport analysis, effective mass
    estimation, Pisarenko benchmarking, and carrier concentration optimization.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SPB Modeling & Transport Optimization — Seebeck Prime")
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
        self.scat_combo.addItem("Acoustic Phonon (λ = 0, r = -1/2) [Standard]", 0.0)
        self.scat_combo.addItem("Alloy / Polar Optical (λ = 1, r = 1/2)", 1.0)
        self.scat_combo.addItem("Ionized Impurity (λ = 2, r = 3/2)", 2.0)

        self.temp_unit_combo = QComboBox()
        self.temp_unit_combo.addItems(["K", "°C"])

        self.seebeck_unit_combo = QComboBox()
        self.seebeck_unit_combo.addItems(["μV/K", "V/K", "mV/K"])

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
            "Carrier Conc. n (cm⁻³)",
            "Reduced Fermi η\n(Calculated)",
            "Effective Mass m_d*/m_e\n(Calculated)",
            "Lorenz Number L\n(10⁻⁸ W·Ω/K²)",
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
        self.pis_mu0_spin.setToolTip("Intrinsic non-degenerate mobility parameter μ₀ in cm²/(V·s)")

        pis_row.addWidget(QLabel("Effective Mass m_d*/m_e:"))
        pis_row.addWidget(self.pis_mass_spin)
        pis_row.addSpacing(15)
        pis_row.addWidget(QLabel("Temperature (K):"))
        pis_row.addWidget(self.pis_temp_spin)
        pis_row.addSpacing(15)
        pis_row.addWidget(QLabel("Intrinsic Mobility μ₀ (cm²/Vs):"))
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

        single_form.addRow("Seebeck |S| (μV/K):", self.single_s_spin)
        single_form.addRow("Carrier Density n (cm⁻³):", self.single_n_spin)
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
        <h3>Single Parabolic Band (SPB) Transport Model — Scientific Summary</h3>
        <p><b>Core Assumptions:</b></p>
        <ul>
            <li>Single conduction or valence band with parabolic energy dispersion: <i>E(k) = ℏ²k² / (2m*)</i>.</li>
            <li>Relaxation time approximation with power-law energy dependence: <i>τ(E) = τ₀ E^(λ - 1/2)</i>.</li>
            <li>Default acoustic phonon scattering (λ = 0, r = -1/2).</li>
        </ul>
        <p><b>Validity Limitations (When NOT to rely solely on SPB):</b></p>
        <ul>
            <li><b>Bipolar transport:</b> At high temperatures or in narrow-gap materials, both electrons and holes contribute.</li>
            <li><b>Multi-band / Non-parabolicity:</b> High carrier concentrations may populate secondary band valleys or probe non-parabolic band structure (Kane model).</li>
            <li><b>Model Status:</b> Results (effective mass m_d*, reduced Fermi level η, predicted optimum) are <i>Model-Calculated</i>, not directly measured.</li>
        </ul>
        <p><b>Key Equations:</b></p>
        <ul>
            <li><i>S(η) = (k_B/e) · [ ((λ+2) F_{λ+1}(η)) / ((λ+1) F_λ(η)) - η ]</i></li>
            <li><i>L(η) = (k_B/e)² · [ ((λ+3) F_{λ+2}(η)) / ((λ+1) F_λ(η)) - (S(η)/(k_B/e) + η)² ]</i></li>
            <li><i>n = 4π (2 m_d* k_B T / h²)^(3/2) · F_{1/2}(η)</i></li>
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

        self.plot_lorenz_btn = QPushButton(" Plot Lorenz L(η)")
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

                    t_k = convert_temperature_to_kelvin(t_val, temp_unit)

                    # Seebeck to μV/K — the working unit of the SPB
                    # application models (application-layer conversion;
                    # unrecognized units pass through as before).
                    s_uvk = abs(seebeck_to_uvk(s_val, seebeck_unit))

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

            results, mean_m = calculate_spb_batch_rows(
                temps_k, seebecks_uv_k, ns_cm3, rows, lambda_scat
            )

            # Update Table
            for result in results:
                idx = result.row_index
                eta_item = QTableWidgetItem(f"{result.reduced_fermi_level:.3f}")
                eta_item.setFlags(eta_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                eta_item.setBackground(Qt.GlobalColor.lightGray)
                self.table.setItem(idx, 3, eta_item)

                m_item = QTableWidgetItem(f"{result.effective_mass:.3f}")
                m_item.setFlags(m_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                m_item.setBackground(Qt.GlobalColor.lightGray)
                self.table.setItem(idx, 4, m_item)

                l_item = QTableWidgetItem(f"{result.lorenz_display_value:.3f}")
                l_item.setFlags(l_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                l_item.setBackground(Qt.GlobalColor.lightGray)
                self.table.setItem(idx, 5, l_item)

            self.table_status.setText(
                f"Calculated {len(rows)} data points. Mean Effective Mass m_d* = {mean_m:.3f} m_e | Scattering λ = {lambda_scat}"
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
                regime = "Non-degenerate (Boltzmann regime, η < -2)"
            elif eta > 4.0:
                regime = "Degenerate (Metallic/Sommerfeld regime, η > 4)"
            else:
                regime = "Intermediate degeneracy (-2 ≤ η ≤ 4)"

            self.single_result_label.setText(
                f"<b>Density-of-States Effective Mass m_d*:</b> <span style='color: #27ae60; font-weight: bold;'>{m_eff:.4f} m_e</span><br>"
                f"<b>Reduced Fermi Level η:</b> {eta:.3f} (<i>{regime}</i>)<br>"
                f"<b>Lorenz Number L:</b> {lorenz:.4e} W·Ω/K² ({lorenz * 1e8:.3f} × 10⁻⁸ W·Ω/K²)<br>"
                f"<b>Model Scattering:</b> λ = {lambda_scat}"
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
        mean_parameters = calculate_spb_batch_mean_parameters(
            temps_k, seebecks_uv_k, ns_cm3, lambda_scat
        )
        if mean_parameters is not None:
            mean_m, mean_t = mean_parameters
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
                f"Model Effective Mass m_d* : {m_eff:.3f} m_e at T = {t_k:.1f} K (λ = {lambda_scat})\n"
                f"Optimal Carrier Conc. n_opt: {n_opt:.3e} cm⁻³ (η_opt = {eta_opt:.2f})\n"
                f"Maximum Power Factor PF_max: {pf_max:.3f} mW/(m·K²)\n"
                f"Intrinsic Mobility Parameter: μ₀ = {mu_0:.1f} cm²/(V·s)\n"
            )

            # Create Figure
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            # Subplot 1: Pisarenko Plot S vs n
            ax1.semilogx(n_curve, s_curve, "-", color="#2980b9", linewidth=2.2, label=f"Pisarenko: m_d* = {m_eff:.2f} m_e")

            if len(ns_cm3) > 0:
                ax1.semilogx(ns_cm3, seebecks_uv_k, "ro", markersize=6, label="Experimental Data")

            ax1.axvline(n_opt, color="#e67e22", linestyle="--", alpha=0.8, label=f"n_opt = {n_opt:.2e} cm⁻³")
            ax1.set_xlabel("Carrier Concentration n (cm⁻³)", fontsize=11)
            ax1.set_ylabel("Seebeck Coefficient |S| (μV/K)", fontsize=11)
            ax1.set_title(f"Pisarenko Plot (T = {t_k:.0f} K)", fontsize=12, fontweight="bold")
            ax1.grid(True, which="both", linestyle="--", alpha=0.5)
            ax1.legend(loc="best")

            # Subplot 2: Power Factor vs n
            ax2.semilogx(n_pf_curve, pf_curve, "-", color="#27ae60", linewidth=2.2, label="Calculated PF(n)")
            ax2.plot(n_opt, pf_max, "*", color="#c0392b", markersize=12, label=f"PF_max = {pf_max:.2f} mW/mK²")
            ax2.set_xlabel("Carrier Concentration n (cm⁻³)", fontsize=11)
            ax2.set_ylabel("Power Factor (mW/mK²)", fontsize=11)
            ax2.set_title("Predicted Power Factor vs. Doping", fontsize=12, fontweight="bold")
            ax2.grid(True, which="both", linestyle="--", alpha=0.5)
            ax2.legend(loc="best")

            fig.tight_layout()

            pw = PlotWindow(fig, title=f"Pisarenko & Optimization (m_d* = {m_eff:.2f} m_e)", parent=self)
            pw.show()

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))

    def plot_lorenz_curve(self):
        """Plots the Lorenz number L vs reduced Fermi level η and Seebeck S."""
        try:
            lambda_scat = float(self.scat_combo.currentData())
            eta_grid = np.linspace(-6.0, 10.0, 100)
            s_grid = [spb_domain.seebeck_from_reduced_fermi_level(e, lambda_scat) for e in eta_grid]
            l_grid = [spb_domain.rigorous_lorenz_number(e, lambda_scat) * 1e8 for e in eta_grid]
            l_kim = [spb_domain.estimate_lorenz(s) * 1e8 for s in s_grid]

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

            # Left: L vs η
            ax1.plot(eta_grid, l_grid, "-", color="#8e44ad", linewidth=2.0, label="SPB Rigorous L(η)")
            # Reference lines use the domain constants instead of hard-coded
            # literals (SE-007): the Sommerfeld value and the non-degenerate
            # limit of the Kim et al. empirical Lorenz fit.
            ax1.axhline(
                LEGACY_DEFAULT_LORENZ * 1e8,
                color="gray",
                linestyle=":",
                label=f"Sommerfeld L\u2080 = {LEGACY_DEFAULT_LORENZ * 1e8:.3f}",
            )
            ax1.axhline(
                1.50,
                color="orange",
                linestyle=":",
                label="Non-deg. Limit L = 1.50",
            )
            ax1.set_xlabel("Reduced Fermi Level η = E_F / (k_B·T)", fontsize=11)
            ax1.set_ylabel("Lorenz Number L (10⁻⁸ W·Ω/K²)", fontsize=11)
            ax1.set_title("Lorenz Number vs. Fermi Level", fontsize=12, fontweight="bold")
            ax1.grid(True, linestyle="--", alpha=0.5)
            ax1.legend()

            # Right: L vs |S|
            ax2.plot(s_grid, l_grid, "-", color="#8e44ad", linewidth=2.0, label="SPB Rigorous")
            ax2.plot(s_grid, l_kim, "--", color="#e67e22", linewidth=1.5, label="Kim et al. (2015) fit")
            ax2.set_xlabel("Seebeck Coefficient |S| (μV/K)", fontsize=11)
            ax2.set_ylabel("Lorenz Number L (10⁻⁸ W·Ω/K²)", fontsize=11)
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
