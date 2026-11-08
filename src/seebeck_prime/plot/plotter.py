import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QMessageBox
from src.ui.widgets.plot_window import PlotWindow

from src.ui.logic.table_handler import (
    COL_TEMP,
    COL_EC,
    COL_SEEBECK,
    COL_PF,
    COL_K_TOTAL,
    COL_K_E,
    COL_K_L,
    COL_ZT,
)
import src.ui.logic.weighted_mobility_logic as wm_logic
import src.ui.logic.unit_converter as unit_converter

# Mapping from logical column index to (value_col_name, uncertainty_col_name)
_COL_MAP = {
    COL_TEMP: ("Temperature", None),
    COL_EC: ("Electrical Conductivity", "±σ"),
    COL_SEEBECK: ("Seebeck Coeff.", "±S"),
    COL_PF: ("Power Factor", "±PF"),
    COL_K_TOTAL: ("Thermal Cond.", "±κ"),
    COL_K_E: ("Electronic TC", "±κₑ"),
    COL_K_L: ("Lattice TC", "±κₗ"),
    COL_ZT: ("ZT", "±ZT"),
}


def get_table_data(main_window, y_col_index):
    """Gathers data from the main_window.data DataFrame for plotting, including errors if mode is active."""
    df = main_window.data
    error_mode = main_window.error_mode

    x_col_name = _COL_MAP[COL_TEMP][0]
    y_col_name, y_unc_col_name = _COL_MAP[y_col_index]

    if x_col_name not in df.columns or y_col_name not in df.columns:
        return None, None, None, None

    # Extract data
    x_data_raw = df[x_col_name]
    y_data_raw = df[y_col_name]
    x_err_raw = pd.Series([0.0] * len(df))  # Temperature usually has no uncertainty
    y_err_raw = (
        df[y_unc_col_name]
        if error_mode and y_unc_col_name and y_unc_col_name in df.columns
        else pd.Series([0.0] * len(df))
    )

    # Combine and filter out rows with NaN in x or y data
    combined_df = pd.DataFrame(
        {"x": x_data_raw, "y": y_data_raw, "x_err": x_err_raw, "y_err": y_err_raw}
    ).dropna(subset=["x", "y"])

    if combined_df.empty:
        return None, None, None, None

    # Sort by X data
    combined_df = combined_df.sort_values(by="x")

    x_data = combined_df["x"].tolist()
    y_data = combined_df["y"].tolist()
    x_err = combined_df["x_err"].tolist()
    y_err = combined_df["y_err"].tolist()

    return x_data, y_data, x_err, y_err


def create_plot(main_window, y_col_index):
    """Creates a plot of the specified column vs. Temperature."""
    x_data, y_data, x_err, y_err = get_table_data(main_window, y_col_index)

    if x_data is None:
        return

    # Get labels
    if main_window.error_mode:
        x_h_idx = 0
        h_idx = y_col_index * 2 - 1 if y_col_index > 0 else 0
    else:
        x_h_idx = COL_TEMP
        h_idx = y_col_index

    x_label = main_window.table.horizontalHeaderItem(x_h_idx).text().replace("\n", " ")
    y_label = main_window.table.horizontalHeaderItem(h_idx).text().replace("\n", " ")
    title = f"{y_label} vs. {x_label}"

    # Create and show the plot window
    plot_win = PlotWindow(main_window)

    # We pass the data in a trace-like structure to support error bars
    trace = {
        "x": x_data,
        "y": y_data,
        "xerr": x_err if any(x_err) else None,
        "yerr": y_err if any(y_err) else None,
        "label": y_label,
    }

    plot_win.subplots = [
        {"traces": [trace], "title": title, "xlabel": x_label, "ylabel": y_label}
    ]
    plot_win.draw_plot()

    main_window.plot_windows.append(plot_win)
    plot_win.show()


def plot_all_properties(main_window):
    """Plots all relevant properties vs Temperature."""
    properties_to_plot = [
        COL_SEEBECK,
        COL_EC,
        COL_PF,
        COL_K_TOTAL,
        COL_K_L,
        COL_K_E,
        COL_ZT,
    ]

    # Check if we have any data
    has_any_data = False
    for col in properties_to_plot:
        x_data, _, _, _ = get_table_data(main_window, col)
        if x_data:
            has_any_data = True
            create_plot(main_window, col)

    if not has_any_data:
        QMessageBox.warning(main_window, "No Data", "No valid data to plot.")


def plot_custom_layout(main_window, selection):
    """Plots selected properties in a custom grid layout."""
    selected_props = selection["selected_properties"]
    rows = selection["rows"]
    cols = selection["cols"]

    if not selected_props:
        return

    PROP_MAP = {
        "Seebeck Coeff.": COL_SEEBECK,
        "Electrical Conductivity": COL_EC,
        "Power Factor": COL_PF,
        "Thermal Cond.": COL_K_TOTAL,
        "Electronic TC": COL_K_E,
        "Lattice TC": COL_K_L,
        "ZT": COL_ZT,
        "Weighted Mobility": -1,  # Special flag
    }

    subplots_data = []
    x_label = main_window.table.horizontalHeaderItem(COL_TEMP).text().replace("\n", " ")

    for prop_name in selected_props:
        col_idx = PROP_MAP.get(prop_name)
        if col_idx is None:
            continue

        if prop_name == "Weighted Mobility":
            # Special handling for on-the-fly calculation
            t_data, _, _, _ = get_table_data(main_window, COL_TEMP)
            s_data, _, _, _ = get_table_data(main_window, COL_SEEBECK)
            sigma_data, _, _, _ = get_table_data(main_window, COL_EC)

            if t_data and s_data and sigma_data:
                # We need to ensure we have aligned data (get_table_data sorts by T, so if all rows present, should be fine)
                # But get_table_data skips rows with missing Y. If S or Sigma is missing but T is there...
                # This might be tricky if data is sparse.
                # Ideally we use main_window.data directly which is easier.

                try:
                    df = main_window.data.copy()
                    df = df.apply(pd.to_numeric, errors="coerce")

                    # Filter valid rows
                    mask = (
                        (df["Temperature"].notna())
                        & (df["Electrical Conductivity"].notna())
                        & (df["Seebeck Coeff."].notna())
                    )
                    valid_df = df[mask].sort_values("Temperature")

                    if not valid_df.empty:
                        # Base units are K, S/m, V/K
                        # Target for formula: K, mOhm.cm, absolute uV/K

                        T_K = valid_df["Temperature"].values
                        # Sigma S/m -> Rho mOhm.cm
                        # Rho (Ohm m) = 1 / Sigma (S/m)
                        # 1 Ohm m = 100,000 mOhm cm
                        Rho_mOhm_cm = 1e5 / valid_df["Electrical Conductivity"].values

                        # Seebeck V/K -> uV/K
                        S_uVK = valid_df["Seebeck Coeff."].values * 1e6

                        mu_w = wm_logic.calculate_weighted_mobility(
                            T_K, Rho_mOhm_cm, np.abs(S_uVK)
                        )

                        title = "Weighted Mobility vs. Temperature"
                        y_label = "Weighted Mobility (cm²/Vs)"

                        trace = {
                            "x": T_K.tolist(),
                            "y": mu_w.tolist(),
                            "xerr": None,
                            "yerr": None,
                            "label": y_label,
                        }

                        subplots_data.append(
                            {
                                "traces": [trace],
                                "title": title,
                                "xlabel": "Temperature (K)",
                                "ylabel": y_label,
                                "x": T_K.tolist(),
                                "y": mu_w.tolist(),
                            }
                        )
                        continue  # Done with this prop
                except Exception as e:
                    print(f"Error calculating Weighted Mobility for plot: {e}")

            continue  # Skip if failed or no data, or if it was Weighted Mobility handled above

        col_idx = PROP_MAP.get(prop_name)
        if col_idx is None or col_idx == -1:  # -1 Handled above already
            continue

        x_data, y_data, x_err, y_err = get_table_data(main_window, col_idx)

        if x_data:
            if main_window.error_mode:
                h_idx = col_idx * 2 - 1 if col_idx > 0 else 0
            else:
                h_idx = col_idx

            y_label = (
                main_window.table.horizontalHeaderItem(h_idx).text().replace("\n", " ")
            )
            title = f"{y_label} vs. {x_label}"

            trace = {
                "x": x_data,
                "y": y_data,
                "xerr": x_err if any(x_err) else None,
                "yerr": y_err if any(y_err) else None,
                "label": y_label,
            }

            subplots_data.append(
                {
                    "traces": [trace],
                    "title": title,
                    "xlabel": x_label,
                    "ylabel": y_label,
                    "x": x_data,  # For backward compat in export if needed
                    "y": y_data,
                }
            )

    if not subplots_data:
        QMessageBox.warning(main_window, "No Data", "No valid data to plot.")
        return

    plot_win = PlotWindow(main_window)
    plot_win.plot_multi(subplots_data, rows, cols)
    main_window.plot_windows.append(plot_win)
    plot_win.show()
