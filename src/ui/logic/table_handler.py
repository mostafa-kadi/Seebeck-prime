import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QHeaderView, QTableWidgetItem, QMessageBox

# Shared column constants
from src.seebeck_prime.domain.constants import (
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
    ERROR_COLUMN_HEADERS,
    INPUT_COLUMNS_BASE,
)


def get_column_headers(error_mode=False):
    return ERROR_COLUMN_HEADERS if error_mode else COLUMN_HEADERS


def get_input_columns(error_mode=False):
    if not error_mode:
        return INPUT_COLUMNS_BASE
    # In error mode (without ±T): T=0, EC=1, S=3, K=7
    return [0, 1, 3, 7]


def setup_table_properties(app):
    """Sets visual and behavioral properties for the main table."""
    headers = get_column_headers(app.error_mode)
    app.table.setColumnCount(len(headers))
    app.table.setHorizontalHeaderLabels(headers)

    header = app.table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    # Use stretch for last section only if not too many columns
    header.setStretchLastSection(not app.error_mode)

    # Enable sorting (optional, can be messy with manual edits)
    app.table.setSortingEnabled(False)


def reset_and_create_new_sheet(app, rows=100):
    """Clears the table and creates a new empty sheet."""
    app.table.clearContents()
    app.table.setRowCount(rows)
    headers = get_column_headers(app.error_mode)
    # Initialize empty data frame
    app.data = pd.DataFrame(columns=headers, index=range(rows))
    # Fill with NaNs (or empty strings logic handled elsewhere)


def update_headers(app):
    """Update table headers to reflect current unit selections."""
    # This logic rebuilds headers based on current unit combos
    new_headers = list(app.HEADERS)

    # Map column logical names to the combo boxes holding their units
    # Note: Using hardcoded indices or a mapping is fine
    # Temperature (col 0)
    # Conductivity (col 1) -> combo is self.unit_combos['Electrical Conductivity']
    # Seebeck (col 2) -> self.unit_combos['Seebeck Coeff.']
    # Total k (col 4) -> self.unit_combos['Thermal Cond.']

    unit_map = {
        0: "Temperature",
        1: "Electrical Conductivity",
        2: "Seebeck Coeff.",
        4: "Thermal Cond.",
    }

    for col_idx, key in unit_map.items():
        if key in app.unit_combos:
            combo = app.unit_combos[key]
            if combo is not None:
                unit = combo.currentText()
                base_name = app.HEADERS[col_idx]
                # If standard header doesn't have unit syntax, just append
                new_headers[col_idx] = f"{base_name} ({unit})"

    app.table.setHorizontalHeaderLabels(new_headers)


def load_data_into_table(app, df: pd.DataFrame, is_base_units=False):
    """Populates the QTableWidget with data from a pandas DataFrame."""
    # 1. Update internal data storage (and ensure base units)
    if not is_base_units:
        app.data = app._convert_df_to_base_units(df)
    else:
        app.data = df

    # 2. Update UI (convert base -> display)
    headers = get_column_headers(app.error_mode)
    rows_needed = len(df)
    app.table.setRowCount(rows_needed + 50)  # Buffer
    app.table.clearContents()
    app.table.blockSignals(True)

    for r in range(rows_needed):
        for c, col_name in enumerate(headers):
            if col_name in app.data.columns:
                val = app.data.iloc[r, c]
                if pd.notna(val):
                    # We convert units for both main columns and error columns
                    # Error columns stay in the same unit as their parent main column

                    # Determine logical column index for unit conversion
                    if app.error_mode:
                        # Map indices to logical types:
                        # 0: T, 1: Sigma, 2: Sigma_err, 3: Seebeck, 4: Seebeck_err, 5: PF, 6: PF_err, ...
                        # Mapping: 0->0, 1->1, 2->1, 3->2, 4->2, 5->3, 6->3, 7->4, 8->4, ...
                        # Formula: if c==0: 0 else: (c+1)//2
                        logical_c = 0 if c == 0 else (c + 1) // 2
                    else:
                        logical_c = c

                    display_val = app._get_display_value(val, None, logical_c)
                    item = QTableWidgetItem(str(display_val))
                    app.table.setItem(r, c, item)

    app.table.blockSignals(False)


def _sync_df_from_table(app):
    """Reads the entire table into the self.data DataFrame in base units."""
    rows = app.table.rowCount()
    cols = app.table.columnCount()

    data_dict = {col: [] for col in app.HEADERS}

    for r in range(rows):
        for c, col_name in enumerate(app.HEADERS):
            item = app.table.item(r, c)
            val = None
            if item and item.text().strip():
                try:
                    display_val = float(item.text().strip())
                    # Apply unit conversion to both main and error columns
                    if app.error_mode:
                        logical_c = 0 if c == 0 else (c + 1) // 2
                    else:
                        logical_c = c

                    val, _ = app._convert_to_base_unit(display_val, None, logical_c)
                except ValueError:
                    val = None
            data_dict[col_name].append(val)

    app.data = pd.DataFrame(data_dict)


import re


def get_robust_mapped_dataframe(source_df: pd.DataFrame, search_groups):
    """
    Generic robust mapper that finds best-matching columns based on aliases.
    """
    source_cols = [c.lower().strip() for c in source_df.columns]
    used_indices = set()
    mapped_df = pd.DataFrame()

    for target, aliases in search_groups:
        sorted_aliases = sorted(aliases, key=len, reverse=True)
        found = False
        for alias in sorted_aliases:
            for idx, src_col in enumerate(source_cols):
                if idx in used_indices:
                    continue

                if len(alias) > 2:
                    if alias in src_col:
                        mapped_df[target] = source_df.iloc[:, idx]
                        found = True
                        used_indices.add(idx)
                        break
                else:
                    pattern = rf"\b{re.escape(alias)}\b"
                    if re.search(pattern, src_col):
                        if alias == "s" and (
                            re.search(r"s/[mc]", src_col) or "conductivity" in src_col
                        ):
                            continue
                        if alias == "k" and (
                            "temp" in src_col or src_col.endswith("(k)")
                        ):
                            continue
                        mapped_df[target] = source_df.iloc[:, idx]
                        found = True
                        used_indices.add(idx)
                        break
            if found:
                break
    return mapped_df


def _get_mapped_dataframe(app, source_df: pd.DataFrame):
    """
    Robustly maps source columns (from CSV/Excel) to the application's
    standard columns (Temperature, Seebeck, Conductivity, Thermal Cond).
    """
    # Target names in main application:
    # Temperature (0), Elec. Cond. (1), Seebeck (2), Thermal Cond. (4)
    SEARCH_GROUPS = [
        ("Temperature", ["temperature", "temp", "t"]),
        ("Seebeck Coeff.", ["seebeck", "alpha", "α", "coeff", "coefficient", "s"]),
        (
            "Electrical Conductivity",
            ["sigma", "conductivity", "electrical", "ec", "resistivity", "rho"],
        ),
        ("Thermal Cond.", ["kappa", "thermal", "k", "kappa_total"]),
    ]

    mapped_df = get_robust_mapped_dataframe(source_df, SEARCH_GROUPS)

    # Merge into standards structure (ensure all app.HEADERS exist)
    new_df = pd.DataFrame(columns=app.HEADERS)
    for col in mapped_df.columns:
        if col in new_df.columns:
            new_df[col] = mapped_df[col]

    return new_df


def on_paste_recalculate(app):
    """Slot to handle recalculation after a paste operation."""
    # Sync visual table -> internal DF
    _sync_df_from_table(app)

    # Run calcs (using the internal logic moved to app methods or new logic module)
    app.recalculate_all_properties()


def _convert_df_to_base_units(app, df: pd.DataFrame):
    """Converts an entire DataFrame from display units to base units."""
    # Assuming the DF comes in with values matching the CURRENT selection
    # We iterate and apply conversion
    new_df = df.copy()
    for col_idx, col_name in enumerate(app.HEADERS):
        if col_name in new_df.columns:
            # Vectorized convert would be nice, but _convert_to_base_unit is scalar
            # We can map it.
            new_df[col_name] = new_df[col_name].apply(
                lambda x: (
                    app._convert_to_base_unit(x, None, col_idx)[0] if pd.notna(x) else x
                )
            )
    return new_df


def interpolate_k_values(app, temps, k_values, unit="K", k_errs=None):
    """
    Interpolates thermal conductivity values and errors onto the main table's temperature points.
    """
    # 1. Get target temperatures from main table
    main_temps = []
    rows = app.table.rowCount()
    for r in range(rows):
        item = app.table.item(r, COL_TEMP)
        if item and item.text().strip():
            try:
                # We need the base unit (K) value.
                # Assuming the table display is updated but underlying data frame app.data is source of truth?
                # Actually, reading table item is "display" unit.
                # Safer: Read from app.data["Temperature"]
                val = app.data.at[r, "Temperature"]
                if not pd.isna(val):
                    main_temps.append((r, float(val)))
            except Exception:
                pass

    if not main_temps:
        QMessageBox.warning(
            app,
            "No Targets",
            "No temperature data found in the main sheet to interpolate onto.",
        )
        return

    # 2. Convert incoming data keys to Kelvin if needed
    normalized_temps = []
    for t in temps:
        if unit == "°C":
            normalized_temps.append(t + 273.15)
        else:
            normalized_temps.append(t)

    normalized_ks = k_values

    # Sort for interpolation
    sorted_indices = np.argsort(normalized_temps)
    x_sort = np.array(normalized_temps)[sorted_indices]
    y_sort = np.array(normalized_ks)[sorted_indices]

    y_err_sort = None
    if k_errs and len(k_errs) == len(temps):
        y_err_sort = np.array(k_errs)[sorted_indices]

    # 3. Interpolate
    app.table.blockSignals(True)
    for r_idx, t_kelvin in main_temps:
        k_new = np.interp(t_kelvin, x_sort, y_sort)
        app.data.at[r_idx, "Thermal Cond."] = k_new

        if y_err_sort is not None:
            k_err_new = np.interp(t_kelvin, x_sort, y_err_sort)
            # Store into "±u(κ)" column if it exists in data
            if "±u(κ)" in app.data.columns:
                app.data.at[r_idx, "±u(κ)"] = k_err_new

    # 4. Refresh Table
    load_data_into_table(app, app.data, is_base_units=True)
    app.table.blockSignals(False)
    app.recalculate_all_properties()
