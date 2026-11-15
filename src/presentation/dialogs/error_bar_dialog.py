from PyQt6.QtWidgets import (
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
from PyQt6.QtCore import Qt
import qtawesome as qta


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

        sys_layout.addRow("Ref. Seebeck Err (μV/K):", s_err_layout)

        # Add a small note at the bottom of the group
        unit_note = QLabel(
            "<i>Note: All Seebeck values in this tool are handled in μV/K.</i>"
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
                from seebeck_prime.application.services import ThermoelectricAnalyzer

                parent_window = self.parent()
                data_store = getattr(parent_window, "measurement_data_store", None)
                if data_store is None:
                    raise RuntimeError("The application measurement data store is not configured.")

                analyzer = ThermoelectricAnalyzer(
                    seebeck_raw_file=file_path,
                    data_store=data_store,
                )
                self.df_sb_raw = analyzer.process_raw_seebeck()
                if self.df_sb_raw is not None and not self.df_sb_raw.empty:
                    self.seebeck_view_btn.setEnabled(True)
                    # Optional: export processed Seebeck to disk if user wants
                    # dir_name = os.path.dirname(file_path)
                    # base_name = os.path.splitext(os.path.basename(file_path))[0]
                    # export_path = os.path.join(dir_name, f"{base_name}_Processed_Seebeck.xlsx")
                    # self.df_sb_raw.to_excel(export_path, index=False)
            except Exception as e:
                QMessageBox.critical(self, "Seebeck Processing Error", str(e))

    def show_seebeck_help(self):
        """Shows informative help about Seebeck units."""
        QMessageBox.information(
            self,
            "Seebeck Unit Information",
            "<h3>Seebeck Coefficient Units</h3>"
            "<p>In this application and error propagation tool:</p>"
            "<ul>"
            "<li><b>Input/Display:</b> Seebeck values and their uncertainties are handled in <b>Microvolt/Kelvin (μV/K)</b>.</li>"
            "<li><b>Internal Calculation:</b> For physical transport equations (like Power Factor or Lorenz number Estimation), "
            "the Seebeck is automatically converted to <b>Volt/Kelvin (V/K)</b> to ensure unit consistency.</li>"
            "</ul>"
            "<p>The 'Ref. Seebeck Err' should be provided in μV/K.</p>",
        )

    def view_seebeck(self):
        if self.df_sb_raw is not None:
            from seebeck_prime.presentation.dialogs.processed_data_dialog import ProcessedDataDialog

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
