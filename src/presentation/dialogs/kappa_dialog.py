import numpy as np
import qtawesome as qta
from PyQt6.QtWidgets import (
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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from seebeck_prime.presentation.table_widget import ClipboardAwareTableWidget
from seebeck_prime.application.unit_conversion import from_base_value
from seebeck_prime.presentation.plot_window import PlotWindow
from seebeck_prime.presentation.plot_data_dialog import PlotDataDialog

# Logic Import
import seebeck_prime.presentation.kappa_logic as kappa_logic


class KappaToolDialog(QDialog):
    """
    A dialog to analyze, calculate, extrapolate and interpolate thermal conductivity (kappa) values
    and export them to the main application window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Thermal Conductivity Analysis")
        self.units = {"temp": "K", "density": "g/cm³"}
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
            ["Manual Input for κ", "Calculate from α, Cp, ρ"]
        )
        self.kappa_mode_combo.currentIndexChanged.connect(self.update_table_for_mode)
        controls_layout.addRow("κ Calculation Mode:", self.kappa_mode_combo)

        # Temperature unit
        self.temp_unit_combo = QComboBox()
        self.temp_unit_combo.addItems(["K", "°C"])
        self.temp_unit_combo.currentTextChanged.connect(self.on_unit_changed)
        controls_layout.addRow("Temperature Unit:", self.temp_unit_combo)

        # Density input
        density_layout = QHBoxLayout()
        self.density_edit = QLineEdit("6.0")
        self.density_unit_combo = QComboBox()
        self.density_unit_combo.addItems(["g/cm³", "kg/m³"])
        self.density_edit.textChanged.connect(self.calculate_properties)
        self.density_unit_combo.currentTextChanged.connect(self.on_unit_changed)
        density_layout.addWidget(self.density_edit)
        density_layout.addWidget(self.density_unit_combo)
        controls_layout.addRow("Bulk Density (ρ):", density_layout)

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

        density_err_layout.addWidget(QLabel("Area (mm²):"), 1, 0)
        density_err_layout.addWidget(self.area_edit, 1, 1)
        density_err_layout.addWidget(QLabel("Err (mm²):"), 1, 2)
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
        self.dp_unit_combo.addItems(["J/mol·K", "J/kg·K"])
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
        import os

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Laser Flash Data", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return

        try:
            file_service = getattr(self.parent_window, "table_file_service", None)
            if file_service is None:
                raise RuntimeError("The application file service is not configured.")
            raw_df = file_service.load(file_path)
            from seebeck_prime.presentation.kappa_logic import (
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
                file_service.save(df_lf, export_path)

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
            # Temperature: the mapped source column is already in Kelvin
            # ("T_K"). The previous magnitude heuristic (< 273 -> +273.15)
            # silently corrupted genuine sub-273 K measurements (e.g. 250 K
            # became 523 K) and subtracted 273.15 from Kelvin values when the
            # display unit was degrees Celsius. The value is now converted
            # for display only; the read path converts it back to Kelvin.
            # See docs/SCIENTIFIC_EQUATION_AUDIT.md, issue SE-004.
            t_val = row_data.get("T_K")
            t_display = from_base_value(t_val, self.units["temp"], "temperature")
            self.source_table.setItem(i, 0, QTableWidgetItem(f"{t_display:.2f}"))

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
                # alpha (1), ±alpha (2), Cp (3), ±Cp (4), kappa (5), ±kappa (6)
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
                "Diffusivity (α)\n(mm²/s)",
                "Specific Heat (Cp)\n(J/g·K)",
                "Thermal Cond. (κ)\n(W/mK)",
            ]
            self.source_table.setHorizontalHeaderLabels(headers)
            self.source_table.setColumnHidden(1, is_manual_mode)
            self.source_table.setColumnHidden(2, is_manual_mode)
        else:
            self.source_table.setColumnCount(7)
            headers = [
                f"Temperature ({temp_unit})",
                "α (mm²/s)",
                "±α",
                "Cp (J/g·K)",
                "±Cp",
                "κ (W/mK)",
                "±κ",
            ]
            self.source_table.setHorizontalHeaderLabels(headers)
            # Control visibility
            for i in range(1, 6):
                self.source_table.setColumnHidden(i, is_manual_mode)

        self.density_edit.setEnabled(not is_manual_mode)
        self.density_unit_combo.setEnabled(not is_manual_mode)

        # Update button text for clarity
        if is_manual_mode:
            self.export_button.setText("Interpolate/Export Manual κ")
        else:
            self.export_button.setText("Export Calculated κ")

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
            ("Thermal Diffusivity (α)", True),
            ("Specific Heat (Cp)", True),
            ("Thermal Conductivity (κ)", True),
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
