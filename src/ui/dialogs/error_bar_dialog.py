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
)
from PyQt6.QtCore import Qt


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
        layout.addWidget(mode_group)

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

        self.manual_radio.toggled.connect(lambda: self.file_group.setEnabled(False))
        self.file_radio.toggled.connect(lambda: self.file_group.setEnabled(True))

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

        self.seebeck_ref_err_edit = QLineEdit("2.0")  # Systematic error for reference

        sys_layout.addRow("Ref. Seebeck Err (μV/K):", self.seebeck_ref_err_edit)

        sys_group.setLayout(sys_layout)
        layout.addWidget(sys_group)

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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
                "temp_err_pct": 0.0,  # Removed from UI
                "seebeck_err_pct": 0.0,  # Removed from UI
                "sigma_err_pct": 0.0,  # Removed from UI
                "kappa_err_pct": 0.0,  # Removed from UI
            }

        except ValueError:
            return None
