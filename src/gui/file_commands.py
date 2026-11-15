"""Presentation commands for table-file workflows."""

from __future__ import annotations

import os

from PyQt6.QtWidgets import QFileDialog, QMessageBox


def new_file(app) -> None:
    app.reset_and_create_new_sheet()
    app.current_file_path = None
    app.setWindowTitle("ThermoElectric Analysis Pro v2.4 - New Project")


def open_file(app) -> None:
    file_path, _ = QFileDialog.getOpenFileName(
        app,
        "Open Data File",
        "",
        "Data Files (*.csv *.xlsx *.txt *.tsv);;CSV (*.csv);;Excel (*.xlsx);;Text Files (*.txt *.tsv)",
    )
    if not file_path:
        return

    try:
        df = app.table_file_service.load(file_path)
        if df.empty:
            QMessageBox.warning(app, "File Empty", "The selected file contains no data.")
            return

        mapped_df = app._get_mapped_dataframe(df)
        app.load_data_into_table(mapped_df)
        app.current_file_path = file_path
        app.setWindowTitle(
            f"ThermoElectric Analysis Pro v2.4 - {os.path.basename(file_path)}"
        )
        app.recalculate_all_properties()
    except Exception as exc:
        QMessageBox.critical(app, "Error", f"Could not open file:\n{exc}")


def save_file(app) -> None:
    if app.current_file_path:
        _write_to_file(app, app.current_file_path)
    else:
        save_as_file(app)


def save_as_file(app) -> None:
    file_path, _ = QFileDialog.getSaveFileName(
        app, "Save Data As", "", "CSV Files (*.csv);;Excel Files (*.xlsx);;Text Files (*.txt *.tsv)"
    )
    if not file_path:
        return

    if _write_to_file(app, file_path):
        app.current_file_path = file_path
        app.setWindowTitle(
            f"ThermoElectric Analysis Pro v2.4 - {os.path.basename(file_path)}"
        )


def _write_to_file(app, path: str) -> bool:
    app._sync_df_from_table()
    try:
        app.table_file_service.save(app.data, path)
        app.statusBar().showMessage(f"Saved to {path}", 3000)
        return True
    except Exception as exc:
        QMessageBox.critical(app, "Save Error", f"Could not save file:\n{exc}")
        return False
