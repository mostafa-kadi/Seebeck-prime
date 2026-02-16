import sys
import pandas as pd
import numpy as np
import os

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTableWidgetItem,
    QHeaderView,
    QMenu,
    QFileDialog,
    QMessageBox,
    QComboBox,
    QLabel,
    QToolBar,
    QPushButton,
    QProgressBar,
    QToolButton,
)
from PyQt6.QtGui import QAction
import qtawesome as qta
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
import scienceplots

# --- New Module Imports ---
from src.ui.widgets.table_widget import ClipboardAwareTableWidget
from src.ui.widgets.plot_window import PlotWindow
from src.ui.dialogs.kappa_dialog import KappaToolDialog
from src.ui.dialogs.multi_sample_dialog import MultiSampleDialog
from src.ui.dialogs.plot_data_dialog import PlotDataDialog
from src.ui.dialogs.weighted_mobility_dialog import WeightedMobilityDialog
from src.ui.dialogs.device_efficiency_dialog import DeviceEfficiencyDialog

# Logic Modules
import src.ui.logic.file_handler as file_handler
import src.ui.logic.table_handler as table_handler
import src.ui.logic.unit_converter as unit_converter
import src.ui.logic.plot_handler as plot_handler
import src.ui.logic.ui_builder as ui_builder

import src.core.calculations as calc
import src.core.error_propagation as error_calc
from src.ui.dialogs.error_bar_dialog import ErrorBarDialog

#  Constants for column indices are now in table_handler
from src.ui.logic.table_handler import (
    COL_TEMP,
    COL_EC,
    COL_SEEBECK,
    COL_PF,
    COL_K_TOTAL,
    COL_K_E,
    COL_K_L,
    COL_ZT,
    BASE_COLUMN_COUNT,
    COLUMN_HEADERS,
    INPUT_COLUMNS_BASE,
    get_column_headers,
    get_input_columns,
)


class ThermoelectricApp(QMainWindow):
    """
    Main application window for analyzing thermoelectric data.
    This class handles the UI, user interactions, and coordinates with the data model.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seebeck Prime")
        self.setWindowIcon(qta.icon("fa5s.thermometer-half", color="#e67e22"))
        self.setGeometry(100, 100, 1200, 800)

        # Set default plot style to scienceplots
        plt.style.use(["science", "notebook"])

        # --- State Management ---
        self.current_file_path = None
        self.data = pd.DataFrame(columns=COLUMN_HEADERS)

        # --- Unit settings with default values ---
        self.units = {
            "temp": "K",
            "ec": "S/cm",
            "pf": "mW/mK²",
            "k": "W/mK",
            "seebeck": "μV/K",
        }

        self.plot_windows = []  # To hold references to open plot windows
        self.error_mode = False
        self.uncertainties = None
        self.init_ui()
        self.reset_and_create_new_sheet()
        self.kappa_tool_dialog = KappaToolDialog(parent=self)

    def init_ui(self, rows=100):
        """Initialize the main UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        ui_builder.create_menu_bar(self)
        ui_builder.create_toolbar(self)

        # --- Spreadsheet Table ---
        # Using the separated widget
        self.table = ClipboardAwareTableWidget(rows, BASE_COLUMN_COUNT)
        main_layout.addWidget(self.table)
        self.setup_table_properties()

        self.create_status_bar()
        self.table.bulkDataChanged.connect(self.on_paste_recalculate)
        self.table.cellChanged.connect(self.on_cell_changed)

        # Add Device Efficiency Tool to Menu (Manually injecting since ui_builder is separate)
        menu_bar = self.menuBar()
        # Try to find "Tools" or "Analyze" menu, or create one
        tools_menu = None
        for action in menu_bar.actions():
            if action.text() in ["&Tools", "Tools", "&Analyze", "Analyze"]:
                tools_menu = action.menu()
                break

        if tools_menu:
            tools_menu.addSeparator()
            dev_eff_action = QAction("Device Efficiency Calculator", self)
            dev_eff_action.triggered.connect(self.open_device_efficiency_tool)
            tools_menu.addAction(dev_eff_action)

    def setup_table_properties(self):
        """Sets visual and behavioral properties for the main table."""
        # Define headers based on what app actually uses or table handler needs
        # We need to make sure self.HEADERS is available for the handler if it uses it
        self.HEADERS = COLUMN_HEADERS
        # Create map for unit combos
        self.unit_combos = {
            "Temperature": self.temp_combo,
            "Electrical Conductivity": self.ec_combo,
            "Seebeck Coeff.": None,  # No dedicated combo for Seebeck in toolbar
            "Power Factor": self.pf_combo,
            "Thermal Cond.": None,  # No dedicated combo for Thermal Cond in toolbar
        }

        table_handler.setup_table_properties(self)

        # Modern stylesheet for the table
        stylesheet = """
            QTableWidget {
                gridline-color: #e0e0e0;
                font-size: 10pt;
            }
            QTableWidget::item:selected {
                background-color: #d4eaf7;
                color: black;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #dcdcdc;
                font-weight: bold;
            }
        """
        self.table.setStyleSheet(stylesheet)

    def create_status_bar(self):
        """Creates the status bar for showing messages and progress."""
        self.statusBar().showMessage("Ready")
        self.progress_bar = QProgressBar(self)
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

    # --- Data and Calculation Logic ---

    def on_cell_changed(self, row, column):
        """Handle data changes, convert to base units, and trigger updates."""
        item = self.table.item(row, column)
        if not item:
            return

        # Block signals to prevent feedback loops when we re-format the cell
        self.table.blockSignals(True)
        try:
            display_value_str = item.text()
            if display_value_str.strip() == "":
                self.data.iloc[row, column] = np.nan
            else:
                display_value = float(display_value_str)
                # Convert from the user's display unit to the base unit for storage
                base_value = self._convert_to_base_unit(display_value, column)
                self.data.iloc[row, column] = base_value

                # Re-format the entered number in the cell for consistency
                item.setText(f"{display_value:.4f}")

            # Recalculate if an input column was changed
            if column in get_input_columns(self.error_mode):
                self.recalculate_all_properties()
        finally:
            self.table.blockSignals(False)

    def on_paste_recalculate(self):
        """Slot to handle recalculation after a paste operation."""
        table_handler.on_paste_recalculate(self)

        self.statusBar().showMessage("Calculation complete.", 3000)
        self.progress_bar.hide()
        self.table.blockSignals(False)

    def toggle_error_bars(self, checked):
        """Toggles the display of error bar columns."""
        if checked:
            dialog = ErrorBarDialog(self)
            if dialog.exec():
                self.uncertainties = dialog.get_values()
                self.error_mode = True
                self.statusBar().showMessage("Error bars activated.")
            else:
                # User cancelled dialog, uncheck button
                self.sender().setChecked(False)
                return
        else:
            self.error_mode = False
            self.statusBar().showMessage("Error bars deactivated.")

        # Update table structure
        self.HEADERS = get_column_headers(self.error_mode)
        # We need to map the data to the new structure or re-sync
        # For simplicity, if turning on, we'll keep existing data and add 0s for errors
        # If turning off, we'll strip error columns

        old_data = self.data.copy()
        new_headers = self.HEADERS

        if self.error_mode:
            # Create new DF with error columns
            new_df = pd.DataFrame(columns=new_headers, index=old_data.index)
            # Map old columns (Temperature -> Temperature, etc.)
            mapping = {
                "Temperature": "Temperature",
                "Electrical Conductivity": "Electrical Conductivity",
                "Seebeck Coeff.": "Seebeck Coeff.",
                "Power Factor": "Power Factor",
                "Thermal Cond.": "Thermal Cond.",
                "Electronic TC": "Electronic TC",
                "Lattice TC": "Lattice TC",
                "ZT": "ZT",
            }
            for old_col, new_col in mapping.items():
                if old_col in old_data.columns:
                    new_df[new_col] = old_data[old_col]
            self.data = new_df
        else:
            # Strip error columns
            self.data = old_data[[h for h in old_data.columns if h in COLUMN_HEADERS]]

        table_handler.setup_table_properties(self)
        self.load_data_into_table(self.data, is_base_units=True)

        if self.error_mode:
            self.recalculate_all_properties()

    def recalculate_all_properties(self):
        """
        Core calculation function. It now operates on the internal DataFrame.
        It reads all user inputs from the table, calculates derived properties,
        and updates the table.
        """
        self.table.blockSignals(True)
        self.statusBar().showMessage("Calculating...")
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # The DataFrame self.data is now the source of truth.
        df = self.data.copy()
        df = df.apply(pd.to_numeric, errors="coerce")

        # 1. Base Calculations
        df["Power Factor"] = calc.calculate_pf(
            df["Seebeck Coeff."], df["Electrical Conductivity"]
        )

        method = self.kappa_method_combo.currentText()
        if method == "Seebeck-Derived":
            lorenz = calc.estimate_lorenz(df["Seebeck Coeff."] * 1e6)
        else:
            lorenz = calc.DEFAULT_LORENZ

        df["Electronic TC"] = calc.calculate_kappa_e(
            df["Electrical Conductivity"], df["Temperature"], lorenz
        )
        df["Lattice TC"] = calc.calculate_kappa_l(
            df["Thermal Cond."], df["Electronic TC"]
        )
        df["ZT"] = calc.calculate_zt(
            df["Power Factor"], df["Temperature"], df["Thermal Cond."]
        )

        # 2. Error Propagation (if mode active)
        if self.error_mode and self.uncertainties:
            u = self.uncertainties

            if u.get("mode") == "file":
                # File-based calculation
                try:
                    analyzer = error_calc.ThermoelectricAnalyzer(
                        four_probe_file=u.get("fp_file"),
                        lf_file=u.get("lf_file"),
                        seebeck_raw_file=u.get("seebeck_raw_file"),
                        lorenz=(
                            "auto"
                            if self.kappa_method_combo.currentText()
                            == "Seebeck-Derived"
                            else (
                                self.lorenz_val
                                if hasattr(self, "lorenz_val")
                                else calc.DEFAULT_LORENZ
                            )
                        ),
                        width=u.get("width"),
                        width_err=u.get("width_err"),
                        thickness=u.get("thickness"),
                        thickness_err=u.get("thickness_err"),
                        probe_length=u.get("probe_length"),
                        probe_length_err=u.get("probe_length_err"),
                        seebeck_ref_err=u.get("seebeck_ref_err", 0.0),
                    )
                    file_df = analyzer.calculate_transport()

                    if file_df is not None and not file_df.empty:
                        # --- Export processed files to disk as requested ---
                        try:
                            # Use Four-Probe file's directory as base, fallback to Laser Flash or Seebeck Raw
                            base_file = (
                                u.get("fp_file")
                                or u.get("lf_file")
                                or u.get("seebeck_raw_file")
                            )
                            if base_file:
                                dir_name = os.path.dirname(base_file)
                                base_name = os.path.splitext(
                                    os.path.basename(base_file)
                                )[0]

                                # 1. Merged Transport Table ("same file" context)
                                export_main = os.path.join(
                                    dir_name, f"{base_name}_Processed_Transport.xlsx"
                                )
                                file_df.to_excel(export_main, index=False)

                                # 2. Laser Flash Content Table
                                if analyzer.lf_processed is not None:
                                    export_lf = os.path.join(
                                        dir_name, f"{base_name}_LF_Content.xlsx"
                                    )
                                    analyzer.lf_processed.to_excel(
                                        export_lf, index=False
                                    )

                                # 3. Seebeck Raw Content Table
                                if analyzer.seebeck_raw_processed is not None:
                                    export_sb = os.path.join(
                                        dir_name, f"{base_name}_Seebeck_Processed.xlsx"
                                    )
                                    analyzer.seebeck_raw_processed.to_excel(
                                        export_sb, index=False
                                    )

                                self.statusBar().showMessage(
                                    f"Processed files saved to {dir_name}", 5000
                                )
                        except Exception as export_err:
                            print(f"Error exporting processed files: {export_err}")

                        # T_K -> Temperature
                        # sigma -> Electrical Conductivity, sigma_err -> ±σ
                        # S -> Seebeck Coeff., S_err -> ±u(S)
                        # PF -> Power Factor, PF_err -> ±u(PF)
                        # kappa -> Thermal Cond., kappa_err -> ±u(κ)
                        # kappa_e -> Electronic TC, kappa_e_err -> ±u(κₑ)
                        # kappa_L -> Lattice TC, kappa_L_err -> ±u(κₗ)
                        # ZT -> ZT, ZT_err -> ±u(ZT)

                        mapping = {
                            "T_K": "Temperature",
                            "sigma": "Electrical Conductivity",
                            "sigma_err": "±σ",
                            "S": "Seebeck Coeff.",
                            "S_err": "±u(S)",
                            "PF": "Power Factor",
                            "PF_err": "±u(PF)",
                            "kappa": "Thermal Cond.",
                            "kappa_err": "±u(κ)",
                            "kappa_e": "Electronic TC",
                            "kappa_e_err": "±u(κₑ)",
                            "kappa_L": "Lattice TC",
                            "kappa_L_err": "±u(κₗ)",
                            "ZT": "ZT",
                            "ZT_err": "±u(ZT)",
                        }

                        # Create a new structure
                        new_df = pd.DataFrame(columns=get_column_headers(True))
                        for file_col, app_col in mapping.items():
                            if (
                                file_col in file_df.columns
                                and app_col in new_df.columns
                            ):
                                new_df[app_col] = file_df[file_col]

                        self.data = new_df
                        # Re-load into table
                        self.load_data_into_table(self.data, is_base_units=True)
                        self.statusBar().showMessage(
                            "Calculated from measurement files and exported to disk."
                        )
                        self.progress_bar.hide()
                        self.table.blockSignals(False)
                        return  # Exit early as we've already updated table
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    QMessageBox.warning(
                        self, "Error", f"Failed to process measurement files:\n{str(e)}"
                    )

            # Manual mode (percentage based)
            t_err = df["Temperature"] * u["temp_err_pct"]
            s_err = df["Seebeck Coeff."] * u["seebeck_err_pct"]
            ec_err = df["Electrical Conductivity"] * u["sigma_err_pct"]
            k_err = df["Thermal Cond."] * u["kappa_err_pct"]
            l_err = 0.0  # Lorenz number is treated as a fixed number

            df["±σ"] = ec_err
            df["±u(S)"] = s_err

            df["±u(PF)"] = error_calc.calculate_pf_error(
                df["Seebeck Coeff."], s_err, df["Electrical Conductivity"], ec_err
            )

            # Error in Thermal Conductivity
            # If we already have values in the table (e.g. from Kappa tool), use them
            if "±u(κ)" in df.columns and not df["±u(κ)"].isna().all():
                k_err = df["±u(κ)"]
            else:
                k_err = df["Thermal Cond."] * u["kappa_err_pct"]

            df["±u(κ)"] = k_err

            df["±u(κₑ)"] = error_calc.calculate_kappa_e_error(
                df["Electrical Conductivity"],
                ec_err,
                df["Temperature"],
                t_err,
                lorenz,
                l_err,
            )

            df["±u(κₗ)"] = error_calc.calculate_kappa_l_error(df["±u(κ)"], df["±u(κₑ)"])

            df["±u(ZT)"] = error_calc.calculate_zt_error(
                df["Power Factor"],
                df["±u(PF)"],
                df["Temperature"],
                t_err,
                df["Thermal Cond."],
                k_err,
            )

        # 3. Update the table with the new data
        self.data = df
        self.load_data_into_table(self.data, is_base_units=True)

        self.statusBar().showMessage("Calculation complete.", 3000)
        self.progress_bar.hide()
        self.table.blockSignals(False)

    # --- Unit Conversion Helpers ---

    def on_unit_changed(self):
        """A generic slot to handle unit changes and recalculate."""
        self.units["temp"] = self.temp_combo.currentText()
        self.units["ec"] = self.ec_combo.currentText()
        self.units["pf"] = self.pf_combo.currentText()
        unit_converter.on_unit_changed(self)

    def _convert_to_base_unit(self, value, column_index):
        return unit_converter._convert_to_base_unit(self, value, column_index)

    def _convert_from_base_unit(self, value, column_index):
        return unit_converter._convert_from_base_unit(self, value, column_index)

    def _get_display_value(self, value, column_index):
        return unit_converter._get_display_value(self, value, column_index)

    # --- UI and File Operations ---

    def update_headers(self):
        """Update table headers to reflect current unit selections."""
        table_handler.update_headers(self)

    def reset_and_create_new_sheet(self, rows=100):
        """Clears the table and creates a new empty sheet."""
        table_handler.reset_and_create_new_sheet(self, rows)

    def new_file(self):
        file_handler.new_file(self)

    def open_file(self):
        file_handler.open_file(self)

    def save_file(self):
        file_handler.save_file(self)

    def save_as_file(self):
        file_handler.save_as_file(self)

    def _write_to_file(self, path):
        file_handler._write_to_file(self, path)

    def _sync_df_from_table(self):
        table_handler._sync_df_from_table(self)

    def load_data_into_table(self, df: pd.DataFrame, is_base_units=False):
        table_handler.load_data_into_table(self, df, is_base_units)

    def _get_mapped_dataframe(self, source_df: pd.DataFrame) -> pd.DataFrame:
        return table_handler._get_mapped_dataframe(self, source_df)

    def _convert_df_to_base_units(self, df: pd.DataFrame) -> pd.DataFrame:
        return table_handler._convert_df_to_base_units(self, df)

    def confirm_action(self, message):
        """Helper to show a confirmation dialog."""
        return (
            QMessageBox.question(
                self,
                "Confirm",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )

    # --- Tool Opening Methods ---

    def open_kappa_tool_dialog(self):
        """Opens the Kappa Tool dialog."""
        self.kappa_tool_dialog.show()

    def open_multi_sample_tool(self):
        """Opens the Multi-Sample Comparison tool."""
        self.multi_sample_dialog = MultiSampleDialog(self)
        self.multi_sample_dialog.show()

    def open_weighted_mobility_tool(self):
        """Opens the Weighted Mobility Calculator tool."""
        self.weighted_mobility_dialog = WeightedMobilityDialog(self)

        # Auto-populate if data exists
        if not self.data.empty:
            # Extract columns (Base units: T=K, Sigma=S/m, S=V/K)
            try:
                # Filter for valid rows (at least T)
                # Note: self.data might have NaNs

                # Conversion to Dialog Default "base" units (K, S/cm, uV/K)
                # T: K -> K (x1)
                # Sigma: S/m -> S/cm (x0.01)
                # S: V/K -> uV/K (x1e6)

                # Make sure we use the column names from COLUMN_HEADERS or self.data columns
                # We can access via indices or names. Names are safer if indices shift.
                # "Temperature", "Electrical Conductivity", "Seebeck Coeff."

                temps = self.data["Temperature"].astype(float).values
                sigmas = (
                    self.data["Electrical Conductivity"].astype(float).values * 0.01
                )
                seebecks = self.data["Seebeck Coeff."].astype(float).values * 1e6

                # Filter out rows where all are NaN (or just T is NaN)
                mask = ~np.isnan(temps)

                self.weighted_mobility_dialog.populate_data(
                    temps[mask], sigmas[mask], seebecks[mask]
                )
            except Exception as e:
                print(f"Error auto-populating weighted mobility: {e}")

        self.weighted_mobility_dialog.show()

    def open_device_efficiency_tool(self):
        """Opens the Device-Level Efficiency Calculator."""
        self.device_efficiency_dialog = DeviceEfficiencyDialog(self)

        # Auto-populate if data exists
        if not self.data.empty:
            try:
                # Column headers in app: 'Temperature', 'Electrical Conductivity', 'Seebeck Coeff.', 'Thermal Cond.'
                # Units in app data (base): Temperature=K, EC=S/m, Seebeck=V/K, TC=W/mK
                # Units expected by dialog: K, uV/K, S/cm, W/mK

                temps = self.data["Temperature"].astype(float).values
                seebecks = (
                    self.data["Seebeck Coeff."].astype(float).values * 1e6
                )  # V/K -> uV/K
                sigmas = (
                    self.data["Electrical Conductivity"].astype(float).values * 0.01
                )  # S/m -> S/cm
                kappas = self.data["Thermal Cond."].astype(float).values

                mask = ~np.isnan(temps)

                self.device_efficiency_dialog.populate_data(
                    temps[mask], seebecks[mask], sigmas[mask], kappas[mask]
                )
            except Exception as e:
                print(f"Error auto-populating device efficiency: {e}")

        self.device_efficiency_dialog.show()

    def interpolate_k_values(self, temps, k_values, unit="K"):
        """
        Public method to be called by the KappaToolDialog to update the main sheet.
        """
        table_handler.interpolate_k_values(self, temps, k_values, unit)

    # --- Plotting ---

    def create_plot(self, y_col_index):
        """Creates a plot of the specified column vs. Temperature."""
        plot_handler.create_plot(self, y_col_index)

    def plot_all_properties(self):
        """Plots all relevant properties vs Temperature in separate windows."""
        plot_handler.plot_all_properties(self)

    def open_plot_selection_dialog(self):
        """Opens the PlotDataDialog to select properties and layout."""
        dialog = PlotDataDialog(self)
        if dialog.exec():
            selection = dialog.get_selection()
            plot_handler.plot_custom_layout(self, selection)

    def about_app(self):
        """Shows the about dialog."""
        QMessageBox.about(
            self,
            "About Seebeck Prime",
            "<b>Seebeck Prime</b><br>"
            "Version 2.0<br><br>"
            "An application for analyzing thermoelectric material properties.<br>"
            "Built with Python and PyQt6.",
        )
