from PyQt6.QtWidgets import (
from PyQt6.QtCore import Qt
import qtawesome as qta
import numpy as np
from src.ui.widgets.table_widget import ClipboardAwareTableWidget
import src.ui.logic.device_efficiency_logic as logic
from PyQt6.QtGui import QColor
from src.core.constants import R_GAS_CONSTANT
from src.core.calculations import calculate_molecular_weight
from src.ui.widgets.plot_window import PlotWindow
from src.ui.dialogs.plot_data_dialog import PlotDataDialog
import src.ui.logic.kappa_logic as kappa_logic
import os
import pandas as pd
from src.core.analyzer import process_sample_data, plot_comparisons
from src.core.calculations import DEFAULT_LORENZ
from src.ui.dialogs.plot_settings_dialog import PlotSettingsDialog
import src.ui.logic.ui_utils as ui_utils
import src.ui.logic.weighted_mobility_logic as wm_logic
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
                "Seebeck (Î¼V/K)",
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
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QLabel,
    QGroupBox,
    QPushButton,
    QFileDialog,
    QRadioButton,
    QToolButton,
    QMessageBox,
)


class ErrorBarDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Measurement Uncertainties")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- Mode Selection ---
        mode_group = QGroupBox("Error Calculation Mode")
        mode_layout = QVBoxLayout()
        self.manual_radio = QRadioButton("Manual Uncertainty (%)")
        self.file_radio = QRadioButton("Calculate from Measurement Files")
        self.manual_radio.setChecked(True)

        mode_layout.addWidget(self.manual_radio)
        mode_layout.addWidget(self.file_radio)
        mode_group.setLayout(mode_layout)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # --- Manual Percentage Inputs ---
        self.manual_group = QGroupBox("Manual Uncertainties (%)")
        manual_layout = QFormLayout()

        self.temp_err_edit = QLineEdit("1.0")
        self.sigma_err_edit = QLineEdit("3.0")
        self.seebeck_err_edit = QLineEdit("3.0")
        self.kappa_err_edit = QLineEdit("5.0")

        manual_layout.addRow("Temperature Error (%):", self.temp_err_edit)
        manual_layout.addRow("Conductivity Error (%):", self.sigma_err_edit)
        manual_layout.addRow("Seebeck Error (%):", self.seebeck_err_edit)
        manual_layout.addRow("Thermal Cond. Error (%):", self.kappa_err_edit)

        self.manual_group.setLayout(manual_layout)
        layout.addWidget(self.manual_group)

        # --- File Selection ---
        self.file_group = QGroupBox("Measurement Files")
        file_layout = QFormLayout()

        # Seebeck Raw File
        self.seebeck_path_edit = QLineEdit()
        self.seebeck_browse_btn = QPushButton("Browse...")
        self.seebeck_view_btn = QPushButton("View Table")
        self.seebeck_view_btn.setEnabled(False)
        self.seebeck_browse_btn.clicked.connect(self.browse_seebeck)
        self.seebeck_view_btn.clicked.connect(self.view_seebeck)
        sb_h_layout = QHBoxLayout()
        sb_h_layout.addWidget(self.seebeck_path_edit)
        sb_h_layout.addWidget(self.seebeck_browse_btn)
        sb_h_layout.addWidget(self.seebeck_view_btn)

        file_layout.addRow("Seebeck Raw File:", sb_h_layout)

        self.file_group.setLayout(file_layout)
        layout.addWidget(self.file_group)

        self.file_group.setEnabled(False)

        self.manual_radio.toggled.connect(self.toggle_mode)
        self.file_radio.toggled.connect(self.toggle_mode)

        self.df_lf = None
        self.df_lf = None
        self.df_sb_raw = None

        # --- Geometric / Physical Uncertainties ---
        self.geom_group = QGroupBox("Geometry / Physical Uncertainties")
        geom_layout = QFormLayout()

        # Width
        width_layout = QHBoxLayout()
        self.width_edit = QLineEdit("2.0")
        self.width_err_edit = QLineEdit("0.1")
        width_layout.addWidget(QLabel("Val (mm):"))
        width_layout.addWidget(self.width_edit)
        width_layout.addWidget(QLabel("Err (mm):"))
        width_layout.addWidget(self.width_err_edit)
        geom_layout.addRow("Sample Width (w):", width_layout)

        # Thickness
        thick_layout = QHBoxLayout()
        self.thickness_edit = QLineEdit("1.0")
        self.thickness_err_edit = QLineEdit("0.05")
        thick_layout.addWidget(QLabel("Val (mm):"))
        thick_layout.addWidget(self.thickness_edit)
        thick_layout.addWidget(QLabel("Err (mm):"))
        thick_layout.addWidget(self.thickness_err_edit)
        geom_layout.addRow("Sample Thickness (t):", thick_layout)

        # Probe spacing
        len_layout = QHBoxLayout()
        self.length_edit = QLineEdit("5.0")
        self.length_err_edit = QLineEdit("0.2")
        len_layout.addWidget(QLabel("Val (mm):"))
        len_layout.addWidget(self.length_edit)
        len_layout.addWidget(QLabel("Err (mm):"))
        len_layout.addWidget(self.length_err_edit)
        geom_layout.addRow("Probe Spacing (L):", len_layout)

        self.geom_group.setLayout(geom_layout)
        layout.addWidget(self.geom_group)

        # --- Measurement System Uncertainties ---
        sys_group = QGroupBox("System Uncertainties")
        sys_layout = QFormLayout()

        # Seebeck Reference Error with Help Button
        s_err_layout = QHBoxLayout()
        self.seebeck_ref_err_edit = QLineEdit("2.0")  # Systematic error for reference
        self.s_help_btn = QToolButton()
        self.s_help_btn.setIcon(qta.icon("fa5s.question-circle", color="#3498db"))
        self.s_help_btn.setToolTip("Click for help on Seebeck units and uncertainties")
        self.s_help_btn.clicked.connect(self.show_seebeck_help)

        s_err_layout.addWidget(self.seebeck_ref_err_edit)
        s_err_layout.addWidget(self.s_help_btn)

        sys_layout.addRow("Ref. Seebeck Err (Î¼V/K):", s_err_layout)

        # Add a small note at the bottom of the group
        unit_note = QLabel(
            "<i>Note: All Seebeck values in this tool are handled in Î¼V/K.</i>"
        )
        unit_note.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        sys_layout.addRow(unit_note)

        sys_group.setLayout(sys_layout)
        layout.addWidget(sys_group)

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def toggle_mode(self):
        is_manual = self.manual_radio.isChecked()
        self.manual_group.setVisible(is_manual)
        self.file_group.setVisible(not is_manual)
        # Geometry might be needed for both? Or just file mode usually implies advanced specific errors.
        # But manual percentages override detailed props.
        self.geom_group.setVisible(not is_manual)
        self.seebeck_ref_err_edit.setEnabled(not is_manual)

    def browse_seebeck(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Seebeck Raw Data", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.seebeck_path_edit.setText(file_path)
            try:
                from src.core.error_propagation import ThermoelectricAnalyzer
                import os

                analyzer = ThermoelectricAnalyzer(seebeck_raw_file=file_path)
                self.df_sb_raw = analyzer.process_raw_seebeck()
                if self.df_sb_raw is not None and not self.df_sb_raw.empty:
                    self.seebeck_view_btn.setEnabled(True)
                    # Optional: export processed Seebeck to disk if user wants
                    # dir_name = os.path.dirname(file_path)
                    # base_name = os.path.splitext(os.path.basename(file_path))[0]
                    # export_path = os.path.join(dir_name, f"{base_name}_Processed_Seebeck.xlsx")
                    # self.df_sb_raw.to_excel(export_path, index=False)
            except Exception as e:
                print(f"Auto-processing Seebeck failed: {e}")

    def show_seebeck_help(self):
        """Shows informative help about Seebeck units."""
        QMessageBox.information(
            self,
            "Seebeck Unit Information",
            "<h3>Seebeck Coefficient Units</h3>"
            "<p>In this application and error propagation tool:</p>"
            "<ul>"
            "<li><b>Input/Display:</b> Seebeck values and their uncertainties are handled in <b>Microvolt/Kelvin (Î¼V/K)</b>.</li>"
            "<li><b>Internal Calculation:</b> For physical transport equations (like Power Factor or Lorenz number Estimation), "
            "the Seebeck is automatically converted to <b>Volt/Kelvin (V/K)</b> to ensure unit consistency.</li>"
            "</ul>"
            "<p>The 'Ref. Seebeck Err' should be provided in Î¼V/K.</p>",
        )

    def view_seebeck(self):
        if self.df_sb_raw is not None:
            from src.ui.dialogs.processed_data_dialog import ProcessedDataDialog

            dialog = ProcessedDataDialog(
                self.df_sb_raw, title="Seebeck Raw Processed Data", parent=self
            )
            dialog.exec()

    def get_values(self):
        """Returns a dictionary of the input values."""
        try:
            return {
                "mode": "file" if self.file_radio.isChecked() else "manual",
                "fp_file": None,
                "seebeck_raw_file": self.seebeck_path_edit.text(),
                "lf_file": "",
                "width": (
                    float(self.width_edit.text()) if self.width_edit.text() else None
                ),
                "width_err": (
                    float(self.width_err_edit.text())
                    if self.width_err_edit.text()
                    else 0.0
                ),
                "thickness": (
                    float(self.thickness_edit.text())
                    if self.thickness_edit.text()
                    else None
                ),
                "thickness_err": (
                    float(self.thickness_err_edit.text())
                    if self.thickness_err_edit.text()
                    else 0.0
                ),
                "probe_length": (
                    float(self.length_edit.text()) if self.length_edit.text() else None
                ),
                "probe_length_err": (
                    float(self.length_err_edit.text())
                    if self.length_err_edit.text()
                    else 0.0
                ),
                "seebeck_ref_err": (
                    float(self.seebeck_ref_err_edit.text())
                    if self.seebeck_ref_err_edit.text()
                    else 0.0
                ),
                "temp_err_pct": (
                    float(self.temp_err_edit.text()) / 100.0
                    if self.temp_err_edit.text()
                    else 0.0
                ),
                "seebeck_err_pct": (
                    float(self.seebeck_err_edit.text()) / 100.0
                    if self.seebeck_err_edit.text()
                    else 0.0
                ),
                "sigma_err_pct": (
                    float(self.sigma_err_edit.text()) / 100.0
                    if self.sigma_err_edit.text()
                    else 0.0
                ),
                "kappa_err_pct": (
                    float(self.kappa_err_edit.text()) / 100.0
                    if self.kappa_err_edit.text()
                    else 0.0
                ),
            }

        except ValueError:
            return None
    QDialog,
    QVBoxLayout,
    QHeaderView,
    QPushButton,
    QDialogButtonBox,
    QMessageBox,
    QTableWidgetItem,
    QLabel,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QInputDialog,
    QGridLayout,
)


# Logic Import


class KappaToolDialog(QDialog):
    """
    A dialog to analyze, calculate, extrapolate and interpolate thermal conductivity (kappa) values
    and export them to the main application window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Thermal Conductivity Analysis")
        self.units = {"temp": "K", "density": "g/cmÂ³"}
        self.molecular_weight = None
        self.atoms_per_formula_unit = 0
        self.setMinimumSize(550, 450)
        self.init_ui()

    def init_ui(self):
        """Initializes the user interface of the dialog."""
        layout = QVBoxLayout(self)

        # --- Main controls group ---
        controls_group = QGroupBox("Settings")
        controls_layout = QFormLayout(controls_group)

        # Kappa calculation mode
        self.kappa_mode_combo = QComboBox()
        self.kappa_mode_combo.addItems(
            ["Manual Input for Îº", "Calculate from Î±, Cp, Ï"]
        )
        self.kappa_mode_combo.currentIndexChanged.connect(self.update_table_for_mode)
        controls_layout.addRow("Îº Calculation Mode:", self.kappa_mode_combo)

        # Temperature unit
        self.temp_unit_combo = QComboBox()
        self.temp_unit_combo.addItems(["K", "Â°C"])
        self.temp_unit_combo.currentTextChanged.connect(self.on_unit_changed)
        controls_layout.addRow("Temperature Unit:", self.temp_unit_combo)

        # Density input
        density_layout = QHBoxLayout()
        self.density_edit = QLineEdit("6.0")
        self.density_unit_combo = QComboBox()
        self.density_unit_combo.addItems(["g/cmÂ³", "kg/mÂ³"])
        self.density_edit.textChanged.connect(self.calculate_properties)
        self.density_unit_combo.currentTextChanged.connect(self.on_unit_changed)
        density_layout.addWidget(self.density_edit)
        density_layout.addWidget(self.density_unit_combo)
        controls_layout.addRow("Bulk Density (Ï):", density_layout)

        # Density Error Inputs - Expanded
        density_err_group = QGroupBox("Density Parameters")
        density_err_layout = QGridLayout()

        self.thickness_edit = QLineEdit("1.0")
        self.thickness_err_edit = QLineEdit("0.05")
        self.area_edit = QLineEdit("50.0")  # e.g. mm^2
        self.area_err_edit = QLineEdit("2.0")
        self.weight_edit = QLineEdit("0.5")  # grams
        self.weight_err_edit = QLineEdit("0.001")

        density_err_layout.addWidget(QLabel("Thickness (mm):"), 0, 0)
        density_err_layout.addWidget(self.thickness_edit, 0, 1)
        density_err_layout.addWidget(QLabel("Err (mm):"), 0, 2)
        density_err_layout.addWidget(self.thickness_err_edit, 0, 3)

        density_err_layout.addWidget(QLabel("Area (mmÂ²):"), 1, 0)
        density_err_layout.addWidget(self.area_edit, 1, 1)
        density_err_layout.addWidget(QLabel("Err (mmÂ²):"), 1, 2)
        density_err_layout.addWidget(self.area_err_edit, 1, 3)

        density_err_layout.addWidget(QLabel("Weight (g):"), 2, 0)
        density_err_layout.addWidget(self.weight_edit, 2, 1)
        density_err_layout.addWidget(QLabel("Err (g):"), 2, 2)
        density_err_layout.addWidget(self.weight_err_edit, 2, 3)

        density_err_group.setLayout(density_err_layout)
        # Initially hidden until error mode is checked
        self.density_err_group = density_err_group
        self.density_err_group.setVisible(False)

        controls_layout.addRow(density_err_group)

        # Uncertainty Toggle
        self.calc_errors_check = QCheckBox("Calculate Uncertainties (Error Bars)")
        self.calc_errors_check.toggled.connect(self.toggle_error_mode)
        controls_layout.addRow(self.calc_errors_check)

        # Laser Flash Import Button
        self.lf_import_btn = QPushButton(" Import from Laser Flash File...")
        self.lf_import_btn.setIcon(qta.icon("fa5s.file-excel", color="#27ae60"))
        self.lf_import_btn.clicked.connect(self.browse_lf)
        controls_layout.addRow("Data Import:", self.lf_import_btn)

        layout.addWidget(controls_group)

        # --- Dulong-Petit Law Group ---
        dp_group = QGroupBox("Dulong-Petit Law Analysis")
        dp_layout = QFormLayout(dp_group)

        self.formula_edit = QLineEdit()
        self.formula_edit.setPlaceholderText("e.g., Al2O3, Bi2Te3")
        dp_layout.addRow("Chemical Formula:", self.formula_edit)

        self.calc_mw_button = QPushButton(" Calculate Molecular Weight")
        self.calc_mw_button.setIcon(qta.icon("fa5s.atom"))
        self.calc_mw_button.clicked.connect(self._calculate_molecular_weight)
        dp_layout.addRow(self.calc_mw_button)

        self.mw_result_label = QLabel("MW: N/A g/mol, Atoms: N/A")
        self.mw_result_label.setStyleSheet("font-weight: bold;")
        dp_layout.addRow(self.mw_result_label)

        # DP Value and Unit Selection
        dp_val_layout = QHBoxLayout()
        self.dp_unit_combo = QComboBox()
        self.dp_unit_combo.addItems(["J/molÂ·K", "J/kgÂ·K"])
        self.dp_unit_combo.currentIndexChanged.connect(self.update_dp_display)

        self.dp_val_label = QLabel("Limit: N/A")
        self.dp_val_label.setStyleSheet("color: blue; font-weight: bold;")

        dp_val_layout.addWidget(QLabel("Display Unit:"))
        dp_val_layout.addWidget(self.dp_unit_combo)
        dp_val_layout.addSpacing(10)
        dp_val_layout.addWidget(self.dp_val_label)
        dp_val_layout.addStretch()
        dp_layout.addRow(dp_val_layout)

        self.plot_dp_check = QCheckBox("Overlay Dulong-Petit Limit on Cp Plot")
        self.plot_dp_check.setEnabled(False)
        dp_layout.addRow(self.plot_dp_check)
        layout.addWidget(dp_group)

        # --- Data Entry Area ---
        self.source_table = ClipboardAwareTableWidget(20, 4)
        self.source_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.source_table.setAlternatingRowColors(True)
        self.source_table.cellChanged.connect(self.on_cell_changed)
        layout.addWidget(self.source_table)

        # --- Action Buttons for Data Tab ---
        action_button_layout = QHBoxLayout()
        self.calc_plot_button = QPushButton(" Calculate & Plot")
        self.calc_plot_button.setIcon(qta.icon("fa5s.chart-line"))
        self.calc_plot_button.clicked.connect(self.calculate_and_plot)
        self.export_button = QPushButton(" Export to Main Sheet")
        self.export_button.setIcon(qta.icon("fa5s.file-export"))
        self.export_button.clicked.connect(self.export_kappa_values)
        action_button_layout.addWidget(self.calc_plot_button)
        action_button_layout.addWidget(self.export_button)
        layout.addLayout(action_button_layout)

        # --- Dialog Buttons (Close) ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.update_table_for_mode()  # Set initial state

    def browse_lf(self):
        from PyQt6.QtWidgets import QFileDialog
        from src.core.error_propagation import ThermoelectricAnalyzer
        import os

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Laser Flash Data", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return

        try:
            import pandas as pd

            raw_df = pd.read_excel(file_path)
            from src.ui.logic.kappa_logic import (
                smart_map_lf_data,
                process_grouped_lf_data,
            )

            df_mapped = smart_map_lf_data(raw_df)
            if df_mapped is not None and not df_mapped.empty:
                # Combine points by temperature (round to nearest 10)
                df_lf = process_grouped_lf_data(df_mapped)

                # Check if we have uncertainties (std > 0)
                has_errors = any(
                    df_lf[[c for c in df_lf.columns if c.startswith("d")]].max() > 0
                )
                if has_errors:
                    self.calc_errors_check.setChecked(True)

                # Switch to Calculation Mode automatically
                self.kappa_mode_combo.setCurrentIndex(1)
                self.populate_from_df(df_lf)

                # Export processed table to disk
                dir_name = os.path.dirname(file_path)
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                export_path = os.path.join(
                    dir_name, f"{base_name}_LF_Content_Table.xlsx"
                )
                df_lf.to_excel(export_path, index=False)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Imported and averaged {len(df_lf)} temperature groups from Laser Flash file.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "No Data",
                    "Could not extract valid data from the selected Laser Flash file.",
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Import Error", f"Failed to import Laser Flash data:\n{str(e)}"
            )

    def populate_from_df(self, df):
        """Populates the source table from a processed/grouped Laser Flash DataFrame."""
        self.source_table.blockSignals(True)
        self.source_table.clearContents()
        self.source_table.setRowCount(max(20, len(df)))

        is_error_mode = self.calc_errors_check.isChecked()

        for i, row_data in df.iterrows():
            # Temp
            t_val = row_data.get("T_K")
            if t_val < 273 and self.units["temp"] == "K":
                t_val += 273.15
            elif t_val > 273 and self.units["temp"] == "Â°C":
                t_val -= 273.15
            self.source_table.setItem(i, 0, QTableWidgetItem(f"{t_val:.2f}"))

            if not is_error_mode:
                # alpha (1), Cp (2), kappa (3)
                a = row_data.get("alpha", np.nan)
                cp = row_data.get("cp", np.nan)
                k = row_data.get("kappa", np.nan)
                if not np.isnan(a):
                    self.source_table.setItem(i, 1, QTableWidgetItem(f"{a:.6g}"))
                if not np.isnan(cp):
                    self.source_table.setItem(i, 2, QTableWidgetItem(f"{cp:.6g}"))
                if not np.isnan(k):
                    self.source_table.setItem(i, 3, QTableWidgetItem(f"{k:.6g}"))
            else:
                # alpha (1), Â±alpha (2), Cp (3), Â±Cp (4), kappa (5), Â±kappa (6)
                a = row_data.get("alpha", np.nan)
                da = row_data.get("dalpha", 0.0)
                cp = row_data.get("cp", np.nan)
                dcp = row_data.get("dcp", 0.0)
                k = row_data.get("kappa", np.nan)
                dk = row_data.get("dkappa", 0.0)

                if not np.isnan(a):
                    self.source_table.setItem(i, 1, QTableWidgetItem(f"{a:.6g}"))
                self.source_table.setItem(i, 2, QTableWidgetItem(f"{da:.6g}"))
                if not np.isnan(cp):
                    self.source_table.setItem(i, 3, QTableWidgetItem(f"{cp:.6g}"))
                self.source_table.setItem(i, 4, QTableWidgetItem(f"{dcp:.6g}"))
                if not np.isnan(k):
                    self.source_table.setItem(i, 5, QTableWidgetItem(f"{k:.6g}"))
                self.source_table.setItem(i, 6, QTableWidgetItem(f"{dk:.6g}"))

        self.source_table.blockSignals(False)
        self.calculate_properties()

    def on_unit_changed(self):
        """Update unit state and table headers. Recalculate if needed."""
        self.units["temp"] = self.temp_unit_combo.currentText()
        self.units["density"] = self.density_unit_combo.currentText()
        self.update_table_for_mode()
        self.calculate_properties()  # Recalculate kappa if density unit changes

    def toggle_error_mode(self, checked):
        """Toggles the visibility of error columns and inputs."""
        # Show/Hide the detailed density error group
        if hasattr(self, "density_err_group"):
            self.density_err_group.setVisible(checked)

        self.update_table_for_mode()
        self.calculate_properties()

    def update_table_for_mode(self):
        """
        Configures the table visibility and editability based on the selected
        calculation mode.
        """
        is_manual_mode = self.kappa_mode_combo.currentIndex() == 0
        is_error_mode = self.calc_errors_check.isChecked()
        temp_unit = self.units["temp"]

        if not is_error_mode:
            self.source_table.setColumnCount(4)
            headers = [
                f"Temperature ({temp_unit})",
                "Diffusivity (Î±)\n(mmÂ²/s)",
                "Specific Heat (Cp)\n(J/gÂ·K)",
                "Thermal Cond. (Îº)\n(W/mK)",
            ]
            self.source_table.setHorizontalHeaderLabels(headers)
            self.source_table.setColumnHidden(1, is_manual_mode)
            self.source_table.setColumnHidden(2, is_manual_mode)
        else:
            self.source_table.setColumnCount(7)
            headers = [
                f"Temperature ({temp_unit})",
                "Î± (mmÂ²/s)",
                "Â±Î±",
                "Cp (J/gÂ·K)",
                "Â±Cp",
                "Îº (W/mK)",
                "Â±Îº",
            ]
            self.source_table.setHorizontalHeaderLabels(headers)
            # Control visibility
            for i in range(1, 6):
                self.source_table.setColumnHidden(i, is_manual_mode)

        self.density_edit.setEnabled(not is_manual_mode)
        self.density_unit_combo.setEnabled(not is_manual_mode)

        # Update button text for clarity
        if is_manual_mode:
            self.export_button.setText("Interpolate/Export Manual Îº")
        else:
            self.export_button.setText("Export Calculated Îº")

        for row in range(self.source_table.rowCount()):
            item = self.source_table.item(row, 3)
            if not item:
                item = QTableWidgetItem()
                self.source_table.setItem(row, 3, item)

            if is_manual_mode:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                item.setBackground(Qt.GlobalColor.white)
            else:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setBackground(QColor("#f0f0f0"))

    def on_cell_changed(self, row, column):
        """
        Automatically recalculates kappa when alpha or cp is changed in
        'Calculate' mode.
        """
        is_manual_mode = self.kappa_mode_combo.currentIndex() == 0
        if is_manual_mode:
            return  # No auto-calculation in manual mode

        if column in [1, 2, 3, 4]:  # alpha, da, cp, or dcp
            self.calculate_properties()

    def update_dp_display(self):
        """Updates the DP limit label based on the selected unit."""
        kappa_logic.update_dp_display(self)

    def _calculate_molecular_weight(self):
        """Calculates molecular weight and atoms per formula unit."""
        kappa_logic._calculate_molecular_weight(self)

    def calculate_and_plot(self):
        """Calculates properties and opens the custom plot selection dialog."""
        self.calculate_properties()

        custom_props = [
            ("Thermal Diffusivity (Î±)", True),
            ("Specific Heat (Cp)", True),
            ("Thermal Conductivity (Îº)", True),
        ]

        if self.molecular_weight and self.plot_dp_check.isChecked():
            custom_props.append(("Molar Specific Heat (Molar Cp)", True))

        dialog = PlotDataDialog(self, custom_properties=custom_props)
        if dialog.exec():
            selection = dialog.get_selection()
            kappa_logic.draw_custom_plot(self, selection)

    def calculate_properties(self):
        """Core calculation logic for thermal conductivity."""
        kappa_logic.calculate_properties(self)

    def read_source_data(self):
        """Reads and validates the data from the source table, returning a dict."""
        return kappa_logic.read_source_data(self)

    def export_kappa_values(self):
        """
        Reads source data, triggers the interpolation in the main window,
        and closes the dialog on success.
        """
        if not self.parent_window:
            QMessageBox.critical(
                self, "Error", "Could not find the main application window."
            )
            return

        # Ensure data is calculated before exporting
        self.calculate_properties()
        data = self.read_source_data()

        # Filter for valid data points for interpolation
        valid_temps = []
        valid_ks = []
        valid_dk = []

        # Check if we have error data available in the dictionary
        has_errors = "dk" in data and len(data["dk"]) == len(data["temps"])

        for i, t in enumerate(data["temps"]):
            k = data["ks"][i]
            if not np.isnan(t) and not np.isnan(k):
                valid_temps.append(t)
                valid_ks.append(k)
                if has_errors:
                    dk = data["dk"][i]
                    valid_dk.append(dk if not np.isnan(dk) else 0.0)

        if len(valid_temps) < 2:
            QMessageBox.warning(
                self,
                "Insufficient Data",
                "Please provide at least two valid Temperature and Thermal Cond. data points to export.",
            )
            return

        # Sort data by temperature for interpolation
        if valid_dk:
            sorted_pairs = sorted(zip(valid_temps, valid_ks, valid_dk))
            final_temps, final_ks, final_dk = zip(*sorted_pairs)
        else:
            sorted_pairs = sorted(zip(valid_temps, valid_ks))
            final_temps, final_ks = zip(*sorted_pairs)
            final_dk = None

        try:
            # Call the main window's existing interpolation function
            # Note: This checks if the method exists on parent
            if hasattr(self.parent_window, "interpolate_k_values"):
                self.parent_window.interpolate_k_values(
                    list(final_temps),
                    list(final_ks),
                    self.units["temp"],
                    k_errs=list(final_dk) if final_dk else None,
                )

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"{len(final_temps)} data points were used to update the 'Thermal Cond.' column in the main sheet.",
                )
                self.accept()  # Close the dialog on success
            else:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    "Parent window does not support interpolation (method missing).",
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Interpolation Error",
                f"An error occurred during the process:\n{e}",
            )
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QLabel,
    QGroupBox,
    QProgressBar,
)


class MultiSampleDialog(QDialog):
    """
    Dialog to manage multiple samples, process them individually,
    and generate comparison plots or a multi-sheet Excel file.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Multi-Sample Comparison Tool")
        self.setMinimumSize(500, 400)
        self.samples = {}  # {SampleName: DataFrame}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- Sample List Group ---
        list_group = QGroupBox("Samples to Compare")
        list_layout = QVBoxLayout(list_group)

        self.sample_list_widget = QListWidget()
        list_layout.addWidget(self.sample_list_widget)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(" Add Sample(s)...")
        self.add_btn.setIcon(qta.icon("fa5s.plus"))
        self.add_btn.clicked.connect(self.add_samples)

        self.clear_btn = QPushButton(" Clear All")
        self.clear_btn.setIcon(qta.icon("fa5s.trash-alt"))
        self.clear_btn.clicked.connect(self.clear_samples)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.clear_btn)
        list_layout.addLayout(btn_layout)

        layout.addWidget(list_group)

        # --- Actions Group ---
        action_group = QGroupBox("Actions")
        action_layout = QHBoxLayout(action_group)

        self.process_btn = QPushButton(" Process & Plot Comparisons")
        self.process_btn.setIcon(qta.icon("fa5s.chart-line"))
        self.process_btn.setStyleSheet("font-weight: bold; padding: 5px;")
        self.process_btn.clicked.connect(self.run_analysis)

        self.export_btn = QPushButton(" Export Multi-Sheet Excel")
        self.export_btn.setIcon(qta.icon("fa5s.file-excel"))
        self.export_btn.clicked.connect(self.export_excel)

        action_layout.addWidget(self.process_btn)
        action_layout.addWidget(self.export_btn)

        layout.addWidget(action_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Help label
        help_label = QLabel(
            "Tip: Each sample row will be processed individually to calculate PF, Îºe, ÎºL, and ZT."
        )
        help_label.setStyleSheet("color: gray; font-style: italic;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

    def add_samples(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Sample Data", "", "Data Files (*.csv *.xlsx)"
        )
        if not files:
            return

        for file_path in files:
            try:
                if file_path.endswith(".xlsx"):
                    xl = pd.ExcelFile(file_path)
                    for sheet_name in xl.sheet_names:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                        sample_name = f"{os.path.basename(file_path)} [{sheet_name}]"
                        self._add_to_dict_and_list(sample_name, df)
                else:
                    df = pd.read_csv(file_path)
                    sample_name = os.path.basename(file_path)
                    self._add_to_dict_and_list(sample_name, df)
            except Exception as e:
                QMessageBox.warning(
                    self, "Load Error", f"Failed to load {file_path}:\n{e}"
                )

    def _add_to_dict_and_list(self, name, df):
        from src.ui.logic.table_handler import get_robust_mapped_dataframe

        # Target names in MultiSampleDialog: Temperature, Seebeck, Sigma, Kappa_total
        SEARCH_GROUPS = [
            ("Temperature", ["temperature", "temp", "t"]),
            ("Seebeck", ["seebeck", "alpha", "Î±", "coeff", "coefficient", "s"]),
            (
                "Sigma",
                ["sigma", "conductivity", "electrical", "ec", "resistivity", "rho"],
            ),
            ("Kappa_total", ["kappa", "thermal", "k", "kappa_total"]),
        ]

        mapped_df = get_robust_mapped_dataframe(df, SEARCH_GROUPS)

        found_count = len(mapped_df.columns)
        missing_cols = [
            target for target, _ in SEARCH_GROUPS if target not in mapped_df.columns
        ]

        if found_count < 4:
            QMessageBox.warning(
                self,
                "Incomplete Data",
                f"Sample '{name}' is missing required columns: {', '.join(missing_cols)}.\n"
                f"Required: Temperature, Seebeck, Sigma (Electrical Conductivity), Kappa_total.\n"
                f"This sample will be skipped.",
            )
            return

        self.samples[name] = mapped_df

        self.samples[name] = mapped_df
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked)
        self.sample_list_widget.addItem(item)

    def clear_samples(self):
        self.samples.clear()
        self.sample_list_widget.clear()

    def run_analysis(self):
        # Filter checked samples
        checked_samples = {}
        for i in range(self.sample_list_widget.count()):
            item = self.sample_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                name = item.text()
                if name in self.samples:
                    checked_samples[name] = self.samples[name]

        if not checked_samples:
            QMessageBox.information(
                self, "No Selection", "Please check at least one sample to compare."
            )
            return

        try:
            processed_data = {}
            for name, df in checked_samples.items():
                processed_data[name] = process_sample_data(df)

            # Open settings dialog first
            settings_dialog = PlotSettingsDialog(
                list(processed_data.keys()), parent=self
            )
            if settings_dialog.exec() == QDialog.Accepted:
                settings = settings_dialog.get_settings()
                figures = plot_comparisons(
                    processed_data, settings=settings, show=False
                )

                # Wrap each figure in our custom PlotWindow GUI
                for fig in figures:
                    pw = PlotWindow(self.parent())
                    pw.set_figure(fig)
                    pw.show()
                    # If the parent is ThermoelectricApp, track the windows
                    if hasattr(self.parent(), "plot_windows"):
                        self.parent().plot_windows.append(pw)
        except Exception as e:
            QMessageBox.critical(
                self, "Processing Error", f"Failed to process samples:\n{str(e)}"
            )

    def export_excel(self):
        if not self.samples:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Multi-Sample Results",
            "Comparison_Results.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not path:
            return

        try:
            with pd.ExcelWriter(path) as writer:
                for name, df in self.samples.items():
                    processed_df = process_sample_data(df)
                    processed_df.to_excel(
                        writer, sheet_name=name[:31], index=False
                    )  # Excel sheet name limit
            QMessageBox.information(
                self, "Success", f"Data exported successfully to {path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export Excel:\n{e}")
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


class PlotSettingsDialog(QDialog):
    def __init__(self, sample_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Settings")
        self.setMinimumSize(600, 500)
        self.sample_names = sample_names

        # Default properties to plot
        self.properties = [
            ("Sigma", "Electrical Conductivity (S/m)"),
            ("Seebeck", "Seebeck Coefficient (V/K)"),
            ("Power Factor", "Power Factor (W/mKÂ²)"),
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
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QHBoxLayout,
    QLabel,
)


class ProcessedDataDialog(QDialog):
    def __init__(self, df, title="Processed Data", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.df = df
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        if self.df is None or self.df.empty:
            layout.addWidget(QLabel("No data to display."))
        else:
            self.table = QTableWidget()
            self.table.setColumnCount(len(self.df.columns))
            self.table.setRowCount(len(self.df))
            self.table.setHorizontalHeaderLabels(self.df.columns)

            for i in range(len(self.df)):
                for j in range(len(self.df.columns)):
                    val = self.df.iloc[i, j]
                    item = QTableWidgetItem(
                        f"{val:.6g}" if isinstance(val, (float, int)) else str(val)
                    )
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(i, j, item)

            self.table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )
            layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
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
        self.temp_unit_combo.addItems(["K", "Â°C"])

        self.rho_unit_combo = QComboBox()
        self.rho_unit_combo.addItems(["mÎ©Â·cm", "S/cm", "Î©Â·m", "S/m"])
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
                "Seebeck (Î¼V/K)",
                "Weighted Mobility\n(cmÂ²/Vs)",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        # Constants Info
        info_label = QLabel(
            "Based on Snyder et al. approximation.\nFormula: Î¼_w = 331 * (mÎ©cm/Ï) * (T/300)^-1.5 * F(S)"
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
                        if temp_unit == "Â°C":
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
