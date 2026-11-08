import os
import pandas as pd
from PyQt6.QtWidgets import QFileDialog, QMessageBox


def new_file(app):
    """Resets the application to a blank state."""
    app.reset_and_create_new_sheet()
    app.current_file_path = None
    app.setWindowTitle("ThermoElectric Analysis Pro v2.4 - New Project")


def open_file(app):
    """Opens a CSV or Excel file and loads it into the table."""
    file_path, _ = QFileDialog.getOpenFileName(
        app,
        "Open Data File",
        "",
        "Data Files (*.csv *.xlsx);;CSV (*.csv);;Excel (*.xlsx)",
    )
    if not file_path:
        return

    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Basic validation
        if df.empty:
            QMessageBox.warning(
                app, "File Empty", "The selected file contains no data."
            )
            return

        # Attempt to "smart map" columns just like pasting
        mapped_df = app._get_mapped_dataframe(df)

        # Convert to base units for internal storage if units were detected/assumed
        # (This logic might overlap with on_paste_recalculate, but let's trust _get_mapped returns raw values)
        # Actually, for file load, we usually assume the file has "Sheet Units" or "Base Units"?
        # For simplicity, we assume loaded data matches the CURRENT display units or are standard.
        # But _get_mapped_dataframe tries to normalize.

        app.load_data_into_table(mapped_df)

        # Update app state
        app.current_file_path = file_path
        app.setWindowTitle(
            f"ThermoElectric Analysis Pro v2.4 - {os.path.basename(file_path)}"
        )

        # Trigger recalculation (optional, but good practice)
        app.recalculate_all_properties()

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"DEBUG: Error opening file: {e}")
        QMessageBox.critical(app, "Error", f"Could not open file:\n{str(e)}")


def save_file(app):
    """Saves the current data to the open file, or verifies 'Save As'."""
    if app.current_file_path:
        _write_to_file(app, app.current_file_path)
    else:
        save_as_file(app)


def save_as_file(app):
    """Prompts for a path and saves the table data."""
    file_path, _ = QFileDialog.getSaveFileName(
        app, "Save Data As", "", "CSV Files (*.csv);;Excel Files (*.xlsx)"
    )
    if file_path:
        _write_to_file(app, file_path)
        app.current_file_path = file_path
        app.setWindowTitle(
            f"ThermoElectric Analysis Pro v2.4 - {os.path.basename(file_path)}"
        )


def _write_to_file(app, path):
    """Helper to write the current table data to disk."""
    app._sync_df_from_table()
    # Save the internal data (which is in base units).
    # OR save what's on screen? Typically users expect to save what they see or raw data.
    # The current implementation saves app.data (base units).
    # Let's adjust to save what the user sees if that was the legacy behavior,
    # but standards suggest saving raw/base is safer.
    # Based on legacy code: self.data.to_csv(...)

    try:
        if path.endswith(".csv"):
            app.data.to_csv(path, index=False)
        else:
            app.data.to_excel(path, index=False)

        app.statusBar().showMessage(f"Saved to {path}", 3000)
    except Exception as e:
        QMessageBox.critical(app, "Save Error", f"Could not save file:\n{str(e)}")
