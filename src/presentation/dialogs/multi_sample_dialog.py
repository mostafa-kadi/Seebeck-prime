from PyQt6.QtWidgets import (
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
from PyQt6.QtCore import Qt
import qtawesome as qta
from seebeck_prime.presentation.multi_sample_plots import plot_comparisons
import seebeck_prime.presentation.validation_notices as validation_notices
from seebeck_prime.application.use_cases import (
    process_multi_sample_data as process_sample_data,
    process_multi_sample_batch,
    validate_multi_sample_properties,
)
from seebeck_prime.application.data_mapping import get_robust_mapped_dataframe
from seebeck_prime.application.table_files import MultiSampleFileError
from seebeck_prime.presentation.dialogs.plot_settings_dialog import PlotSettingsDialog
from seebeck_prime.presentation.plot_window import PlotWindow


class MultiSampleDialog(QDialog):
    """
    Dialog to manage multiple samples, process them individually,
    and generate comparison plots or a multi-sheet Excel file.
    """

    def __init__(self, parent=None, table_file_service=None):
        super().__init__(parent)
        self.setWindowTitle("Multi-Sample Comparison Tool")
        self.setMinimumSize(500, 400)
        self.samples = {}  # {SampleName: DataFrame}
        self.table_file_service = table_file_service or getattr(
            parent, "table_file_service", None
        )

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
            "Tip: Each sample row will be processed individually to calculate PF, κe, κL, and ZT."
        )
        help_label.setStyleSheet("color: gray; font-style: italic;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

    def add_samples(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Sample Data", "", "Data Files (*.csv *.xlsx *.txt *.tsv)"
        )
        if not files:
            return

        file_service = getattr(self, "table_file_service", None)
        if file_service is None:
            QMessageBox.critical(
                self,
                "Import Unavailable",
                "The application file service is not configured.",
            )
            return

        for result in file_service.load_multi_sample_files(files):
            if isinstance(result, MultiSampleFileError):
                QMessageBox.warning(
                    self,
                    "Load Error",
                    f"Failed to load {result.path}:\n{result.message}",
                )
            else:
                name, frame = result
                self._add_to_dict_and_list(name, frame)

    def _add_to_dict_and_list(self, name, df):
        # Target names in MultiSampleDialog: Temperature, Seebeck, Sigma, Kappa_total
        SEARCH_GROUPS = [
            ("Temperature", ["temperature", "temp", "t"]),
            ("Seebeck", ["seebeck", "alpha", "α", "coeff", "coefficient", "s"]),
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
            processed_data = process_multi_sample_batch(checked_samples)

            # Surface scientific validation notices (for example a negative
            # lattice thermal conductivity) before the results are plotted or
            # exported. The computed values are not modified; the user is
            # told. Audit finding D-01.
            notices = validate_multi_sample_properties(processed_data)
            if notices:
                QMessageBox.warning(
                    self,
                    "Scientific validation warning",
                    validation_notices.format_detail(notices),
                )

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

        file_service = getattr(self, "table_file_service", None)
        if file_service is None:
            QMessageBox.critical(
                self,
                "Export Unavailable",
                "The application file service is not configured.",
            )
            return

        try:
            tables = [
                (name[:31], process_sample_data(df))
                for name, df in self.samples.items()
            ]
            file_service.save_workbook(tables, path)
            QMessageBox.information(
                self, "Success", f"Data exported successfully to {path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export Excel:\n{e}")
