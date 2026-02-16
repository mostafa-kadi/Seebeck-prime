import numpy as np
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


def get_table_data(table, y_col_index, error_mode=False):
    """Gathers data from the table for plotting, including errors if mode is active."""
    x_data = []
    y_data = []
    x_err = []
    y_err = []

    # Map logical indices to actual table column indices
    if error_mode:
        x_idx = 0  # Temperature is always 0 and single
        x_err_idx = -1
        # Data columns start at 1 and are paired: 1,2; 3,4; etc.
        # logical 1 -> actual 1, logical 2 -> actual 3...
        y_idx = y_col_index * 2 - 1 if y_col_index > 0 else 0
        y_err_idx = y_idx + 1 if y_col_index > 0 else -1
    else:
        x_idx = COL_TEMP
        x_err_idx = -1
        y_idx = y_col_index
        y_err_idx = -1

    for row in range(table.rowCount()):
        item_x = table.item(row, x_idx)
        item_y = table.item(row, y_idx)

        if item_x and item_y and item_x.text().strip() and item_y.text().strip():
            try:
                xv = float(item_x.text())
                yv = float(item_y.text())

                # Try getting errors
                xe = 0.0
                if x_err_idx != -1:
                    item_xe = table.item(row, x_err_idx)
                    if item_xe and item_xe.text().strip():
                        xe = float(item_xe.text())

                ye = 0.0
                if y_err_idx != -1:
                    item_ye = table.item(row, y_err_idx)
                    if item_ye and item_ye.text().strip():
                        ye = float(item_ye.text())

                x_data.append(xv)
                y_data.append(yv)
                x_err.append(xe)
                y_err.append(ye)
            except ValueError:
                continue

    if not x_data:
        return None, None, None, None

    # Sort data by X for proper line plotting
    # We zip all 4 to keep them aligned
    sorted_quads = sorted(zip(x_data, y_data, x_err, y_err))
    x_data, y_data, x_err, y_err = zip(*sorted_quads)

    return x_data, y_data, x_err, y_err


def create_plot(main_window, y_col_index):
    """Creates a plot of the specified column vs. Temperature."""
    x_data, y_data, x_err, y_err = get_table_data(
        main_window.table, y_col_index, main_window.error_mode
    )

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
        x_data, _, _, _ = get_table_data(main_window.table, col, main_window.error_mode)
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
            t_data, _, _, _ = get_table_data(
                main_window.table, COL_TEMP, main_window.error_mode
            )
            s_data, _, _, _ = get_table_data(
                main_window.table, COL_SEEBECK, main_window.error_mode
            )
            sigma_data, _, _, _ = get_table_data(
                main_window.table, COL_EC, main_window.error_mode
            )

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

        x_data, y_data, x_err, y_err = get_table_data(
            main_window.table, col_idx, main_window.error_mode
        )

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
